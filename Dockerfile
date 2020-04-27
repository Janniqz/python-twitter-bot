FROM python:3.8-alpine AS builder

WORKDIR /usr/src/app

RUN python -m venv .venv && .venv/bin/pip install --no-cache-dir -U pip setuptools

COPY requirements.txt .

RUN .venv/bin/pip install --no-cache-dir -r requirements.txt \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' \+

######################################

FROM python:3.8-alpine

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app /usr/src/app

COPY tweepy_video ./tweepy_video
COPY config.json .
COPY pyth-twitter-bot.py .

ENV PATH="/usr/src/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["python", "pyth-twitter-bot.py"]