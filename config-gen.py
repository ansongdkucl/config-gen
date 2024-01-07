import tkinter
from tkinter import ttk
import csv
from ftplib import FTP
import os

username = os.environ.get('username')
password = os.environ.get('passwordAD')

# Configure logging
# No need to configure logging here since you are using print statements for messages

def submit_data():
    # Get the data from variables
    hostname = host_name_var.get()
    ip_address = ip_name_var.get()
    snmp_location = snmp_name_var.get()
    data_vlan_id = data_id_var.get()
    data_vlan_name = data_name_var.get()
    voice_vlan_id = voice_id_var.get()
    voice_vlan_name = voice_name_var.get()
    
    model = title_combobox_var.get()

    # Write data to CSV file
    with open("data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([hostname, ip_address, snmp_location, data_vlan_id, data_vlan_name, voice_vlan_id, voice_vlan_name, model])

    print("Data submitted and written to CSV!")

    # Upload CSV file to FTP server
    upload_to_ftp()

def upload_to_ftp():
    ftp_server_ip = "10.36.50.60"
    ftp_username = username
    ftp_password = password
    ftp_directory = "/home/cceadan"  # Change this to the desired remote directory

    try:
        # Connect to FTP server
        with FTP(ftp_server_ip, ftp_username, ftp_password) as ftp:
            # Change to the remote directory (create if not exists)
            ftp.cwd(ftp_directory)

            # Upload the file
            with open("data.csv", "rb") as file:
                ftp.storbinary(f"STOR data.csv", file)

            # Update the message label text
            message_label.config(text="File 'data.csv' uploaded to FTP server successfully.", fg="green")
    except Exception as e:
        # Update the message label text
        message_label.config(text=f"Error uploading file to FTP server: {e}", fg="red")

# GUI setup
window = tkinter.Tk()
window.title("Configuration Manager")

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
title_combobox = ttk.Combobox(user_info_frame, values=["1", "C9300L-48PF-4X", "C9200L-24P-4X", "C9300-48U", "WS-C2960X-48FPD-L", "WS-C3650-48FD-L"], textvariable=title_combobox_var)
title_label.grid(row=18, column=2)
title_combobox.grid(row=19, column=2)

# Submit Button
submit_button = tkinter.Button(frame, text="Submit", command=submit_data)
submit_button.grid(row=2, column=0, sticky="sw", pady=10, padx=10)

# Message Label
message_label = tkinter.Label(frame, text="", fg="green")  # You can customize color and other properties
message_label.grid(row=3, column=0, pady=10, padx=10)

window.mainloop()
