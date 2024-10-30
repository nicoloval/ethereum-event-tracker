import unittest
import subprocess

class TestEventTracker(unittest.TestCase):

    def test_event_tracker_execution(self):
        """Test that event_tracker.py runs without errors."""
        result = subprocess.run(
            ['python', 'event_tracker.py', '-n', 'TestContract', '-a', '0x123', '-e', 'TestEvent'],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Script failed with error: {result.stderr}")

if __name__ == '__main__':
    unittest.main()
