from web3 import Web3


# decode logs to get ipfs hash
# Generate a dictionary mapping event signature hashes to event ABIs
def generate_event_abi_map(json_abi):
    event_abi_map = {}
    for abi_entry in json_abi:
        # print(abi_entry)
        if abi_entry['type'] == 'event':
            event_signature = f"{abi_entry['name']}({','.join([input['type'] for input in abi_entry['inputs']])})"
            # the ox depends on web3 version
            event_signature_hash = '0x' + Web3.keccak(text=event_signature).hex()
            event_abi_map[event_signature_hash] = abi_entry    
    return event_abi_map                    
    
def decode_log(log, event_abi_map, contract):
    # Match the event signature hash
    # the 0x is to match web3 version
    event_signature_hash = '0x' + log['topics'][0].hex() if log['topics'] else None
    event_abi = event_abi_map.get(event_signature_hash)

    if event_abi:
        # Decode the log based on the matched event ABI
        return contract.events[event_abi['name']]().process_log(log)
    else:
        return None
