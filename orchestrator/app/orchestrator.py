import asyncio
import websockets
import json
import random
import pandas as pd
import argparse

# Server details
SERVER_URL = 'ws://localhost:5000'

# Device ID for the orchestrator
device_id = 'orchestrator'

async def send_command(websocket, command):
    """Sends a command to the server."""
    message = {
        'event': 'add_command',
        'data': {
            'device_id': command.get('device_id', 'some_device_id'),
            'command': command
        }
    }
    await websocket.send(json.dumps(message))
    response = await websocket.recv()
    response_data = json.loads(response)
    if response_data.get('event') == 'command_status' and response_data['data']['status'] == 'Command added':
        print(f"Command sent successfully: {command}")
        return response_data['data']['command_id']
    else:
        print(f"Error sending command: {response_data}")
        return None

def read_xlsx_line_by_line(file_path):
    """Reads an XLSX file line by line using pandas."""
    df = pd.read_excel(file_path)
    for index, row in df.iterrows():
        yield row.to_dict()

async def orchestrator_loop(file_path):
    uri = f"{SERVER_URL}?device_id={device_id}"
    async with websockets.connect(uri) as websocket:
        print("Connected to server")
        while True:  # Continuous operation
            for row in read_xlsx_line_by_line(file_path):
                try:
                    # Construct command from Excel row data
                    command = {
                        'character': row.get('Character', ''),
                        'dialogue': row.get('Dialogue', ''),
                        'number': row.get('Number', 1),
                        'platform': row.get('IMA', 'default_platform'),
                        'wait_time': row.get('Wait Time (seconds)', 5)
                    }

                    # Send the command to the server
                    command_id = await send_command(websocket, command)

                    # Wait for the specified time before sending the next command
                    wait_time = command['wait_time']
                    print(f"Waiting for {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

                except Exception as e:
                    print(f"Error processing row: {e}")
            print("Reached end of file. Restarting from beginning...")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Orchestrator for distributed command execution system.")
    parser.add_argument('--file', type=str, required=True, help="Path to the Excel file containing commands.")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    asyncio.run(orchestrator_loop(args.file))