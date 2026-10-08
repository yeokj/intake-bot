import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
import httpx

from app.core.config import settings
from app.models.brief import ProjectBrief
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class BaseDeliveryHandler(ABC):
    @abstractmethod
    async def deliver(
        self, session_id: str, brief: ProjectBrief, transcript: List[ChatMessage]
    ) -> Dict[str, Any]:
        """Dispatches brief and transcript to the destination channel."""
        pass


class LocalFileDeliveryHandler(BaseDeliveryHandler):
    """
    Guaranteed local persistence. Logs deliveries to disk so no intake
    record is lost if remote services or credentials are not yet configured.
    """
    def __init__(self, output_dir: str = "data/deliveries"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    async def deliver(
        self, session_id: str, brief: ProjectBrief, transcript: List[ChatMessage]
    ) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{session_id}.json"
        filepath = os.path.join(self.output_dir, filename)

        payload = {
            "session_id": session_id,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "brief": brief.model_dump(),
            "transcript": [m.model_dump() for m in transcript],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info(f"Delivered brief locally to {filepath}")
        return {"channel": "local", "status": "success", "file": filepath}


class AirtableDeliveryHandler(BaseDeliveryHandler):
    """
    Dispatches the structured ProjectBrief directly to an Airtable Base.
    """
    def __init__(self):
        self.api_key = settings.AIRTABLE_API_KEY
        self.base_id = settings.AIRTABLE_BASE_ID
        self.table_name = settings.AIRTABLE_TABLE_NAME

    async def deliver(
        self, session_id: str, brief: ProjectBrief, transcript: List[ChatMessage]
    ) -> Dict[str, Any]:
        if not self.api_key or not self.base_id:
            logger.info("Airtable delivery skipped: Missing credentials in config.")
            return {
                "channel": "airtable",
                "status": "skipped",
                "reason": "Missing API Key or Base ID",
            }

        url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        raw_transcript = "\n".join([f"{m.role.upper()}: {m.content}" for m in transcript])

        fields = {
            "Client / Business": brief.client_name_or_business,
            "Business Type": brief.business_type,
            "Suggested Service": brief.suggested_service_category,
            "Budget Range": brief.rough_budget_range,
            "Timeline": brief.target_timeline,
            "Current Situation": brief.current_situation,
            "Goals & Needs": "\n• " + "\n• ".join(brief.goals_and_needs),
            "Flagged Unknowns": "\n• " + "\n• ".join(brief.flagged_unknowns),
            "Session ID": session_id,
            "Full Transcript": raw_transcript,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json={"fields": fields})
                if response.status_code in (200, 201):
                    record_id = response.json().get("id")
                    logger.info(f"Delivered brief to Airtable. Record ID: {record_id}")
                    return {"channel": "airtable", "status": "success", "record_id": record_id}
                else:
                    logger.error(f"Airtable delivery failed: {response.text}")
                    return {"channel": "airtable", "status": "failed", "error": response.text}
        except Exception as e:
            logger.error(f"Airtable delivery error: {str(e)}")
            return {"channel": "airtable", "status": "error", "error": str(e)}


class DeliveryService:
    def __init__(self):
        self.local_handler = LocalFileDeliveryHandler()
        self.airtable_handler = AirtableDeliveryHandler()

    async def dispatch_brief(
        self, session_id: str, brief: ProjectBrief, transcript: List[ChatMessage]
    ) -> Dict[str, Any]:
        """
        Coordinates delivery across configured channels with guaranteed local fallback.
        """
        channels = [c.strip().lower() for c in settings.DELIVERY_CHANNELS.split(",") if c.strip()]
        results = {}

        # 1. Local disk backup is always written
        results["local"] = await self.local_handler.deliver(session_id, brief, transcript)

        # 2. Airtable if enabled in DELIVERY_CHANNELS
        if "airtable" in channels:
            results["airtable"] = await self.airtable_handler.deliver(session_id, brief, transcript)

        return results


delivery_service = DeliveryService()