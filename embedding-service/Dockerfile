FROM python:3.6

# system packages
RUN apt-get update
RUN apt-get install -y python-pybind11
RUN apt-get install -y supervisor

# python packages
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

# python app
COPY . /app
EXPOSE 5060
ENV FLASK_APP app.py
ENV FLASK_DEBUG 0

RUN groupadd -g 999 appuser && useradd -r -u 999 -g appuser appuser
USER appuser

RUN touch supervisord.log

CMD ["/usr/bin/supervisord"]
