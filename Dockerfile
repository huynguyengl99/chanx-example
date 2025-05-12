FROM ghcr.io/astral-sh/uv:python3.11-alpine AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /code
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
ADD . /code
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.11-alpine

# Copy the application from the builder
COPY --from=builder /code /code

# Place executables in the environment at the front of the path
ENV PATH="/code/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=$PYTHONPATH:/code/chanx_example
ENV DJANGO_SECRET_KEY=this_is_the_temporary_secret_key
ENV DJANGO_SETTINGS_MODULE=config.settings.base

WORKDIR /code/chanx_example

RUN python manage.py collectstatic --no-input
EXPOSE 8000

# Run the FastAPI application by default
CMD ["gunicorn", "config.wsgi", "-c", "gunicorn.conf.py"]

# Use the below CMD instead if you use websocket
# CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "config.asgi:application"]
