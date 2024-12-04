from dotenv import load_dotenv
from web3 import Web3
import os
import sample.log_decoder
from sample.log_filters import make_filter, retry_on_error
from sample.parse_solidity_event import parse_solidity_event
import json

# Load environment variables from .env file
# load_dotenv('tests/.env')
load_dotenv('.env')

# Define the RPC URL
rpc_url = os.getenv('RPC_URL')

# Establish a Web3 connection
w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 40}))

f = open("stETH.json")
# f = open("tests/stETH.json")
contract_abi = json.load(f)
event = parse_solidity_event("stETH-Transfer.sol")
# event = parse_solidity_event("tests/stETH-Transfer.sol")
args = {
    'fromBlock': 12000000,
    'toBlock': 12000200,
    'address': "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
    'topics': ['0x' + Web3.keccak(text=event['event_name'] + '(' + ",".join(event['types']) + ')').hex()]
}
filter_params = make_filter(args)

@retry_on_error()
def get_logs_try(w3, filter_params):
    logs = w3.eth.get_logs(filter_params)
    return logs

logs = get_logs_try(w3, filter_params)
