"""
File-backed persistence for roadmap drafts and progress state.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from roadmap_models import Roadmap, build_progress_summary, model_to_dict, recalculate_checkpoint_statuses


class FileRoadmapRepository:
    def __init__(self, storage_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = storage_path or os.path.join(base_dir, "data", "roadmaps.json")
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as file:
                json.dump({}, file, ensure_ascii=False, indent=2)

    def _load_store(self) -> Dict[str, Dict[str, object]]:
        with open(self.storage_path, "r", encoding="utf-8") as file:
            content = json.load(file)
        return content if isinstance(content, dict) else {}

    def _save_store(self, store: Dict[str, Dict[str, object]]) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as file:
            json.dump(store, file, ensure_ascii=False, indent=2)

    def _touch(self, roadmap: Roadmap) -> Roadmap:
        roadmap.updatedAt = self._now_iso()
        return roadmap

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def save(self, roadmap: Roadmap) -> Roadmap:
        roadmap.nodes = recalculate_checkpoint_statuses(roadmap.nodes)
        roadmap = self._touch(roadmap)
        store = self._load_store()
        store[roadmap.roadmapId] = model_to_dict(roadmap)
        self._save_store(store)
        return roadmap

    def get(self, roadmap_id: str) -> Optional[Roadmap]:
        store = self._load_store()
        data = store.get(roadmap_id)
        if not data:
            return None
        return Roadmap(**data)

    def list(self) -> List[Roadmap]:
        return [Roadmap(**item) for item in self._load_store().values()]

    def accept(self, roadmap_id: str) -> Roadmap:
        roadmap = self.get(roadmap_id)
        if roadmap is None:
            raise ValueError(f"Roadmap '{roadmap_id}' does not exist.")
        roadmap.status = "ACTIVE"
        return self.save(roadmap)

    def update_progress(self, roadmap_id: str, node_id: str, status: str) -> Roadmap:
        roadmap = self.get(roadmap_id)
        if roadmap is None:
            raise ValueError(f"Roadmap '{roadmap_id}' does not exist.")

        valid_statuses = {"NOT_STARTED", "LEARNING", "COMPLETED"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid lesson status '{status}'.")

        target = next((node for node in roadmap.nodes if node.id == node_id), None)
        if target is None:
            raise ValueError(f"Node '{node_id}' does not exist in roadmap '{roadmap_id}'.")
        if target.type != "LESSON":
            raise ValueError("Only lesson nodes can be updated manually.")

        target.status = status
        roadmap.nodes = recalculate_checkpoint_statuses(roadmap.nodes)
        return self.save(roadmap)

    def get_progress(self, roadmap_id: str) -> Dict[str, object]:
        roadmap = self.get(roadmap_id)
        if roadmap is None:
            raise ValueError(f"Roadmap '{roadmap_id}' does not exist.")
        return build_progress_summary(roadmap)
