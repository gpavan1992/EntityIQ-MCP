import express from 'express';
import { spawn } from 'child_process';
import cors from 'cors';

const app = express();
app.use(cors());
app.use(express.json());

let mcpProcess: any = null;

// Start MCP subprocess on startup
function startMCPServer() {
  mcpProcess = spawn('python3', ['server.py']);
  
  mcpProcess.stderr.on('data', (data: Buffer) => {
    console.error(`MCP stderr: ${data}`);
  });
  
  mcpProcess.on('error', (err: Error) => {
    console.error(`MCP process error: ${err}`);
  });
}

startMCPServer();

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.post('/mcp', (req, res) => {
  const request = req.body;
  
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  // Send request to MCP
  const requestLine = JSON.stringify(request) + '\n';
  mcpProcess.stdin.write(requestLine);
  
  // Read response
  mcpProcess.stdout.once('data', (data: Buffer) => {
    const response = data.toString().trim();
    res.write(`data: ${response}\n\n`);
    res.end();
  });
  
  // Timeout after 5 seconds
  setTimeout(() => {
    if (!res.writableEnded) {
      res.write(`data: ${JSON.stringify({ error: 'Timeout' })}\n\n`);
      res.end();
    }
  }, 5000);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
