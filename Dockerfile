FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get upgrade -y && apt-get -y install ffmpeg
WORKDIR /code/
COPY pyproject.toml uv.lock /code/
RUN uv sync

# Bake model into image so you don't redownload every start
ARG WHISPER_MODEL_SIZE=distil-small.en
RUN --mount=type=cache,target=/root/.cache/huggingface \
    uv run python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL_SIZE}')"

COPY ./scainner/ .

CMD [ "uv", "run", "python", "main.py" ]
