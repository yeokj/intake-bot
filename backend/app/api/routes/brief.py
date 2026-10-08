import logging
from fastapi import APIRouter, HTTPException, Query
from app.models.brief import ProjectBrief
from app.services.llm_service import llm_service
from app.services.storage_service import storage_service
from app.services.delivery import delivery_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brief", tags=["Brief"])


@router.post("/generate", response_model=ProjectBrief)
async def generate_project_brief(
    session_id: str = Query(..., description="Session identifier")
):
    messages = storage_service.get_messages(session_id)
    if not messages:
        raise HTTPException(
            status_code=404,
            detail="No conversation history found for this session."
        )

    try:
        # 1. Generate structured brief
        brief = await llm_service.generate_brief(messages)
        storage_service.save_brief(session_id, brief)

        # 2. Dispatch to delivery pipeline (local disk backup + Airtable if configured)
        delivery_results = await delivery_service.dispatch_brief(session_id, brief, messages)
        logger.info(f"Delivery results for session {session_id}: {delivery_results}")

        return brief
    except Exception as e:
        logger.error(f"Failed to generate and deliver brief: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate brief: {str(e)}"
        )


@router.get("/{session_id}", response_model=ProjectBrief)
async def get_saved_brief(session_id: str):
    brief = storage_service.get_brief(session_id)
    if not brief:
        raise HTTPException(
            status_code=404,
            detail="Brief not found for this session."
        )
    return brief