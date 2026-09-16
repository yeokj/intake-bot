from fastapi import APIRouter, HTTPException, Query
from app.models.brief import ProjectBrief
from app.services.llm_service import llm_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/brief", tags=["Brief"])


@router.post("/generate", response_model=ProjectBrief)
async def generate_project_brief(session_id: str = Query(..., description="Session identifier")):
    messages = storage_service.get_messages(session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="No conversation history found for this session.")

    try:
        brief = await llm_service.generate_brief(messages)
        storage_service.save_brief(session_id, brief)
        return brief
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate brief: {str(e)}")


@router.get("/{session_id}", response_model=ProjectBrief)
async def get_saved_brief(session_id: str):
    brief = storage_service.get_brief(session_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found for this session.")
    return brief