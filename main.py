import json
import os
import uuid
import time
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from coze_client import CozeClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
bot_id = os.getenv("BOT_ID")

# Ensure necessary environment variables are set
assert bot_id, "BOT_ID not found in environment variables"

# Initialize FastAPI
app = FastAPI()


# Define request and response models
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    user: Optional[str] = None
    stream: Optional[bool] = False


class ChatCompletionResponseChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionResponseChoice(BaseModel):
    index: int
    delta: ChatCompletionResponseChoiceDelta
    logprobs: Optional[dict] = None
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Optional[dict] = None


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, authorization: str = Header(None)):
    """
    Endpoint to handle chat completions.
    """
    try:
        # Extract token from the Authorization header
        if not authorization:
            raise HTTPException(status_code=400, detail="Authorization header missing")
        token = authorization.split(" ")[1]

        # Initialize CozeClient with the token
        coze_client = CozeClient(token)

        # Prepare the request for CozeClient
        coze_request = {
            "bot_id": bot_id,
            "user": request.user if request.user else "default_user",
            "query": request.messages[-1].content,
            "chat_history": [{"role": msg.role, "content": msg.content} for msg in request.messages[:-1]],
            "stream": request.stream
        }

        # Handle streaming responses
        if request.stream:
            return StreamingResponse(event_generator(coze_request, request.model, coze_client),
                                     media_type="text/event-stream")

        # Handle non-streaming responses
        else:
            response = coze_client.chat_non_stream(coze_request)
            return JSONResponse(content=format_response(response, request.model))

    except Exception as e:
        # Handle any exceptions that occur and return a 500 error
        raise HTTPException(status_code=500, detail=str(e))


async def event_generator(coze_request, model, coze_client):
    """
    Asynchronous generator to handle streaming responses.
    """
    async for stream_resp in coze_client.chat_stream(coze_request):
        print(stream_resp)
        yield format_stream_response(stream_resp, model)
        if stream_resp.get("is_finish"):
            yield format_finish_response(model)
            break


def format_response(response, model):
    """
    Format the response for non-streaming chat completions.
    """
    if response.get("messages") is not None and len(response.get("messages")) > 0:
        content = response.get("messages", {})[0].get("content", "")
    else:
        raise HTTPException(status_code=400, detail="No content found in response")
    return {
        "id": "chatcmpl-" + str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content
            },
            "logprobs": None,
            "finish_reason": "stop"
        }],
        "usage": response.get("usage")
    }


def format_stream_response(stream_resp, model):
    """
    Format the response for each chunk of streaming chat completions.
    """
    delta = {
        "role": stream_resp.get("message", {}).get("role"),
        "content": stream_resp.get("message", {}).get("content", "")
    }
    if "role" in stream_resp:
        delta["role"] = stream_resp["role"]

    response = {
        "id": "chatcmpl-" + str(uuid.uuid4()),
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": delta,
            "logprobs": None,
            "finish_reason": None
        }]
    }
    return f"{json.dumps(response)}\n"


def format_finish_response(model):
    """
    Format the final response to indicate the end of a streaming chat completion.
    """
    finish_response = {
        "id": "chatcmpl-" + str(uuid.uuid4()),
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "logprobs": None,
            "finish_reason": "stop"
        }]
    }
    return f"{json.dumps(finish_response)}\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)