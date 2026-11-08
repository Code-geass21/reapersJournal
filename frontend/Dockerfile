# Stage 1: Build the React application
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files and install all dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the code and compile the production build
COPY . .
RUN npm run build

# Stage 2: Serve the optimized static files
FROM node:20-alpine
WORKDIR /app

# Install 'serve', a lightweight static file server
RUN npm install -g serve

# Copy only the compiled static assets from the builder stage
COPY --from=builder /app/dist ./dist

# Run on port 5173 to perfectly match your existing nginx.conf and docker-compose.yml
CMD ["serve", "-s", "dist", "-l", "5173"]
