# Two-stage: build the Vite/React bundle, then run the read-only Python API that
# serves both the bundle and /api/*. Self-contained — NOT bind-mounted at runtime
# (the compose `..:/app` mount would otherwise shadow a baked-in dist), so the
# source is COPY'd into the image here.
# WORKDIR mirrors the repo layout (dashboard/web) so vite's outDir "../api/static"
# resolves to /dashboard/api/static — copied into the runtime stage below.
FROM node:20-slim AS web
WORKDIR /dashboard/web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /dashboard
RUN pip install "psycopg[binary]>=3.1" "fastapi>=0.115" "uvicorn>=0.30"
COPY api/ ./api/
# Built static bundle from the web stage (vite outDir = api/static).
COPY --from=web /dashboard/api/static ./api/static
ENV DASHBOARD_DIST=/dashboard/api/static
EXPOSE 8888
# app.py = FastAPI port of server.py (same endpoints/SQL, see app.py docstring).
# Revert to `python api/server.py` to roll back to the http.server implementation.
CMD ["python", "api/app.py"]
