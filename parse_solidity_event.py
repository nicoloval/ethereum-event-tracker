import re

def parse_solidity_event(file_path):
    # Define regular expressions to match event name and parameters
    event_pattern = re.compile(r'event\s+(\w+)\s*\((.*?)\);', re.DOTALL)
    param_pattern = re.compile(r'(\w+\d*)\s*(indexed\s+)?(\w+)')

    # Read the .sol file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Find the first event match
    match = event_pattern.search(content)
    if match:
        # Extract event name and parameter list
        event_name = match.group(1)
        param_list = match.group(2).strip()
        
        # Initialize lists to store extracted information
        fields = []
        types = []
        indexed = []
        
        # Find all parameter matches
        for param in param_pattern.finditer(param_list):
            param_type = param.group(1)
            is_indexed = param.group(2) is not None
            param_name = param.group(3)
            
            types.append(param_type)
            fields.append(param_name)
            indexed.append(is_indexed)
        
        return {
            "event_name": event_name,
            "fields": fields,
            "types": types,
            "indexed": indexed
        }
    else:
        return None



# # Example 1: Transfer
# file_path = './event/stETH-Transfer.sol'
# result = parse_solidity_event(file_path)
# if result:
#     print("Event Name:", result["event_name"])
#     print("Fields:", result["fields"])
#     print("Types:", result["types"])
# else:
#     print("No event found in the file.")

# # Example 2: Transfer
# file_path = './event/stETH-TransferShares.sol'
# result = parse_solidity_event(file_path)
# if result:
#     print("Event Name:", result["event_name"])
#     print("Fields:", result["fields"])
#     print("Types:", result["types"])
# else:
#     print("No event found in the file.")
