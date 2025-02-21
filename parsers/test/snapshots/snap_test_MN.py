# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_exchange 1"] = [
    {
        "datetime": "2024-02-17T06:00:00+08:00",
        "netFlow": 5.180265,
        "sortedZoneKeys": "CN->MN",
        "source": "https://ndc.energy.mn/",
        "sourceType": "measured",
    }
]

snapshots["test_production 1"] = [
    {
        "datetime": "2024-02-17T06:00:00+08:00",
        "production": {"solar": 24.88, "unknown": 959.3, "wind": 65.4},
        "source": "https://ndc.energy.mn/",
        "sourceType": "measured",
        "zoneKey": "MN",
    }
]
