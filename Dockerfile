FROM python:3.11-slim

# to stop Python from writing .pyc files and force it to print logs instantly
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose FastAPI port 
EXPOSE 8000

# The command to start the web server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]