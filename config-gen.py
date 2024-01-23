import tkinter
from tkinter import ttk
import csv
from jinja2 import Environment, FileSystemLoader
import ipaddress
import json
from ftplib import FTP
import os
import logging
import secrets_store


username = os.environ.get('username')
password = os.environ.get('passwordAD')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to the templates directory
relative_templates_path = 'templates'


# Combine the script directory and the relative path to get the absolute path to templates
templates_path = os.path.join(script_directory, relative_templates_path)




env = Environment(loader=FileSystemLoader(templates_path))

# FTP server details
ftp_server_ip = "10.36.50.60"
ftp_username = username
ftp_password = password
ip_acl = ""  # Initialize ip_acl as an empty string

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
        with FTP() as ftp:
            ftp.connect(ftp_server_ip)
            ftp.login(ftp_username, ftp_password)
            with open(local_file, 'wb') as csv_file:
                ftp.retrbinary(f"RETR {remote_file}", csv_file.write)

        logger.info(f"writing config to local file")
    except Exception as e:
        logger.error(f"Error downloading file from FTP server: {e}")

def upload_to_ftp(ftp_server_ip, ftp_username, ftp_password, local_file, remote_file):
    config_path = 'generated_configs'
    config_path = os.path.join(script_directory,config_path,remote_file)
    success = False
    try:
        with FTP() as ftp:
            ftp.connect(ftp_server_ip)
            ftp.login(ftp_username, ftp_password)
            print(config_path)
            with open(config_path, 'rb') as file:
                print(f'attempt to upload {local_file}')
                ftp.storbinary(f"STOR {remote_file}", file)

        logger.info(f"Uploaded {local_file} to FTP server as {remote_file}")
        success = True
    except Exception as e:
        logger.error(f"Error uploading file to FTP server: {e}")

    return success

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
        subnet=subnet,
        ip_acl=ip_acl,
    )

    return output

def submit_data():
    global ip_acl

    # Get the data from variables
    hostname = host_name_var.get()
    ip_address = ip_name_var.get()
    snmp_location = snmp_name_var.get()
    data_vlan_id = data_id_var.get()
    data_vlan_name = data_name_var.get()
    voice_vlan_id = voice_id_var.get()
    voice_vlan_name = voice_name_var.get()

    model = title_combobox_var.get()

    # Calculate the first free octets of the ip_address (assuming it's in the format 'xxx.xxx.xxx.xxx')
    ip_octets = ip_address.split('.')
    ip_acl = '.'.join(ip_octets[:3])  # Take the first three octets

    # Write data to CSV file
    with open("data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([hostname, ip_address, snmp_location, data_vlan_id, data_vlan_name, voice_vlan_id, voice_vlan_name, model])

    print("Data submitted and written to CSV!")

    # Check if the checkbox is ticked before proceeding with the upload
    if upload_var.get() == 1:
        # Upload the local file to the FTP server
        remote_filename = f"{hostname}-confg"
        success = upload_to_ftp(ftp_server_ip, ftp_username, ftp_password, 'data.csv', remote_filename)
        #success = upload_to_ftp(ftp_server_ip, ftp_username, ftp_password, local_file, remote_filename)
        

        if success:
            message_label.config(text="FTP Upload Successful", fg="green")
        else:
            message_label.config(text="FTP Upload Failed", fg="red")

    ren_main()

def ren_main():
    # Download 'data.csv' from FTP server to the local directory
    #download_csv_from_ftp(ftp_server_ip, ftp_username, ftp_password, 'data.csv', 'data.csv')

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
                    subnet=location_data["subnet_mask"],
                )

                # Save the rendered output to a local file
                
                relative_config_path = 'generated_configs'
                local_filename = f"{hostname}-confg"
                local_path = os.path.join(script_directory, relative_config_path,local_filename)
                print(local_path)
                with open(local_path, 'w') as local_file:
                    local_file.write(rendered_output)
                
                
                if upload_var.get() == 1:
                # Upload the local file to the FTP server
                    remote_filename = f"{hostname}-confg"
                    upload_to_ftp(ftp_server_ip, ftp_username, ftp_password, local_filename, remote_filename)
            else:
                logger.warning(f"No matching location found for IP address: {ip_address}")

# GUI setup
window = tkinter.Tk()
window.title("Configuration Manager v1")

frame = tkinter.Frame(window)
frame.pack()

# Label Creation
user_info_frame = tkinter.LabelFrame(frame, text="User Information")
user_info_frame.grid(row=0, column=0)

# Labels
host_name_label = tkinter.Label(user_info_frame, text="Hostname")
host_name_label.grid(row=1, column=0)

ip_name_label = tkinter.Label(user_info_frame, text="IP Address")
ip_name_label.grid(row=1, column=1)

snmp_label = tkinter.Label(user_info_frame, text="SNMP Location")
snmp_label.grid(row=1, column=2)

data_label = tkinter.Label(user_info_frame, text="Data VLAN id")
data_label.grid(row=13, column=0)

voice_label = tkinter.Label(user_info_frame, text="Data VLAN Name")
voice_label.grid(row=13, column=1)

data_label = tkinter.Label(user_info_frame, text="Voice VLAN id")
data_label.grid(row=18, column=0)

voice_label = tkinter.Label(user_info_frame, text="Voice VLAN Name")
voice_label.grid(row=18, column=1)

# Creating Data Entry
host_name_var = tkinter.StringVar()
ip_name_var = tkinter.StringVar()
snmp_name_var = tkinter.StringVar()
data_id_var = tkinter.StringVar()
data_name_var = tkinter.StringVar()
voice_id_var = tkinter.StringVar()
voice_name_var = tkinter.StringVar()

host_name_entry = tkinter.Entry(user_info_frame, textvariable=host_name_var)
ip_name_entry = tkinter.Entry(user_info_frame, textvariable=ip_name_var)
snmp_name_entry = tkinter.Entry(user_info_frame, textvariable=snmp_name_var)
data_id_entry = tkinter.Entry(user_info_frame, textvariable=data_id_var)
data_name_entry = tkinter.Entry(user_info_frame, textvariable=data_name_var)
voice_id_entry = tkinter.Entry(user_info_frame, textvariable=voice_id_var)
voice_name_entry = tkinter.Entry(user_info_frame, textvariable=voice_name_var)

host_name_entry.grid(row=2, column=0)
ip_name_entry.grid(row=2, column=1)
snmp_name_entry.grid(row=2, column=2)
data_id_entry.grid(row=15, column=0)
data_name_entry.grid(row=15, column=1)
voice_id_entry.grid(row=19, column=0)
voice_name_entry.grid(row=19, column=1)

title_label = tkinter.Label(user_info_frame, text="Model")
title_combobox_var = tkinter.StringVar()
title_combobox = tkinter.ttk.Combobox(user_info_frame, values=["C9200L-24P-4X", "C9300-48U", "WS-C3650-48FD-L"], textvariable=title_combobox_var)
title_label.grid(row=18, column=2)
title_combobox.grid(row=19, column=2)

# Checkbutton to indicate whether to upload the file or not
upload_var = tkinter.IntVar()
upload_checkbox = tkinter.Checkbutton(frame, text="Upload to FTP", variable=upload_var)
upload_checkbox.grid(row=2, column=0, pady=10, padx=10)

# Submit Button
submit_button = tkinter.Button(frame, text="Submit", command=submit_data)
submit_button.grid(row=2, column=0, sticky="sw", pady=10, padx=10)

# Message Label
message_label = tkinter.Label(frame, text="", fg="green")
message_label.grid(row=3, column=0, pady=10, padx=10)

window.mainloop()