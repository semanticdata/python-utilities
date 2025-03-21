# This script is used to monitor the system resources of the machine.
# It is a simple script that uses the psutil library to get the system information.
# pip install psutil matplotlib customtkinter numpy

import psutil
import time
from datetime import datetime
import platform
import os
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from collections import deque
import numpy as np


class SystemMonitor:
    def __init__(self, log_to_file=False):
        self.cpu_count = psutil.cpu_count()
        self.cpu_count_logical = psutil.cpu_count(logical=True)
        self.log_to_file = log_to_file  # New attribute for logging option
        self.running = False
        self.data_points = 60  # Store 60 seconds of data
        self.cpu_history = deque([0] * self.data_points, maxlen=self.data_points)
        self.memory_history = deque([0] * self.data_points, maxlen=self.data_points)
        self.network_recv_history = deque(
            [0] * self.data_points, maxlen=self.data_points
        )
        self.network_send_history = deque(
            [0] * self.data_points, maxlen=self.data_points
        )
        self.last_network_recv = 0
        self.last_network_send = 0

    def get_cpu_info(self):
        """Get CPU usage information."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        return {
            "cpu_percent": cpu_percent,
            "cpu_freq": cpu_freq,
            "cpu_count": self.cpu_count,
            "cpu_count_logical": self.cpu_count_logical,
        }

    def get_memory_info(self):
        """Get memory usage information."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent,
            },
        }

    def get_disk_info(self):
        """Get disk usage information."""
        partitions = psutil.disk_partitions()
        disk_info = {}

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info[partition.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                }
            except Exception:
                continue
        return disk_info

    def get_network_info(self):
        """Get network information."""
        network_info = psutil.net_io_counters()
        return {
            "bytes_sent": network_info.bytes_sent,
            "bytes_recv": network_info.bytes_recv,
            "packets_sent": network_info.packets_sent,
            "packets_recv": network_info.packets_recv,
        }

    def get_network_connections(self):
        """Get network connections information."""
        connections = psutil.net_connections()
        for conn in connections:
            print(conn)

    def format_bytes(self, bytes):
        """Convert bytes to human readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024

    def stop_monitoring(self):
        self.running = False

    def monitor(self, interval=1, update_callback=None):
        """Monitor system resources continuously."""
        self.running = True
        try:
            log_file = None
            if self.log_to_file:
                log_file = open("log.txt", "a")

            while self.running:
                # Get system info
                cpu_info = self.get_cpu_info()
                memory_info = self.get_memory_info()
                network_info = self.get_network_info()

                # Update histories
                cpu_avg = sum(cpu_info["cpu_percent"]) / len(cpu_info["cpu_percent"])
                self.cpu_history.append(cpu_avg)
                self.memory_history.append(memory_info["percent"])

                # Calculate network speed
                network_recv_speed = (
                    network_info["bytes_recv"] - self.last_network_recv
                ) / interval
                network_send_speed = (
                    network_info["bytes_sent"] - self.last_network_send
                ) / interval
                self.network_recv_history.append(network_recv_speed)
                self.network_send_history.append(network_send_speed)
                self.last_network_recv = network_info["bytes_recv"]
                self.last_network_send = network_info["bytes_sent"]

                # Generate log output
                log_output = "\n" + "=" * 50 + "\n"
                log_output += (
                    f"System Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                log_output += "=" * 50 + "\n"

                # CPU Information
                log_output += "\nCPU Information:\n"
                log_output += f"Physical cores: {cpu_info['cpu_count']}\n"
                log_output += f"Logical cores: {cpu_info['cpu_count_logical']}\n"
                for i, percentage in enumerate(cpu_info["cpu_percent"]):
                    log_output += f"Core {i}: {percentage}%\n"

                # Memory Information
                log_output += "\nMemory Information:\n"
                log_output += f"Total: {self.format_bytes(memory_info['total'])}\n"
                log_output += (
                    f"Available: {self.format_bytes(memory_info['available'])}\n"
                )
                log_output += f"Used: {self.format_bytes(memory_info['used'])} ({memory_info['percent']}%)\n"
                log_output += f"Swap Used: {self.format_bytes(memory_info['swap']['used'])} ({memory_info['swap']['percent']}%)\n"

                # Disk Information
                disk_info = self.get_disk_info()
                log_output += "\nDisk Information:\n"
                for mount_point, usage in disk_info.items():
                    log_output += f"\nMount Point: {mount_point}\n"
                    log_output += f"Total: {self.format_bytes(usage['total'])}\n"
                    log_output += f"Used: {self.format_bytes(usage['used'])} ({usage['percent']}%)\n"
                    log_output += f"Free: {self.format_bytes(usage['free'])}\n"

                # Network Information
                log_output += "\nNetwork Information:\n"
                log_output += (
                    f"Bytes Sent: {self.format_bytes(network_info['bytes_sent'])}\n"
                )
                log_output += (
                    f"Bytes Received: {self.format_bytes(network_info['bytes_recv'])}\n"
                )
                log_output += f"Packets Sent: {network_info['packets_sent']}\n"
                log_output += f"Packets Received: {network_info['packets_recv']}\n"

                if self.log_to_file:
                    log_file.write(log_output)
                print(log_output)

                if update_callback:
                    update_callback()

                time.sleep(interval)

            if log_file:
                log_file.close()

        except Exception as e:
            print(f"Error: {e}")
            self.running = False


class MonitoringApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("System Monitor")
        self.app.geometry("1200x800")

        self.monitor = SystemMonitor()
        self.monitoring_thread = None
        self.interface_frames = []

        # Get system info once at startup
        self.system_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node()
        }

        self.setup_ui()

    def setup_ui(self):
        # Create main frames with specific weights
        self.control_frame = ctk.CTkFrame(self.app, width=400)
        self.control_frame.pack(side="left", fill="both", padx=10, pady=10, expand=True)
        self.control_frame.pack_propagate(False)

        self.graphs_frame = ctk.CTkFrame(self.app)
        self.graphs_frame.pack(side="right", fill="both", padx=10, pady=10, expand=True)

        # Add system info section
        self.system_info_frame = ctk.CTkFrame(self.control_frame)
        self.system_info_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(self.system_info_frame, text="System Information", font=("Arial", 16, "bold")).pack(pady=5)
        
        info_text = f"OS: {self.system_info['system']} {self.system_info['release']}\n"
        info_text += f"Hostname: {self.system_info['hostname']}\n"
        info_text += f"Architecture: {self.system_info['machine']}\n"
        info_text += f"Processor: {self.system_info['processor']}"
        
        system_info_label = ctk.CTkLabel(self.system_info_frame, text=info_text, justify="left")
        system_info_label.pack(padx=10, pady=5)

        # Create control section
        control_section = ctk.CTkFrame(self.control_frame)
        control_section.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ctk.CTkButton(
            control_section, 
            text="Start Monitoring", 
            command=self.toggle_monitoring
        )
        self.start_button.pack(pady=5)
        
        self.update_interfaces_button = ctk.CTkButton(
            control_section, 
            text="Update Interfaces", 
            command=self.update_interfaces
        )
        self.update_interfaces_button.pack(pady=5)

        self.log_var = ctk.BooleanVar(value=False)
        self.log_checkbox = ctk.CTkCheckBox(
            control_section, 
            text="Log to log.txt", 
            variable=self.log_var
        )
        self.log_checkbox.pack(pady=5)

        # Create interfaces section
        self.interfaces_frame = ctk.CTkScrollableFrame(
            self.control_frame, 
            label_text="Network Interfaces",
            height=400
        )
        self.interfaces_frame.pack(fill="both", expand=True, pady=10)

        self.setup_graphs()

    def setup_graphs(self):
        self.figure, (self.ax1, self.ax2, self.ax3) = plt.subplots(
            3, 1, figsize=(8, 6), height_ratios=[1, 1, 1]
        )
        self.figure.subplots_adjust(hspace=0.4)
        self.figure.set_facecolor("#2b2b2b")

        # Common graph settings
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor("#2b2b2b")
            ax.tick_params(colors="white", labelsize=8)
            ax.grid(True, color="gray", alpha=0.3, linestyle='--')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')

        # CPU Usage
        self.ax1.set_title("CPU Usage %", color="white", pad=10, fontsize=10)
        self.ax1.set_ylim(0, 100)
        self.ax1.set_xlabel("Time (s)", color="white", fontsize=8)

        # Memory Usage
        self.ax2.set_title("Memory Usage %", color="white", pad=10, fontsize=10)
        self.ax2.set_ylim(0, 100)
        self.ax2.set_xlabel("Time (s)", color="white", fontsize=8)

        # Network Usage
        self.ax3.set_title("Network Usage (MB/s)", color="white", pad=10, fontsize=10)
        self.ax3.set_xlabel("Time (s)", color="white", fontsize=8)

        self.canvas = FigureCanvasTkAgg(self.figure, self.graphs_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_graphs(self):
        if not self.monitor.running:
            return

        time_points = list(range(len(self.monitor.cpu_history)))

        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Update CPU graph with enhanced visuals
        self.ax1.plot(time_points, list(self.monitor.cpu_history), color="#00ff00", linewidth=2)
        self.ax1.fill_between(time_points, list(self.monitor.cpu_history), alpha=0.2, color="#00ff00")
        self.ax1.set_title("CPU Usage %", color="white", pad=10, fontsize=10)
        self.ax1.set_ylim(0, 100)
        self.ax1.grid(True, color="gray", alpha=0.3, linestyle='--')
        self.ax1.tick_params(colors="white")

        # Update Memory graph with enhanced visuals
        self.ax2.plot(time_points, list(self.monitor.memory_history), color="#00ff00", linewidth=2)
        self.ax2.fill_between(time_points, list(self.monitor.memory_history), alpha=0.2, color="#00ff00")
        self.ax2.set_title("Memory Usage %", color="white", pad=10, fontsize=10)
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True, color="gray", alpha=0.3, linestyle='--')
        self.ax2.tick_params(colors="white")

        # Update Network graph with enhanced visuals
        recv_mb = [x / 1024 / 1024 for x in self.monitor.network_recv_history]
        send_mb = [x / 1024 / 1024 for x in self.monitor.network_send_history]
        
        self.ax3.plot(time_points, recv_mb, color="#00ff00", label="Download", linewidth=2)
        self.ax3.plot(time_points, send_mb, color="#ff0000", label="Upload", linewidth=2)
        self.ax3.fill_between(time_points, recv_mb, alpha=0.2, color="#00ff00")
        self.ax3.fill_between(time_points, send_mb, alpha=0.2, color="#ff0000")
        self.ax3.set_title("Network Usage (MB/s)", color="white", pad=10, fontsize=10)
        self.ax3.grid(True, color="gray", alpha=0.3, linestyle='--')
        self.ax3.tick_params(colors="white")
        self.ax3.legend(loc='upper right', facecolor="#2b2b2b", labelcolor="white")

        # Apply common settings to all axes
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor("#2b2b2b")
            ax.tick_params(colors="white", labelsize=8)
            ax.set_xlabel("Time (s)", color="white", fontsize=8)
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')

        self.canvas.draw()

    def update_interfaces(self):
        """Update the network interfaces display"""
        # Clear existing interface frames
        for frame in self.interface_frames:
            frame.destroy()
        self.interface_frames.clear()

        try:
            # Get stats for each network interface
            net_if_stats = psutil.net_if_stats()
            net_io_counters = psutil.net_io_counters(pernic=True)

            for interface, stats in net_if_stats.items():
                # Create a frame for each interface
                interface_frame = ctk.CTkFrame(self.interfaces_frame)
                interface_frame.pack(fill="x", padx=5, pady=5)
                self.interface_frames.append(interface_frame)

                # Interface name and status header with larger font
                header_frame = ctk.CTkFrame(interface_frame)
                header_frame.pack(fill="x", padx=5, pady=2)

                name_label = ctk.CTkLabel(
                    header_frame,
                    text=f"{interface}",
                    font=("Arial", 16, "bold"),  # Increased font size
                )
                name_label.pack(side="left", padx=5)

                status_color = "green" if stats.isup else "red"
                status_label = ctk.CTkLabel(
                    header_frame,
                    text=f"{'●' if stats.isup else '○'} {'Up' if stats.isup else 'Down'}",
                    text_color=status_color,
                    font=("Arial", 14),  # Increased font size
                )
                status_label.pack(side="right", padx=5)

                # Speed indicator with larger font
                speed_label = ctk.CTkLabel(
                    interface_frame,
                    text=f"Speed: {stats.speed if stats.speed else 'Unknown'} Mb/s",
                    font=("Arial", 14),  # Increased font size
                )
                speed_label.pack(anchor="w", padx=5)

                if interface in net_io_counters:
                    io = net_io_counters[interface]

                    # Traffic statistics in two columns
                    stats_frame = ctk.CTkFrame(interface_frame)
                    stats_frame.pack(fill="x", padx=5, pady=2)

                    # Left column - Received
                    recv_frame = ctk.CTkFrame(stats_frame)
                    recv_frame.pack(side="left", fill="x", expand=True, padx=2)

                    ctk.CTkLabel(
                        recv_frame, text="Received", font=("Arial", 12, "bold")
                    ).pack()
                    ctk.CTkLabel(
                        recv_frame, text=f"↓ {self.monitor.format_bytes(io.bytes_recv)}"
                    ).pack()
                    ctk.CTkLabel(
                        recv_frame, text=f"Packets: {io.packets_recv:,}"
                    ).pack()
                    ctk.CTkLabel(recv_frame, text=f"Errors: {io.errin}").pack()
                    ctk.CTkLabel(recv_frame, text=f"Drops: {io.dropin}").pack()

                    # Right column - Sent
                    sent_frame = ctk.CTkFrame(stats_frame)
                    sent_frame.pack(side="right", fill="x", expand=True, padx=2)

                    ctk.CTkLabel(
                        sent_frame, text="Sent", font=("Arial", 12, "bold")
                    ).pack()
                    ctk.CTkLabel(
                        sent_frame, text=f"↑ {self.monitor.format_bytes(io.bytes_sent)}"
                    ).pack()
                    ctk.CTkLabel(
                        sent_frame, text=f"Packets: {io.packets_sent:,}"
                    ).pack()
                    ctk.CTkLabel(sent_frame, text=f"Errors: {io.errout}").pack()
                    ctk.CTkLabel(sent_frame, text=f"Drops: {io.dropout}").pack()

        except Exception as e:
            error_frame = ctk.CTkFrame(self.interfaces_frame)
            error_frame.pack(fill="x", padx=5, pady=5)
            self.interface_frames.append(error_frame)
            ctk.CTkLabel(error_frame, text=f"Error getting interfaces: {str(e)}").pack()

    def toggle_monitoring(self):
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            # Start monitoring
            self.monitor = SystemMonitor(self.log_var.get())
            self.monitoring_thread = threading.Thread(
                target=self.monitor.monitor,
                kwargs={"update_callback": self.update_graphs},
            )
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            self.start_button.configure(text="Stop Monitoring")
        else:
            # Stop monitoring
            self.monitor.stop_monitoring()
            self.monitoring_thread.join(timeout=1)
            self.start_button.configure(text="Start Monitoring")

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = MonitoringApp()
    app.run()
