from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import math


@dataclass
class Node:
    id: str
    type: str
    level: int
    pos: Optional[Tuple[float, float, float]]
    attrs: Dict[str, Any]
    name: Optional[str] = None


@dataclass
class Edge:
    a: str
    b: str
    weight: float
    attrs: Dict[str, Any]


@dataclass
class Meta:
    building_name: str
    unit: str
    format_version: int
    group: str


@dataclass
class RoutingNode:
    id: str
    level: int
    pos: Optional[Tuple[float, float, float]]


@dataclass
class RoutingEdge:
    target: int
    weight: float
    is_floor_transition: bool
    is_stairs: bool
    is_elevator: bool
    accessible: bool
