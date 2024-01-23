import tkinter as tk
from tkinter import ttk, scrolledtext
import serial.tools.list_ports
import serial

class SerialConsole:
    def __init__(self, master):
        self.master = master
        self.master.title("Serial Console")

        # Get available COM ports
        self.available_ports = [port.device for port in serial.tools.list_ports.comports()]

        if not self.available_ports:
            print("No COM ports found. Please check your connections.")
            self.master.destroy()
            return

        # Create Serial Port
        self.serial_port = serial.Serial()

        # Create COM Port Drop-down
        self.com_port_var = tk.StringVar()
        self.com_port_var.set(self.available_ports[0])
        self.com_port_menu = ttk.Combobox(master, textvariable=self.com_port_var, values=self.available_ports)
        self.com_port_menu.pack()

        # Create Text Widget
        self.text_widget = scrolledtext.ScrolledText(master, wrap=tk.WORD)
        self.text_widget.pack(expand=True, fill="both")

        # Create Entry Widget
        self.entry_widget = tk.Entry(master)
        self.entry_widget.pack(expand=True, fill="x")
        self.entry_widget.bind("<Return>", self.send_command)

        # Connect to Serial Port
        self.connect_serial_port()

    def connect_serial_port(self):
        try:
            self.serial_port.port = self.com_port_var.get()
            self.serial_port.open()
            print(f"Connected to {self.serial_port.port}")
            self.read_from_serial()
        except Exception as e:
            print(f"Error opening serial port: {e}")

    def send_command(self, event):
        command = self.entry_widget.get() + "\n"
        self.serial_port.write(command.encode('utf-8'))
        self.entry_widget.delete(0, 'end')

    def read_from_serial(self):
        while True:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('utf-8')
                    self.text_widget.insert(tk.END, data)
                    self.text_widget.see(tk.END)
            except Exception as e:
                print(f"Error reading from serial port: {e}")
                break

if __name__ == "__main__":
    root = tk.Tk()
    console = SerialConsole(root)
    root.mainloop()
