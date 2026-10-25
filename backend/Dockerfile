FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install them first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code (including the 'app' folder)
COPY . .

# Default command for the backend service (worker overrides this in compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
