# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.3

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Copy source code
COPY . .

# Install the project itself
RUN poetry install

# Set environment variables for headless operation
ENV SDL_VIDEODRIVER=dummy
ENV DISPLAY=:99

# Default command
CMD ["poetry", "run", "the-dark-closet"]
