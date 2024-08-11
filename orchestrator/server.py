import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from queue import Queue
import threading
import uuid

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

command_queue = Queue()
device_status = {}
device_queues = {}
lock = threading.Lock()

@app.route('/')
def index():
    return "Android Emulator Orchestrator is running!"

@app.route('/add_command', methods=['POST'])
def add_command():
    try:
        data = request.json
        device_id = data['device_id']
        command = data['command']
        command_id = str(uuid.uuid4())
        with lock:
            if device_id not in device_queues:
                device_queues[device_id] = Queue()
            device_queues[device_id].put((command_id, command))
        logger.info(f"Command added to queue for device {device_id}")
        return jsonify({"status": "Command added to queue", "command_id": command_id}), 200
    except Exception as e:
        logger.error(f"Error adding command: {str(e)}")
        return jsonify({"error": "Failed to add command"}), 400

@socketio.on('connect')
def handle_connect():
    device_id = request.args.get('device_id')
    with lock:
        device_status[device_id] = 'ready'
    logger.info(f"Device {device_id} connected")
    emit('status', {'status': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    device_id = request.args.get('device_id')
    with lock:
        if device_id in device_status:
            del device_status[device_id]
        if device_id in device_queues:
            del device_queues[device_id]
    logger.info(f"Device {device_id} disconnected")

@socketio.on('command_result')
def handle_command_result(data):
    device_id = data['device_id']
    command_id = data['command_id']
    result = data['result']
    with lock:
        device_status[device_id] = 'ready'
    logger.info(f"Command {command_id} result from {device_id}: {result}")
    send_next_command(device_id)

def send_next_command(device_id):
    with lock:
        if device_id in device_queues and not device_queues[device_id].empty():
            command_id, command = device_queues[device_id].get()
            socketio.emit('execute_command', {'device_id': device_id, 'command_id': command_id, 'command': command})
            device_status[device_id] = 'busy'
            logger.info(f"Sent command {command_id} to device {device_id}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)