import pytest
from pytest_httpx import HTTPXMock
from src.citybikes_client import fetch_network_snapshot

FAKE_RESPONSE = {
    "network": {
        "stations": [
            {
                "id": "abc123",
                "name": "Test Station",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "timestamp": "2026-03-17T12:00:00+00:00",
                "free_bikes": 5,
                "empty_slots": 10,
                "extra": {
                    "uid": "42",
                    "renting": 1,
                    "returning": 1,
                    "ebikes": 2,
                },
            }
        ]
    }
}


def test_fetch_network_snapshot_success(httpx_mock: HTTPXMock):
    """Client correctly parses a valid API response."""
    httpx_mock.add_response(json=FAKE_RESPONSE)

    snap = fetch_network_snapshot(
        network_id="velib",
        city="Paris",
        country="France",
    )

    assert snap.network_id == "velib"
    assert snap.city == "Paris"
    assert snap.station_count == 1
    assert snap.stations[0].free_bikes == 5
    assert snap.stations[0].capacity == 15
    assert snap.stations[0].occupancy_rate == pytest.approx(0.3333, rel=1e-3)


def test_fetch_network_snapshot_skips_invalid_stations(httpx_mock: HTTPXMock):
    """Stations that fail validation are skipped, not crashing the pipeline."""
    bad_response = {
        "network": {
            "stations": [
                {
                    "id": "bad",
                    "name": "Bad Station",
                    "latitude": 999.0,  # Invalid latitude
                    "longitude": 2.3522,
                    "timestamp": "2026-03-17T12:00:00+00:00",
                    "free_bikes": 5,
                    "empty_slots": 10,
                    "extra": {},
                }
            ]
        }
    }
    httpx_mock.add_response(json=bad_response)

    snap = fetch_network_snapshot(
        network_id="velib",
        city="Paris",
        country="France",
    )

    # Invalid station skipped — snapshot has 0 valid stations
    assert snap.station_count == 0


def test_fetch_network_snapshot_empty_network(httpx_mock: HTTPXMock):
    """An empty station list is handled gracefully."""
    httpx_mock.add_response(json={"network": {"stations": []}})

    snap = fetch_network_snapshot(
        network_id="velib",
        city="Paris",
        country="France",
    )

    assert snap.station_count == 0
    assert snap.active_stations == 0
