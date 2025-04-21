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

import eventlet
from .operation_manager import OperationManager
from .models.device import Device
from .shared_state import SharedState
from ..utils.errors import BaseError
import logging
import configparser
config = configparser.ConfigParser()
lock = eventlet.semaphore.Semaphore()

class HourManagerBase(OperationManager):
    def __init__(self, state: SharedState):
        """
        Initializes the HourManager instance.

        Args:
            state (SharedState): The shared state object used to manage the state across the application.

        Attributes:
            devices_errors (dict[str, dict[str, bool]]): A dictionary to track errors for devices. 
                The outer dictionary uses device identifiers as keys, and the inner dictionary 
                maps error types (as strings) to their boolean status.
        """
        self.devices_errors: dict[str, dict[str, bool]] = {}
        super().__init__(state=state)

    def update_devices_time(self, selected_ips: list[str]):
        """
        Updates the time on the specified devices and handles any errors encountered.
        This method clears the existing device errors, manages threads to update the time
        on the specified devices, and processes any errors that occur during the update.
        Args:
            selected_ips (list[str]): A list of IP addresses of the devices to update.
        Returns:
            dict: A dictionary containing any errors encountered during the update process,
                  where the keys are device IPs and the values are dictionaries of error details.
        Error Handling:
            - If a device reports a "battery failing" error, the battery status for that device
              is updated.
            - Any exceptions raised during error handling are logged as warnings with a custom
              error code (3000).
        """
        self.devices_errors.clear()
        super().manage_threads_to_devices(selected_ips=selected_ips, function=self.update_device_time_of_one_device)

        if len(self.devices_errors) > 0:
            try:
                for ip, errors in self.devices_errors.items():
                    if errors.get("battery failing"):
                        self.update_battery_status(ip)
            except Exception as e:
                BaseError(3000, str(e), level="warning")

        return self.devices_errors
        
    def update_device_time_of_one_device(self, device: Device):
        raise NotImplementedError("Las subclases deberian implementar este error")

    def update_battery_status(self, p_ip: str):
        """
        Updates the battery status of a device in the 'info_devices.txt' file based on its IP address.
        This method reads the 'info_devices.txt' file, searches for the line corresponding to the given IP address,
        and updates the battery status to "False". The updated content is then written back to the file.
        Args:
            p_ip (str): The IP address of the device whose battery status needs to be updated.
        Raises:
            BaseError: If an exception occurs during the file operation, it raises a BaseError with code 3001
                       and the exception message.
        """
        try:
            with open('info_devices.txt', 'r') as file:
                lines: list[str] = file.readlines()

            new_lines: list[str] = []
            for line in lines:
                parts: list[str] = line.strip().split(' - ')
                ip: str = parts[3]
                if ip == p_ip:
                    parts[6] = "False"
                new_lines.append(' - '.join(parts) + '\n')

            with lock:
                with open('info_devices.txt', 'w') as file:
                    file.writelines(new_lines)

            logging.info("Estado de pila actualizado correctamente en {}".format(p_ip))
        except Exception as e:
            BaseError(3001, str(e))