FROM base

WORKDIR /app

# copy app files
COPY . .

RUN pipenv install --system --deploy --ignore-pipfile --sequential
# RUN pip3 install -r requirements.txt
