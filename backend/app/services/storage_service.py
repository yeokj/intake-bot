import json
import os
from typing import Dict, List, Optional
from app.models.chat import ChatMessage
from app.models.brief import ProjectBrief


class StorageService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        # In-memory cache for fast session lookup
        self._sessions: Dict[str, List[ChatMessage]] = {}
        self._briefs: Dict[str, ProjectBrief] = {}

    def save_messages(self, session_id: str, messages: List[ChatMessage]):
        self._sessions[session_id] = messages
        # Persist session to disk
        file_path = os.path.join(self.data_dir, f"{session_id}_chat.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([m.model_dump() for m in messages], f, indent=2)

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        if session_id in self._sessions:
            return self._sessions[session_id]
        file_path = os.path.join(self.data_dir, f"{session_id}_chat.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                messages = [ChatMessage(**m) for m in raw]
                self._sessions[session_id] = messages
                return messages
        return []

    def save_brief(self, session_id: str, brief: ProjectBrief):
        self._briefs[session_id] = brief
        file_path = os.path.join(self.data_dir, f"{session_id}_brief.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(brief.model_dump(), f, indent=2)

    def get_brief(self, session_id: str) -> Optional[ProjectBrief]:
        if session_id in self._briefs:
            return self._briefs[session_id]
        file_path = os.path.join(self.data_dir, f"{session_id}_brief.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                brief = ProjectBrief(**json.load(f))
                self._briefs[session_id] = brief
                return brief
        return None


storage_service = StorageService()