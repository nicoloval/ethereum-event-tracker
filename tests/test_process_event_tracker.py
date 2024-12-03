import unittest
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv('tests/.env')
import subprocess
import os

class TestProcessEventTracker(unittest.TestCase):

    def test_process_event_tracker(self):
        # Define the command to run the process_event_tracker script
        cmd = [
            'python', 'sample/process_event_tracker.py',
            '-n', 'tests/stETH.json',
            '-a', '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84',
            '-e', 'tests/stETH-Transfer.sol',
            '-f', '17000000',
            '-t', '17000100',
            '-l', './log.txt',
            '-o', 'output.parquet',
            '-r', os.getenv('RPC_URL')
        ]

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"Process failed with return code {result.returncode}. Output: {result.stdout}, Error: {result.stderr}")

        # Check if the output file exists and measure the number of events
        output_file_path = 'output.parquet'
        if os.path.exists(output_file_path):
            import pyarrow.parquet as pq
            table = pq.read_table(output_file_path)
            num_events = table.num_rows
            print(f"Number of events in the output file: {num_events}")

        # if os.path.exists('output.parquet'):
        #     os.remove('output.parquet')
        # if os.path.exists('./log.txt'):
        #     os.remove('./log.txt')

if __name__ == "__main__":
    unittest.main()
