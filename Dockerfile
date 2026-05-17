FROM node:20-slim

WORKDIR /app

# Copy all files
COPY package.json package-lock.json tsconfig.json http_server.ts ./
COPY server.py .

# Install Node deps
RUN npm ci

# Install Python
RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*

EXPOSE 3000

CMD ["npx", "tsx", "http_server.ts"]
