"""Domain models used by the enterprise risk analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    COMPANY = "Company"
    EXECUTIVE = "Executive"
    PRODUCT = "Product"


class RelationType(str, Enum):
    INVESTS_IN = "Invests_in"
    SUPPLIES = "Supplies"
    MANAGES = "Manages"
    PRODUCES = "Produces"
    DEPENDS_ON = "Depends_on"
    PARTNERS_WITH = "Partners_with"
    AFFECTS = "Affects"


@dataclass(frozen=True)
class Entity:
    name: str
    type: NodeType
    evidence: str = ""

    @property
    def key(self) -> str:
        return f"{self.type.value}:{self.name}"


@dataclass(frozen=True)
class Relation:
    source: Entity
    relation: RelationType
    target: Entity
    evidence: str = ""
    weight: float = 1.0


@dataclass
class ExtractionResult:
    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)


@dataclass(frozen=True)
class MetaPathScore:
    name: str
    description: str
    score: float
    matched_paths: list[list[str]]


@dataclass(frozen=True)
class AnalysisResult:
    target_company: str
    risk_score: int
    primary_meta_path: str
    cascade_reasoning_chain: list[str]
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_company": self.target_company,
            "risk_score": self.risk_score,
            "primary_meta_path": self.primary_meta_path,
            "cascade_reasoning_chain": self.cascade_reasoning_chain,
            "suggested_action": self.suggested_action,
        }
