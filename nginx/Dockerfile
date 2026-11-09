# Stage 1: Build the React application
FROM node:20-alpine AS frontend-builder
WORKDIR /app

# Copy package files first for layer caching
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of the frontend code and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy the compiled React build from Stage 1
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy your custom Nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
