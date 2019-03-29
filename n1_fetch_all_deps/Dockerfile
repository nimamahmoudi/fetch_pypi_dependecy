FROM python:3.6-slim
LABEL maintainer="nima.mahmoudi@ualberta.ca"

WORKDIR /usr/app

COPY ./data ./data

COPY ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./ .

VOLUME /usr/app/packages

CMD [ "python", "-u", "main.py"]
