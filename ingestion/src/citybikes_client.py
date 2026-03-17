import logging
from pathlib import Path

import httpx
import yaml
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.models import NetworkSnapshot, StationExtra, StationSnapshot

logger = logging.getLogger(__name__)

BASE_URL = "https://api.citybik.es/v2"


def load_cities(config_path: Path) -> list[dict]:
    """Load the list of networks to ingest from the YAML config file."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config["networks"]


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _fetch_network(client: httpx.Client, network_id: str) -> dict:
    """
    Fetch raw station data for one network from the API.
    Decorated with @retry — automatically retries on HTTP errors.
    """
    url = f"{BASE_URL}/networks/{network_id}?fields=stations"
    logger.info(f"Fetching {url}")
    response = client.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_network_snapshot(
    network_id: str,
    city: str,
    country: str,
) -> NetworkSnapshot:
    """
    Fetch and validate all stations for one network.
    Returns a NetworkSnapshot containing validated StationSnapshot objects.
    """
    with httpx.Client() as client:
        raw = _fetch_network(client, network_id)

    raw_stations = raw.get("network", {}).get("stations", [])
    logger.info(f"Raw stations received for {network_id}: {len(raw_stations)}")

    stations = []
    validation_errors = 0

    for raw_station in raw_stations:
        try:
            station = StationSnapshot(
                id=raw_station["id"],
                name=raw_station["name"],
                latitude=raw_station["latitude"],
                longitude=raw_station["longitude"],
                timestamp=raw_station["timestamp"],
                free_bikes=raw_station["free_bikes"],
                empty_slots=raw_station.get("empty_slots"),
                extra=StationExtra(**(raw_station.get("extra") or {})),
                network_id=network_id,
            )
            stations.append(station)
        except Exception as e:
            validation_errors += 1
            logger.warning(
                f"Validation failed for station {raw_station.get('id', 'unknown')}"
                f" in {network_id}: {e}"
            )

    if validation_errors:
        logger.warning(
            f"{network_id}: {validation_errors}/{len(raw_stations)} "
            f"stations failed validation and were skipped"
        )

    logger.info(f"{network_id}: {len(stations)} valid stations")

    return NetworkSnapshot(
        network_id=network_id,
        city=city,
        country=country,
        stations=stations,
    )


def fetch_all_networks(config_path: Path) -> list[NetworkSnapshot]:
    """
    Fetch all networks listed in the config file.
    Returns a list of NetworkSnapshot objects, one per city.
    """
    cities = load_cities(config_path)
    snapshots = []

    for city_config in cities:
        network_id = city_config["id"]
        try:
            snapshot = fetch_network_snapshot(
                network_id=network_id,
                city=city_config["city"],
                country=city_config["country"],
            )
            snapshots.append(snapshot)
        except Exception as e:
            # Log the error but continue with remaining cities
            # One failing city should not abort the entire pipeline run
            logger.error(f"Failed to fetch {network_id}: {e}")

    logger.info(f"Fetched {len(snapshots)}/{len(cities)} networks successfully")
    return snapshots
