from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from utils.xunfei_spark import XunFeiSpark
import json
from schemas.aigc import ChatRequest
import os
import requests

router = APIRouter(tags=["星火大模型"])
SPARK_API_URL = os.getenv('AIGC_API_URL')

@router.post("/api/chat")
async def chat_with_spark(request: ChatRequest):
    headers = {
        "Authorization": f"Bearer {os.getenv('AIGC_API_PASSWORD')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": request.model,
        "messages": request.messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "stream": request.stream
    }

    try:
        if request.stream:
            # 流式处理
            response = requests.post(
                SPARK_API_URL,
                headers=headers,
                json=payload,
                stream=True
            )
            
            def generate():
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data:"):
                            yield decoded_line[5:].strip() + "\n\n"
                            
            return generate()
            
        else:
            # 非流式处理
            response = requests.post(
                SPARK_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
            result = response.json()
            if result.get("code") != 0:
                raise HTTPException(status_code=500, detail=result.get("message"))
                
            return {
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage"),
                "status": "success"  # 添加明确状态标识
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))