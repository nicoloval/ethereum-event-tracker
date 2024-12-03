import unittest
import subprocess
import os

class TestParallelEventTracker(unittest.TestCase):

    def test_parallel_event_tracker(self):
        # Define the command to run the parallel_event_tracker script
        cmd = [
            'python', 'sample/parallel_event_tracker.py',
            '-n', 'tests/stETH.json',
            '-a', '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84',
            '-e', 'tests/stETH-Transfer.sol',
            '-f', '12000000',
            '-t', '12000010',
            '-c', '2',  # Number of cores
            '-r', 'http://localhost:8547',
            '-l', './logs',
            '-o', './output',
            '-x', 'test_output'
        ]

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"Process failed with return code {result.returncode}. Output: {result.stdout}, Error: {result.stderr}")

        # Check if the output file exists and measure the number of events
        output_file_path = './output/test_output-12000000-12000010.parquet'
        if os.path.exists(output_file_path):
            import pyarrow.parquet as pq
            table = pq.read_table(output_file_path)
            num_events = table.num_rows
            print(f"Number of events in the output file: {num_events}")
        # if os.path.exists('./output'):
        #     for file in os.listdir('./output'):
        #         os.remove(os.path.join('./output', file))
        #     os.rmdir('./output')

if __name__ == "__main__":
    unittest.main()
