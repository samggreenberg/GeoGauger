"""OSM data builder — downloads Geofabrik extracts, parses streets, populates the database."""

import json
import logging
import os
import urllib.request
from collections import defaultdict
from pathlib import Path

import osmium
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Base, SessionLocal, StreetLocation, engine

logger = logging.getLogger("geogauger.osm_builder")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Default regions to download. Override with GEOGAUGER_REGIONS env var (JSON array).
# Each region: {"url": "...", "country": "...", "state": "..." (optional)}
DEFAULT_REGIONS = [
    {
        "url": "https://download.geofabrik.de/north-america/us/delaware-latest.osm.pbf",
        "country": "US",
        "state": "Delaware",
    },
]

# Highway types we care about (skip footpaths, cycleways, etc.)
ROAD_TYPES = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "unclassified",
    "motorway_link",
    "trunk_link",
    "primary_link",
    "secondary_link",
    "tertiary_link",
    "living_street",
}


def get_regions() -> list[dict]:
    """Return the list of regions to download, from env var or defaults."""
    env = os.environ.get("GEOGAUGER_REGIONS")
    if env:
        return json.loads(env)
    return DEFAULT_REGIONS


class StreetHandler(osmium.SimpleHandler):
    """Pyosmium handler that collects named streets with their centroid coordinates."""

    def __init__(self):
        super().__init__()
        # street_name -> list of (lat, lon) centroids per way segment
        self.streets: dict[str, list[tuple[float, float]]] = defaultdict(list)

    def way(self, w):
        tags = w.tags
        highway = tags.get("highway")
        name = tags.get("name")
        if not highway or not name or highway not in ROAD_TYPES:
            return

        try:
            lats = []
            lons = []
            for node in w.nodes:
                if node.location.valid():
                    lats.append(node.location.lat)
                    lons.append(node.location.lon)
            if lats:
                centroid_lat = sum(lats) / len(lats)
                centroid_lon = sum(lons) / len(lons)
                self.streets[name].append((centroid_lat, centroid_lon))
        except osmium.InvalidLocationError:
            pass


def download_pbf(url: str, dest: Path) -> Path:
    """Download a PBF file if it doesn't already exist locally."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        logger.info("PBF already downloaded: %s", dest.name)
        return dest

    logger.info("Downloading %s ...", url)

    def _report(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            if block_num % 200 == 0:
                logger.info("  %d%% (%d / %d bytes)", pct, downloaded, total_size)

    urllib.request.urlretrieve(url, dest, reporthook=_report)
    logger.info("Download complete: %s", dest.name)
    return dest


def parse_pbf(pbf_path: Path) -> dict[str, tuple[float, float]]:
    """Parse a PBF file and return {street_name: (avg_lat, avg_lon)}."""
    logger.info("Parsing %s ...", pbf_path.name)
    handler = StreetHandler()
    handler.apply_file(str(pbf_path), locations=True)

    # Deduplicate: average all segment centroids per street name
    result = {}
    for name, coords in handler.streets.items():
        avg_lat = sum(c[0] for c in coords) / len(coords)
        avg_lon = sum(c[1] for c in coords) / len(coords)
        result[name] = (avg_lat, avg_lon)

    logger.info("Extracted %d unique streets from %s", len(result), pbf_path.name)
    return result


def populate_db(
    streets: dict[str, tuple[float, float]], country: str, state: str | None
) -> int:
    """Bulk-insert parsed streets into the database. Returns row count."""
    if not streets:
        return 0

    db: Session = SessionLocal()
    try:
        rows = [
            {
                "street_name": name,
                "city": None,
                "state": state,
                "country": country,
                "latitude": lat,
                "longitude": lon,
            }
            for name, (lat, lon) in streets.items()
        ]

        # Insert in chunks to avoid huge transactions
        chunk_size = 5000
        for i in range(0, len(rows), chunk_size):
            db.execute(StreetLocation.__table__.insert(), rows[i : i + chunk_size])
        db.commit()
        logger.info("Inserted %d streets for %s/%s", len(rows), country, state or "")
        return len(rows)
    finally:
        db.close()


def build_db_if_needed() -> bool:
    """Check if the DB needs populating; if so, download OSM data and build it.

    Returns True if the database was built, False if it was already populated.
    """
    if os.environ.get("GEOGAUGER_SKIP_BUILD"):
        logger.info("GEOGAUGER_SKIP_BUILD is set, skipping OSM data build")
        return False

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        count = db.query(func.count(StreetLocation.id)).scalar()
        if count and count > 0:
            logger.info("Database already has %d streets, skipping build", count)
            return False
    finally:
        db.close()

    regions = get_regions()
    if not regions:
        logger.info("No regions configured, skipping build")
        return False

    logger.info("Database is empty — building from %d region(s)...", len(regions))
    total = 0
    for region in regions:
        url = region["url"]
        filename = url.rsplit("/", 1)[-1]
        pbf_path = DATA_DIR / filename

        download_pbf(url, pbf_path)
        streets = parse_pbf(pbf_path)
        inserted = populate_db(streets, region["country"], region.get("state"))
        total += inserted

    logger.info("Build complete: %d total streets across %d region(s)", total, len(regions))
    return True
