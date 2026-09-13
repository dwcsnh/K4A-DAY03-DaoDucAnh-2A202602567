"""
Roadmap Agent CLI MVP.

This implementation focuses on:
- roadmap generation
- external resource retrieval through a local MCP layer
- deterministic validation and checkpoint unlocking
- persistent roadmap/progress storage

Human-in-the-loop refinement is intentionally deferred.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import MCPRoadmapServer
from prompts import ROADMAP_AGENT_SYSTEM_PROMPT, build_learning_area_prompt
from providers import get_llm_provider
from roadmap_models import (
    Constraints,
    Resource,
    Roadmap,
    RoadmapEdge,
    RoadmapGenerationRequest,
    RoadmapNode,
    build_progress_summary,
    model_to_dict,
    validate_roadmap_graph,
)
from roadmap_repository import FileRoadmapRepository

load_dotenv()


def load_test_cases() -> List[Dict[str, Any]]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(base_dir, "config", "test_cases.example.json")
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_waterfall_trace(trace_data: List[Dict[str, Any]]) -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as file:
        json.dump(trace_data, file, ensure_ascii=False, indent=2)
    print(f"Saved {len(trace_data)} trace events to {trace_path}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def roadmap_id() -> str:
    return f"roadmap_{uuid.uuid4().hex[:10]}"


def normalize_level(level: str) -> str:
    normalized = (level or "BEGINNER").strip().upper()
    if normalized not in {"BEGINNER", "INTERMEDIATE", "ADVANCED"}:
        return "BEGINNER"
    return normalized


def learning_topic_guardrail_message() -> str:
    return (
        "Please enter your input again with a topic you want to learn, "
        "such as 'Docker', 'AWS Cloud', or 'I want to learn Python for automation'."
    )


class AgentRunError(ValueError):
    def __init__(self, message: str, trace: List[Dict[str, Any]]):
        super().__init__(message)
        self.trace = trace


class RoadmapAgent:
    def __init__(self, provider, mcp_server: MCPRoadmapServer, repository: FileRoadmapRepository):
        self.provider = provider
        self.mcp_server = mcp_server
        self.repository = repository

    @staticmethod
    def _stream_line(message: str) -> None:
        print(message, flush=True)

    def _announce(self, label: str, message: str) -> None:
        self._stream_line(f"{label} {message}")

    @staticmethod
    def _compact_json(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(", ", ": "))

    def _append_trace(self, trace: List[Dict[str, Any]], action_type: str, **payload: Any) -> None:
        event = {"step": len(trace) + 1, "action_type": action_type}
        event.update(payload)
        trace.append(event)

    def _generate_blueprint(self, request: RoadmapGenerationRequest, trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        request_payload = model_to_dict(request)
        prompt = build_learning_area_prompt(request_payload)
        self._announce("THINK", "Planning the roadmap structure from the user goal.")
        started_at = time.time()
        blueprint = self.provider.generate_json(prompt, system_prompt=ROADMAP_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - started_at) * 1000, 2)

        status = blueprint.get("status", "READY") if isinstance(blueprint, dict) else "READY"
        if status == "REJECTED":
            message = blueprint.get("message") or learning_topic_guardrail_message()
            self._announce("OBSERVE", f"Model guardrail rejected the request in {latency_ms} ms.")
            self._append_trace(
                trace,
                "MODEL_GUARDRAIL_REJECTION",
                input=request_payload,
                output={"status": status, "message": message},
                latency_ms=latency_ms,
            )
            raise ValueError(message)

        areas = blueprint.get("areas") if isinstance(blueprint, dict) else None
        if not isinstance(areas, list) or not areas:
            raise ValueError("The agent could not generate a usable roadmap blueprint.")

        normalized_areas = []
        for index, area in enumerate(areas, start=1):
            if not isinstance(area, dict):
                continue
            title = str(area.get("title") or f"{request.topic} lesson {index}").strip()
            description = str(area.get("description") or f"Learn the core concepts behind {title}.").strip()
            objectives = area.get("learningObjectives") or [
                f"Understand the essentials of {title}",
                f"Practice {title} with a concrete example",
            ]
            minutes = int(area.get("estimatedMinutes") or 90)
            normalized_areas.append(
                {
                    "title": title,
                    "description": description,
                    "learningObjectives": [str(item).strip() for item in objectives if str(item).strip()],
                    "estimatedMinutes": max(45, minutes),
                }
            )

        if len(normalized_areas) < 5:
            raise ValueError("The generated roadmap blueprint is too small for the MVP acceptance criteria.")

        blueprint["areas"] = normalized_areas[:7]
        blueprint["title"] = str(blueprint.get("title") or f"{request.topic} Learning Roadmap").strip()
        blueprint["topic"] = str(blueprint.get("topic") or request.topic).strip()
        blueprint["goal"] = str(blueprint.get("goal") or request.goal).strip()
        self._announce(
            "OBSERVE",
            f"Planned {len(blueprint['areas'])} learning areas in {latency_ms} ms.",
        )

        self._append_trace(
            trace,
            "PLAN_ROADMAP",
            input=request_payload,
            output={
                "title": blueprint["title"],
                "topic": blueprint["topic"],
                "areas": [area["title"] for area in blueprint["areas"]],
            },
            latency_ms=latency_ms,
        )
        return blueprint

    def _search_resources_for_area(
        self,
        request: RoadmapGenerationRequest,
        area: Dict[str, Any],
        trace: List[Dict[str, Any]],
        area_index: int,
    ) -> List[Resource]:
        query = f"{request.topic} {area['title']}"
        self._announce("THINK", f"Looking for resources for '{area['title']}'.")
        self._announce(
            "ACTION",
            f"search_resources({self._compact_json({'query': query, 'topic': request.topic, 'level': request.level, 'max_results': 3})})",
        )
        started_at = time.time()
        response = self.mcp_server.call_tool(
            "search_resources",
            {
                "query": query,
                "topic": request.topic,
                "level": request.level,
                "max_results": 3,
            },
        )
        latency_ms = round((time.time() - started_at) * 1000, 2)
        result = response["result"]
        self._announce(
            "OBSERVE",
            f"search_resources returned status={result.get('status')} source={result.get('source_mode')} in {latency_ms} ms.",
        )

        self._append_trace(
            trace,
            "TOOL_EXECUTION",
            tool_name="search_resources",
            arguments={"query": query, "topic": request.topic, "level": request.level, "max_results": 3},
            observation=result,
            latency_ms=latency_ms,
        )

        if result.get("status") == "EXECUTION_ERROR":
            message = result.get("error", "The resource search tool failed.")
            self._append_trace(
                trace,
                "ERROR",
                thought="External resource search failed while building the roadmap.",
                output=message,
            )
            raise ValueError(
                f"Could not find resources for '{area['title']}'. {message}"
            )
        if result.get("status") == "NO_RESULTS":
            message = (
                f"Could not find any learning resources for '{area['title']}' "
                f"under topic '{request.topic}'."
            )
            self._append_trace(
                trace,
                "ERROR",
                thought="The resource search tool returned no usable resources.",
                output=message,
            )
            raise ValueError(message)

        results = result.get("results", [])[:2]
        resources: List[Resource] = []
        for resource_index, item in enumerate(results):
            details = item
            if area_index <= 2 and resource_index == 0 and item.get("resource_id"):
                self._announce(
                    "ACTION",
                    f"get_resource_details({self._compact_json({'resource_id': item['resource_id']})})",
                )
                started_at = time.time()
                detail_response = self.mcp_server.call_tool(
                    "get_resource_details",
                    {"resource_id": item["resource_id"]},
                )
                detail_latency = round((time.time() - started_at) * 1000, 2)
                detail_result = detail_response["result"]
                self._announce(
                    "OBSERVE",
                    f"get_resource_details returned status={detail_result.get('status')} in {detail_latency} ms.",
                )
                self._append_trace(
                    trace,
                    "TOOL_EXECUTION",
                    tool_name="get_resource_details",
                    arguments={"resource_id": item["resource_id"]},
                    observation=detail_result,
                    latency_ms=detail_latency,
                )
                if detail_result.get("status") == "SUCCESS":
                    details = detail_result["resource"]

            resources.append(
                Resource(
                    title=details["title"],
                    url=details["url"],
                    type=details["type"],
                    description=details.get("description"),
                    source=details.get("source"),
                )
            )

        return resources

    def _build_nodes_and_edges(
        self,
        request: RoadmapGenerationRequest,
        blueprint: Dict[str, Any],
        lesson_resources: List[List[Resource]],
    ) -> Tuple[List[RoadmapNode], List[RoadmapEdge]]:
        self._announce("THINK", "Building lessons, checkpoints, and dependency edges.")
        nodes: List[RoadmapNode] = []
        edges: List[RoadmapEdge] = []

        previous_anchor_id: Optional[str] = None
        checkpoint_buffer: List[str] = []
        checkpoint_titles: List[str] = []
        checkpoint_count = 0
        order = 1
        areas = blueprint["areas"]

        for index, area in enumerate(areas, start=1):
            lesson_id = f"lesson_{index:02d}"
            prerequisites = [previous_anchor_id] if previous_anchor_id else []

            lesson = RoadmapNode(
                id=lesson_id,
                type="LESSON",
                title=area["title"],
                description=area["description"],
                order=order,
                prerequisites=prerequisites,
                status="NOT_STARTED",
                resources=lesson_resources[index - 1],
                learningObjectives=area["learningObjectives"],
                estimatedMinutes=area["estimatedMinutes"],
            )
            nodes.append(lesson)
            order += 1

            for prerequisite in prerequisites:
                edges.append(
                    RoadmapEdge(
                        id=f"edge_{prerequisite}_to_{lesson_id}",
                        source=prerequisite,
                        target=lesson_id,
                    )
                )

            checkpoint_buffer.append(lesson_id)
            checkpoint_titles.append(area["title"])
            previous_anchor_id = lesson_id

            lessons_remaining = len(areas) - index
            should_insert_checkpoint = (
                len(checkpoint_buffer) == 3
                or (lessons_remaining == 0 and checkpoint_count == 0 and len(areas) >= 4)
                or (lessons_remaining == 0 and len(checkpoint_buffer) >= 2)
            )

            if not should_insert_checkpoint:
                continue

            checkpoint_count += 1
            checkpoint_id = f"checkpoint_{checkpoint_count:02d}"
            checkpoint = RoadmapNode(
                id=checkpoint_id,
                type="CHECKPOINT",
                title=f"Checkpoint {checkpoint_count}",
                description=(
                    f"Validate progress across {'; '.join(checkpoint_titles)} "
                    f"for the {request.topic} roadmap."
                ),
                order=order,
                prerequisites=list(checkpoint_buffer),
                status="LOCKED",
                resources=[],
                learningObjectives=[],
            )
            nodes.append(checkpoint)
            order += 1

            for prerequisite in checkpoint_buffer:
                edges.append(
                    RoadmapEdge(
                        id=f"edge_{prerequisite}_to_{checkpoint_id}",
                        source=prerequisite,
                        target=checkpoint_id,
                    )
                )

            previous_anchor_id = checkpoint_id
            checkpoint_buffer = []
            checkpoint_titles = []

        self._announce(
            "OBSERVE",
            f"Built {len(nodes)} nodes and {len(edges)} edges for the roadmap graph.",
        )
        return nodes, edges

    def _validate_and_save(self, roadmap: Roadmap, trace: List[Dict[str, Any]]) -> Roadmap:
        self._announce("THINK", "Validating the roadmap graph before persistence.")
        started_at = time.time()
        validate_roadmap_graph(roadmap)
        latency_ms = round((time.time() - started_at) * 1000, 2)
        self._announce("OBSERVE", f"Validation completed in {latency_ms} ms.")
        self._append_trace(
            trace,
            "VALIDATE_ROADMAP",
            roadmap_id=roadmap.roadmapId,
            output={"nodes": len(roadmap.nodes), "edges": len(roadmap.edges)},
            latency_ms=latency_ms,
        )

        self._announce("THINK", "Saving the roadmap and checkpoint state.")
        started_at = time.time()
        saved = self.repository.save(roadmap)
        latency_ms = round((time.time() - started_at) * 1000, 2)
        self._announce("OBSERVE", f"Saved roadmap {saved.roadmapId} in {latency_ms} ms.")
        self._append_trace(
            trace,
            "SAVE_ROADMAP",
            roadmap_id=saved.roadmapId,
            output={"status": saved.status, "storage": self.repository.storage_path},
            latency_ms=latency_ms,
        )
        return saved

    def generate_roadmap(self, request: RoadmapGenerationRequest) -> Tuple[Roadmap, List[Dict[str, Any]]]:
        trace: List[Dict[str, Any]] = []
        try:
            self._announce(
                "THINK",
                f"Understanding the goal '{request.goal}' for topic '{request.topic}' at level '{request.level}'.",
            )
            self._append_trace(
                trace,
                "UNDERSTAND_GOAL",
                input=model_to_dict(request),
                thought="Analyze the goal, level, and constraints before creating the roadmap.",
            )

            blueprint = self._generate_blueprint(request, trace)
            lesson_resources = [
                self._search_resources_for_area(request, area, trace, area_index=index)
                for index, area in enumerate(blueprint["areas"], start=1)
            ]
            nodes, edges = self._build_nodes_and_edges(request, blueprint, lesson_resources)

            timestamp = now_iso()
            roadmap = Roadmap(
                roadmapId=roadmap_id(),
                title=blueprint["title"],
                topic=blueprint["topic"],
                goal=blueprint["goal"],
                level=request.level,
                status="DRAFT",
                constraints=request.constraints,
                nodes=nodes,
                edges=edges,
                createdAt=timestamp,
                updatedAt=timestamp,
            )

            saved = self._validate_and_save(roadmap, trace)
            summary = build_progress_summary(saved)
            self._announce(
                "FINAL",
                f"Created roadmap '{saved.title}' with {summary['total']} lessons and {len(summary['checkpoints'])} checkpoints.",
            )
            self._append_trace(
                trace,
                "FINAL_ANSWER",
                roadmap_id=saved.roadmapId,
                output={
                    "title": saved.title,
                    "lesson_count": summary["total"],
                    "checkpoint_count": len(summary["checkpoints"]),
                },
                thought="Return a persisted draft roadmap with deterministic checkpoint state.",
            )
            return saved, trace
        except ValueError as error:
            self._announce("ERROR", str(error))
            self._append_trace(
                trace,
                "ERROR",
                thought="The roadmap generation flow failed and must return an error to the user.",
                output=str(error),
            )
            raise AgentRunError(str(error), trace) from error

    def accept_roadmap(self, roadmap_id_value: str, trace: Optional[List[Dict[str, Any]]] = None) -> Roadmap:
        self._announce("ACTION", f"accept_roadmap({self._compact_json({'roadmapId': roadmap_id_value})})")
        started_at = time.time()
        roadmap = self.repository.accept(roadmap_id_value)
        latency_ms = round((time.time() - started_at) * 1000, 2)
        self._announce("OBSERVE", f"Roadmap {roadmap.roadmapId} is now {roadmap.status} in {latency_ms} ms.")
        if trace is not None:
            self._append_trace(
                trace,
                "ACCEPT_ROADMAP",
                roadmap_id=roadmap.roadmapId,
                output={"status": roadmap.status},
                latency_ms=latency_ms,
            )
        return roadmap

    def update_progress(
        self,
        roadmap_id_value: str,
        node_id: str,
        status: str,
        trace: Optional[List[Dict[str, Any]]] = None,
    ) -> Roadmap:
        self._announce(
            "ACTION",
            f"update_progress({self._compact_json({'roadmapId': roadmap_id_value, 'nodeId': node_id, 'status': status})})",
        )
        started_at = time.time()
        roadmap = self.repository.update_progress(roadmap_id_value, node_id, status)
        latency_ms = round((time.time() - started_at) * 1000, 2)
        self._announce("OBSERVE", f"Updated {node_id} to {status} in {latency_ms} ms.")
        if trace is not None:
            self._append_trace(
                trace,
                "UPDATE_PROGRESS",
                roadmap_id=roadmap.roadmapId,
                node_id=node_id,
                output={"status": status, "checkpoints": build_progress_summary(roadmap)["checkpoints"]},
                latency_ms=latency_ms,
            )
        return roadmap


def print_roadmap(roadmap: Roadmap) -> None:
    print(f"\nRoadmap: {roadmap.title} [{roadmap.status}]")
    print(f"Goal: {roadmap.goal}")
    print(f"Level: {roadmap.level}")
    if roadmap.constraints.hoursPerDay or roadmap.constraints.deadlineWeeks:
        print(
            "Constraints: "
            f"hoursPerDay={roadmap.constraints.hoursPerDay or '-'}, "
            f"deadlineWeeks={roadmap.constraints.deadlineWeeks or '-'}"
        )

    for node in sorted(roadmap.nodes, key=lambda item: item.order):
        prereqs = ", ".join(node.prerequisites) if node.prerequisites else "-"
        print(f"- {node.id} | {node.type} | {node.title} | status={node.status} | prerequisites={prereqs}")
        if node.type == "LESSON":
            for resource in node.resources[:2]:
                print(f"    resource: {resource.title} ({resource.source})")


def print_progress_summary(roadmap: Roadmap) -> None:
    summary = build_progress_summary(roadmap)
    print(
        f"Progress: {summary['completed']}/{summary['total']} lessons completed "
        f"({summary['percentage']}%)"
    )
    for checkpoint in summary["checkpoints"]:
        print(f"- {checkpoint['id']}: {checkpoint['status']}")


def run_test_suite(agent: RoadmapAgent, tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    all_traces: List[Dict[str, Any]] = []

    for test_case in tests:
        print("\n==================================================")
        print(f"[{test_case['id']}] {test_case['type']} | complexity={test_case['complexity']}")
        print(f"Expected: {test_case['expected_behavior']}")

        request = RoadmapGenerationRequest(**test_case["request"])
        roadmap, trace = agent.generate_roadmap(request)

        after_generation = test_case.get("afterGeneration", {})
        if after_generation.get("accept"):
            roadmap = agent.accept_roadmap(roadmap.roadmapId, trace)

        complete_first_lessons = int(after_generation.get("completeFirstLessons", 0))
        if complete_first_lessons > 0:
            lesson_ids = [node.id for node in roadmap.nodes if node.type == "LESSON"][:complete_first_lessons]
            for node_id in lesson_ids:
                roadmap = agent.update_progress(roadmap.roadmapId, node_id, "COMPLETED", trace)

        if after_generation.get("reloadAndVerify"):
            reloaded = agent.repository.get(roadmap.roadmapId)
            if reloaded is None:
                raise ValueError(f"Roadmap {roadmap.roadmapId} could not be reloaded from persistence.")
            agent._append_trace(
                trace,
                "RELOAD_ROADMAP",
                roadmap_id=reloaded.roadmapId,
                output={"status": reloaded.status, "node_count": len(reloaded.nodes)},
            )
            roadmap = reloaded

        summary = build_progress_summary(roadmap)
        expected_checkpoint_status = test_case.get("expectedCheckpointStatus")
        if expected_checkpoint_status:
            first_checkpoint = summary["checkpoints"][0]["status"] if summary["checkpoints"] else None
            if first_checkpoint != expected_checkpoint_status:
                raise ValueError(
                    f"Expected first checkpoint status {expected_checkpoint_status}, got {first_checkpoint}."
                )

        print(f"Generated roadmap_id={roadmap.roadmapId} with {summary['total']} lessons")
        print_progress_summary(roadmap)
        all_traces.extend(trace)

    return all_traces


def interactive_mode(agent: RoadmapAgent) -> None:
    print("Interactive Roadmap Agent")
    print("Type 'exit' at any prompt to stop.\n")

    while True:
        goal = input("What do you want to learn? ").strip()
        if not goal or goal.lower() in {"exit", "quit"}:
            break

        topic = input("Topic label (press Enter to reuse the goal): ").strip() or goal
        if topic.lower() in {"exit", "quit"}:
            break

        level = normalize_level(input("Level [BEGINNER/INTERMEDIATE/ADVANCED] (default BEGINNER): ").strip() or "BEGINNER")
        hours_raw = input("Hours per day (optional): ").strip()
        if hours_raw.lower() in {"exit", "quit"}:
            break
        weeks_raw = input("Deadline in weeks (optional): ").strip()
        if weeks_raw.lower() in {"exit", "quit"}:
            break

        constraints = Constraints(
            hoursPerDay=float(hours_raw) if hours_raw else None,
            deadlineWeeks=int(weeks_raw) if weeks_raw else None,
        )
        request = RoadmapGenerationRequest(topic=topic, goal=goal, level=level, constraints=constraints)
        try:
            roadmap, trace = agent.generate_roadmap(request)
            save_waterfall_trace(trace)
            print_roadmap(roadmap)
            print_progress_summary(roadmap)
        except AgentRunError as error:
            if error.trace:
                save_waterfall_trace(error.trace)
            print(f"\nAgent error: {error}")
            retry = input("Please enter the input again, or type 'exit' to stop: ").strip().lower()
            if retry in {"exit", "quit"}:
                break
            continue

        accept = input("Accept this roadmap now? [y/N]: ").strip().lower()
        if accept == "y":
            roadmap = agent.accept_roadmap(roadmap.roadmapId)
            print(f"Roadmap {roadmap.roadmapId} is now {roadmap.status}.")

        while True:
            lesson_choice = input("Enter a lesson id to mark COMPLETED, or press Enter to finish: ").strip()
            if not lesson_choice:
                break
            try:
                roadmap = agent.update_progress(roadmap.roadmapId, lesson_choice, "COMPLETED")
                print_progress_summary(roadmap)
            except ValueError as error:
                print(f"Could not update progress: {error}")

        next_prompt = input("\nPress Enter to ask for another roadmap, or type 'exit' to stop: ").strip().lower()
        if next_prompt in {"exit", "quit"}:
            break


if __name__ == "__main__":
    print("==========================================================")
    print("ROADMAP AGENT MVP")
    print("==========================================================")

    provider = get_llm_provider()
    mcp_server = MCPRoadmapServer()
    repository = FileRoadmapRepository()
    agent = RoadmapAgent(provider, mcp_server, repository)

    print(f"LLM Provider: {provider.__class__.__name__}")
    print(f"MCP Server: {mcp_server.server_name}")
    print(f"Persistence: {repository.storage_path}\n")

    tests = load_test_cases()

    if "--interactive" in sys.argv:
        interactive_mode(agent)
    elif "--all" in sys.argv:
        traces = run_test_suite(agent, tests)
        save_waterfall_trace(traces)
    else:
        interactive_mode(agent)
