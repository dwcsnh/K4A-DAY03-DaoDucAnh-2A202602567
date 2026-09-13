"""
LLM providers for roadmap blueprint generation with a deterministic offline fallback.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


def _extract_json_block(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty LLM response.")

    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    direct = re.search(r"(\{.*\})", text, re.DOTALL)
    if direct:
        return json.loads(direct.group(1))

    raise ValueError("No JSON object found in LLM response.")


def _extract_request_payload(prompt: str) -> Dict[str, Any]:
    match = re.search(
        r"INPUT_REQUEST_JSON_START\s*(\{.*?\})\s*INPUT_REQUEST_JSON_END",
        prompt,
        re.DOTALL,
    )
    if not match:
        return {}
    return json.loads(match.group(1))


def _topic_key(topic: str) -> str:
    lowered = topic.lower()
    if "aws" in lowered or "amazon web services" in lowered:
        return "aws"
    if "docker" in lowered:
        return "docker"
    if "kubernetes" in lowered or "k8s" in lowered:
        return "kubernetes"
    if "python" in lowered:
        return "python"
    if "react" in lowered:
        return "react"
    return "generic"


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.strip().split())


def _looks_like_learning_topic_request(payload: Dict[str, Any]) -> bool:
    goal = _normalize_whitespace(str(payload.get("goal") or "")).lower()
    topic = _normalize_whitespace(str(payload.get("topic") or "")).lower()
    combined = f"{goal} {topic}".strip()

    if not combined:
        return False

    blocked_phrases = {
        "hi",
        "hello",
        "hey",
        "how are you",
        "what can you do",
        "who are you",
        "tell me a joke",
        "thanks",
        "thank you",
    }
    if combined in blocked_phrases:
        return False

    greeting_tokens = {"hi", "hello", "hey", "thanks", "thank", "yo"}
    combined_words = re.findall(r"[a-zA-Z]+", combined)
    if combined_words and all(word in greeting_tokens for word in combined_words):
        return False

    learning_markers = (
        "learn",
        "study",
        "roadmap",
        "topic",
        "beginner",
        "intermediate",
        "advanced",
        "practice",
        "master",
        "understand",
        "want to learn",
        "want to study",
        "hoc",
        "học",
        "lo trinh",
        "lộ trình",
    )
    if any(marker in combined for marker in learning_markers):
        return True

    if "?" in combined:
        return False

    topic_words = re.findall(r"[a-zA-Z0-9+#.\-]+", topic or goal)
    if not topic_words:
        return False

    stopwords = {
        "a",
        "an",
        "the",
        "please",
        "something",
        "anything",
        "this",
        "that",
        "it",
        "roadmap",
        "learn",
        "study",
        "topic",
    }
    meaningful_words = [word for word in topic_words if word not in stopwords]
    return bool(meaningful_words) and len(topic_words) <= 8


def _minutes_for_level(level: str, base: int) -> int:
    if level == "ADVANCED":
        return base + 45
    if level == "INTERMEDIATE":
        return base + 20
    return base


def _generic_areas(topic: str, level: str) -> List[Dict[str, Any]]:
    return [
        {
            "title": f"{topic} Foundations",
            "description": f"Build the vocabulary, core concepts, and mental models needed to learn {topic} effectively.",
            "learningObjectives": [
                f"Explain the main building blocks of {topic}",
                f"Describe where {topic} is used in real projects",
                "Identify the essential terminology with confidence",
            ],
            "estimatedMinutes": _minutes_for_level(level, 75),
        },
        {
            "title": f"Core {topic} Workflow",
            "description": f"Learn the normal end-to-end workflow so you can move from theory into hands-on practice.",
            "learningObjectives": [
                f"Follow a beginner-friendly {topic} workflow",
                f"Use the common tools involved in {topic}",
                "Spot the difference between setup, execution, and troubleshooting steps",
            ],
            "estimatedMinutes": _minutes_for_level(level, 90),
        },
        {
            "title": f"Practical {topic} Exercises",
            "description": f"Reinforce understanding through concrete tasks and guided exercises in {topic}.",
            "learningObjectives": [
                f"Complete a small practice task in {topic}",
                "Debug common beginner mistakes",
                "Reflect on what changed after each iteration",
            ],
            "estimatedMinutes": _minutes_for_level(level, 90),
        },
        {
            "title": f"{topic} Patterns and Tradeoffs",
            "description": f"Understand the common design choices, strengths, and tradeoffs that shape {topic} work.",
            "learningObjectives": [
                f"Compare two or three common {topic} patterns",
                "Explain tradeoffs in simple language",
                "Choose a sensible default for small projects",
            ],
            "estimatedMinutes": _minutes_for_level(level, 100),
        },
        {
            "title": f"{topic} Capstone",
            "description": f"Apply the roadmap in a compact project so the concepts become durable and practical.",
            "learningObjectives": [
                f"Build a small but complete {topic} project",
                "Document the steps, decisions, and lessons learned",
                "Identify the next milestone after the MVP",
            ],
            "estimatedMinutes": _minutes_for_level(level, 120),
        },
    ]


def _template_areas(topic: str, level: str) -> List[Dict[str, Any]]:
    key = _topic_key(topic)
    templates = {
        "aws": [
            ("Cloud Fundamentals", "Understand AWS global infrastructure, pricing basics, and the shared responsibility model.", ["Explain regions and availability zones", "Describe the shared responsibility model", "Match core AWS services to common use cases"], 75),
            ("IAM and Account Security", "Learn users, groups, roles, and least-privilege access patterns before working with services.", ["Create a mental model for IAM entities", "Differentiate users, roles, and policies", "Apply least-privilege thinking to simple scenarios"], 90),
            ("Compute With EC2", "Explore instances, AMIs, storage options, and the EC2 lifecycle through practical examples.", ["Explain how EC2 instances are launched", "Choose an instance type for a simple workload", "Understand the role of AMIs and attached storage"], 105),
            ("Object Storage With S3", "Learn bucket structure, object access, storage classes, and simple hosting patterns.", ["Describe S3 buckets and objects", "Explain how permissions affect access", "Compare common storage classes"], 90),
            ("Networking With VPC", "Understand subnets, route tables, gateways, and security groups so services can communicate safely.", ["Explain the purpose of a VPC", "Describe subnet and route table relationships", "Choose between security groups and network ACLs"], 110),
            ("Architecture and Reliability", "Bring the services together with well-architected patterns, monitoring, and operational thinking.", ["Apply Well-Architected pillars at a high level", "Outline a small resilient AWS architecture", "Identify cost and reliability tradeoffs"], 120),
        ],
        "docker": [
            ("Container Fundamentals", "Build intuition for images, containers, registries, and why containerization matters.", ["Explain the difference between images and containers", "Describe a typical Docker workflow", "Identify common use cases for containers"], 75),
            ("Docker CLI and Local Workflow", "Use the CLI to run, inspect, and manage containers efficiently.", ["Run and stop containers with confidence", "Inspect container state and logs", "Understand the lifecycle of local images"], 90),
            ("Building Images With Dockerfiles", "Create reproducible images with practical Dockerfiles and sensible layering.", ["Read a Dockerfile line by line", "Build a local image for a sample app", "Recognize how layers affect rebuild speed"], 100),
            ("Data Persistence and Volumes", "Keep data outside containers and choose the right storage strategy for development work.", ["Differentiate bind mounts and volumes", "Persist application data safely", "Troubleshoot common file-mount issues"], 95),
            ("Container Networking", "Connect containers, expose ports, and understand how services discover each other.", ["Map ports correctly", "Explain bridge networking basics", "Connect multiple services on a shared network"], 105),
            ("Multi-Container Applications With Compose", "Package a realistic local stack with Compose so services can be run together.", ["Read and write a basic compose file", "Coordinate multiple services locally", "Apply environment variables and service dependencies"], 110),
        ],
        "kubernetes": [
            ("Kubernetes Architecture", "Understand clusters, the control plane, worker nodes, and why orchestration matters.", ["Explain the role of the control plane", "Describe how nodes run workloads", "Connect containers to orchestration concepts"], 80),
            ("Pods and Workloads", "Learn pods, replica management, and the main workload abstractions used in day-to-day practice.", ["Explain what a pod represents", "Compare pods and deployments", "Understand why replicas matter"], 90),
            ("Deployments and Rollouts", "Use manifests to deploy applications and reason about rollout strategies.", ["Read a simple deployment manifest", "Apply and inspect a deployment", "Describe how rollouts and rollbacks work"], 105),
            ("Services and Networking", "Expose workloads correctly and understand service discovery patterns inside the cluster.", ["Differentiate ClusterIP, NodePort, and LoadBalancer", "Explain how services route traffic", "Troubleshoot a basic connectivity issue"], 105),
            ("Configuration and Secrets", "Separate config from code and use the core primitives for safe application delivery.", ["Use ConfigMaps conceptually", "Explain when secrets are needed", "Keep runtime configuration manageable"], 95),
            ("Observability and Operations", "Learn the operational habits that make Kubernetes usable beyond hello-world demos.", ["Inspect workloads with kubectl", "Read common status signals", "Recognize operational tradeoffs in cluster management"], 120),
        ],
        "python": [
            ("Python Syntax and Data Types", "Learn Python syntax, variables, collections, and control flow from a practical lens.", ["Write and read basic Python expressions", "Choose between common collection types", "Follow control flow clearly"], 75),
            ("Functions and Modules", "Organize code into reusable functions and modules as programs grow.", ["Define clean function boundaries", "Import from modules correctly", "Separate reusable logic from scripts"], 90),
            ("Tooling and Virtual Environments", "Set up isolated environments and a healthy local development workflow.", ["Create and activate a virtual environment", "Install packages responsibly", "Explain why dependency isolation matters"], 85),
            ("Files, Errors, and Debugging", "Handle real-world program input and deal with failure cases without panic.", ["Read and write local files", "Catch and raise exceptions intentionally", "Debug small issues step by step"], 95),
            ("Testing With pytest", "Learn the basics of automated tests so code changes stay safe and repeatable.", ["Write a basic pytest test", "Run a test suite locally", "Read a failing assertion and fix the code"], 100),
            ("Build a Small Project", "Consolidate the learning into a small command-line or automation project.", ["Plan a small Python project", "Implement it in manageable pieces", "Reflect on next steps after the first version"], 120),
        ],
        "react": [
            ("React Foundations", "Learn components, JSX, props, and the mental model of declarative UI.", ["Explain what a React component is", "Pass data through props", "Describe why React updates the UI predictably"], 75),
            ("State and Events", "Build interactive interfaces by managing state and handling user events cleanly.", ["Use state to drive UI changes", "Handle common browser events", "Connect user actions to state transitions"], 95),
            ("Rendering Lists and Forms", "Model repeated UI patterns and controlled forms in a maintainable way.", ["Render lists with keys correctly", "Build a controlled form", "Validate and update form state intentionally"], 95),
            ("Effects and Data Fetching", "Understand side effects, data loading, and asynchronous UI updates.", ["Explain when to use an effect", "Fetch data for a simple screen", "Handle loading and error states"], 105),
            ("Component Architecture", "Break features into reusable components and lift state to the right level.", ["Choose component boundaries", "Lift state without overcomplicating the tree", "Identify reusable UI patterns"], 105),
            ("Ship a Mini App", "Apply the roadmap in a small project that combines routing, state, and real UI behavior.", ["Plan a small React feature", "Implement it incrementally", "Evaluate what should improve in a second iteration"], 120),
        ],
    }

    selected = templates.get(key)
    if not selected:
        return _generic_areas(topic, level)

    areas = []
    for title, description, objectives, minutes in selected:
        areas.append(
            {
                "title": title,
                "description": description,
                "learningObjectives": objectives,
                "estimatedMinutes": _minutes_for_level(level, minutes),
            }
        )
    return areas


def _build_mock_blueprint(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not _looks_like_learning_topic_request(payload):
        return {
            "status": "REJECTED",
            "message": "Please enter your input again with a topic you want to learn.",
        }

    topic = payload.get("topic") or "Learning Goal"
    goal = payload.get("goal") or f"Learn {topic} effectively."
    level = payload.get("level") or "BEGINNER"
    return {
        "status": "READY",
        "title": f"{topic} Learning Roadmap",
        "topic": topic,
        "goal": goal,
        "areas": _template_areas(topic, level),
    }


class BaseLLMProvider:
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    def __init__(self):
        self.model_name = "offline-roadmap-mock-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"Offline mock provider received: {prompt}"

    def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        payload = _extract_request_payload(prompt)
        return _build_mock_blueprint(payload)


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return MockOfflineProvider().generate(prompt, system_prompt)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=0.2,
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception:
            return MockOfflineProvider().generate(prompt, system_prompt)

    def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return MockOfflineProvider().generate_json(prompt, system_prompt)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=0.2,
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            return json.loads(response.text or "{}")
        except Exception:
            return MockOfflineProvider().generate_json(prompt, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return MockOfflineProvider().generate(prompt, system_prompt)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except Exception:
            return MockOfflineProvider().generate(prompt, system_prompt)

    def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return MockOfflineProvider().generate_json(prompt, system_prompt)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            text = response.choices[0].message.content or "{}"
            return json.loads(text)
        except Exception:
            raw_text = self.generate(prompt, system_prompt)
            try:
                return _extract_json_block(raw_text)
            except Exception:
                return MockOfflineProvider().generate_json(prompt, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    provider_type = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider_type == "gemini":
        return GeminiProvider()
    if provider_type == "openai":
        return OpenAIProvider()
    return MockOfflineProvider()
