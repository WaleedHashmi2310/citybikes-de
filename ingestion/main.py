import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("CityBikes ingestion job starting...")
    # Populated in later substeps
    logger.info("CityBikes ingestion job complete.")


if __name__ == "__main__":
    main()
