import unittest
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv('tests/.env')

class TestWeb3Connection(unittest.TestCase):

    def test_web3_connection(self):
        # Define the RPC URL
        rpc_url = os.getenv('RPC_URL')
        
        # Establish a Web3 connection
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 40}))
        
        # Assert that the connection is successful
        self.assertTrue(w3.is_connected(), "Web3 is not connected to the RPC port")

if __name__ == "__main__":
    unittest.main()
