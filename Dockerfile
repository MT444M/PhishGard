# Dockerfile for PhishGard with GPU support

# Use official Python image with CUDA support
FROM nvcr.io/nvidia/pytorch:23.10-py3

WORKDIR /app

# Copy application code
COPY backend/ .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
ENV NVIDIA_VISIBLE_DEVICES=all

# Start the application
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main_api:app"]