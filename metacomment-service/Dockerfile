FROM python:3.6

COPY . /app
WORKDIR /app
# RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pip install cython
RUN pip install -r requirements.txt
EXPOSE 5060
ENTRYPOINT ["python"]
CMD ["app.py"]
