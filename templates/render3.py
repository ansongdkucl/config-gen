from jinja2 import Environment, FileSystemLoader
import csv
import ipaddress
import json

# Set up the Jinja2 environment with a file system loader
env = Environment(loader=FileSystemLoader('/home/ansongdk/scripts/templates'))

# Load data from the YAML file
with open('/home/ansongdk/scripts/templates/csv_data.csv', 'r') as f:
    csv_data = csv.reader(f)
   # next(csv_data)  # Skip header row
    for row in csv_data:
        model = row[0]
        hostname = row[1]
        ip_address = row[2]
        access_vlan = row[3]
        voice_vlan = row[4]
        location = row[5]
       # print(model)
    with open('network_config.json', 'r') as json_file:
    #with open('importjson.py', 'r') as json_file:
        network_data = json.load(json_file)
        print(network_data)
        print(ip_address)
     

    
        # Convert the IP address string to an ipaddress.IPv4Address object
        ip = ipaddress.IPv4Address(ip_address)

        # Iterate through each location in the network_data dictionary
        for location, data in network_data.items():
            network_address = ipaddress.IPv4Network(f"{data['network_address']}/{data['subnet_mask']}", strict=False)
            if ip in network_address:
                # The IP address falls within the range of this location
                print(data["subnet_mask"])
                print(data["gateway"])
            
            # If no match is found
            template_file = model + '.j2'

            # Load the template from the specified file
            template = env.get_template(template_file)

            # Render the template with the provided data
            output = template.render(
                model=model,
                hostname=hostname,
                ip_address=ip_address,
                access_vlan=access_vlan,
                voice_vlan=voice_vlan,
                location=location,
                gateway=data["gateway"],
                subnet=data["subnet_mask"]
            )

            # Print the rendered output
          
            print(output)

