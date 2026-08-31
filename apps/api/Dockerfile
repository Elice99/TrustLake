FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker layer caching skips this step
# when only application code changes, not requirements.txt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# --reload is intentional here: this stub is a dev-only service.
# A production image (not needed until later stages) would drop --reload
# and switch to a non-root user and a process manager.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
