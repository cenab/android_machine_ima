import asyncio
import websockets
import json
import uuid
import subprocess
import os

async def connect_to_server(device_id):
    uri = f"ws://<server-ip>:5000?device_id={device_id}"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"status": "ready"}))

        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data['type'] == 'execute_command':
                command_id = data['command_id']
                command = data['command']
                result = await execute_command(command)
                await websocket.send(json.dumps({
                    "device_id": device_id,
                    "command_id": command_id,
                    "result": result
                }))

async def execute_command(command):
    if command.startswith("adb "):
        return await run_adb_command(command)
    elif command.startswith("script:"):
        return await run_interaction_script(command[7:])
    else:
        return {"status": "failure", "message": "Unknown command type"}

async def run_adb_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "failure", "error": str(e), "output": e.stderr}

async def run_interaction_script(script_name):
    script_path = os.path.join("/usr/local/bin/interaction_scripts", script_name)
    try:
        result = subprocess.run(f"bash {script_path}", shell=True, check=True, capture_output=True, text=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "failure", "error": str(e), "output": e.stderr}

if __name__ == "__main__":
    device_id = str(uuid.uuid4())
    asyncio.get_event_loop().run_until_complete(connect_to_server(device_id))