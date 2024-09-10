import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from queue import Queue
import threading
import uuid
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

command_queue = Queue()
device_status = {}
device_queues = {}
device_sockets = {}
lock = threading.Lock()
device_connection_order = 0
device_connection_order_dict = {}

orchestrator_connected = False
orchestrator = None

@app.route('/')
def hello():
    return "Hello, World!"

@socketio.on('connect')
def handle_connect(auth):
    global orchestrator_connected, orchestrator, device_connection_order
    device_id = request.args.get('device_id')
    if device_id == "orchestrator" and not orchestrator_connected:
        orchestrator_connected = True
        orchestrator = request.sid
        emit('status', {'status': 'Connected to server'})
        logger.info(f"Orchestrator connected with sid {request.sid}")
    elif device_id == "orchestrator" and orchestrator_connected:
        disconnect()
    else:
        device_status[device_id] = 'ready'
        device_sockets[device_id] = request.sid
        device_connection_order += 1
        device_connection_order_dict[device_connection_order] = device_id
        logger.info(f"Device {device_id} connected with sid {request.sid}")
        emit('status', {'status': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    global orchestrator_connected, orchestrator
    device_id = request.args.get('device_id')
    with lock:
        if device_id in device_status:
            del device_status[device_id]
        if device_id in device_queues:
            del device_queues[device_id]
        if device_id in device_sockets:
            del device_sockets[device_id]
        if device_id == "orchestrator":
            orchestrator_connected = False
            orchestrator = None
    logger.info(f"Device {device_id} disconnected")

@socketio.on('add_command')
def handle_add_command(data):
    try:
        command = data['command']
        command_id = str(uuid.uuid4())
        with lock:
            device_id = device_connection_order_dict[command['number']]
            if device_id not in device_queues:
                device_queues[device_id] = Queue()
            device_queues[device_id].put((command_id, command))
        logger.info(f"Command {command_id} added to queue for device {device_id}")
        emit('command_status', {"status": "Command added", "command_id": command_id})
        send_next_command(device_id)
    except Exception as e:
        logger.error(f"Error adding command: {str(e)}")
        emit('command_status', {"status": "Failed to add command"})

@socketio.on('command_result')
def handle_command_result(data):
    try:
        # If data is a string, try to parse it as JSON
        if isinstance(data, str):
            data = json.loads(data)
        
        # Check if the data is wrapped in an 'event' and 'data' structure
        if 'event' in data and data['event'] == 'command_result' and 'data' in data:
            data = data['data']
        
        device_id = data['device_id']
        command_id = data['command_id']
        result = data['result']
        
        with lock:
            device_status[device_id] = 'ready'
        logger.info(f"Command {command_id} result from {device_id}: {result}")
        send_next_command(device_id)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON data: {data}")
    except KeyError as e:
        logger.error(f"Missing key in data: {e}")
    except Exception as e:
        logger.error(f"Error handling command result: {str(e)}")

def send_next_command(device_id):
    with lock:
        if device_id in device_queues and not device_queues[device_id].empty():
            command_id, command = device_queues[device_id].get()
            if device_id in device_sockets:
                sid = device_sockets[device_id]
                socketio.emit('execute_command', {
                    'event': 'execute_command',
                    'data': {
                        'device_id': device_id,
                        'command_id': command_id,
                        'command': command
                    }
                }, to=sid)
                device_status[device_id] = 'busy'
                logger.info(f"Sent command {command_id} to device {device_id} using sid {sid}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)