FROM python:3.12-slim

WORKDIR /app

# Copy requirements from the backend folder
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend python code
COPY backend/app ./app

# Copy the database migrations from the db folder into the image
COPY db/migrations ./db/migrations

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
