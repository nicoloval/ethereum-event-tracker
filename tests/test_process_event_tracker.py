import unittest
import subprocess

class TestProcessEventTracker(unittest.TestCase):

    def test_process_event_tracker(self):
        # Define the command to run the process_event_tracker script
        cmd = [
            'python', 'sample/process_event_tracker.py',
            '-n', 'tests/stETH.json',
            '-a', '0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84',
            '-e', 'tests/stETH-Transfer.sol',
            '-f', '12000000',
            '-t', '12000010',
            '-p',  # Append flag
            '-l', './log.txt',
            '-o', 'output.parquet',
            '-r', 'http://localhost:8547'
        ]

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check if the process ran successfully
        self.assertEqual(result.returncode, 0, f"Process failed with return code {result.returncode}. Output: {result.stdout}, Error: {result.stderr}")

if __name__ == "__main__":
    unittest.main()
