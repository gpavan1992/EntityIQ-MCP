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
    print("Starting MCP server subprocess...", file=sys.stderr, flush=True)
    mcp_process = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    print(f"MCP process started with PID {mcp_process.pid}", file=sys.stderr, flush=True)
    
    # Give subprocess time to start
    await asyncio.sleep(1)
    yield
    
    if mcp_process:
        mcp_process.terminate()
        try:
            mcp_process.wait(timeout=5)
        except:
            mcp_process.kill()

app = FastAPI(lifespan=lifespan)

async def send_to_mcp(data: dict) -> dict:
    """Send JSON to MCP process and read response with timeout"""
    global request_counter, mcp_process
    
    async with lock:
        request_counter += 1
        data['id'] = request_counter
        
        request_line = json.dumps(data) + "\n"
        print(f"[REQ {request_counter}] Sending: {request_line[:100]}", file=sys.stderr, flush=True)
        
        try:
            mcp_process.stdin.write(request_line)
            mcp_process.stdin.flush()
        except Exception as e:
            print(f"[REQ {request_counter}] WRITE ERROR: {e}", file=sys.stderr, flush=True)
            return {"error": f"Failed to write to MCP: {str(e)}"}
        
        # Read with timeout
        try:
            loop = asyncio.get_event_loop()
            response_line = await asyncio.wait_for(
                loop.run_in_executor(None, mcp_process.stdout.readline),
                timeout=5.0
            )
            print(f"[REQ {request_counter}] Got response: {response_line[:100] if response_line else 'EMPTY'}", file=sys.stderr, flush=True)
            
            if response_line:
                return json.loads(response_line)
            return {"error": "Empty response from MCP"}
        except asyncio.TimeoutError:
            print(f"[REQ {request_counter}] TIMEOUT waiting for response", file=sys.stderr, flush=True)
            return {"error": "Timeout waiting for MCP response"}
        except Exception as e:
            print(f"[REQ {request_counter}] READ ERROR: {e}", file=sys.stderr, flush=True)
            return {"error": f"Failed to read from MCP: {str(e)}"}

async def sse_stream(request_body: dict):
    """Stream MCP messages via SSE"""
    try:
        print(f"SSE stream starting for method: {request_body.get('method')}", file=sys.stderr, flush=True)
        response = await send_to_mcp(request_body)
        print(f"SSE yielding response", file=sys.stderr, flush=True)
        
        yield f"data: {json.dumps(response)}\n\n"
        
    except Exception as e:
        print(f"SSE EXCEPTION: {e}", file=sys.stderr, flush=True)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/mcp")
async def mcp_handler(request: Request):
    """Handle MCP protocol via SSE streaming"""
    print(f"MCP handler called", file=sys.stderr, flush=True)
    try:
        body = await request.json()
        print(f"Parsed request body", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"JSON parse error: {e}", file=sys.stderr, flush=True)
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
