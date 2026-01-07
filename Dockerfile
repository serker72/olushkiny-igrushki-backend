FROM python:3.13.5

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_INSTALLER_METADATA=1

RUN apt-get update -y && apt-get upgrade -y
RUN pip install --upgrade pip
RUN pip install uv

WORKDIR /app
COPY ./pyproject.toml .

RUN uv pip install --system --no-cache -r pyproject.toml

COPY . .
