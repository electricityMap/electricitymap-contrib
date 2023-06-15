import datetime as dt
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from logging import Logger
from typing import AbstractSet, Any, Dict, Optional, Union

from pydantic import BaseModel, PrivateAttr, ValidationError, validator

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG
from electricitymap.contrib.config.constants import PRODUCTION_MODES, STORAGE_MODES
from electricitymap.contrib.lib.models.constants import VALID_CURRENCIES
from electricitymap.contrib.lib.types import ZoneKey

LOWER_DATETIME_BOUND = datetime(2000, 1, 1, tzinfo=timezone.utc)


class Mix(BaseModel, ABC):
    def set_value(self, mode: str, value: Optional[float]) -> None:
        """
        Sets the value of a production mode.
        This can be used if the Production has been initialized empty
        and is being filled in a loop.
        """
        self.__setattr__(mode, value)


class ProductionMix(Mix):
    """
    Contains the production mix for a zone at a given time.
    All values should be positives, otherwise they will be set to None
    and a warning will be logged.
    All values are in MW.
    """

    # We use a private attribute to keep track of the modes that have been set to None.
    _corrected_negative_values: set = PrivateAttr(set())
    biomass: Optional[float] = None
    coal: Optional[float] = None
    gas: Optional[float] = None
    geothermal: Optional[float] = None
    hydro: Optional[float] = None
    nuclear: Optional[float] = None
    oil: Optional[float] = None
    solar: Optional[float] = None
    unknown: Optional[float] = None
    wind: Optional[float] = None

    def __init__(self, **data: Any):
        """
        Overriding the constructor to check for negative values and set them to None.
        This method also keeps track of the modes that have been corrected.
        Note: This method does NOT allow to set negative values to zero for self consumption.
        As we want self consumption to be set to zero, on a fine grained level with the set_value method.
        """
        super().__init__(**data)
        for attr, value in data.items():
            if value is not None and value < 0:
                self._corrected_negative_values.add(attr)
                self.__setattr__(attr, None)

    def dict(
        self,
        *,
        include: Optional[Union[set, dict]] = None,
        exclude: Optional[Union[set, dict]] = None,
        by_alias: bool = False,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        keep_corrected_negative_values: bool = False,
    ) -> Dict[str, Any]:
        """Overriding the dict method to add the corrected negative values as Nones."""
        production_mix = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        if keep_corrected_negative_values:
            for corrected_negative_mode in self._corrected_negative_values:
                if corrected_negative_mode not in production_mix:
                    production_mix[corrected_negative_mode] = None
        return production_mix

    def __setattr__(
        self,
        name: str,
        value: Optional[float],
    ) -> None:
        """
        Overriding the setattr method to check for negative values and set them to None.
        This method also keeps track of the modes that have been corrected.
        """
        if not name in PRODUCTION_MODES:
            raise ValueError(f"Unknown production mode: {name}")
        if value is not None and value < 0:
            self._corrected_negative_values.add(name)
            value = None
        return super().__setattr__(name, value)

    def set_value(
        self,
        mode: str,
        value: Optional[float],
        correct_negative_with_zero: bool = False,
    ) -> None:
        """
        Set the value of a production mode. Negative values are set to None by default.
        If correct_negative_with_zero is set to True, negative values will be set to 0 instead of None.
        This method keeps track of values that have been corrected.
        """
        if correct_negative_with_zero and value is not None and value < 0:
            value = 0
            self._corrected_negative_values.add(mode)
        self.__setattr__(mode, value)

    @property
    def has_corrected_negative_values(self) -> bool:
        return len(self._corrected_negative_values) > 0

    @property
    def corrected_negative_modes(self) -> AbstractSet[str]:
        return self._corrected_negative_values


class StorageMix(Mix):
    """
    Contains the storage mix for a zone at a given time.
    All values are in MW.
    Values can be both positive (when storing energy) or negative (when the storage is discharged).
    """

    battery: Optional[float] = None
    hydro: Optional[float] = None

    def __setattr__(self, name: str, value: Optional[float]) -> None:
        """
        Overriding the setattr method to raise an error if the mode is unknown.
        """
        if not name in STORAGE_MODES:
            raise ValueError(f"Unknown storage mode: {name}")
        return super().__setattr__(name, value)


class EventSourceType(str, Enum):
    measured = "measured"
    forecasted = "forecasted"
    estimated = "estimated"


class Event(BaseModel, ABC):
    """
    An abstract class representing all types of electricity events that can occur in a zone.
    sourceType: How was the event observed.
    Should be set to forecasted if the point is a forecast provided by a datasource.
    Should be set to estimated if the point is an estimate or data that has not been consolidated yet by the datasource.
    zoneKey: The zone key of the zone the event is happening in.
    datetime: The datetime of the event.
    source: The source of the event.
    We currently use the root url of the datasource. Ex: edf.fr
    """

    # The order of the attributes matters for the validation.
    # As the validators are called in the order of the attributes, we need to make sure that the sourceType is validated before the datetime.
    sourceType: EventSourceType = EventSourceType.measured
    zoneKey: ZoneKey
    datetime: datetime
    source: str

    @validator("zoneKey")
    def _validate_zone_key(cls, v):
        if v not in ZONES_CONFIG:
            raise ValueError(f"Unknown zone: {v}")
        return v

    @validator("datetime")
    def _validate_datetime(cls, v: dt.datetime, values: Dict[str, Any]):
        if v.tzinfo is None:
            raise ValueError(f"Missing timezone: {v}")
        if v < LOWER_DATETIME_BOUND:
            raise ValueError(f"Date is before 2000, this is not plausible: {v}")
        if values.get(
            "sourceType", EventSourceType.measured
        ) != EventSourceType.forecasted and v.astimezone(timezone.utc) > datetime.now(
            timezone.utc
        ) + timedelta(
            days=1
        ):
            raise ValueError(
                f"Date is in the future and this is not a forecasted point: {v}"
            )
        return v

    @staticmethod
    @abstractmethod
    def create(*args, **kwargs) -> "Event":
        """To avoid having one Event failure crashing the whole parser, we use a factory method to create the Event."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """As part of a backwards compatibility, the points will be converted to a dict before being sent to the database."""
        pass


class Exchange(Event):
    """
    An event class representing the net exchange between two zones.
    netFlow: The net flow of electricity between the two zones.
    It should be positive if the zoneKey on the left of the arrow is exporting electricity to the zoneKey on the right of the arrow.
    Negative otherwise.
    """

    netFlow: float

    @validator("zoneKey")
    def _validate_zone_key(cls, v: str):
        if "->" not in v:
            raise ValueError(f"Not an exchange key: {v}")
        zone_keys = v.split("->")
        if zone_keys != sorted(zone_keys):
            raise ValueError(f"Exchange key not sorted: {v}")
        if v not in EXCHANGES_CONFIG:
            raise ValueError(f"Unknown zone: {v}")
        return v

    @validator("netFlow")
    def _validate_value(cls, v: float):
        # TODO in the future those checks should be performed in the data quality layer.
        if abs(v) > 100000:
            raise ValueError(f"Exchange is implausibly high, above 100GW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        netFlow: float,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> Optional["Exchange"]:
        try:
            return Exchange(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                netFlow=netFlow,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(f"Error(s) creating exchange Event {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "sortedZoneKeys": self.zoneKey,
            "netFlow": self.netFlow,
            "source": self.source,
            "sourceType": self.sourceType,
        }


class TotalProduction(Event):
    """Represents the total production of a zone at a given time. The value is in MW."""

    value: float

    @validator("value")
    def _validate_value(cls, v: float):
        if v < 0:
            raise ValueError(f"Total production cannot be negative: {v}")
        # TODO in the future those checks should be performed in the data quality layer.
        if v > 500000:
            raise ValueError(f"Total production is implausibly high, above 500GW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> Optional["TotalProduction"]:
        try:
            return TotalProduction(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                value=value,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(f"Error(s) creating total production Event {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "generation": self.value,
            "source": self.source,
            "sourceType": self.sourceType,
        }


class ProductionBreakdown(Event):
    production: Optional[ProductionMix] = None
    storage: Optional[StorageMix] = None
    """
    An event representing the production and storage breakdown of a zone at a given time.
    If a production mix is supplied it should not be fully empty.
    """

    @validator("production")
    def _validate_production_mix(cls, v):
        if v is not None and not v.has_corrected_negative_values:
            if all(value is None for value in v.dict().values()):
                raise ValueError("Mix is completely empty")
        return v

    @validator("storage")
    def _validate_storage_mix(cls, v):
        if v is not None:
            if all(value is None for value in v.dict().values()):
                return None
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        production: Optional[ProductionMix] = None,
        storage: Optional[StorageMix] = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> Optional["ProductionBreakdown"]:
        try:
            # Log warning if production has been corrected.
            if production is not None and production.has_corrected_negative_values:
                logger.warning(
                    f"Negative production values were detected: {production._corrected_negative_values}.\
                    They have been set to None."
                )
            return ProductionBreakdown(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                production=production,
                storage=storage,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating production breakdown Event {datetime}: {e}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "production": self.production.dict(
                exclude_none=True, keep_corrected_negative_values=True
            )
            if self.production
            else {},
            "storage": self.storage.dict(exclude_none=True) if self.storage else {},
            "source": self.source,
            "sourceType": self.sourceType,
        }


class TotalConsumption(Event):
    """Reprensent the total consumption of a zone. The total consumption is expressed in MW."""

    consumption: float

    @validator("consumption")
    def _validate_consumption(cls, v: float):
        if v < 0:
            raise ValueError(f"Total consumption cannot be negative: {v}")
        # TODO in the future those checks should be performed in the data quality layer.
        if v > 500000:
            raise ValueError(f"Total consumption is implausibly high, above 500GW: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> Optional["TotalConsumption"]:
        try:
            return TotalConsumption(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                consumption=consumption,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(
                f"Error(s) creating total consumption Event {datetime}: {e}",
                extra={
                    "zoneKey": zoneKey,
                    "datetime": datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "kind": "consumption",
                },
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "consumption": self.consumption,
            "source": self.source,
            "sourceType": self.sourceType,
        }


class Price(Event):
    price: float
    currency: str

    @validator("currency")
    def _validate_currency(cls, v: str):
        if v not in VALID_CURRENCIES:
            raise ValueError(f"Unknown currency: {v}")
        return v

    @staticmethod
    def create(
        logger: Logger,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float,
        currency: str,
        sourceType: EventSourceType = EventSourceType.measured,
    ) -> Optional["Price"]:
        try:
            return Price(
                zoneKey=zoneKey,
                datetime=datetime,
                source=source,
                price=price,
                currency=currency,
                sourceType=sourceType,
            )
        except ValidationError as e:
            logger.error(f"Error(s) creating price Event {datetime}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datetime": self.datetime,
            "zoneKey": self.zoneKey,
            "currency": self.currency,
            "price": self.price,
            "source": self.source,
            "sourceType": self.sourceType,
        }
