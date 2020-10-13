FROM python:3.8

# system packages
RUN apt-get update
RUN apt-get install -y python-pybind11

# python packages
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

# python app
COPY . /app
EXPOSE 8080

# run
ENV TRANSFORMERS_CACHE /root/.cache/transformers/
ENV API_ROOT_PATH /api/colibert
CMD python app.py
