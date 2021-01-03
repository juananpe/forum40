import logging
import os
import psycopg2
import requests
import subprocess
from abc import abstractmethod
from datetime import datetime

from config import settings, secrets

# db configuration

DB_NAME = "omp"
DB_USER = "postgres"

# standard logger
logger = logging.getLogger('ForumTask')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class ForumTask:
    def __init__(self, taskname, host="postgres", port=5432):
        self.taskname = taskname
        self.logger = logger
        self.host = host
        self.port = port
        self.conn = None
        self.cursor = None
        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=DB_NAME,
                user=DB_USER,
                password=secrets['db_password'].decode('utf8')
            )
        except:
            self.logger.error(f"Could not connect to database ({DB_USER}:***@{host}:{port}/{DB_NAME})")
            exit(1)

        self.cursor = self.conn.cursor()

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def set_logger(self, logger):
        self.logger = logger


class ForumProcessor(ForumTask):

    def __init__(self, taskname, host="postgres", port=5432):
        super().__init__(taskname, host, port)
        self.total_steps = 1
        self.current_step = 0
        self.message_log = []
        self.pid = os.getpid()

    def __del__(self):
        if self.conn:
            if self.current_step and self.get_progress() < 1:
                self.update_state(self.current_step, self.taskname + " aborted.")
            self.cursor.close()
            self.conn.close()

    def set_total(self, total_steps):
        self.total_steps = total_steps

    def get_progress(self):
        return self.current_step / self.total_steps

    def update_state(self, step, message):
        self.current_step = step
        self.message_log.append(message)
        self.cursor.execute(
            """INSERT INTO tasks (pid, name, message, progress, timestamp) VALUES (%s, %s, %s, %s, %s)""",
            (self.pid, self.taskname, message, self.get_progress(), datetime.now().isoformat())
        )
        self.conn.commit()

    @abstractmethod
    def process(self):
        pass


class SingleProcessManager:
    def __init__(self, pg_host, pg_port):
        self.commands = {}
        self.processes = {}
        self.history = ForumTask("task_history", pg_host, pg_port)

    def register_process(self, name, command):
        self.commands[name] = command
        self.processes[name] = 0

    def tasks(self):
        result = {
            "tasks": list(self.commands.keys())
        }
        return result

    def poll(self):
        for task in self.processes.keys():
            proc = self.processes[task]
            if proc:
                if proc.poll() is not None:
                    # unset registered task
                    self.processes[task] = 0

    def invoke(self, task, source_id, arguments=[]):
        # check arguments (only 2 allowed of max length 32 characters)
        arg_lengths = [len(arg) for arg in arguments]
        if arguments and (len(arguments) > 6 or max(arg_lengths) > 32):
            raise ValueError("Invalid arguments passed.")

        # invoke task
        try:

            # check for terminated tasks
            self.poll()

            if not self.processes[task] or task == 'update':  # allow update task in parallel

                # start process
                popen_command = ["python"] + self.commands[task] + [source_id] + arguments
                proc = subprocess.Popen(popen_command)

                # register process
                self.processes[task] = proc

                result = {
                    "message": f"Task {task} started for source_id {source_id}.",
                    "pid": proc.pid
                }

            else:

                result = {
                    "message": f"Task {task} is still running.",
                    "pid": self.processes[task].pid
                }

            return result

        except KeyError:
            message = f"Unknown task {task}"
            logger.error(message)
            return {"error": message}

    def abort(self, task):
        try:
            # check for terminated tasks
            self.poll()

            if self.processes[task]:
                pid = self.processes[task].pid
                self.processes[task].terminate()
                result = {
                    "message": f"Task {task} stopped.",
                    "pid": pid
                }
            else:
                result = {
                    "message": f"Task {task} is not running."
                }

            return result

        except KeyError:
            message = f"Unknown task {task}"
            logger.error(message)
            return {"error": message}

    def status(self, task, n=50):
        try:
            # check for terminated tasks
            self.poll()

            if self.processes[task]:

                status_log = []
                progress = 0

                pid = self.processes[task].pid
                self.history.cursor.execute(
                    """SELECT message, progress, timestamp FROM tasks WHERE name=%s AND pid=%s ORDER BY timestamp DESC LIMIT %s""",
                    (task, pid, n)
                )
                status_entries = self.history.cursor.fetchall()
                if status_entries:
                    progress = status_entries[0][1]
                    # status_entries.reverse()
                    status_log = "\n".join([str(e) for e in status_entries])

                result = {
                    "task": task,
                    "pid": pid,
                    "progress": progress,
                    "log": status_log
                }
            else:
                result = {
                    "message": f"Task {task} is not running."
                }

            return result

        except KeyError:
            message = f"Unknown task {task}"
            logger.error(message)
            return {"error": message}

    def clear(self):
        # check for terminated tasks
        self.poll()

        running_tasks = False
        for task in self.processes.keys():
            if self.processes[task]:
                running_tasks = True
                break

        if running_tasks:
            result = {
                "message": "Task history not cleared due to ongoing tasks."
            }
        else:
            self.history.cursor.execute(
                """TRUNCATE TABLE public.tasks RESTART IDENTITY"""
            )
            self.history.conn.commit()
            result = {
                "message": "Task history cleared."
            }
        return result


def concat(title: str, text: str) -> str:
    """
    Concatenates comment's title and text
    :param title: comment title
    :param text: comment text
    :return: concatenated comment text
    """
    title = title if title else ''
    text = text if text else ''
    return (title + ' ' + text).strip()


def get_embeddings(string_list):
    url = os.getenv('EMBEDDING_SERVICE_URL', settings.EMBEDDING_SERVICE_URL)

    response = requests.post(
        url,
        json={"texts": string_list},
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
    )

    if response.ok:
        return response.json(), True
    else:
        print(f"Error: could not retrieve embeddings from {url}")
        return response.reason, False
