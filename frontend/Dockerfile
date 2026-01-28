# Frontend Dockerfile - Multi-stage build

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
# Using npm install instead of npm ci to handle lockfile mismatches
# This is more forgiving when package.json changes
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
