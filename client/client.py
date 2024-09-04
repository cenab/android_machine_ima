import asyncio
import websockets
import json
import uuid
from client.commands import (send_discord_message, send_messenger_message, send_signal_message,
                             send_skype_message, send_slack_message, send_teams_message,
                             send_telegram_message, send_whatsapp_message)
from client.collectors.tcp.tcp_dump_manager import TcpDumpManager
from client.collectors.ports.network_stats_collector import NetworkStatsCollector

EXECUTED_LIST = {
    'discord': False, 'messenger': False, 'signal': False, 'skype': False,
    'slack': False, 'teams': False, 'telegram': False, 'whatsapp': False
}

async def connect_to_server(device_id, port_collector, tcpdump_manager):
    try:
        port_collector.start()
        tcpdump_manager.run_tcpdump()
        
        server_ip = ""
        port = 5000
        device_id = "{device_id}"

        # Constructing the URI
        uri = f"ws://[{server_ip}]:{port}?device_id={device_id}"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"event": "ready", "data": {"status": "ready"}}))

            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if data.get('event') == 'execute_command':
                    command_data = data['data']
                    command_id = command_data['command_id']
                    command = command_data['command']
                    result = await execute_command(command)

                    await websocket.send(json.dumps({
                        "event": "command_result",
                        "data": {
                            "device_id": device_id,
                            "command_id": command_id,
                            "result": result
                        }
                    }))

                    # Wait for the specified time before processing the next command
                    wait_time = command.get('wait_time', 5)
                    await asyncio.sleep(wait_time)

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed, stopping collectors.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        stop_collectors(port_collector, tcpdump_manager)

async def execute_command(command):
    try:
        platform = command.get('platform')
        character = command.get('character', '')
        dialogue = command.get('dialogue', '')
        number = command.get('number', 1)

        if platform and dialogue:
            message = f"{character}: {dialogue}"
            if number > 1:
                message += f" (x{number})"
            result = post_message_to_the_chat(message, platform)
            return {"status": "success", "output": result.stdout if result else ""}
        else:
            return {"status": "failure", "error": "Invalid command structure"}
    except Exception as e:
        return {"status": "failure", "error": str(e)}

def post_message_to_the_chat(message, platform):
    executed = EXECUTED_LIST[platform]
    platform_functions = {
        'discord': send_discord_message,
        'messenger': send_messenger_message,
        'signal': send_signal_message,
        'skype': send_skype_message,
        'slack': send_slack_message,
        'teams': send_teams_message,
        'telegram': send_telegram_message,
        'whatsapp': send_whatsapp_message
    }
    
    if platform in platform_functions:
        result = platform_functions[platform](message, executed)
        EXECUTED_LIST[platform] = True
        return result
    else:
        print("Unsupported platform")
        return None

def stop_collectors(port_collector, tcpdump_manager):
    port_collector.stop()
    tcpdump_manager.stop_tcpdump()

if __name__ == "__main__":
    print("Starting client")
    device_id = str(uuid.uuid4())
    port_collector = NetworkStatsCollector()
    tcpdump_manager = TcpDumpManager()
    asyncio.run(connect_to_server(device_id, port_collector, tcpdump_manager))