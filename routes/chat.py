import os
from fastapi import APIRouter, HTTPException
from anthropic import Anthropic, APIStatusError
from models.schemas import ChatRequest, ChatResponse, UsageStats

router = APIRouter(tags=["chat"])
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    # TODO: Add per-IP or per-user rate limiting
    # TODO: Log request metadata (model, token counts, latency) to a database
    try:
        kwargs = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": [m.model_dump() for m in request.messages],
        }
        if request.system:
            kwargs["system"] = request.system

        response = client.messages.create(**kwargs)
    except APIStatusError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.message))

    # TODO: Persist conversation to database for multi-turn history
    return ChatResponse(
        content=response.content[0].text,
        model=response.model,
        usage=UsageStats(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        ),
    )
