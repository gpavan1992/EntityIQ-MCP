"""
HTTP wrapper for EntityIQ MCP.
Exposes stdio-based MCP server over HTTP for Railway deployment.
"""

import asyncio
import json
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import uvicorn
import subprocess

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""
    yield

app = FastAPI(title="EntityIQ MCP", lifespan=lifespan)

mcp_process = None

@app.on_event("startup")
async def startup():
    """Start MCP server on startup."""
    global mcp_process
    try:
        mcp_process = subprocess.Popen(
            [sys.executable, "/app/server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    except Exception as e:
        print(f"Failed to start MCP server: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Shutdown MCP server."""
    global mcp_process
    if mcp_process:
        try:
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
        except:
            mcp_process.kill()

@app.get("/health")
async def health():
    """Health check endpoint for Railway."""
    return {"status": "ok", "service": "EntityIQ MCP"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "EntityIQ MCP",
        "version": "1.0.0",
        "description": "Public business intelligence MCP server",
        "tools": 8,
        "status": "ready"
    }

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """MCP message endpoint."""
    try:
        if mcp_process:
            mcp_process.stdin.write(json.dumps(request) + "\n")
            mcp_process.stdin.flush()
            
            response_line = mcp_process.stdout.readline()
            if response_line:
                return json.loads(response_line)
            else:
                return {"error": "No response from MCP server"}
        else:
            raise HTTPException(status_code=503, detail="MCP server not running")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
