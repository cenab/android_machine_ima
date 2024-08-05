import asyncio
import websockets
import json
import uuid

async def connect_to_server(device_id):
    uri = f"ws://<server-ip>:5000?device_id={device_id}"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"status": "ready"}))

        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data['type'] == 'execute_command':
                command = data['command']
                # Execute the command (replace with actual command execution logic)
                result = execute_command(command)
                # Send result back to the server
                await websocket.send(json.dumps({"device_id": device_id, "result": result}))

def execute_command(command):
    # Placeholder for command execution logic
    # Replace with actual command execution on the emulator
    print(f"Executing command: {command}")
    return "success"  # or "failure" based on execution

# Start the client for a specific device
random_uuid = uuid.uuid4()
device_id = str(random_uuid)
asyncio.get_event_loop().run_until_complete(connect_to_server(device_id))
