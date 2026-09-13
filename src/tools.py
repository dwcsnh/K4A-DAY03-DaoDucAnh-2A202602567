"""
External resource tools exposed through the local MCP server.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests


class ResourceSearchError(RuntimeError):
    """Raised when live resource search fails or returns no usable results."""


TOOLS_SCHEMA = [
    {
        "name": "search_resources",
        "description": "Search external learning resources for a roadmap lesson or topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing the learning area to research."
                },
                "topic": {
                    "type": "string",
                    "description": "The main roadmap topic, such as AWS or Docker."
                },
                "level": {
                    "type": "string",
                    "description": "Learner level: BEGINNER, INTERMEDIATE, or ADVANCED."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of resources to return.",
                    "default": 5
                }
            },
            "required": ["query", "topic"]
        }
    },
    {
        "name": "get_resource_details",
        "description": "Fetch detailed metadata for a resource returned from search_resources.",
        "parameters": {
            "type": "object",
            "properties": {
                "resource_id": {
                    "type": "string",
                    "description": "The identifier of the resource returned by search_resources."
                }
            },
            "required": ["resource_id"]
        }
    }
]


MOCK_RESOURCE_CATALOG: List[Dict[str, Any]] = [
    {
        "resource_id": "aws-cloud-basics",
        "topic": "aws",
        "level": "BEGINNER",
        "title": "Amazon EC2 Regions and Availability Zones",
        "url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html",
        "type": "DOCUMENTATION",
        "description": "Explains AWS regions, availability zones, and how global infrastructure is organized.",
        "source": "docs.aws.amazon.com",
        "keywords": ["aws", "cloud", "regions", "availability zones", "infrastructure", "basics"],
    },
    {
        "resource_id": "aws-shared-responsibility",
        "topic": "aws",
        "level": "BEGINNER",
        "title": "AWS Shared Responsibility Model",
        "url": "https://aws.amazon.com/compliance/shared-responsibility-model/",
        "type": "DOCUMENTATION",
        "description": "Introduces the security ownership model that underpins AWS services.",
        "source": "aws.amazon.com",
        "keywords": ["aws", "security", "shared responsibility", "compliance", "fundamentals"],
    },
    {
        "resource_id": "aws-iam",
        "topic": "aws",
        "level": "BEGINNER",
        "title": "AWS IAM User Guide Introduction",
        "url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
        "type": "DOCUMENTATION",
        "description": "Covers users, groups, roles, and policies in AWS IAM.",
        "source": "docs.aws.amazon.com",
        "keywords": ["aws", "iam", "security", "roles", "policies", "identity"],
    },
    {
        "resource_id": "aws-ec2",
        "topic": "aws",
        "level": "BEGINNER",
        "title": "Amazon EC2 Concepts",
        "url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html",
        "type": "DOCUMENTATION",
        "description": "Walks through AMIs, instances, storage, networking, and pricing concepts for EC2.",
        "source": "docs.aws.amazon.com",
        "keywords": ["aws", "ec2", "compute", "instances", "amis", "pricing"],
    },
    {
        "resource_id": "aws-s3",
        "topic": "aws",
        "level": "BEGINNER",
        "title": "Amazon S3 User Guide",
        "url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html",
        "type": "DOCUMENTATION",
        "description": "Covers buckets, objects, storage classes, permissions, and S3 basics.",
        "source": "docs.aws.amazon.com",
        "keywords": ["aws", "s3", "storage", "buckets", "objects", "permissions"],
    },
    {
        "resource_id": "aws-vpc",
        "topic": "aws",
        "level": "INTERMEDIATE",
        "title": "What is Amazon VPC?",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html",
        "type": "DOCUMENTATION",
        "description": "Introduces VPC networking concepts such as subnets, route tables, and gateways.",
        "source": "docs.aws.amazon.com",
        "keywords": ["aws", "networking", "vpc", "subnets", "routing", "security groups"],
    },
    {
        "resource_id": "aws-well-architected",
        "topic": "aws",
        "level": "INTERMEDIATE",
        "title": "AWS Well-Architected Framework",
        "url": "https://aws.amazon.com/architecture/well-architected/",
        "type": "DOCUMENTATION",
        "description": "A practical framework for designing secure, reliable, and efficient AWS systems.",
        "source": "aws.amazon.com",
        "keywords": ["aws", "architecture", "reliability", "performance", "cost", "well architected"],
    },
    {
        "resource_id": "docker-get-started",
        "topic": "docker",
        "level": "BEGINNER",
        "title": "Docker Get Started",
        "url": "https://docs.docker.com/get-started/",
        "type": "DOCUMENTATION",
        "description": "A guided introduction to containers, images, and the Docker workflow.",
        "source": "docs.docker.com",
        "keywords": ["docker", "containers", "basics", "cli", "workflow", "images"],
    },
    {
        "resource_id": "docker-dockerfile",
        "topic": "docker",
        "level": "BEGINNER",
        "title": "Dockerfile Overview",
        "url": "https://docs.docker.com/build/concepts/dockerfile/",
        "type": "DOCUMENTATION",
        "description": "Explains how Dockerfiles are structured and how images are built reproducibly.",
        "source": "docs.docker.com",
        "keywords": ["docker", "dockerfile", "images", "build", "layers"],
    },
    {
        "resource_id": "docker-networking",
        "topic": "docker",
        "level": "INTERMEDIATE",
        "title": "Docker Engine Networking Overview",
        "url": "https://docs.docker.com/engine/network/",
        "type": "DOCUMENTATION",
        "description": "Covers bridge, host, overlay, and container networking patterns.",
        "source": "docs.docker.com",
        "keywords": ["docker", "networking", "ports", "dns", "bridge", "containers"],
    },
    {
        "resource_id": "docker-storage",
        "topic": "docker",
        "level": "INTERMEDIATE",
        "title": "Docker Storage",
        "url": "https://docs.docker.com/engine/storage/",
        "type": "DOCUMENTATION",
        "description": "Introduces volumes, bind mounts, and persistence patterns for containers.",
        "source": "docs.docker.com",
        "keywords": ["docker", "storage", "volumes", "mounts", "persistence"],
    },
    {
        "resource_id": "docker-compose",
        "topic": "docker",
        "level": "INTERMEDIATE",
        "title": "Docker Compose Overview",
        "url": "https://docs.docker.com/compose/",
        "type": "DOCUMENTATION",
        "description": "Shows how to define and run multi-container applications with Compose.",
        "source": "docs.docker.com",
        "keywords": ["docker", "compose", "multi-container", "services", "workflow"],
    },
    {
        "resource_id": "k8s-overview",
        "topic": "kubernetes",
        "level": "BEGINNER",
        "title": "Kubernetes Concepts Overview",
        "url": "https://kubernetes.io/docs/concepts/overview/",
        "type": "DOCUMENTATION",
        "description": "Introduces the core architecture and concepts of Kubernetes.",
        "source": "kubernetes.io",
        "keywords": ["kubernetes", "overview", "cluster", "control plane", "concepts"],
    },
    {
        "resource_id": "k8s-pods",
        "topic": "kubernetes",
        "level": "BEGINNER",
        "title": "Pods",
        "url": "https://kubernetes.io/docs/concepts/workloads/pods/",
        "type": "DOCUMENTATION",
        "description": "Explains the smallest deployable unit in Kubernetes and how pods behave.",
        "source": "kubernetes.io",
        "keywords": ["kubernetes", "pods", "containers", "workloads"],
    },
    {
        "resource_id": "k8s-deployments",
        "topic": "kubernetes",
        "level": "INTERMEDIATE",
        "title": "Run a Stateless Application Using a Deployment",
        "url": "https://kubernetes.io/docs/tasks/run-application/run-stateless-application-deployment/",
        "type": "DOCUMENTATION",
        "description": "A practical deployment walkthrough using manifests and rollout commands.",
        "source": "kubernetes.io",
        "keywords": ["kubernetes", "deployment", "rollout", "replicas", "manifest"],
    },
    {
        "resource_id": "k8s-services",
        "topic": "kubernetes",
        "level": "INTERMEDIATE",
        "title": "Service",
        "url": "https://kubernetes.io/docs/concepts/services-networking/service/",
        "type": "DOCUMENTATION",
        "description": "Covers service discovery, load balancing, and pod exposure strategies.",
        "source": "kubernetes.io",
        "keywords": ["kubernetes", "services", "networking", "discovery", "load balancing"],
    },
    {
        "resource_id": "python-tutorial",
        "topic": "python",
        "level": "BEGINNER",
        "title": "The Python Tutorial",
        "url": "https://docs.python.org/3/tutorial/",
        "type": "DOCUMENTATION",
        "description": "Official Python tutorial covering syntax, data structures, functions, and modules.",
        "source": "docs.python.org",
        "keywords": ["python", "basics", "syntax", "functions", "modules"],
    },
    {
        "resource_id": "python-venv",
        "topic": "python",
        "level": "BEGINNER",
        "title": "venv - Creation of virtual environments",
        "url": "https://docs.python.org/3/library/venv.html",
        "type": "DOCUMENTATION",
        "description": "Explains isolated Python environments and dependency management basics.",
        "source": "docs.python.org",
        "keywords": ["python", "venv", "virtual environments", "tooling", "dependencies"],
    },
    {
        "resource_id": "pytest-start",
        "topic": "python",
        "level": "INTERMEDIATE",
        "title": "Getting Started With pytest",
        "url": "https://docs.pytest.org/en/stable/getting-started.html",
        "type": "DOCUMENTATION",
        "description": "A hands-on introduction to writing and running automated tests with pytest.",
        "source": "docs.pytest.org",
        "keywords": ["python", "testing", "pytest", "quality", "automation"],
    },
    {
        "resource_id": "react-learn",
        "topic": "react",
        "level": "BEGINNER",
        "title": "React Learn",
        "url": "https://react.dev/learn",
        "type": "DOCUMENTATION",
        "description": "Official React learning path covering components, state, effects, and thinking in React.",
        "source": "react.dev",
        "keywords": ["react", "components", "state", "hooks", "frontend"],
    },
    {
        "resource_id": "react-state",
        "topic": "react",
        "level": "BEGINNER",
        "title": "Managing State",
        "url": "https://react.dev/learn/managing-state",
        "type": "DOCUMENTATION",
        "description": "Shows how state flows through components and how to structure UI updates.",
        "source": "react.dev",
        "keywords": ["react", "state", "props", "ui", "frontend"],
    },
]

LIVE_RESOURCE_CACHE: Dict[str, Dict[str, Any]] = {}


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _topic_slug(topic: str) -> str:
    lowered = _normalize(topic)
    if "amazon web services" in lowered or "aws" in lowered:
        return "aws"
    if "docker" in lowered:
        return "docker"
    if "kubernetes" in lowered or "k8s" in lowered:
        return "kubernetes"
    if "react" in lowered:
        return "react"
    if "python" in lowered:
        return "python"
    return lowered


def _score_catalog_item(item: Dict[str, Any], query: str, topic: str, level: str) -> int:
    query_terms = set(_normalize(query).split())
    topic_terms = set(_normalize(topic).split())
    keywords = set(item.get("keywords", []))
    searchable = set(_normalize(item["title"]).split()) | set(_normalize(item["description"]).split())

    score = 0
    score += len(query_terms & searchable) * 3
    score += len(query_terms & keywords) * 4
    score += len(topic_terms & searchable) * 2
    if item.get("topic") == _topic_slug(topic):
        score += 6
    if level and item.get("level") == level.upper():
        score += 1
    return score


def _serialize_resource(item: Dict[str, Any], score: int) -> Dict[str, Any]:
    return {
        "resource_id": item["resource_id"],
        "title": item["title"],
        "url": item["url"],
        "type": item["type"],
        "description": item["description"],
        "source": item["source"],
        "level": item["level"],
        "score": score,
    }


def _search_catalog(query: str, topic: str, level: str, max_results: int) -> List[Dict[str, Any]]:
    scored = []
    for item in MOCK_RESOURCE_CATALOG:
        score = _score_catalog_item(item, query, topic, level)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["title"]))
    results = [_serialize_resource(item, score) for score, item in scored[:max_results]]
    return results


def _search_tavily(query: str, topic: str, max_results: int) -> Optional[List[Dict[str, Any]]]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": f"{topic} {query}",
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return None

    raw_results = payload.get("results", [])
    if not raw_results:
        raise ResourceSearchError(
            f"Tavily did not return any resources for query '{query}' under topic '{topic}'."
        )

    results = []
    for index, item in enumerate(raw_results, start=1):
        resource_id = f"live-{abs(hash(item.get('url', '')))}-{index}"
        source = urlparse(item.get("url", "")).netloc or "unknown"
        resource = {
            "resource_id": resource_id,
            "title": item.get("title") or f"{topic} resource {index}",
            "url": item.get("url") or "",
            "type": "ARTICLE",
            "description": (item.get("content") or "").strip()[:280],
            "source": source,
            "level": "UNKNOWN",
            "score": max_results - index + 1,
        }
        LIVE_RESOURCE_CACHE[resource_id] = resource
        results.append(resource)
    return results


def execute_search_resources(query: str, topic: str, level: str = "BEGINNER", max_results: int = 5) -> str:
    limit = max(1, min(int(max_results), 8))
    source_mode = "mock_catalog"

    if os.getenv("TAVILY_API_KEY"):
        live_results = _search_tavily(query, topic, limit)
        if live_results is None:
            results = _search_catalog(query, topic, level, limit)
            source_mode = "mock_catalog_fallback"
        else:
            results = live_results
            source_mode = "tavily"
    else:
        results = _search_catalog(query, topic, level, limit)

    status = "SUCCESS" if results else "NO_RESULTS"
    return json.dumps(
        {
            "status": status,
            "query": query,
            "topic": topic,
            "results": results,
            "source_mode": source_mode,
        },
        ensure_ascii=False,
    )


def execute_get_resource_details(resource_id: str) -> str:
    for item in MOCK_RESOURCE_CATALOG:
        if item["resource_id"] == resource_id:
            return json.dumps(
                {
                    "status": "SUCCESS",
                    "resource": _serialize_resource(item, score=10),
                },
                ensure_ascii=False,
            )

    live_item = LIVE_RESOURCE_CACHE.get(resource_id)
    if live_item:
        return json.dumps(
            {
                "status": "SUCCESS",
                "resource": live_item,
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "NOT_FOUND",
            "message": f"Resource '{resource_id}' was not found in the MCP catalog.",
        },
        ensure_ascii=False,
    )


TOOL_ROUTER = {
    "search_resources": execute_search_resources,
    "get_resource_details": execute_get_resource_details,
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    handler = TOOL_ROUTER.get(tool_name)
    if handler is None:
        return json.dumps(
            {
                "status": "UNKNOWN_TOOL",
                "error": f"Tool '{tool_name}' does not exist.",
            },
            ensure_ascii=False,
        )

    try:
        return handler(**arguments)
    except Exception as error:
        return json.dumps(
            {
                "status": "EXECUTION_ERROR",
                "error": str(error),
            },
            ensure_ascii=False,
        )
