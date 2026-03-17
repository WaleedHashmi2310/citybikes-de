import logging
import sys
from pathlib import Path

from src.citybikes_client import fetch_all_networks
from src.storage import get_storage_backend

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config" / "cities.yml"


def main() -> None:
    logger.info("CityBikes ingestion job starting...")

    backend = get_storage_backend()
    snapshots = fetch_all_networks(CONFIG_PATH)

    success = 0
    failed = 0

    for snap in snapshots:
        try:
            path = backend.write(snap)
            logger.info(
                f"{snap.city} ({snap.network_id}): "
                f"{snap.station_count} stations written to {path}"
            )
            success += 1
        except Exception as e:
            logger.error(f"Failed to write {snap.network_id}: {e}")
            failed += 1

    logger.info(f"Ingestion complete. " f"Success: {success}/{success + failed} networks.")

    if failed > 0:
        logger.error(f"{failed} network(s) failed to write.")
        sys.exit(1)


if __name__ == "__main__":
    main()
