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
        disk = psutil.disk_usage("/")
        self.safe_addstr(y, x, "Disk Usage:", curses.color_pair(3) | curses.A_BOLD)
        self.safe_addstr(y + 1, x + 2, f"Total: {get_size(disk.total)}")
        self.safe_addstr(y + 2, x + 2, f"Used: {get_size(disk.used)} ({disk.percent}%)")
        self.safe_addstr(y + 3, x + 2, f"Free: {get_size(disk.free)}")

    def draw_network_info(self, y, x):
        net_io = psutil.net_io_counters()
        self.safe_addstr(y, x, "Network:", curses.color_pair(4) | curses.A_BOLD)
        self.safe_addstr(y + 1, x + 2, f"Bytes Sent: {get_size(net_io.bytes_sent)}")
        self.safe_addstr(y + 2, x + 2, f"Bytes Recv: {get_size(net_io.bytes_recv)}")

    def draw_processes(self, y, x):
        height, _ = self.stdscr.getmaxyx()
        max_processes = min(5, height - y - 1)
        if max_processes <= 0:
            return

        self.safe_addstr(y, x, "Top Processes:", curses.color_pair(5) | curses.A_BOLD)
        processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"]
        ):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        processes.sort(key=lambda x: x["cpu_percent"], reverse=True)

        for i, proc in enumerate(processes[:max_processes]):
            process_text = (
                f"{proc['name'][:15]:<15} "
                f"PID: {proc['pid']:<6} "
                f"CPU: {proc['cpu_percent']:>5.1f}% "
                f"MEM: {proc['memory_percent']:>5.1f}%"
            )
            self.safe_addstr(y + i + 1, x + 2, process_text)

    def draw_battery_info(self, y, x):
        """Draw battery information if available"""
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                self.safe_addstr(y, x, "Battery:", curses.color_pair(5) | curses.A_BOLD)
                self.safe_addstr(y + 1, x + 2, f"Charge: {battery.percent}%")
                if battery.power_plugged:
                    self.safe_addstr(y + 2, x + 2, "Status: Plugged In")
                else:
                    remain = battery.secsleft
                    if remain != -1:
                        hours = remain // 3600
                        minutes = (remain % 3600) // 60
                        self.safe_addstr(y + 2, x + 2, f"Time left: {hours}h {minutes}m")
                    
    def draw_temperature_info(self, y, x):
        """Draw temperature information if available"""
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                self.safe_addstr(y, x, "Temperatures:", curses.color_pair(2) | curses.A_BOLD)
                row = 1
                for name, entries in temps.items():
                    for entry in entries:
                        if row > 3: break  # Limit to 3 sensors
                        self.safe_addstr(y + row, x + 2, 
                            f"{name[:10]}: {entry.current:.1f}°C")
                        row += 1

    def draw_system_info(self, y, x):
        """Draw system uptime and load"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60

        self.safe_addstr(y, x, "System Info:", curses.color_pair(1) | curses.A_BOLD)
        self.safe_addstr(y + 1, x + 2, f"Uptime: {days}d {hours}h {minutes}m")
        
        try:
            load1, load5, load15 = psutil.getloadavg()
            self.safe_addstr(y + 2, x + 2, f"Load avg: {load1:.1f}, {load5:.1f}, {load15:.1f}")
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

                # Draw all components
                self.draw_header(0, 0)
                self.draw_system_info(3, 0)
                self.draw_cpu_info(7, 0)
                self.draw_memory_info(7, 40)
                self.draw_disk_info(14, 0)
                self.draw_network_info(14, 40)
                self.draw_battery_info(21, 0)
                self.draw_temperature_info(21, 40)
                self.draw_processes(28, 0)

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
