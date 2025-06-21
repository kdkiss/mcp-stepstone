FROM node:22-slim

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN npm install

# Build TypeScript code (optional if using tsx directly)
# RUN npm run build

# Default command (using tsx for runtime TS support)
CMD ["npx", "tsx", "src/index.ts"]
