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

    def draw_header(self, y, x):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.safe_addstr(y, x, f"System Monitor - {now}", curses.A_BOLD)
        self.safe_addstr(y + 1, x, "Press 'q' to quit", curses.A_DIM)

    def draw_cpu_info(self, y, x):
        # CPU information
        cpu_percent = psutil.cpu_percent()
        self.safe_addstr(y, x, "CPU Usage:", curses.color_pair(1) | curses.A_BOLD)
        self.safe_addstr(y, x + 15, f"{cpu_percent}%")

        # Per-core CPU usage
        cpu_percents = psutil.cpu_percent(percpu=True)
        height, _ = self.stdscr.getmaxyx()
        max_cores = height - y - 3  # Leave some space for other sections
        for i, percent in enumerate(cpu_percents[:max_cores]):
            self.safe_addstr(y + i + 1, x + 2, f"Core {i}: {percent}%")

    def draw_memory_info(self, y, x):
        memory = psutil.virtual_memory()
        self.safe_addstr(y, x, "Memory Usage:", curses.color_pair(2) | curses.A_BOLD)
        self.safe_addstr(y + 1, x + 2, f"Total: {get_size(memory.total)}")
        self.safe_addstr(
            y + 2, x + 2, f"Used: {get_size(memory.used)} ({memory.percent}%)"
        )
        self.safe_addstr(y + 3, x + 2, f"Free: {get_size(memory.free)}")

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
                self.draw_cpu_info(3, 0)
                self.draw_memory_info(3, 40)
                self.draw_disk_info(8, 40)
                self.draw_network_info(13, 40)
                self.draw_processes(12, 0)

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
