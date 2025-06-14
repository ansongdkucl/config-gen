import tkinter as tk
from tkinter import ttk, messagebox
import csv
from jinja2 import Environment, FileSystemLoader
import ipaddress
import json
import os
import sys
import re
import paramiko
from typing import Dict, Optional, Any, Tuple
import logging

# Constants
# Constants
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running in a bundle (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Running in normal Python environment
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Get paths that work in both development and compiled versions
TEMPLATES_PATH = resource_path('templates')
CONFIGS_PATH = resource_path('generated_configs')
NETWORK_CONFIG_FILE = resource_path('network_config.json')



FTP_SERVER_IP = '10.36.50.60'  # Hardcoded FTP IP

class NetworkConfigGenerator:
    def __init__(self):
        self.setup_logging()
        self.ensure_directories_exist()
        self.ftp_username = None
        self.ftp_password = None
        self.authenticated = False
        
    def setup_logging(self):
        """Initialize logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def ensure_directories_exist(self):
        """Ensure required directories exist"""
        os.makedirs(TEMPLATES_PATH, exist_ok=True)
        os.makedirs(CONFIGS_PATH, exist_ok=True)
        
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with FTP server"""
        try:
            # Test SFTP connection
            transport = paramiko.Transport((FTP_SERVER_IP, 22))
            transport.connect(username=username, password=password)
            transport.close()
            
            self.ftp_username = username
            self.ftp_password = password
            self.authenticated = True
            self.logger.info("Authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            self.authenticated = False
            return False

    def is_valid_mac_address(self, mac_address: str) -> bool:
        """Validate MAC address format"""
        if not mac_address:
            return False
            
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}){6}$')
        is_valid = bool(mac_pattern.match(mac_address))
        
        if is_valid:
            self.logger.info(f"Valid MAC address: {mac_address}")
        else:
            self.logger.warning(f"Invalid MAC address: {mac_address}")
            
        return is_valid

    def find_location(self, ip_address: str, network_data: Dict) -> Optional[Dict]:
        """Find network location data for a given IP address"""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            
            for location, data in network_data.items():
                network = ipaddress.IPv4Network(
                    f"{data['network_address']}/{data['subnet_mask']}", 
                    strict=False
                )
                if ip in network:
                    return data
                    
        except ipaddress.AddressValueError as e:
            self.logger.error(f"Invalid IP address {ip_address}: {e}")
            
        return None

    def upload_with_sftp(self, local_file: str, remote_file: str) -> bool:
        """Upload file to SFTP server"""
        if not self.authenticated:
            self.logger.error("Cannot upload - not authenticated")
            return False
            
        self.logger.info(f"Starting SFTP upload to {FTP_SERVER_IP}")
        
        try:
            transport = paramiko.Transport((FTP_SERVER_IP, 22))
            transport.connect(username=self.ftp_username, password=self.ftp_password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            remote_directory = "ztp"
            remote_path = f"{remote_directory}/{remote_file}"
            
            sftp.put(local_file, remote_path)
            sftp.close()
            transport.close()
            
            self.logger.info(f"Uploaded {local_file} to {FTP_SERVER_IP} as {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"SFTP upload failed: {e}")
            return False

    def render_template(
        self,
        model: str,
        hostname: str,
        ip_address: str,
        access_vlan_id: str,
        access_vlan_name: str,
        voice_vlan_id: str,
        voice_vlan_name: str,
        location: str,
        gateway: str,
        subnet: str,
        ip_acl: str
    ) -> str:
        """Render configuration template using Jinja2"""
        try:
            env = Environment(loader=FileSystemLoader(TEMPLATES_PATH))
            template_file = f"{model}.j2"
            template = env.get_template(template_file)
            
            return template.render(
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
            
        except Exception as e:
            self.logger.error(f"Template rendering failed: {e}")
            raise

    def save_to_csv(self, filename: str, data: Dict) -> None:
        """Save configuration data to CSV file"""
        try:
            with open(filename, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    data['hostname'],
                    data['ip_address'],
                    data['location'],
                    data['access_vlan_id'],
                    data['access_vlan_name'],
                    data['voice_vlan_id'],
                    data['voice_vlan_name'],
                    data['model']
                ])
            self.logger.info(f"Data written to CSV file: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to write CSV file: {e}")
            raise

    def generate_configuration(self, data: Dict) -> bool:
        """Generate and save network configuration"""
        try:
            with open(NETWORK_CONFIG_FILE, 'r') as json_file:
                network_data = json.load(json_file)
                
            location_data = self.find_location(data['ip_address'], network_data)
            
            if not location_data:
                self.logger.error(f"No matching location found for IP: {data['ip_address']}")
                return False
                
            ip_octets = data['ip_address'].split('.')
            ip_acl = '.'.join(ip_octets[:3])
            
            rendered_config = self.render_template(
                model=data['model'],
                hostname=data['hostname'],
                ip_address=data['ip_address'],
                access_vlan_id=data['access_vlan_id'],
                access_vlan_name=data['access_vlan_name'],
                voice_vlan_id=data['voice_vlan_id'],
                voice_vlan_name=data['voice_vlan_name'],
                location=data['location'],
                gateway=location_data["gateway"],
                subnet=location_data["subnet_mask"],
                ip_acl=ip_acl
            )
            
            local_filename = f"{data['hostname']}-confg"
            local_path = os.path.join(CONFIGS_PATH, local_filename)
            
            with open(local_path, 'w') as local_file:
                local_file.write(rendered_config)
                
            self.logger.info(f"Configuration saved to {local_path}")
            
            if data.get('upload') and self.authenticated:
                remote_filename = (
                    f"{data['mac_address']}.py" if data.get('mac_address') 
                    else f"{data['hostname']}-confg"
                )
                return self.upload_with_sftp(local_path, remote_filename)
            
            return True
                
        except Exception as e:
            self.logger.error(f"Configuration generation failed: {e}")
            return False

class AuthenticationDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Authentication Required")
        self.top.geometry("300x150")
        self.top.resizable(False, False)
        
        # Make the dialog modal
        self.top.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up authentication dialog UI"""
        frame = tk.Frame(self.top)
        frame.pack(pady=20)
        
        # Username
        tk.Label(frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.username_var).grid(row=0, column=1, padx=5, pady=5)
        
        # Password
        tk.Label(frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.password_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.password_var, show="*").grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.top)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Login", command=self.on_login).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=10)
        
    def on_login(self):
        """Handle login button click"""
        self.username = self.username_var.get()
        self.password = self.password_var.get()
        
        if not self.username or not self.password:
            messagebox.showerror("Error", "Username and password are required")
            return
            
        self.top.destroy()
        
    def on_cancel(self):
        """Handle cancel button click"""
        self.username = None
        self.password = None
        self.top.destroy()
        
    def get_credentials(self) -> Tuple[str, str]:
        """Show dialog and return credentials"""
        self.top.wait_window()
        return (self.username, self.password)

class ConfigurationGUI:
    def __init__(self, generator: NetworkConfigGenerator):
        self.generator = generator
        self.window = tk.Tk()
        self.window.title("Configuration Manager v1")
        
        # Authenticate first
        if not self.authenticate():
            self.window.destroy()
            return
            
        self.setup_ui()
        
    def authenticate(self) -> bool:
        """Show authentication dialog and verify credentials"""
        auth_dialog = AuthenticationDialog(self.window)
        username, password = auth_dialog.get_credentials()
        
        if not username or not password:
            return False
            
        if self.generator.authenticate(username, password):
            return True
        else:
            messagebox.showerror("Authentication Failed", 
                               "Invalid credentials or unable to connect to server")
            return False
        
    def setup_ui(self):
        """Set up the user interface"""
        frame = tk.Frame(self.window)
        frame.pack()
        
        # User Information Frame
        user_info_frame = tk.LabelFrame(frame, text="User Information")
        user_info_frame.grid(row=0, column=0)
        
        # Create input fields
        self.create_input_fields(user_info_frame)
        
        # Model selection
        self.create_model_selector(user_info_frame)
        
        # Upload checkbox and submit button
        self.create_action_controls(frame)
        
        # Message label
        self.message_label = tk.Label(frame, text="", fg="green")
        self.message_label.grid(row=3, column=0, pady=10, padx=10)
        
    def create_input_fields(self, parent):
        """Create input fields for network configuration"""
        # Hostname
        tk.Label(parent, text="Hostname").grid(row=1, column=0)
        self.hostname_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.hostname_var).grid(row=2, column=0)
        
        # IP Address
        tk.Label(parent, text="IP Address").grid(row=1, column=1)
        self.ip_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.ip_var).grid(row=2, column=1, pady=10, padx=10)
        
        # SNMP Location
        tk.Label(parent, text="SNMP Location").grid(row=1, column=2)
        self.snmp_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.snmp_var).grid(row=2, column=2, pady=10, padx=10)
        
        # Data VLAN
        tk.Label(parent, text="Data VLAN id").grid(row=13, column=0)
        self.data_id_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.data_id_var).grid(row=15, column=0, pady=10, padx=10)
        
        tk.Label(parent, text="Data VLAN Name").grid(row=13, column=1)
        self.data_name_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.data_name_var).grid(row=15, column=1, pady=10, padx=10)
        
        # Voice VLAN
        tk.Label(parent, text="Voice VLAN id").grid(row=18, column=0)
        self.voice_id_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.voice_id_var).grid(row=19, column=0, pady=10, padx=10)
        
        tk.Label(parent, text="Voice VLAN Name").grid(row=18, column=1)
        self.voice_name_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.voice_name_var).grid(row=19, column=1, pady=10, padx=10)
        
        # MAC Address
        tk.Label(parent, text="Mac Address - ztp only").grid(row=13, column=2)
        self.mac_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.mac_var).grid(row=15, column=2, pady=10, padx=10)
        
    def create_model_selector(self, parent):
        """Create model selection combobox"""
        tk.Label(parent, text="Model").grid(row=18, column=2)
        self.model_var = tk.StringVar()
        model_combobox = ttk.Combobox(
            parent, 
            values=[
                "C9200L-24P-4X",
                "C9300L-48P-4X",
                "WS-C3650-48FD-L",
                "ZTP-C9200L-24P-4X",
                "ZTP-C9200L-24P-4X"
            ], 
            textvariable=self.model_var
        )
        model_combobox.grid(row=19, column=2)
        
    def create_action_controls(self, parent):
        """Create action buttons and checkboxes"""
        # Upload checkbox
        self.upload_var = tk.IntVar()
        tk.Checkbutton(parent, text="Upload to FTP", variable=self.upload_var).grid(
            row=2, column=0, pady=10, padx=10
        )
        
        # Submit button
        tk.Button(parent, text="Submit", command=self.submit_data).grid(
            row=2, column=0, sticky="sw", pady=10, padx=10
        )
        
    def submit_data(self):
        """Handle form submission"""
        try:
            mac_address = self.mac_var.get()
            
            if mac_address and not self.generator.is_valid_mac_address(mac_address):
                self.message_label.config(
                    text="Invalid MAC (should be 12 characters 0-9 & a-f)", 
                    fg="red"
                )
                return
                
            config_data = {
                'hostname': self.hostname_var.get(),
                'ip_address': self.ip_var.get(),
                'location': self.snmp_var.get(),
                'access_vlan_id': self.data_id_var.get(),
                'access_vlan_name': self.data_name_var.get(),
                'voice_vlan_id': self.voice_id_var.get(),
                'voice_vlan_name': self.voice_name_var.get(),
                'model': self.model_var.get(),
                'mac_address': mac_address,
                'upload': bool(self.upload_var.get())
            }
            
            self.generator.save_to_csv('data.csv', config_data)
            success = self.generator.generate_configuration(config_data)
            
            if success:
                self.message_label.config(text="Operation completed successfully", fg="green")
            else:
                self.message_label.config(text="Operation completed with warnings", fg="orange")
            
        except Exception as e:
            self.generator.logger.error(f"Error in submit_data: {e}")
            self.message_label.config(text="Operation failed", fg="red")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def run(self):
        """Run the application"""
        self.window.mainloop()

if __name__ == "__main__":
    os.makedirs(TEMPLATES_PATH, exist_ok=True)
    os.makedirs(CONFIGS_PATH, exist_ok=True)

    generator = NetworkConfigGenerator()
    app = ConfigurationGUI(generator)
    
    # Only run if authentication was successful
    if hasattr(app, 'window'):
        app.run()