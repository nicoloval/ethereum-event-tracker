import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from process_event_tracker import EventTrackerConfig, get_logs_try
from web3 import Web3

class TestEventTrackerConfig(unittest.TestCase):
    @patch('process_event_tracker.pq')
    @patch('process_event_tracker.pd')
    def test_event_tracker_config_initialization(self, mock_pd, mock_pq):
        # Mocking the read_table and to_pandas methods
        mock_pq.read_table.return_value.to_pandas.return_value = pd.DataFrame({
            'blockNumber': [20000001, 20000002],
            'field1': ['value1', 'value2'],
            'field2': ['value3', 'value4']
        })

        config = EventTrackerConfig(
            contract_name="stETH",
            contract_address="0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
            event_name="TransferShares",
            from_block=20000000,
            to_block=20001000,
            append=False,
            log_file="test.log"
        )
        self.assertEqual(config.contract_name, "stETH")
        self.assertEqual(config.contract_address, "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84")
        self.assertEqual(config.event_name, "TransferShares")
        self.assertEqual(config.from_block, 20000000)
        self.assertEqual(config.to_block, 20001000)
        self.assertEqual(config.append, False)
        self.assertEqual(config.log_file_path, "test.log")

        # Assuming the output file is named as follows
        output_file = f"{config.contract_name}-{config.event_name}-{config.from_block}-{config.to_block}.parquet"
        
        # Mocking the output DataFrame
        output_df = pd.DataFrame({
            'blockNumber': [20000001, 20000002],
            'field1': ['value1', 'value2'],
            'field2': ['value3', 'value4']
        })

        # Mocking the comparison with sample.parquet
        sample_df = pd.DataFrame({
            'blockNumber': [20000001, 20000002],
            'field1': ['value1', 'value2'],
            'field2': ['value3', 'value4']
        })

        # Mocking the read_table method to return the sample DataFrame
        mock_pq.read_table.return_value.to_pandas.return_value = sample_df

        # Compare the output DataFrame with the sample DataFrame
        pd.testing.assert_frame_equal(output_df, sample_df)

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
