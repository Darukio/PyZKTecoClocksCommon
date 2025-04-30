# PyZKTecoClocks: GUI for managing ZKTeco clocks, enabling clock 
# time synchronization and attendance data retrieval.
# Copyright (C) 2024  Paulo Sebastian Spaciuk (Darukio)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import eventlet

class SharedState:
    def __init__(self):
        """
        Initializes the shared state for managing device processing.

        Attributes:
            total_devices (int): The total number of devices to be processed.
            processed_devices (int): The number of devices that have been processed so far.
            lock (eventlet.semaphore.Semaphore): A semaphore to ensure thread-safe access to shared resources.
        """
        self.total_devices = 0
        self.processed_devices = 0
        self.lock = eventlet.semaphore.Semaphore()

    def increment_processed_devices(self):
        """
        Safely increments the count of processed devices in a thread-safe manner.

        This method acquires a lock to ensure that the increment operation is
        performed atomically, preventing race conditions in a multi-threaded
        environment.

        Returns:
            (int): The updated count of processed devices.
        """
        with self.lock:
            self.processed_devices += 1
            return self.processed_devices

    def calculate_progress(self):
        """
        Calculate the progress percentage of processed devices.

        This method calculates the percentage of devices that have been processed
        out of the total number of devices. The calculation is thread-safe as it
        uses a lock to ensure consistency when accessing shared state.

        Returns:
            (int): The progress percentage as an integer. Returns 0 if there are no
            devices to process.
        """
        with self.lock:
            if self.total_devices > 0:
                return int((self.processed_devices / self.total_devices) * 100)
            return 0

    def set_total_devices(self, total):
        """
        Sets the total number of devices.

        This method updates the `total_devices` attribute in a thread-safe manner
        by acquiring a lock before making the modification.

        Args:
            total (int): The total number of devices to set.
        """
        with self.lock:
            self.total_devices = total

    def get_total_devices(self):
        """
        Retrieves the total number of devices.

        Returns:
            (int): The total number of devices.
        """
        return self.total_devices
    
    def reset(self):
        """
        Resets the shared state by setting the count of processed devices to zero.
        This method is typically used to reinitialize the state for a new operation.
        """
        self.processed_devices = 0