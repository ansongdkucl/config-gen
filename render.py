from jinja2 import Environment, FileSystemLoader
import csv
import ipaddress
import json
from ftplib import FTP
import os
import logging

username = os.environ.get('username')
password = os.environ.get('passwordAD')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            with open(local_file, 'wb') as csv_file:
                ftp.retrbinary(f"RETR {remote_file}", csv_file.write)

        logger.info(f"Downloaded {remote_file} from FTP server to {local_file}")
    except Exception as e:
        logger.error(f"Error downloading file from FTP server: {e}")

def upload_to_ftp(ftp_server_ip, ftp_username, ftp_password, local_file, remote_file):
    try:
        with FTP(ftp_server_ip, ftp_username, ftp_password) as ftp:
            with open(local_file, 'rb') as file:
                ftp.storbinary(f"STOR {remote_file}", file)

        logger.info(f"Uploaded {local_file} to FTP server as {remote_file}")
    except Exception as e:
        logger.error(f"Error uploading file to FTP server: {e}")

def render_template(model, hostname, ip_address, access_vlan_id, access_vlan_name, voice_vlan_id, voice_vlan_name, location, gateway, subnet):
    template_file = model + '.j2'
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
        gateway=gateway,
        subnet=subnet
    )

    return output

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
            hostname, ip_address, location, access_vlan_id, access_vlan_name, voice_vlan_id, voice_vlan_name, model = row

            # Load network data from the JSON file
            with open('network_config.json', 'r') as json_file:
                network_data = json.load(json_file)

            # Find the location data for the given IP address
            location_data = find_location(ip_address, network_data)

            if location_data:
                # Render the template
                rendered_output = render_template(
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

                # Save the rendered output to a local file
                local_filename = f"{hostname}-confg.txt"
                with open(local_filename, 'w') as local_file:
                    local_file.write(rendered_output)

                # Upload the local file to the FTP server
                remote_filename = f"{hostname}-confg.txt"
                upload_to_ftp(ftp_server_ip, ftp_username, ftp_password, local_filename, remote_filename)
            else:
                logger.warning(f"No matching location found for IP address: {ip_address}")

if __name__ == "__main__":
    main()
