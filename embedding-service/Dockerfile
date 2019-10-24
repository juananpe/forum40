FROM python:3.6

# system packages
RUN apt-get update
RUN apt-get install -y python-pybind11

# python packages
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

# python app
COPY . /app
EXPOSE 5060
ENV FLASK_APP app.py

# RUN groupadd -g 999 appuser && useradd -r -u 999 -g appuser appuser
# RUN chmod 777 .
# USER appuser

ENV FLASK_DEBUG 0
CMD gunicorn -b 0.0.0.0:5060 --worker-connections 500 --timeout 400 app:app

# ENV FLASK_DEBUG 1
# CMD python -m flask run --host=0.0.0.0 --port=5060