import tkinter
from tkinter import ttk
import csv
from jinja2 import Environment, FileSystemLoader
import ipaddress
import json
from ftplib import FTP
import os
import logging
import paramiko
import re

username = os.environ.get('username')
password = os.environ.get('passwordAD')
server_ip = os.environ.get('ftp_server_ip')

ftp_server_ip = server_ip
ftp_username = username 
ftp_password = password


#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))
print(f'This is the script directory - {script_directory}') 



def is_valid_mac_address(mac_address):
    # Regular expression for a valid MAC address pattern
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}){6}$')
    return bool(mac_pattern.match(mac_address))
    if bool:
        print(f"Valid MAC address: {mac_address}")
    else:
        print(f"Invalid MAC address: {mac_address}")
        return False

def find_location(ip_address, network_data):
    # Convert the IP address string to an ipaddress.IPv4Address object
    ip = ipaddress.IPv4Address(ip_address)

    # Iterate through each location in the network_data dictionary
    for location, data in network_data.items():
        network_address = ipaddress.IPv4Network(f"{data['network_address']}/{data['subnet_mask']}", strict=False)
        if ip in network_address:
            return data

    return None

def upload_with_sftp(hostname, username, password, local_file, remote_file):
  try:
    transport = paramiko.Transport((hostname, 22))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    #Specify the remote directory (e.g., "ztp")
    remote_directory = "ztp"
    
    #Combine the remote directory and filename
    remote_path = f"{remote_directory}/{remote_filename}"
    
    sftp.put(local_path, remote_path)

    sftp.close()
    transport.close()

    print(f"Uploaded {local_file} to {hostname} as {remote_file}")
    return True

  except Exception as e:
    print(f"SFTP upload fail: {e}")
    message_label.config(text="FTP Upload Failed", fg="red")
    return False


def render_template(model, hostname, ip_address, access_vlan_id, access_vlan_name, voice_vlan_id, voice_vlan_name, location,gateway, subnet):
    # Combine the script directory and the relative path to get the absolute path to templates
    relative_templates_path = 'templates'
    templates_path = os.path.join(script_directory, relative_templates_path)
    print(f'This is the templates path - {templates_path}')
    print(f'file=templates_path = os.path.join(script_directory, relative_templates_path)')
    env = Environment(loader=FileSystemLoader(templates_path))
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
    print('starting submit data moudule')
    global ip_acl
    global remote_filename
    # Get the data from variables
    hostname = host_name_var.get()
    ip_address = ip_name_var.get()
    snmp_location = snmp_name_var.get()
    data_vlan_id = data_id_var.get()
    data_vlan_name = data_name_var.get()
    voice_vlan_id = voice_id_var.get()
    voice_vlan_name = voice_name_var.get()

    model = title_combobox_var.get()
    mac_address = mac_add_var.get()
    #Validate the MAC address format
    if mac_address and not is_valid_mac_address(mac_address):
        message_label.config(text="should be 12 characters 0-9 & a-f)", fg="red")
        return

    # Calculate the first free octets of the ip_address (assuming it's in the format 'xxx.xxx.xxx.xxx')
    ip_octets = ip_address.split('.')

    ip_acl = ""  # Initialize ip_acl as an empty string
    ip_acl = '.'.join(ip_octets[:3])  # Take the first three octets

    # Determine the filename based on whether mac_address is provided or not
    if mac_address:
        print('mac address is provided')
        remote_filename = f"{mac_address}.py"
        print(f"intended ztp filename willl be - {remote_filename}")
    else:
        remote_filename = f"{hostname}-confg"

    # Write data to CSV file
    with open("data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([hostname, ip_address, snmp_location, data_vlan_id, data_vlan_name, voice_vlan_id, voice_vlan_name, model])
        print(f"Data written to CSV file: Hostname\n {hostname}\n, ipaddress{ip_address}\n, snmp location: {snmp_location}\n, Data Vlan {data_vlan_id}\n, Vlan Name:{data_vlan_name}\n, Voice id: {voice_vlan_id}\n, Voice Name:{voice_vlan_name}\n, Model:{model}")
   

    # Check if the checkbox is ticked before proceeding with the upload
    if upload_var.get() == 1:
        # FTP server details
        
        # Upload the local file to the FTP server
        try:
            upload_with_sftp(ftp_server_ip, ftp_username, ftp_password, 'data.csv', remote_filename)
            message_label.config(text="FTP Upload Successful", fg="green")
            print(f"FTP Upload Successful: {remote_filename}")
        except Exception as e:
            message_label.config(text="FTP Upload Failed", fg="red")

    ren_main()


def ren_main():
    global local_path
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
                
                #local_path = script_directory /generated_configs/ce9333-example-confg
                local_path = os.path.join(script_directory, relative_config_path,local_filename)
               
                print(f'this is the local path - {local_path}')
                with open(local_path, 'w') as local_file:
                    local_file.write(rendered_output)
                
                
                if upload_var.get() == 1:
                # Upload the local file to the FTP server
                    #remote_filename = f"{hostname}-confg"
                    upload_with_sftp(ftp_server_ip, ftp_username, ftp_password, local_filename, remote_filename)
                 
            else:
                print("No matching location found for IP address: {ip_address}")
           

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

mac_label = tkinter.Label(user_info_frame, text="Mac Address - ztp only")
mac_label.grid(row=13, column=2)



# Creating Data Entry
host_name_var = tkinter.StringVar()
ip_name_var = tkinter.StringVar()
snmp_name_var = tkinter.StringVar()
data_id_var = tkinter.StringVar()
data_name_var = tkinter.StringVar()
voice_id_var = tkinter.StringVar()
voice_name_var = tkinter.StringVar()
mac_add_var = tkinter.StringVar()


host_name_entry = tkinter.Entry(user_info_frame, textvariable=host_name_var)
ip_name_entry = tkinter.Entry(user_info_frame, textvariable=ip_name_var)
snmp_name_entry = tkinter.Entry(user_info_frame, textvariable=snmp_name_var)
data_id_entry = tkinter.Entry(user_info_frame, textvariable=data_id_var)
data_name_entry = tkinter.Entry(user_info_frame, textvariable=data_name_var)
voice_id_entry = tkinter.Entry(user_info_frame, textvariable=voice_id_var)
voice_name_entry = tkinter.Entry(user_info_frame, textvariable=voice_name_var)
mac_add_entry = tkinter.Entry(user_info_frame, textvariable=mac_add_var)



host_name_entry.grid(row=2, column=0)
ip_name_entry.grid(row=2, column=1, pady=10, padx=10)
snmp_name_entry.grid(row=2, column=2, pady=10, padx=10)
data_id_entry.grid(row=15, column=0, pady=10, padx=10)
data_name_entry.grid(row=15, column=1, pady=10, padx=10)
voice_id_entry.grid(row=19, column=0, pady=10, padx=10)
voice_name_entry.grid(row=19, column=1, pady=10, padx=10)
mac_add_entry.grid(row=15, column=2, pady=10, padx=10)

title_label = tkinter.Label(user_info_frame, text="Model")
title_combobox_var = tkinter.StringVar()
title_combobox = tkinter.ttk.Combobox(user_info_frame, values=["C9200L-24P-4X","C9300L-48P-4X","WS-C3650-48FD-L",
                                                               "ZTP-C9200L-24P-4X","ZTP-C9200L-24P-4X"], textvariable=title_combobox_var)
title_label.grid(row=18, column=2)
title_combobox.grid(row=19, column=2)

# Checkbutton to indicate whether to upload the file or not
upload_var = tkinter.IntVar()
upload_checkbox = tkinter.Checkbutton(frame, text="Upload to FTP", variable=upload_var)
upload_checkbox.grid(row=2, column=0, pady=10, padx=10)

# Submit Button
print('')
submit_button = tkinter.Button(frame, text="Submit", command=submit_data)
submit_button.grid(row=2, column=0, sticky="sw", pady=10, padx=10)

# Message Label
message_label = tkinter.Label(frame, text="", fg="green")
message_label.grid(row=3, column=0, pady=10, padx=10)
print('about to enter main loop')
window.mainloop()




