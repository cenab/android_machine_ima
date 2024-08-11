import unittest
from unittest.mock import patch, MagicMock
from orchestrator.server import app, socketio, command_queue, device_status, lock

class TestServer(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.socketio_test_client = socketio.test_client(app)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "Android Emulator Orchestrator is running!")

    @patch('orchestrator.server.command_queue.put')
    def test_add_command(self, mock_put):
        response = self.client.post('/add_command', json={'device_id': 'test_device', 'command': 'test_command'})
        self.assertEqual(response.status_code, 200)
        mock_put.assert_called_once_with(('test_device', 'test_command'))

    def test_handle_connect(self):
        self.socketio_test_client.emit('connect', {'device_id': 'test_device'})
        with lock:
            self.assertEqual(device_status.get('test_device'), 'ready')

    def test_handle_disconnect(self):
        with lock:
            device_status['test_device'] = 'ready'
        self.socketio_test_client.emit('disconnect', {'device_id': 'test_device'})
        with lock:
            self.assertNotIn('test_device', device_status)

    def test_handle_command_result(self):
        self.socketio_test_client.emit('command_result', {'device_id': 'test_device', 'result': 'success'})
        with lock:
            self.assertEqual(device_status.get('test_device'), 'ready')

if __name__ == '__main__':
    unittest.main()