from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class StationExtra(BaseModel):
    """
    Operator-specific fields returned inside the 'extra' object.
    Every field is Optional because different operators return
    different fields — Velib has altitude, Nextbike does not.
    """

    uid: str | int | None = None
    renting: int | None = None
    returning: int | None = None
    last_updated: int | str | None = None  # int (Unix) or ISO string
    has_ebikes: bool | None = None
    ebikes: int | None = None
    normal_bikes: int | None = None
    slots: int | None = None
    address: str | None = None
    altitude: float | None = None

    model_config = {"extra": "allow"}


class StationSnapshot(BaseModel):
    """
    One station reading at one point in time.
    This becomes one row in fact_station_snapshot.
    """

    id: str
    name: str
    latitude: float
    longitude: float
    timestamp: datetime
    free_bikes: int
    empty_slots: int | None = None
    extra: StationExtra = Field(default_factory=StationExtra)

    network_id: str = ""
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    capacity: int | None = None
    occupancy_rate: float | None = None
    ebike_share: float | None = None
    is_empty: bool = False
    is_full: bool = False
    is_offline: bool = False
    data_latency_minutes: float | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def fix_timestamp(cls, v: object) -> object:
        # Some operators return "+00:00Z" which is invalid ISO 8601
        # Strip the trailing Z when a UTC offset is already present
        if isinstance(v, str) and v.endswith("+00:00Z"):
            v = v[:-1]
        return v

    @field_validator("free_bikes")
    @classmethod
    def free_bikes_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"free_bikes cannot be negative, got {v}")
        return v

    @field_validator("latitude")
    @classmethod
    def latitude_valid(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError(f"latitude must be between -90 and 90, got {v}")
        return v

    @field_validator("longitude")
    @classmethod
    def longitude_valid(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError(f"longitude must be between -180 and 180, got {v}")
        return v

    @model_validator(mode="after")
    def compute_derived_fields(self) -> "StationSnapshot":
        # --- Capacity ---
        if self.extra.slots is not None:
            self.capacity = self.extra.slots
        elif self.empty_slots is not None:
            self.capacity = self.free_bikes + self.empty_slots

        # --- Occupancy rate ---
        if self.capacity and self.capacity > 0:
            self.occupancy_rate = round(self.free_bikes / self.capacity, 4)

        # --- E-bike share ---
        ebikes = self.extra.ebikes or 0
        if self.free_bikes > 0 and ebikes > 0:
            self.ebike_share = round(ebikes / self.free_bikes, 4)

        # --- Status flags ---
        self.is_empty = self.free_bikes == 0
        self.is_full = self.empty_slots is not None and self.empty_slots == 0
        self.is_offline = (
            self.free_bikes == 0
            and self.empty_slots == 0
            and self.extra.renting == 0
            and self.extra.returning == 0
        )

        # --- Data latency ---
        # last_updated can be a Unix int or an ISO string depending on operator
        if self.extra.last_updated is not None:
            try:
                if isinstance(self.extra.last_updated, int):
                    source_time = datetime.fromtimestamp(self.extra.last_updated, tz=UTC)
                else:
                    # ISO string — parse it, assume UTC if no timezone
                    source_time = datetime.fromisoformat(self.extra.last_updated).replace(
                        tzinfo=UTC
                    )
                delta = self.ingested_at - source_time
                self.data_latency_minutes = round(delta.total_seconds() / 60, 2)
            except Exception:
                # If parsing fails, skip latency — don't crash the pipeline
                pass

        return self


class NetworkSnapshot(BaseModel):
    """
    All stations for one network from one API poll.
    """

    network_id: str
    city: str
    country: str
    polled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stations: list[StationSnapshot]

    @property
    def station_count(self) -> int:
        return len(self.stations)

    @property
    def active_stations(self) -> int:
        return sum(1 for s in self.stations if not s.is_offline)
