from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse, ChatMessage
from app.services.llm_service import llm_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat_interaction(request: ChatRequest):
    try:
        # Save inbound messages to storage
        storage_service.save_messages(request.session_id, request.messages)

        # Call LLM service to get the next bot turn
        reply_text, is_complete = await llm_service.get_next_response(request.messages)

        assistant_msg = ChatMessage(role="assistant", content=reply_text)

        # Append assistant reply to session history
        updated_messages = request.messages + [assistant_msg]
        storage_service.save_messages(request.session_id, updated_messages)

        return ChatResponse(
            session_id=request.session_id,
            message=assistant_msg,
            is_ready_for_brief=is_complete,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))