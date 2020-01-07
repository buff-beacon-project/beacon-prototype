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
  && pip3 install pipenv --no-cache-dir \
  && rm -rf /var/cache/apk/*

# Create app directory
# RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# Bundle app source
COPY . .

RUN pipenv install --system --deploy --ignore-pipfile --sequential
# RUN pip3 install -r requirements.txt
