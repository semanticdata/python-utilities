# This script is used to monitor the system resources of the machine.
# It is a simple script that uses the psutil library to get the system information.
# pip install psutil windows-curses

import curses
import psutil
import time
from datetime import datetime
import sys


def get_size(bytes):
    """
    Convert bytes to human readable format
    """
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024


class SystemMonitor:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.init_colors()
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(1)  # Make getch() non-blocking
        self.min_height = 12
        self.min_width = 40
        # Add box drawing constants
        self.box_chars = {
            'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
            'h': '═', 'v': '║',
            'ttee': '╤', 'btee': '╧', 'ltee': '╟', 'rtee': '╢'
        }

    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    def safe_addstr(self, y, x, text, attr=curses.A_NORMAL):
        """Safely add a string to the screen, checking boundaries"""
        height, width = self.stdscr.getmaxyx()
        if y < height and x < width:
            # Truncate the text if it would exceed the screen width
            max_length = width - x
            if len(text) > max_length:
                text = text[:max_length]
            try:
                self.stdscr.addstr(y, x, text, attr)
            except curses.error:
                pass  # Ignore errors from writing to bottom-right corner

    def draw_box(self, y, x, height, width, title=""):
        """Draw a box with optional title"""
        # Draw corners
        self.safe_addstr(y, x, self.box_chars['tl'])
        self.safe_addstr(y, x + width - 1, self.box_chars['tr'])
        self.safe_addstr(y + height - 1, x, self.box_chars['bl'])
        self.safe_addstr(y + height - 1, x + width - 1, self.box_chars['br'])
        
        # Draw horizontal lines
        for i in range(1, width - 1):
            self.safe_addstr(y, x + i, self.box_chars['h'])
            self.safe_addstr(y + height - 1, x + i, self.box_chars['h'])
        
        # Draw vertical lines
        for i in range(1, height - 1):
            self.safe_addstr(y + i, x, self.box_chars['v'])
            self.safe_addstr(y + i, x + width - 1, self.box_chars['v'])
        
        # Draw title if provided
        if title:
            self.safe_addstr(y, x + 2, f" {title} ")

    def draw_progress_bar(self, y, x, width, percentage, color_pair=0):
        """Draw a progress bar with percentage"""
        filled = int((width - 2) * percentage / 100)
        self.safe_addstr(y, x, "[")
        
        # Choose color based on percentage
        if percentage >= 80:
            color = 2  # Red for high usage
        elif percentage >= 60:
            color = 3  # Yellow for medium usage
        else:
            color = 1  # Green for low usage
            
        self.safe_addstr(y, x + 1, "█" * filled, curses.color_pair(color))
        self.safe_addstr(y, x + 1 + filled, " " * (width - 2 - filled))
        self.safe_addstr(y, x + width - 1, "]")

    def draw_header(self, y, x):
        """Updated header with double-line box"""
        width = 76  # Total width of the interface
        self.draw_box(y, x, 3, width, "System Monitor")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.safe_addstr(y + 1, x + 2, f"Press 'q' to quit | {now}", curses.A_DIM)

    def draw_cpu_info(self, y, x):
        """Updated CPU information display"""
        self.draw_box(y, x, 7, 35, "CPU Usage")
        cpu_percent = psutil.cpu_percent()
        self.safe_addstr(y + 1, x + 2, f"Total: {cpu_percent:>5.1f}%")
        self.draw_progress_bar(y + 2, x + 2, 30, cpu_percent)
        
        cpu_percents = psutil.cpu_percent(percpu=True)
        for i, percent in enumerate(cpu_percents[:3]):  # Show first 3 cores
            self.safe_addstr(y + 3 + i, x + 2, f"Core {i:>2}: {percent:>5.1f}%")
            self.draw_progress_bar(y + 3 + i, x + 11, 21, percent)

    def draw_memory_info(self, y, x):
        """Updated memory information display"""
        self.draw_box(y, x, 7, 35, "Memory Usage")
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        self.safe_addstr(y + 1, x + 2, f"RAM: {get_size(memory.used)}/{get_size(memory.total)}")
        self.draw_progress_bar(y + 2, x + 2, 30, memory.percent)
        
        self.safe_addstr(y + 4, x + 2, f"Swap: {get_size(swap.used)}/{get_size(swap.total)}")
        self.draw_progress_bar(y + 5, x + 2, 30, swap.percent)

    def draw_disk_info(self, y, x):
        """Updated disk information display"""
        self.draw_box(y, x, 6, 35, "Disk Usage")
        disk = psutil.disk_usage("/")
        
        self.safe_addstr(y + 1, x + 2, f"Total: {get_size(disk.total)}")
        self.safe_addstr(y + 2, x + 2, f"Used: {get_size(disk.used)}")
        self.draw_progress_bar(y + 3, x + 2, 30, disk.percent)
        self.safe_addstr(y + 4, x + 2, f"Free: {get_size(disk.free)}")

    def draw_network_info(self, y, x):
        """Updated network information display"""
        self.draw_box(y, x, 6, 35, "Network I/O")
        net_io = psutil.net_io_counters()
        
        # Calculate speeds (simplified version)
        self.safe_addstr(y + 1, x + 2, f"↑ {get_size(net_io.bytes_sent)}")
        self.safe_addstr(y + 2, x + 2, f"↓ {get_size(net_io.bytes_recv)}")
        
        # Add packet information
        self.safe_addstr(y + 3, x + 2, f"Packets sent: {net_io.packets_sent}")
        self.safe_addstr(y + 4, x + 2, f"Packets recv: {net_io.packets_recv}")

    def draw_processes(self, y, x):
        """Updated process information display"""
        self.draw_box(y, x, 8, 76, "Top Processes")
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
        
        # Header
        self.safe_addstr(y + 1, x + 2, "Name".ljust(20) + "PID".ljust(8) + 
                        "CPU%".rjust(7) + "MEM%".rjust(7), curses.A_BOLD)
        
        # Process list
        for i, proc in enumerate(processes[:5]):
            name = proc['name'][:19].ljust(20)
            pid = str(proc['pid']).ljust(8)
            cpu = f"{proc['cpu_percent']:>6.1f}%"
            mem = f"{proc['memory_percent']:>6.1f}%"
            
            color = curses.color_pair(1)  # Default green
            if proc['cpu_percent'] > 50:
                color = curses.color_pair(2)  # Red for high CPU
            elif proc['cpu_percent'] > 20:
                color = curses.color_pair(3)  # Yellow for medium CPU
                
            self.safe_addstr(y + i + 2, x + 2, 
                           f"{name}{pid}{cpu}{mem}", color)

    def draw_battery_info(self, y, x):
        """Updated battery information display"""
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                self.draw_box(y, x, 5, 35, "Battery Status")
                self.safe_addstr(y + 1, x + 2, 
                    f"Charge: {battery.percent:>3}%")
                self.draw_progress_bar(y + 2, x + 2, 30, battery.percent)
                
                status = "Plugged In" if battery.power_plugged else "On Battery"
                if not battery.power_plugged and battery.secsleft != -1:
                    hours = battery.secsleft // 3600
                    minutes = (battery.secsleft % 3600) // 60
                    status = f"{status} ({hours}h {minutes}m left)"
                self.safe_addstr(y + 3, x + 2, status)

    def draw_temperature_info(self, y, x):
        """Updated temperature information display"""
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                self.draw_box(y, x, 6, 35, "Temperature Sensors")
                row = 1
                for name, entries in temps.items():
                    for entry in entries:
                        if row > 4: break
                        temp = entry.current
                        color = curses.color_pair(1)  # Green for normal
                        if temp > 80:
                            color = curses.color_pair(2)  # Red for hot
                        elif temp > 60:
                            color = curses.color_pair(3)  # Yellow for warm
                            
                        self.safe_addstr(y + row, x + 2, 
                            f"{name[:12]}: {temp:>5.1f}°C", color)
                        row += 1

    def draw_system_info(self, y, x):
        """Draw system uptime and load"""
        self.draw_box(y, x, 4, 35, "System Info")
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60

        self.safe_addstr(y + 1, x + 2, f"Uptime: {days}d {hours}h {minutes}m")
        
        try:
            load1, load5, load15 = psutil.getloadavg()
            self.safe_addstr(y + 2, x + 2, f"Load: {load1:.1f}, {load5:.1f}, {load15:.1f}")
        except AttributeError:
            pass

    def check_terminal_size(self):
        """Check if terminal meets minimum size requirements"""
        height, width = self.stdscr.getmaxyx()
        if height < self.min_height or width < self.min_width:
            self.stdscr.clear()
            message = (
                f"Terminal too small. Min size: {self.min_width}x{self.min_height}"
            )
            try:
                self.stdscr.addstr(0, 0, message)
            except curses.error:
                pass
            self.stdscr.refresh()
            return False
        return True

    def run(self):
        try:
            while True:
                if not self.check_terminal_size():
                    time.sleep(1)
                    continue

                self.stdscr.clear()

                # Updated layout positioning
                self.draw_header(0, 0)
                self.draw_system_info(3, 0)
                self.draw_cpu_info(7, 0)
                self.draw_memory_info(7, 40)
                self.draw_disk_info(14, 0)
                self.draw_network_info(14, 40)
                self.draw_battery_info(20, 0)
                self.draw_temperature_info(20, 40)
                self.draw_processes(25, 0)

                self.stdscr.refresh()

                # Check for quit
                c = self.stdscr.getch()
                if c == ord("q"):
                    break

                time.sleep(1)  # Update every second

        except KeyboardInterrupt:
            pass


def main():
    curses.wrapper(lambda stdscr: SystemMonitor(stdscr).run())


if __name__ == "__main__":
    main()
