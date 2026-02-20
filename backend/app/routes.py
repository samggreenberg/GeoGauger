from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import StreetLocation, get_db
from app.schemas import (
    LocationMatch,
    LocationQuery,
    StreetLocationCreate,
    StreetLocationResponse,
)

router = APIRouter()


@router.post("/locate", response_model=list[LocationMatch])
def locate(query: LocationQuery, db: Session = Depends(get_db)):
    """Given a list of street names, find locations where multiple streets match."""
    if not query.street_names:
        return []

    normalized = [name.strip().lower() for name in query.street_names]

    results = (
        db.query(
            StreetLocation.city,
            StreetLocation.state,
            StreetLocation.country,
            func.avg(StreetLocation.latitude).label("latitude"),
            func.avg(StreetLocation.longitude).label("longitude"),
            func.count(StreetLocation.id).label("match_count"),
            func.group_concat(StreetLocation.street_name).label("matching_streets"),
        )
        .filter(func.lower(StreetLocation.street_name).in_(normalized))
        .group_by(StreetLocation.city, StreetLocation.state, StreetLocation.country)
        .order_by(func.count(StreetLocation.id).desc())
        .all()
    )

    return [
        LocationMatch(
            city=row.city,
            state=row.state,
            country=row.country,
            latitude=row.latitude,
            longitude=row.longitude,
            matching_streets=list(set(row.matching_streets.split(","))),
            match_count=row.match_count,
            total_queried=len(normalized),
        )
        for row in results
    ]


@router.post("/streets", response_model=StreetLocationResponse)
def add_street(street: StreetLocationCreate, db: Session = Depends(get_db)):
    """Add a street location to the database."""
    db_street = StreetLocation(**street.model_dump())
    db.add(db_street)
    db.commit()
    db.refresh(db_street)
    return db_street


@router.get("/streets", response_model=list[StreetLocationResponse])
def list_streets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all street locations in the database."""
    return db.query(StreetLocation).offset(skip).limit(limit).all()
