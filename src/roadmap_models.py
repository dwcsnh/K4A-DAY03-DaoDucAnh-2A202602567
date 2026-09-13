"""
Typed roadmap models and deterministic validation helpers for the Roadmap Agent.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator


Level = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]
RoadmapStatus = Literal["DRAFT", "ACTIVE", "COMPLETED"]
NodeType = Literal["LESSON", "CHECKPOINT"]
NodeStatus = Literal["NOT_STARTED", "LEARNING", "COMPLETED", "LOCKED", "UNLOCKED"]
ResourceType = Literal["DOCUMENTATION", "ARTICLE", "VIDEO", "COURSE"]


class Constraints(BaseModel):
    hoursPerDay: Optional[float] = Field(default=None, gt=0)
    deadlineWeeks: Optional[int] = Field(default=None, gt=0)


class Resource(BaseModel):
    title: str = Field(min_length=3)
    url: str
    type: ResourceType
    description: Optional[str] = None
    source: Optional[str] = None

    @validator("url")
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Resource URLs must be valid http/https URLs.")
        return value


class RoadmapNode(BaseModel):
    id: str = Field(min_length=3)
    type: NodeType
    title: str = Field(min_length=3)
    description: str = Field(min_length=10)
    order: int = Field(ge=1)
    prerequisites: List[str] = Field(default_factory=list)
    status: NodeStatus
    resources: List[Resource] = Field(default_factory=list)
    learningObjectives: List[str] = Field(default_factory=list)
    estimatedMinutes: Optional[int] = Field(default=None, gt=0)

    @validator("learningObjectives", always=True)
    def validate_learning_objectives(cls, value: List[str], values: Dict[str, object]) -> List[str]:
        node_type = values.get("type")
        if node_type == "LESSON" and len(value) < 2:
            raise ValueError("Each lesson must include at least two learning objectives.")
        return value

    @validator("status")
    def validate_status(cls, value: str, values: Dict[str, object]) -> str:
        node_type = values.get("type")
        if node_type == "LESSON" and value not in {"NOT_STARTED", "LEARNING", "COMPLETED"}:
            raise ValueError("Lesson status must be NOT_STARTED, LEARNING, or COMPLETED.")
        if node_type == "CHECKPOINT" and value not in {"LOCKED", "UNLOCKED"}:
            raise ValueError("Checkpoint status must be LOCKED or UNLOCKED.")
        return value


class RoadmapEdge(BaseModel):
    id: str = Field(min_length=3)
    source: str = Field(min_length=3)
    target: str = Field(min_length=3)


class Roadmap(BaseModel):
    roadmapId: str = Field(min_length=5)
    title: str = Field(min_length=3)
    topic: str = Field(min_length=2)
    goal: str = Field(min_length=10)
    level: Level
    status: RoadmapStatus
    constraints: Constraints = Field(default_factory=Constraints)
    nodes: List[RoadmapNode] = Field(default_factory=list)
    edges: List[RoadmapEdge] = Field(default_factory=list)
    createdAt: str
    updatedAt: str

    @validator("nodes")
    def validate_nodes_exist(cls, value: List[RoadmapNode]) -> List[RoadmapNode]:
        if not value:
            raise ValueError("A roadmap must contain at least one node.")
        return value


class RoadmapGenerationRequest(BaseModel):
    topic: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    level: Level = "BEGINNER"
    constraints: Constraints = Field(default_factory=Constraints)

    @validator("topic", "goal")
    def trim_text(cls, value: str) -> str:
        return value.strip()


def model_to_dict(model: BaseModel) -> Dict[str, object]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def validate_roadmap_graph(roadmap: Roadmap) -> None:
    node_map = {node.id: node for node in roadmap.nodes}

    if len(node_map) != len(roadmap.nodes):
        raise ValueError("Every roadmap node must have a unique ID.")

    for node in roadmap.nodes:
        for prerequisite in node.prerequisites:
            if prerequisite not in node_map:
                raise ValueError(f"Prerequisite '{prerequisite}' does not exist in the roadmap.")
            if prerequisite == node.id:
                raise ValueError(f"Node '{node.id}' cannot depend on itself.")

        if node.type == "CHECKPOINT":
            if not node.prerequisites:
                raise ValueError(f"Checkpoint '{node.id}' must depend on at least one lesson.")
            invalid_refs = [ref for ref in node.prerequisites if node_map[ref].type != "LESSON"]
            if invalid_refs:
                raise ValueError(
                    f"Checkpoint '{node.id}' can only depend on lessons, but found: {', '.join(invalid_refs)}."
                )

    for edge in roadmap.edges:
        if edge.source not in node_map or edge.target not in node_map:
            raise ValueError(f"Edge '{edge.id}' references a missing node.")

    visited = set()
    visiting = set()

    def dfs(node_id: str) -> None:
        if node_id in visiting:
            raise ValueError(f"Detected an invalid dependency cycle at '{node_id}'.")
        if node_id in visited:
            return
        visiting.add(node_id)
        for prerequisite in node_map[node_id].prerequisites:
            dfs(prerequisite)
        visiting.remove(node_id)
        visited.add(node_id)

    for node in roadmap.nodes:
        dfs(node.id)


def recalculate_checkpoint_statuses(nodes: List[RoadmapNode]) -> List[RoadmapNode]:
    node_map = {node.id: node for node in nodes}
    for node in nodes:
        if node.type != "CHECKPOINT":
            continue
        node.status = (
            "UNLOCKED"
            if all(node_map[ref].status == "COMPLETED" for ref in node.prerequisites)
            else "LOCKED"
        )
    return nodes


def build_progress_summary(roadmap: Roadmap) -> Dict[str, object]:
    lessons = [node for node in roadmap.nodes if node.type == "LESSON"]
    completed = sum(1 for node in lessons if node.status == "COMPLETED")
    total = len(lessons)
    percentage = int(round((completed / total) * 100)) if total else 0

    checkpoints = [
        {"id": node.id, "status": node.status}
        for node in roadmap.nodes
        if node.type == "CHECKPOINT"
    ]

    return {
        "completed": completed,
        "total": total,
        "percentage": percentage,
        "checkpoints": checkpoints,
    }
