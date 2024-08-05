from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from queue import Queue
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Queue to manage command execution
command_queue = Queue()

# Dictionary to store the status of each emulator
device_status = {}

# Lock for thread-safe access to shared resources
lock = threading.Lock()

@app.route('/')
def index():
    return "Android Emulator Orchestrator is running!"

@app.route('/add_command', methods=['POST'])
def add_command():
    data = request.json
    device_id = data['device_id']
    command = data['command']
    # Add command to the queue
    with lock:
        command_queue.put((device_id, command))
    return jsonify({"status": "Command added to queue"}), 200

def process_commands():
    while True:
        # Get a command from the queue
        device_id, command = command_queue.get()
        with lock:
            # Check if the device is ready to execute a command
            if device_status.get(device_id) == 'ready':
                # Emit command to device via WebSocket
                socketio.emit('execute_command', {'device_id': device_id, 'command': command})
                # Set device status to busy
                device_status[device_id] = 'busy'

@socketio.on('connect')
def handle_connect():
    device_id = request.args.get('device_id')
    with lock:
        device_status[device_id] = 'ready'
    emit('status', {'status': 'Connected to server'})

@socketio.on('command_result')
def handle_command_result(data):
    device_id = data['device_id']
    result = data['result']
    with lock:
        # Update device status
        device_status[device_id] = 'ready'
    # Process the result (success/failure) of the command
    print(f"Command result from {device_id}: {result}")

def start_command_processing_thread():
    thread = threading.Thread(target=process_commands)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    start_command_processing_thread()
    socketio.run(app, host='0.0.0.0', port=5000)
