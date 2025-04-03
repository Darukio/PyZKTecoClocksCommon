"""
    PyZKTecoClocks: GUI for managing ZKTeco clocks, enabling clock 
    time synchronization and attendance data retrieval.
    Copyright (C) 2024  Paulo Sebastian Spaciuk (Darukio)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import threading

class SharedState:
    """
    A class to manage shared state for device processing.
    Attributes:
        total_devices (int): The total number of devices to be processed.
        processed_devices (int): The number of devices that have been processed.
        lock (threading.Lock): A lock to ensure thread-safe operations on shared state.
    Methods:
        increment_processed_devices():
            Increments the count of processed devices in a thread-safe manner.
            Returns the updated count of processed devices.
        calculate_progress():
            Calculates the progress of device processing as a percentage.
            Returns the progress percentage as an integer.
        set_total_devices(total):
            Sets the total number of devices to be processed in a thread-safe manner.
        get_total_devices():
            Returns the total number of devices to be processed.
    """
    def __init__(self):
        self.total_devices = 0
        self.processed_devices = 0
        self.lock = threading.Lock()

    def increment_processed_devices(self):
        with self.lock:
            self.processed_devices += 1
            return self.processed_devices

    def calculate_progress(self):
        with self.lock:
            if self.total_devices > 0:
                return int((self.processed_devices / self.total_devices) * 100)
            return 0

    def set_total_devices(self, total):
        with self.lock:
            self.total_devices = total

    def get_total_devices(self):
        return self.total_devices
    
    def reset(self):
        self.processed_devices = 0