import logging
import unittest
from datetime import datetime, timezone

import freezegun
from mock import patch

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.constants import PRODUCTION_MODES, STORAGE_MODES
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    Exchange,
    Price,
    ProductionBreakdown,
    ProductionMix,
    StorageMix,
    TotalConsumption,
    TotalProduction,
)


class TestExchange(unittest.TestCase):
    def test_create_exchange(self):
        exchange = Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        assert exchange.zoneKey == ZoneKey("AT->DE")
        assert exchange.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert exchange.netFlow == 1
        assert exchange.source == "trust.me"

        exchange = Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=-1,
            source="trust.me",
        )
        assert exchange.netFlow == -1

    def test_raises_if_invalid_exchange(self):
        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("AT->DE"),
                datetime=datetime(2023, 1, 1),
                netFlow=1,
                source="trust.me",
            )

        # This should raise a ValueError because the zoneKey is not an Exchange
        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                netFlow=1,
                source="trust.me",
            )

        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("AT-DE"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                netFlow=1,
                source="trust.me",
            )

        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("UNKNOWN->UNKNOWN"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                netFlow=1,
                source="trust.me",
            )

        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("DE->AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                netFlow=1,
                source="trust.me",
            )

    def test_static_create_logs_error(self):
        logger = logging.Logger("test")
        with patch.object(logger, "error") as mock_error:
            Exchange.create(
                logger=logger,
                zoneKey=ZoneKey("DER->FR"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                netFlow=-1,
                source="trust.me",
            )
            mock_error.assert_called_once()


class TestConsumption(unittest.TestCase):
    def test_create_consumption(self):
        consumption = TotalConsumption(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        assert consumption.zoneKey == ZoneKey("DE")
        assert consumption.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert consumption.consumption == 1
        assert consumption.source == "trust.me"

    def test_raises_if_invalid_consumption(self):
        with self.assertRaises(ValueError):
            TotalConsumption(
                zoneKey=ZoneKey("ATT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=1,
                source="trust.me",
            )
        with self.assertRaises(ValueError):
            TotalConsumption(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1),
                consumption=1,
                source="trust.me",
            )
        with self.assertRaises(ValueError):
            TotalConsumption(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=-1,
                source="trust.me",
            )

    def test_static_create_logs_error(self):
        logger = logging.Logger("test")
        with patch.object(logger, "error") as mock_error:
            TotalConsumption.create(
                logger=logger,
                zoneKey=ZoneKey("DE"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=-1,
                source="trust.me",
            )
            mock_error.assert_called_once()


class TestPrice(unittest.TestCase):
    def test_create_price(self):
        price = Price(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=1,
            source="trust.me",
            currency="EUR",
        )
        assert price.zoneKey == ZoneKey("DE")
        assert price.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert price.price == 1
        assert price.source == "trust.me"
        assert price.currency == "EUR"

    def test_invalid_price_raises(self):
        with self.assertRaises(ValueError):
            Price(
                zoneKey=ZoneKey("ATT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                price=1,
                source="trust.me",
                currency="EUR",
            )
        with self.assertRaises(ValueError):
            Price(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1),
                price=1,
                source="trust.me",
                currency="EUR",
            )
        with self.assertRaises(ValueError):
            Price(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                price=1,
                source="trust.me",
                currency="EURO",
            )


class TestProductionBreakdown(unittest.TestCase):
    def test_create_production_breakdown(self):
        mix = ProductionMix(wind=10)
        breakdown = ProductionBreakdown(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=mix,
            source="trust.me",
        )
        assert breakdown.zoneKey == ZoneKey("DE")
        assert breakdown.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert breakdown.production.wind == 10
        assert breakdown.source == "trust.me"

    def test_create_production_breakdown_with_storage(self):
        mix = ProductionMix(
            wind=10,
            hydro=20,
        )
        storage = StorageMix(
            hydro=10,
        )
        breakdown = ProductionBreakdown(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=mix,
            storage=storage,
            source="trust.me",
        )
        assert breakdown.production.hydro == 20
        assert breakdown.storage.hydro == 10

    def test_invalid_breakdown_raises(self):
        mix = ProductionMix(
            wind=10,
            hydro=20,
        )
        storage = StorageMix(
            hydro=10,
        )
        with self.assertRaises(ValueError):
            ProductionBreakdown(
                zoneKey=ZoneKey("ATT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                production=mix,
                source="trust.me",
            )
        with self.assertRaises(ValueError):
            ProductionBreakdown(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1),
                production=mix,
                source="trust.me",
            )
        with self.assertRaises(ValueError):
            ProductionBreakdown(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                production=ProductionMix(wind=None),
                storage=storage,
                source="trust.me",
            )

    def test_negative_production_gets_corrected(self):
        mix = ProductionMix(
            wind=10,
            hydro=-20,
        )
        logger = logging.Logger("test")
        with patch.object(logger, "warning") as mock_warning:
            breakdown = ProductionBreakdown.create(
                logger=logger,
                zoneKey=ZoneKey("DE"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                production=mix,
                source="trust.me",
            )
            mock_warning.assert_called_once()
            assert breakdown.production.hydro == None
            assert breakdown.production.wind == 10

    @freezegun.freeze_time("2023-01-01")
    def test_forecasted_points(self):
        mix = ProductionMix(wind=10)
        breakdown = ProductionBreakdown(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 2, 1, tzinfo=timezone.utc),
            production=mix,
            source="trust.me",
            sourceType=EventSourceType.forecasted,
        )
        assert breakdown.zoneKey == ZoneKey("DE")
        assert breakdown.datetime == datetime(2023, 2, 1, tzinfo=timezone.utc)
        assert breakdown.production.wind == 10
        assert breakdown.source == "trust.me"
        assert breakdown.sourceType == EventSourceType.forecasted

    @freezegun.freeze_time("2023-01-01")
    def test_non_forecasted_points_in_future(self):
        mix = ProductionMix(wind=10)
        with self.assertRaises(ValueError):
            breakdown = ProductionBreakdown(
                zoneKey=ZoneKey("DE"),
                datetime=datetime(2023, 3, 1, tzinfo=timezone.utc),
                production=mix,
                source="trust.me",
            )

    def test_static_create_logs_error(self):
        logger = logging.Logger("test")
        with patch.object(logger, "error") as mock_error:
            ProductionBreakdown.create(
                logger=logger,
                zoneKey=ZoneKey("DE"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                production=ProductionMix(wind=None),
                source="trust.me",
            )
            mock_error.assert_called_once()


class TestTotalProduction(unittest.TestCase):
    def test_create_generation(self):
        generation = TotalProduction(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            source="trust.me",
            value=1,
        )
        assert generation.zoneKey == ZoneKey("DE")
        assert generation.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert generation.source == "trust.me"
        assert generation.value == 1

    def test_static_create_logs_error(self):
        logger = logging.Logger("test")
        with patch.object(logger, "error") as mock_error:
            TotalProduction.create(
                logger=logger,
                zoneKey=ZoneKey("DE"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                value=-1,
                source="trust.me",
            )
            mock_error.assert_called_once()


class TestMixes(unittest.TestCase):
    def test_production_mix_has_all_production_modes(self):
        mix = ProductionMix()
        for mode in PRODUCTION_MODES:
            assert hasattr(mix, mode)

    def test_storage_mix_has_all_storage_modes(self):
        mix = StorageMix()
        for mode in STORAGE_MODES:
            assert hasattr(mix, mode)
