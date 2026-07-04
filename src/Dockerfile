FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/auto-swing-requirements.txt
RUN pip install -r /tmp/auto-swing-requirements.txt

# Default entrypoint; compose overrides `command:` per service (pipeline vs mcp-server).
# working_dir is /app (auto-swing repo root, bind-mounted), so paths are src/-relative.
CMD ["python", "src/pipeline/scheduler.py"]
