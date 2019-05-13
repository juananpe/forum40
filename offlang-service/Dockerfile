FROM python:3.6

COPY . /app
WORKDIR /app
# RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pip install cython
RUN pip install -r requirements.txt
EXPOSE 5060
ENV FLASK_APP app.py
ENV FLASK_DEBUG 0
CMD gunicorn -b 0.0.0.0:5060 --worker-connections 500 --timeout 400 app:app
