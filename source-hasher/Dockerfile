FROM python:alpine

RUN apk update \
  && apk add --no-cache \
    build-base \
    libzmq \
    musl-dev \
    # python3 \
    python3-dev \
    zeromq-dev \
    py3-zmq \
  && pip3 install --no-cache-dir pipenv \
  && rm -rf /var/cache/apk/*

# Create app directory
# RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# Bundle app source
COPY . .

RUN pipenv install --system --deploy
