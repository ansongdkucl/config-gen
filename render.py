from jinja2 import Environment, FileSystemLoader
import csv
import ipaddress
import json
from ftplib import FTP
import os

username = os.environ.get('username')
password = os.environ.get('passwordAD')


# Set up the Jinja2 environment with a file system loader
env = Environment(loader=FileSystemLoader('/home/ansongdk/scripts/GUI/templates'))

def find_location(ip_address, network_data):
    # Convert the IP address string to an ipaddress.IPv4Address object
    ip = ipaddress.IPv4Address(ip_address)

    # Iterate through each location in the network_data dictionary
    for location, data in network_data.items():
        network_address = ipaddress.IPv4Network(f"{data['network_address']}/{data['subnet_mask']}", strict=False)
        if ip in network_address:
            return data

    return None

def download_csv_from_ftp(ftp_server_ip, ftp_username, ftp_password, remote_file, local_file):
    try:
        with FTP(ftp_server_ip, ftp_username, ftp_password) as ftp:
            ftp.retrbinary(f"RETR {remote_file}", open(local_file, 'wb').write)
            print(f"Downloaded {remote_file} from FTP server to {local_file}")
    except Exception as e:
        print(f"Error downloading file from FTP server: {e}")

def main():
    # FTP server details
    ftp_server_ip = "10.36.50.60"
    ftp_username = username
    ftp_password = password

    # Download 'data.csv' from FTP server to local directory
    download_csv_from_ftp(ftp_server_ip, ftp_username, ftp_password, 'data.csv', 'data.csv')

    # Load data from the downloaded CSV file
    with open('data.csv', 'r') as f:
        csv_data = csv.reader(f)
        for row in csv_data:
            #model, hostname, ip_address, access_vlan, access_name, voice_vlan, voice_name, location = row
            hostname, ip_address, location, access_vlan_id, access_vlan_name, voice_vlan_id, voice_vlan_name, model = row

            # Load network data from the JSON file
            with open('network_config.json', 'r') as json_file:
                network_data = json.load(json_file)

            # Find the location data for the given IP address
            location_data = find_location(ip_address, network_data)

            if location_data:
                template_file = model + '.j2'

                # Load the template from the specified file
                template = env.get_template(template_file)

                # Render the template with the provided data
                output = template.render(
                    model=model,
                    hostname=hostname,
                    ip_address=ip_address,
                    access_vlan_id=access_vlan_id,
                    access_vlan_name=access_vlan_name,
                    voice_vlan_id=voice_vlan_id, 
                    voice_vlan_name=voice_vlan_name,
                    location=location,
                    gateway=location_data["gateway"],
                    subnet=location_data["subnet_mask"]
                )

                # Print the rendered output
                print(output)
            else:
                print(f"No matching location found for IP address: {ip_address}")

if __name__ == "__main__":
    main()
