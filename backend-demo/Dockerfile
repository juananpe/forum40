FROM python:3.6

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt

EXPOSE 5050

CMD ["python", "/usr/src/app/run.py"]
