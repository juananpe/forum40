FROM python:3.6

# system packages
RUN apt-get update
RUN apt-get install -y python-pybind11

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt

EXPOSE 5050

CMD ["python", "/usr/src/app/run.py"]
