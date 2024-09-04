Here is the explanation provided as markdown:

---

# Detailed Explanation of Code

## 1. **Imports**

```python
import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from queue import Queue
import threading
import uuid
```

- **`logging`**: This module is used to log messages for debugging or informational purposes.
- **`Flask`**: A web framework for creating web applications and APIs.
- **`request`**: Used to access incoming request data (like JSON in a POST request).
- **`jsonify`**: Converts Python data into JSON format for sending back as a response.
- **`SocketIO`**: Manages WebSocket connections between the server and clients (devices).
- **`emit`**: Used to send messages over WebSocket.
- **`disconnect`**: Disconnects a WebSocket connection.
- **`Queue`**: A thread-safe FIFO (First-In-First-Out) data structure for storing tasks (commands in this case).
- **`threading`**: Provides the `Lock` object, which helps manage concurrent access to shared data.
- **`uuid`**: Generates unique identifiers (used here for command IDs).

---

## 2. **App and SocketIO Setup**

```python
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
```

- **`app = Flask(__name__)`**: Initializes the Flask application.
- **`socketio = SocketIO(app, cors_allowed_origins='*')`**: Sets up the Flask app to use SocketIO for handling WebSocket connections. The `cors_allowed_origins='*'` allows WebSocket connections from any origin.

---

## 3. **Logging Configuration**

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

- **`logging.basicConfig(level=logging.INFO)`**: Configures the logging system to log messages with a severity level of `INFO` or higher.
- **`logger = logging.getLogger(__name__)`**: Creates a logger object to log messages throughout the application.

---

## 4. **Global Variables**

```python
command_queue = Queue()
device_status = {}
device_queues = {}
device_sockets = {}
lock = threading.Lock()
orchestrator_connected = False
orchestrator = None
```

- **`command_queue`**: A `Queue` object that could hold commands for general processing (currently unused).
- **`device_status`**: A dictionary to track the status (`ready`, `busy`, etc.) of connected devices, keyed by `device_id`.
- **`device_queues`**: A dictionary where each device has its own queue of commands, keyed by `device_id`.
- **`device_sockets`**: A dictionary mapping `device_id` to the socket session ID (`sid`), which identifies the WebSocket connection for each device.
- **`lock`**: A threading lock that ensures thread-safe operations when multiple threads might be modifying the shared dictionaries.
- **`orchestrator_connected`**: A flag that tracks if the orchestrator client is connected.
- **`orchestrator`**: Stores the session ID (`sid`) of the orchestrator WebSocket connection.

---

## 5. **Handle WebSocket Connection (`connect` Event)**

```python
@socketio.on('connect')
def handle_connect():
    global orchestrator_connected, orchestrator
    device_id = request.args.get('device_id')
    if device_id == "orchestrator" and not orchestrator_connected:
        orchestrator_connected = True
        orchestrator = request.sid
        emit('status', {'status': 'Connected to server'})
        logger.info(f"Orchestrator connected with sid {request.sid}")
    elif device_id == "orchestrator" and orchestrator_connected:
        disconnect()
    else:
        with lock:
            device_status[device_id] = 'ready'
            device_sockets[device_id] = request.sid  # Store the socket session id for the device
        logger.info(f"Device {device_id} connected with sid {request.sid}")
        emit('status', {'status': 'Connected to server'})
```

- **`@socketio.on('connect')`**: This function is triggered when a client connects to the WebSocket.
- **`device_id = request.args.get('device_id')`**: Gets the `device_id` from the WebSocket connection request’s query parameters.
- **Handling orchestrator connection**:
  - If the `device_id` is `"orchestrator"` and no orchestrator is connected, it marks the orchestrator as connected and stores its socket session ID (`request.sid`).
  - If an orchestrator is already connected, it disconnects the new connection to avoid multiple orchestrators.
- **Handling device connection**:
  - For other devices (non-orchestrator), it stores the device's status as `ready`, maps the `device_id` to the socket session ID, and logs the connection.

---

## 6. **Handle WebSocket Disconnection (`disconnect` Event)**

```python
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
```

- **`@socketio.on('disconnect')`**: This function is triggered when a client disconnects from the WebSocket.
- **`device_id = request.args.get('device_id')`**: Retrieves the `device_id` from the disconnect request’s query parameters.
- **Thread-safe cleanup**:
  - Using the lock, it removes the `device_id` from the `device_status`, `device_queues`, and `device_sockets` dictionaries.
  - If the disconnected client is the orchestrator, it resets the `orchestrator_connected` flag and the stored `orchestrator` session ID.
- Logs the disconnection.

---

## 7. **Add Command via WebSocket (`add_command` Event)**

```python
@socketio.on('add_command')
def handle_add_command(data):
    try:
        device_id = data['device_id']
        command = data['command']
        command_id = str(uuid.uuid4())
        with lock:
            if device_id not in device_queues:
                device_queues[device_id] = Queue()
            device_queues[device_id].put((command_id, command))
        logger.info(f"Command {command_id} added to queue for device {device_id} via WebSocket")
        emit('command_status', {"status": "Command added", "command_id": command_id}, to=request.sid)
    except Exception as e:
        logger.error(f"Error adding command via WebSocket: {str(e)}")
        emit('command_status', {"status": "Failed to add command"}, to=request.sid)
```

- **`@socketio.on('add_command')`**: This function is triggered when a client sends an `add_command` event via WebSocket.
- **Extracts the `device_id` and `command`** from the received data and generates a unique `command_id` using `uuid.uuid4()`.
- **Adds the command to the device's queue**:
  - If the device does not have a queue yet, it creates one.
  - Adds the `(command_id, command)` tuple to the device's queue in a thread-safe manner using `lock`.
- Logs the command and emits a response back to the client confirming the command addition.

---

## 8. **Handle Command Result (`command_result` Event)**

```python
@socketio.on('command_result')
def handle_command_result(data):
    device_id = data['device_id']
    command_id = data['command_id']
    result = data['result']
    with lock:
        device_status[device_id] = 'ready'
    logger.info(f"Command {command_id} result from {device_id}: {result}")
    send_next_command(device_id)
```

- **`@socketio.on('command_result')`**: Triggered when a device reports the result of a command.
- **Updates device status**: Marks the device as `ready` (available to receive new commands) in a thread-safe way.
- Logs the result and triggers the function to send the next command from the queue.

---

## 9. **Send Next Command**

```python
def send_next_command(device_id):
    with lock:
        if device_id in device_queues and not device_queues[device_id].empty():
            command_id, command = device_queues[device_id].get()
            if device_id in device_sockets:
                sid = device_sockets[device_id]
                socketio.emit('execute_command', {'device_id': device_id, 'command_id': command_id, 'command': command}, to=sid)
                device_status[device_id] = 'busy'
                logger.info(f"Sent command {command_id} to device {device_id} using sid {sid}")
```

- **`send_next_command(device_id)`**: Sends the next command to the specified device, if available.
- It checks if the device's queue is non-empty and retrieves the next command.
- If the device is connected (tracked by `device_sockets`), it emits the command to the corresponding

 socket and marks the device as `busy`.
- Logs the command transmission.

---

## 10. **Run the Application**

```python
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
```

- Runs the Flask-SocketIO application on all network interfaces (`0.0.0.0`) at port 5000.
- **`debug=True`**: Enables Flask’s debug mode for development.
- **`allow_unsafe_werkzeug=True`**: Disables certain Flask security features for development purposes.

---

This is the markdown version of the explanation provided.