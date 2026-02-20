from pydantic import BaseModel


class StreetLocationCreate(BaseModel):
    street_name: str
    city: str | None = None
    state: str | None = None
    country: str
    latitude: float
    longitude: float


class StreetLocationResponse(BaseModel):
    id: int
    street_name: str
    city: str | None
    state: str | None
    country: str
    latitude: float
    longitude: float

    model_config = {"from_attributes": True}


class LocationQuery(BaseModel):
    street_names: list[str]


class LocationMatch(BaseModel):
    city: str | None
    state: str | None
    country: str
    latitude: float
    longitude: float
    matching_streets: list[str]
    match_count: int
    total_queried: int
