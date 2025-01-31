import tkinter as tk
from tkinter import ttk, messagebox
import requests
import socket
import socks

class VPNClient:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("VPN Client")
        self.setup_ui()
        self.server_url = "http://localhost:5000"
        
    def setup_ui(self):
        frame = ttk.Frame(self.window, padding=20)
        frame.grid(row=0, column=0)
        
        ttk.Label(frame, text="Proxy Host:").grid(row=0, column=0)
        self.host_entry = ttk.Entry(frame)
        self.host_entry.grid(row=0, column=1)
        
        ttk.Label(frame, text="Proxy Port:").grid(row=1, column=0)
        self.port_entry = ttk.Entry(frame)
        self.port_entry.grid(row=1, column=1)
        
        ttk.Button(frame, text="Connect", command=self.connect).grid(row=2, column=0)
        ttk.Button(frame, text="Disconnect", command=self.disconnect).grid(row=2, column=1)
        
        self.status_label = ttk.Label(frame, text="Status: Disconnected")
        self.status_label.grid(row=3, columnspan=2)

    def connect(self):
        try:
            response = requests.post(
                f"{self.server_url}/connect",
                json={"host": self.host_entry.get(), "port": self.port_entry.get()}
            )
            if response.json()['status'] == 'connected':
                self.status_label.config(text="Status: Connected", foreground="green")
            else:
                messagebox.showerror("Error", response.json()['message'])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def disconnect(self):
        response = requests.get(f"{self.server_url}/disconnect")
        self.status_label.config(text="Status: Disconnected", foreground="red")

if __name__ == '__main__':
    VPNClient().window.mainloop()
