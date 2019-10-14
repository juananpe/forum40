from celery import Celery
from index_comments import CommentIndexer
import os

# 172.18.0.5

rabbit_host = os.getenv('RABBIT_HOST', 'rabbitmq')

app = Celery("tasks", backend="amqp", broker="amqp://guest:guest@%s:5672//" % rabbit_host)

@app.task
def index_comments(db_host = "postgres", db_port = 5432):

    # start indexing
    indexer = CommentIndexer(db_host, db_port)
    indexer.indexEmbeddings()

    return True

