#!/usr/bin/env python3
import asyncio
import json
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
import subprocess

app = FastAPI()
mcp_process = None
request_queue = asyncio.Queue()
response_map = {}
message_counter = 0

async def mcp_reader():
    """Read responses from MCP server"""
    global response_map
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(
                None, 
                mcp_process.stdout.readline
            )
            if not line:
                break
            response = json.loads(line)
            msg_id = response.get('id')
            if msg_id and msg_id in response_map:
                response_map[msg_id]['result'] = response
                response_map[msg_id]['event'].set()
        except Exception as e:
            print(f"Error reading from MCP: {e}", file=sys.stderr)
            break

async def start_mcp():
    global mcp_process
    mcp_process = subprocess.Popen(
        ["python3", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    asyncio.create_task(mcp_reader())

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_mcp()
    yield
    if mcp_process:
        mcp_process.terminate()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "EntityIQ MCP"}

@app.get("/")
async def root():
    return {"name": "EntityIQ MCP", "version": "1.0.0"}

@app.post("/mcp")
async def mcp_handler(request: dict):
    global message_counter, response_map
    
    if not mcp_process or mcp_process.poll() is not None:
        return {"error": "MCP server not running"}
    
    message_counter += 1
    msg_id = message_counter
    request['id'] = msg_id
    
    # Create event for response
    response_map[msg_id] = {'event': asyncio.Event(), 'result': None}
    
    try:
        # Send request
        request_line = json.dumps(request) + "\n"
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: mcp_process.stdin.write(request_line) or mcp_process.stdin.flush()
        )
        
        # Wait for response (5 second timeout)
        await asyncio.wait_for(response_map[msg_id]['event'].wait(), timeout=5.0)
        result = response_map[msg_id]['result']
        del response_map[msg_id]
        return result
    except asyncio.TimeoutError:
        del response_map[msg_id]
        return {"error": "MCP request timeout"}
    except Exception as e:
        if msg_id in response_map:
            del response_map[msg_id]
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
