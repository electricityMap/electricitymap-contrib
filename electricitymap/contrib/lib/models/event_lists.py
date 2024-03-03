from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from logging import Logger
from typing import Any

import pandas as pd

from electricitymap.contrib.config import ZONES_CONFIG
from electricitymap.contrib.config.capacity import get_capacity_data
from electricitymap.contrib.lib.models.events import (
    Event,
    EventSourceType,
    Exchange,
    Price,
    ProductionBreakdown,
    ProductionMix,
    StorageMix,
    TotalConsumption,
    TotalProduction,
)
from electricitymap.contrib.lib.types import ZoneKey

CAPACITY_STRICT_THRESHOLD = 0
CAPACITY_LOOSE_THRESHOLD = 0.02


class EventList(ABC):
    """A wrapper around Events lists."""

    logger: Logger
    events: dict[datetime, Event]

    def __init__(self, logger: Logger):
        self.events = {}
        self.logger = logger

    def __len__(self):
        return len(self.events)

    def __contains__(self, event: Event):
        return event.datetime in self.events

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def __getitem__(self, datetime):
        pass

    @abstractmethod
    def __setitem__(self, datetime, event: Event):
        pass

    @abstractmethod
    def _append_event(self, event: Event):
        """Appends an event to the list."""
        if event.datetime in self.events:
            self.logger.warning(
                f"Event at {event.datetime} already exists in the list, discarding event.",
                extra={"event": event.to_dict()},
            )
            return
        self.events.update({event.datetime: event})

    @abstractmethod
    def append(self, **kwargs):
        """Handles creation of events and adding it to the batch."""
        # TODO Handle one day the creation of mixed batches.
        pass

    def to_list(self) -> list[dict[str, Any]]:
        """Gives a sorted list representation of the events."""
        return sorted(
            [event.to_dict() for event in self.events.values()],
            key=lambda x: x["datetime"],
        )

    @property
    def dataframe(self) -> pd.DataFrame:
        """Gives the dataframe representation of the events, indexed by datetime."""
        if len(self.events) > 0:
            return pd.DataFrame.from_records(
                [
                    {
                        "datetime": event.datetime,
                        "zoneKey": event.zoneKey,
                        "source": event.source,
                        "sourceType": event.sourceType,
                        "data": event,
                    }
                    for event in self.events.values()
                ]
            ).set_index("datetime")
        else:
            return pd.DataFrame()


class AggregatableEventList(EventList, ABC):
    """An abstract class to supercharge event lists with aggregation capabilities."""

    @classmethod
    def is_completely_empty(
        cls, ungrouped_events: Sequence["AggregatableEventList"], logger: Logger
    ) -> bool:
        """Checks if the lists to be merged have any data."""
        if len(ungrouped_events) == 0:
            return True
        if all(len(event_list.events) == 0 for event_list in ungrouped_events):
            logger.warning(f"All {cls.__name__} are empty.")
            return True
        return False

    @classmethod
    def get_zone_source_type(
        cls,
        events: pd.DataFrame,
    ) -> tuple[ZoneKey, str, EventSourceType]:
        """
        Given a concatenated dataframe of events, return the unique zone, the aggregated sources and the unique source type.
        Raises an error if there are multiple zones or source types.
        It assumes that zoneKey, source and sourceType are present in the dataframe's columns.
        """
        return (
            AggregatableEventList._get_unique_zone(events),
            AggregatableEventList._get_aggregated_sources(events),
            AggregatableEventList._get_unique_source_type(events),
        )

    @classmethod
    def _get_unique_zone(cls, events: pd.DataFrame) -> ZoneKey:
        """
        Given a concatenated dataframe of events, return the unique zone.
        Raises an error if there are multiple zones.
        It assumes that `zoneKey` is present in the dataframe's columns.
        """
        zones = events["zoneKey"].unique()
        if len(zones) != 1:
            raise ValueError(
                f"Trying to merge {cls.__name__} from multiple zones \
                , got {len(zones)}: {', '.join(zones)}"
            )
        return zones[0]

    @classmethod
    def _get_aggregated_sources(cls, events: pd.DataFrame) -> str:
        """
        Given a concatenated dataframe of events, return the aggregated sources.
        It assumes that `source` is present in the dataframe's columns.
        """
        sources = events["source"].unique()
        sources = ", ".join(sources)
        return sources

    @classmethod
    def _get_unique_source_type(cls, events: pd.DataFrame) -> EventSourceType:
        """
        Given a concatenated dataframe of events, return the unique source type.
        Raises an error if there are multiple source types.
        It assumes that `sourceType` is present in the dataframe's columns.
        """
        source_types = events["sourceType"].unique()
        if len(source_types) != 1:
            raise ValueError(
                f"Trying to merge {cls.__name__} from multiple source types \
                , got {len(source_types)}: {', '.join(source_types)}"
            )
        return source_types[0]


class ExchangeList(AggregatableEventList):
    events: dict[datetime, Exchange]

    def __iter__(self):
        return iter(self.events.values())

    def __getitem__(self, event: Exchange):
        return self.events[event.datetime]

    def __setitem__(self, event: Exchange, value: Exchange):
        self.events[event.datetime] = value

    def _append_event(self, event: Exchange):
        return super()._append_event(event)

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        netFlow: float | None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = Exchange.create(
            self.logger, zoneKey, datetime, source, netFlow, sourceType
        )
        if event:
            self._append_event(event)

    @staticmethod
    def merge_exchanges(
        ungrouped_exchanges: list["ExchangeList"], logger: Logger
    ) -> "ExchangeList":
        """
        Given multiple parser outputs, sum the netflows of corresponding datetimes
        to create a unique exchange list. Sources will be aggregated in a
        comma-separated string. Ex: "entsoe, eia".
        """
        exchanges = ExchangeList(logger)
        if ExchangeList.is_completely_empty(ungrouped_exchanges, logger):
            return exchanges

        # Create a dataframe for each parser output, then flatten the exchanges.
        exchange_dfs = [
            pd.json_normalize(exchanges.to_list()).set_index("datetime")
            for exchanges in ungrouped_exchanges
            if len(exchanges.events) > 0
        ]

        exchange_df = pd.concat(exchange_dfs)
        exchange_df = exchange_df.rename(columns={"sortedZoneKeys": "zoneKey"})
        zone_key, sources, source_type = ExchangeList.get_zone_source_type(exchange_df)
        exchange_df = exchange_df.groupby(level="datetime", dropna=False).sum(
            numeric_only=True
        )
        for dt, row in exchange_df.iterrows():
            exchanges.append(
                zone_key, dt.to_pydatetime(), sources, row["netFlow"], source_type
            )  # type: ignore

        return exchanges

    @staticmethod
    def update_exchanges(
        exchanges: "ExchangeList", new_exchanges: "ExchangeList", logger: Logger
    ) -> "ExchangeList":
        """Given a new batch of exchanges, update the existing ones."""
        if len(new_exchanges) == 0:
            return exchanges
        elif len(exchanges) == 0:
            return new_exchanges

        for new_event in new_exchanges:
            if new_event in exchanges:
                existing_event = exchanges[new_event]
                updated_event = Exchange.update(existing_event, new_event)
                exchanges[new_event] = updated_event
            else:
                exchanges._append_event(new_event)

        return exchanges


class ProductionBreakdownList(AggregatableEventList):
    events: dict[datetime, ProductionBreakdown]

    def __iter__(self):
        return iter(self.events.values())

    def __getitem__(self, event: ProductionBreakdown):
        return self.events[event.datetime]

    def __setitem__(self, event: ProductionBreakdown, value: ProductionBreakdown):
        self.events[event.datetime] = value

    def _append_event(self, event: ProductionBreakdown):
        return super()._append_event(event)

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        production: ProductionMix | None = None,
        storage: StorageMix | None = None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = ProductionBreakdown.create(
            self.logger, zoneKey, datetime, source, production, storage, sourceType
        )
        if event:
            self._append_event(event)

    @staticmethod
    def merge_production_breakdowns(
        ungrouped_production_breakdowns: list["ProductionBreakdownList"],
        logger: Logger,
        matching_timestamps_only: bool = False,
    ) -> "ProductionBreakdownList":
        """
        Given multiple parser outputs, sum the production and storage
        of corresponding datetimes to create a unique production breakdown list.
        Sources will be aggregated in a comma-separated string. Ex: "entsoe, eia".
        There should be only one zone in the list of production breakdowns.
        Matching timestamps only will only keep the timestamps where all the production breakdowns have data.
        """
        production_breakdowns = ProductionBreakdownList(logger)
        if ProductionBreakdownList.is_completely_empty(
            ungrouped_production_breakdowns, logger
        ):
            return production_breakdowns
        len_ungrouped_production_breakdowns = len(ungrouped_production_breakdowns)
        df = pd.concat(
            [
                production_breakdowns.dataframe
                for production_breakdowns in ungrouped_production_breakdowns
                if len(production_breakdowns.events) > 0
            ]
        )
        _, _, _ = ProductionBreakdownList.get_zone_source_type(df)

        df = df.drop(columns=["source", "sourceType", "zoneKey"])
        df = df.groupby(level=0, dropna=False)["data"].apply(list)
        if matching_timestamps_only:
            logger.info(
                f"Filtering production breakdowns to keep \
                only the timestamps where all the production breakdowns \
                have data, {len(df[df.apply(lambda x: len(x) != len_ungrouped_production_breakdowns)])}\
                points where discarded."
            )
            df = df[df.apply(lambda x: len(x) == len_ungrouped_production_breakdowns)]
        for row in df:
            prod = ProductionBreakdown.aggregate(row)
            production_breakdowns.events[prod.datetime] = prod
        return production_breakdowns

    @staticmethod
    def update_production_breakdowns(
        production_breakdowns: "ProductionBreakdownList",
        new_production_breakdowns: "ProductionBreakdownList",
        logger: Logger,
    ) -> "ProductionBreakdownList":
        """Given a new batch of production breakdowns, update the existing ones."""
        if len(new_production_breakdowns) == 0:
            return production_breakdowns
        elif len(production_breakdowns) == 0:
            return new_production_breakdowns

        for new_event in new_production_breakdowns:
            if new_event in production_breakdowns:
                existing_event = production_breakdowns[new_event]
                updated_event = ProductionBreakdown.update(existing_event, new_event)
                production_breakdowns[new_event] = updated_event
            else:
                production_breakdowns._append_event(new_event)

        return production_breakdowns

    @staticmethod
    def filter_expected_modes(
        breakdowns: "ProductionBreakdownList",
        strict_storage: bool = False,
        strict_capacity: bool = False,
        by_passed_modes: list[str] | None = None,
    ) -> "ProductionBreakdownList":
        """A temporary method to filter out incomplete production breakdowns which are missing expected modes.
        This method is only to be used on zones for which we know the expected modes and that the source sometimes returns Nones.
        TODO: Remove this method once the outlier detection is able to handle it.
        """

        if by_passed_modes is None:
            by_passed_modes = []

        def select_capacity(capacity_value: float, total_capacity: float) -> bool:
            if strict_capacity:
                return capacity_value > CAPACITY_STRICT_THRESHOLD
            return capacity_value / total_capacity > CAPACITY_LOOSE_THRESHOLD

        events = ProductionBreakdownList(breakdowns.logger)
        for event in breakdowns.events.values():
            capacity_config = ZONES_CONFIG.get(event.zoneKey, {}).get("capacity", {})
            capacity = get_capacity_data(capacity_config, event.datetime)
            total_capacity = sum(capacity.values())
            valid = True
            required_modes = [
                mode
                for mode, capacity_value in capacity.items()
                if select_capacity(capacity_value, total_capacity)
            ]
            required_modes = list(set(required_modes))
            if not strict_storage:
                required_modes = [
                    mode for mode in required_modes if "storage" not in mode
                ]
            required_modes = [
                mode for mode in required_modes if mode not in by_passed_modes
            ]
            for mode in required_modes:
                value = event.get_value(mode)
                if (
                    value is None
                    and mode not in event.production.corrected_negative_modes
                ):
                    valid = False
                    events.logger.warning(
                        f"Discarded production event for {event.zoneKey} at {event.datetime} due to missing {mode} value."
                    )
                    break
            if valid:
                events.append(
                    zoneKey=event.zoneKey,
                    datetime=event.datetime,
                    production=event.production,
                    storage=event.storage,
                    source=event.source,
                )
        return events


class TotalProductionList(EventList):
    events: dict[datetime, TotalProduction]

    def __iter__(self):
        return iter(self.events.values())

    def __getitem__(self, datetime):
        return self.events[datetime]

    def __setitem__(self, datetime, event: Event):
        return super().__setitem__(datetime, event)

    def _append_event(self, event: TotalProduction):
        return super()._append_event(event)

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        value: float | None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = TotalProduction.create(
            self.logger, zoneKey, datetime, source, value, sourceType
        )
        if event:
            self._append_event(event)


class TotalConsumptionList(EventList):
    events: dict[datetime, TotalConsumption]

    def __iter__(self):
        return iter(self.events.values())

    def __getitem__(self, datetime):
        return self.events[datetime]

    def __setitem__(self, datetime, event: TotalConsumption):
        self.events[datetime] = event

    def _append_event(self, event: TotalConsumption):
        return super()._append_event(event)

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        consumption: float | None,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = TotalConsumption.create(
            self.logger, zoneKey, datetime, source, consumption, sourceType
        )
        if event:
            self._append_event(event)


class PriceList(EventList):
    events: dict[datetime, Price]

    def __iter__(self):
        return iter(self.events.values())

    def __getitem__(self, datetime):
        return self.events[datetime]

    def __setitem__(self, datetime, event: Price):
        self.events[datetime] = event

    def _append_event(self, event: Price):
        return super()._append_event(event)

    def append(
        self,
        zoneKey: ZoneKey,
        datetime: datetime,
        source: str,
        price: float | None,
        currency: str,
        sourceType: EventSourceType = EventSourceType.measured,
    ):
        event = Price.create(
            self.logger, zoneKey, datetime, source, price, currency, sourceType
        )
        if event:
            self._append_event(event)
