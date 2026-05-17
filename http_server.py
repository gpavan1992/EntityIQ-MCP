#!/usr/bin/env python3
import asyncio
import json
import sys
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse
from contextlib import asynccontextmanager
import subprocess

app = FastAPI()
mcp_process = None
request_counter = 0

async def send_mcp_request(request_data: dict):
    """Send request to MCP process and get response"""
    global request_counter, mcp_process
    
    request_counter += 1
    msg_id = request_counter
    request_data['id'] = msg_id
    
    # Send to MCP
    request_line = json.dumps(request_data) + "\n"
    mcp_process.stdin.write(request_line)
    mcp_process.stdin.flush()
    
    # Read response
    loop = asyncio.get_event_loop()
    response_line = await loop.run_in_executor(None, mcp_process.stdout.readline)
    
    if response_line:
        return json.loads(response_line)
    return {"error": "No response"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_process
    mcp_process = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd="/Users/gpavan92/Desktop/entityiq-mcp"
    )
    yield
    if mcp_process:
        mcp_process.terminate()
        mcp_process.wait()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/mcp")
async def mcp_handler(request: Request):
    """Handle MCP requests via HTTP POST with JSON-RPC"""
    try:
        body = await request.json()
    except:
        return {"error": "Invalid JSON"}
    
    response = await send_mcp_request(body)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
