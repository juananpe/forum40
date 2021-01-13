from timeit import default_timer as timer

import logging
from abc import abstractmethod
from psycopg2.extras import Json
from typing import Dict, Union

from db.connection import db_pool

# standard logger
logger = logging.getLogger('ForumTask')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)


class ForumTask:
    def __init__(self, taskname):
        self.taskname = taskname
        self.logger = logger
        self.conn = None
        self.cursor = None
        self.conn = db_pool.getconn()
        self.cursor = self.conn.cursor()

    def __del__(self):
        db_pool.putconn(self.conn)

    def set_logger(self, logger):
        self.logger = logger


class ForumProcessor(ForumTask):
    def __init__(self, taskname):
        super().__init__(taskname)
        self.log_conn = db_pool.getconn()
        self.log_conn.autocommit = True

    def __del__(self):
        super().__del__()
        self.log_conn.autocommit = False
        db_pool.putconn(self.log_conn)

    def set_state(self, data: Dict):
        with self.log_conn.cursor() as log_cur:
            log_cur.execute(
                'INSERT INTO tasks (name, data) VALUES (%s, %s)',
                (self.taskname, Json(data))
            )

    def start(self):
        self.set_state({'status': 'starting'})

        start = timer()
        log_data = {}
        result = None
        try:
            result = self.process()
            log_data['status'] = 'finished'
            if result is not None:
                log_data['result'] = result
        except Exception as e:
            logger.exception(e)
            log_data['status'] = 'failed'
            log_data['error'] = str(e)
        finally:
            log_data['duration'] = timer() - start
            self.set_state(log_data)

        return result

    @abstractmethod
    def process(self) -> Union[Dict, None]:
        pass


