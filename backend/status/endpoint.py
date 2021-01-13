from socket import SocketIO
from threading import Lock

from status.subscription import watch_task_updates

thread = None
thread_lock = Lock()


def register(socketio: SocketIO):
    @socketio.on('connect')
    def start_thread():
        global thread
        with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(emit_task_updates, socketio)


def emit_task_updates(socketio):
    for task_update in watch_task_updates():
        socketio.emit('task_update', task_update)
