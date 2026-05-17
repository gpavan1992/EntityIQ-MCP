#!/usr/bin/env python3
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

def generate_sse():
    """Synchronous generator for SSE"""
    yield f"data: {json.dumps({'test': 'works'})}\n\n"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/mcp")
async def mcp_handler(request: Request):
    """Test endpoint"""
    try:
        body = await request.json()
        
        def event_generator():
            yield f"data: {json.dumps({'echo': body, 'status': 'ok'})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
