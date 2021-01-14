FROM continuumio/miniconda3:4.9.2-alpine

WORKDIR /root/app

COPY environment.yml .
RUN conda env create -f environment.yml

COPY ./app .

ENV SENTENCE_TRANSFORMERS_HOME /root/sentence-transformers/
ENV API_ROOT_PATH /
CMD ["/opt/conda/envs/embedding/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5060"]
