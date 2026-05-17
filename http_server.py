#!/usr/bin/env python3
import asyncio
import json
import sys
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import subprocess
from typing import AsyncGenerator

app = FastAPI()
mcp_process = None
request_id_counter = 0
pending_responses = {}

async def mcp_writer(request_data: dict):
    """Send request to MCP server and stream responses"""
    global request_id_counter, pending_responses
    
    request_id_counter += 1
    request_id = request_id_counter
    request_data['id'] = request_id
    
    # Send request to MCP subprocess
    request_line = json.dumps(request_data) + "\n"
    mcp_process.stdin.write(request_line)
    mcp_process.stdin.flush()
    
    # Read response
    loop = asyncio.get_event_loop()
    response_line = await loop.run_in_executor(None, mcp_process.stdout.readline)
    
    if response_line:
        return json.loads(response_line)
    return {"error": "No response from MCP"}

async def stream_sse(request_data: dict) -> AsyncGenerator[str, None]:
    """Stream MCP responses as SSE"""
    try:
        response = await mcp_writer(request_data)
        # SSE format: data: {json}\n\n
        yield f"data: {json.dumps(response)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_process
    mcp_process = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    yield
    if mcp_process:
        mcp_process.terminate()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/mcp")
async def mcp_handler(request: Request):
    """Handle both JSON-RPC and SSE requests"""
    try:
        request_data = await request.json()
    except:
        return {"error": "Invalid JSON"}
    
    # If it's an SSE request, stream responses
    if request.headers.get('accept') == 'text/event-stream':
        return StreamingResponse(stream_sse(request_data), media_type="text/event-stream")
    
    # Otherwise return JSON directly
    response = await mcp_writer(request_data)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
