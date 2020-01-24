FROM base

# Install gunicorn
RUN pip3 install gunicorn

# Install falcon
RUN pip3 install falcon

WORKDIR /app

# copy app files
COPY . .

RUN pipenv install --system --deploy --ignore-pipfile --sequential
# RUN pip3 install -r requirements.txt
