FROM python:3.11-slim

WORKDIR /app

# Install dependencies required for ChromaDB potentially and general bindings
RUN apt-get update && apt-get install -y build-essential curl

# We copy the unified root requirements.txt first if Phase 1/Phase 2 exist
# Assuming the user's workspace contains root `requirements.txt` mapping Phase1+2
# Then we install FastAPI backend requirements.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

# Copy Phase 1 and Phase 2 entirely unchanged matching Part 11 Rule
# COPY phase1/ /app/phase1/
COPY phase2/ /app/phase2/
COPY backend/ /app/backend/

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
