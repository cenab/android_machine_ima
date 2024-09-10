import asyncio
import socketio
import json
import pandas as pd
import argparse
import os

# Server details
SERVER_URL = 'ws://localhost:5000'

# Device ID for the orchestrator
device_id = 'orchestrator'

# Create a Socket.IO client
sio = socketio.AsyncClient()

async def send_command(command):
    """Sends a command to the server."""
    message = {
        'device_id': command.get('device_id', 'some_device_id'),
        'command': command
    }
    try:
        response = await sio.call('add_command', message)
        if response.get('status') == 'Command added':
            print(f"Command sent successfully: {command}")
            return response.get('command_id')
        else:
            print(f"Error sending command: {response}")
            return None
    except Exception as e:
        print(f"Error sending command: {e}")
        return None

def read_xlsx_line_by_line(file_path):
    """Reads an XLSX file line by line using pandas."""
    df = pd.read_excel(file_path)
    for index, row in df.iterrows():
        yield row.to_dict()

async def orchestrator_loop(file_path):
    await sio.connect(f"{SERVER_URL}?device_id={device_id}")
    print("Connected to server")
    try:
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
                    command_id = await send_command(command)

                    # Wait for the specified time before sending the next command
                    wait_time = command['wait_time']
                    print(f"Waiting for {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

                except Exception as e:
                    print(f"Error processing row: {e}")
            print("Reached end of file. Restarting from beginning...")
    except asyncio.CancelledError:
        print("Orchestrator loop was cancelled")
    finally:
        await sio.disconnect()

@sio.event
async def connect():
    print("Connected to server")

@sio.event
async def disconnect():
    print("Disconnected from server")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Orchestrator for distributed command execution system.")
    parser.add_argument('--file', 
                    type=str, 
                    default=os.path.join("..", "dialog", "schedule", "out", "play_dialogue_hamlet_scheduled.xlsx"),
                    help="Path to the Excel file containing commands. (default: %(default)s)")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    try:
        asyncio.run(orchestrator_loop(args.file))
    except KeyboardInterrupt:
        print("Orchestrator stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")