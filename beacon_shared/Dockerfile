FROM python:3-alpine

RUN apk update \
  && apk add --no-cache \
    build-base \
    libzmq \
    libressl-dev \
    musl-dev \
    libffi-dev \
    # python3 \
    python3-dev \
    zeromq-dev \
  && pip3 install --upgrade pip \
  && pip3 install pipenv --no-cache-dir \
  && rm -rf /var/cache/apk/*

# Create app directory
RUN mkdir /app
RUN mkdir /beacon_shared

WORKDIR /beacon_shared

# Copy common files
COPY . .
