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
from eventlet.green import threading

class SharedState:
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