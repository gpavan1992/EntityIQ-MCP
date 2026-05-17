FROM node:20-slim

WORKDIR /app

# Copy Python server
COPY server.py .

# Copy Node wrapper
COPY package.json package-lock.json tsconfig.json http_server.ts ./

# Install Node deps
RUN npm ci

# Install Python
RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*

EXPOSE 3000

CMD ["npx", "tsx", "http_server.ts"]
