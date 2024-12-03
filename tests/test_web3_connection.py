import unittest
from web3 import Web3

class TestWeb3Connection(unittest.TestCase):

    def test_web3_connection(self):
        # Define the RPC URL
        rpc_url = 'http://localhost:8547'
        
        # Establish a Web3 connection
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 40}))
        
        # Assert that the connection is successful
        self.assertTrue(w3.is_connected(), "Web3 is not connected to the RPC port")

if __name__ == "__main__":
    unittest.main()
