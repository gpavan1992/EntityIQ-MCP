#!/usr/bin/env python3
import json
import subprocess
import sys
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

app = FastAPI()
mcp_process = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_process
    print("Starting MCP subprocess...", file=sys.stderr, flush=True)
    mcp_process = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    print(f"MCP started with PID {mcp_process.pid}", file=sys.stderr, flush=True)
    yield
    if mcp_process:
        mcp_process.terminate()
        mcp_process.wait(timeout=5)

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/mcp")
async def mcp_handler(request: Request):
    """Handle MCP via SSE streaming"""
    try:
        body = await request.json()
    except Exception as e:
        return {"error": str(e)}
    
    def event_generator():
        try:
            request_line = json.dumps(body) + "\n"
            mcp_process.stdin.write(request_line)
            mcp_process.stdin.flush()
            print(f"Sent: {request_line[:80]}", file=sys.stderr, flush=True)
            
            response_line = mcp_process.stdout.readline()
            print(f"Got: {response_line[:80] if response_line else 'EMPTY'}", file=sys.stderr, flush=True)
            
            if response_line:
                yield f"data: {response_line}\n\n"
            else:
                yield f"data: {json.dumps({'error': 'No response from MCP'})}\n\n"
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
