FROM continuumio/miniconda3

RUN apt-get update -y

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN while read requirement; do conda install --yes $requirement || pip install $requirement; done < requirements.txt

EXPOSE 5050
CMD [ "python", "run.py" ]