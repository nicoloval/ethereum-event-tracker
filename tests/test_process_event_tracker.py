import unittest
from unittest.mock import patch, MagicMock
from process_event_tracker import EventTrackerConfig, get_logs_try
from web3 import Web3

class TestEventTrackerConfig(unittest.TestCase):
    def test_event_tracker_config_initialization(self):
        config = EventTrackerConfig(
            contract_name="TestContract",
            contract_address="0x1234567890abcdef1234567890abcdef12345678",
            event_name="TestEvent",
            from_block=0,
            to_block=100,
            append=False,
            log_file="test.log"
        )
        self.assertEqual(config.contract_name, "TestContract")
        self.assertEqual(config.contract_address, "0x1234567890abcdef1234567890abcdef12345678")
        self.assertEqual(config.event_name, "TestEvent")
        self.assertEqual(config.from_block, 0)
        self.assertEqual(config.to_block, 100)
        self.assertEqual(config.append, False)
        self.assertEqual(config.log_file_path, "test.log")

class TestGetLogsTry(unittest.TestCase):
    @patch('process_event_tracker.logging')
    def test_get_logs_try_success(self, mock_logging):
        mock_w3 = MagicMock()
        mock_w3.eth.get_logs.return_value = ['log1', 'log2']
        filter_params = {'fromBlock': 0, 'toBlock': 10}

        logs = get_logs_try(mock_w3, filter_params)
        self.assertEqual(logs, ['log1', 'log2'])
        mock_logging.getLogger().info.assert_called_with("Retrieved 2 logs from block 0 to 10")

    @patch('process_event_tracker.logging')
    def test_get_logs_try_exception(self, mock_logging):
        mock_w3 = MagicMock()
        mock_w3.eth.get_logs.side_effect = Exception("Error")
        filter_params = {'fromBlock': 0, 'toBlock': 10}

        logs = get_logs_try(mock_w3, filter_params)
        self.assertEqual(logs, [])
        mock_logging.getLogger().error.assert_called_with("Error retrieving logs: Error")

if __name__ == '__main__':
    unittest.main()
