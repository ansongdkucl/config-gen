import json
import ipaddress
import csv

# Load the network configuration from the JSON file
with open('network_config.json', 'r') as json_file:
    network_data = json.load(json_file)

def find_subnet(ip_address):
    # Convert the IP address string to an ipaddress.IPv4Address object
    ip = ipaddress.IPv4Address(ip_address)

    # Iterate through each location in the network_data dictionary
    for location, data in network_data.items():
        network_address = ipaddress.IPv4Network(f"{data['network_address']}/{data['subnet_mask']}", strict=False)
        if ip in network_address:
            # The IP address falls within the range of this location
            return {
                "location": location,
                "subnet_mask": data["subnet_mask"],
                "gateway": data["gateway"]
            }

    # If no match is found
    return None

# Read IP addresses from the CSV file
csv_file_path = 'your_csv_file.csv'  # Replace with the actual path to your CSV file
result_data = []

with open(csv_file_path, 'r') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        ip_address = row.get('ip_address')
        if ip_address:
            result = find_subnet(ip_address)
            if result:
                result_data.append({
                    "ip_address": ip_address,
                    "location": result["location"],
                    "subnet_mask": result["subnet_mask"],
                    "gateway": result["gateway"]
                })


# Display the results
for result in result_data:
    print(f"IP Address: {result['ip_address']}, Location: {result['location']}, Subnet Mask: {result['subnet_mask']}, Gateway: {result['gateway']}")
