from flask import Flask
from core.proxy_wrapper import ReverseProxied
from huey import SqliteHuey
import logging

# define app
app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.logger.setLevel(logging.INFO)

huey = SqliteHuey(filename='model/huey_tasks.sqlite')
# huey.flush()
