#!/usr/bin/env python3
import asyncio
import json
import sys
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import subprocess
import os

app = FastAPI()
mcp_process = None
request_counter = 0
lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_process
    print("Starting MCP server subprocess...", file=sys.stderr)
    mcp_process = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    print(f"MCP process started with PID {mcp_process.pid}", file=sys.stderr)
    yield
    if mcp_process:
        mcp_process.terminate()
        try:
            mcp_process.wait(timeout=5)
        except:
            mcp_process.kill()

app = FastAPI(lifespan=lifespan)

async def send_to_mcp(data: dict) -> dict:
    """Send JSON to MCP process and read response"""
    global request_counter, mcp_process
    
    async with lock:
        request_counter += 1
        data['id'] = request_counter
        
        request_line = json.dumps(data) + "\n"
        print(f"Sending to MCP: {request_line}", file=sys.stderr)
        mcp_process.stdin.write(request_line)
        mcp_process.stdin.flush()
        
        loop = asyncio.get_event_loop()
        response_line = await loop.run_in_executor(None, mcp_process.stdout.readline)
        print(f"Got response: {response_line}", file=sys.stderr)
        
        if response_line:
            try:
                return json.loads(response_line)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from MCP"}
        return {"error": "No response from MCP"}

async def sse_stream(request_body: dict):
    """Stream MCP messages via SSE"""
    try:
        print(f"SSE stream called with: {request_body}", file=sys.stderr)
        response = await send_to_mcp(request_body)
        print(f"About to yield SSE: {response}", file=sys.stderr)
        
        yield f"data: {json.dumps(response)}\n\n"
        
    except Exception as e:
        print(f"SSE error: {e}", file=sys.stderr)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/mcp")
async def mcp_handler(request: Request):
    """Handle MCP protocol via SSE streaming"""
    try:
        body = await request.json()
    except Exception as e:
        return {"error": f"Invalid JSON: {str(e)}"}
    
    return StreamingResponse(
        sse_stream(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
