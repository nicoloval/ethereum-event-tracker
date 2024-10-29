import re

def parse_solidity_event(file_path):
    # Define regular expressions to match event name and parameters
    event_pattern = re.compile(r'event\s+(\w+)\s*\((.*?)\);', re.DOTALL)
    param_pattern = re.compile(r'(\w+)\s+(\w+)')

    # Read the .sol file content
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Find the first event match
    match = event_pattern.search(content)
    if match:
        # Extract event name and parameter list
        event_name = match.group(1)
        param_list = match.group(2).strip()
        
        # Split parameters by line or comma
        fields = []
        types = []
        
        # Find all parameter matches
        for param in param_pattern.finditer(param_list):
            param_type, param_name = param.groups()
            types.append(param_type)
            fields.append(param_name)
        
        return {
            "event_name": event_name,
            "fields": fields,
            "types": types
        }
    else:
        return None

# # Example usage
# file_path = './events/Transfer.sol'
# result = parse_solidity_event(file_path)
# if result:
#     print("Event Name:", result["event_name"])
#     print("Fields:", result["fields"])
#     print("Types:", result["types"])
# else:
#     print("No event found in the file.")
