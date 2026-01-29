# Use python 3.12 slim image
FROM python:3.12-slim

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --no-cache

# Place .venv/bin at the beginning of PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the application code
COPY . .

# Expose port
EXPOSE 5001

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start the application using gunicorn with a larger timeout for LLM calls
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "3", "--timeout", "300", "app:app"]
