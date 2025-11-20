FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

# this base gives both xvfb and playwright components
# need to install only playwright and other requirements
# including any build essentials

# Install build dependencies (g++, gcc, make, etc.)
RUN --mount=type=cache,target=/root/.cache/apt,id=apt,sharing=locked \
    apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /image
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,id=pip,sharing=locked \
    pip install \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --force-reinstall -r requirements.txt
