from __future__ import annotations
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass



@dataclass
class TimeRange:
    start: datetime
    end: datetime

@dataclass
class Point:
    lat: float
    lon: float

@dataclass
class PointCloud:
    points: list[Point]

    @property
    def lats(self) -> list[float]:
        return [p.lat for p in self.points]

    @property
    def lons(self) -> list[float]:
        return [p.lon for p in self.points]

    @classmethod
    def from_list(cls, coords: list[tuple[float, float]]) -> PointCloud:
        points = [Point(lat, lon) for lat, lon in coords]
        return cls(points)

    def __repr__(self) -> str:
        return f"PointCloud(points={self.points})"

@dataclass
class Query:
    time_range: TimeRange
    points: PointCloud
    name: str = ""

    @property
    def id(self) -> str:
        hash_input = (
            f"{self.time_range.start.isoformat()}_{self.time_range.end.isoformat()}_" +
            "_".join(f"{p.lat}_{p.lon}" for p in self.points.points)
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    @staticmethod
    def from_json(path: Path | str) -> Query:
        path = Path(path)
        with path.open("r") as f:
            data = json.load(f)

        tr = TimeRange(
            start=datetime.fromisoformat(data["time_range"]["start"]),
            end=datetime.fromisoformat(data["time_range"]["end"])
        )
        pc = PointCloud.from_list(data["points"])
        
        return Query(time_range=tr, points=pc, name=data.get("name", ""))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time_range": {
                "start": self.time_range.start.isoformat(),
                "end": self.time_range.end.isoformat()
            },
            "points": [(p.lat, p.lon) for p in self.points.points]
        }

    def __repr__(self) -> str:
        return f"Query(time_range=({self.time_range.start} to {self.time_range.end}), num_points={len(self.points.points)})"
