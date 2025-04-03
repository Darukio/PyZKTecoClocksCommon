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
from .operation_manager import OperationManager
from .models.device import Device
from .shared_state import SharedState
from ..utils.errors import BaseError
import logging
import configparser
config = configparser.ConfigParser()

class HourManagerBase(OperationManager):
    def __init__(self, state: SharedState):
        self.devices_errors: dict[str, dict[str, bool]] = {}
        super().__init__(state=state)

    def update_devices_time(self, selected_ips: list[str]):
        self.devices_errors.clear()
        super().manage_threads_to_devices(selected_ips=selected_ips, function=self.update_device_time_of_one_device)

        if len(self.devices_errors) > 0:
            try:
                for ip, errors in self.devices_errors.items():
                    if errors["battery failing"]:
                        self.update_battery_status(ip)
            except Exception as e:
                BaseError(3000, str(e), level="warning")

        return self.devices_errors
        
    def update_device_time_of_one_device(self, device: Device):
        raise NotImplementedError("Las subclases deberian implementar este error")

    def update_battery_status(self, p_ip: str):
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

            with threading.Lock():
                with open('info_devices.txt', 'w') as file:
                    file.writelines(new_lines)

            logging.info("Estado de pila actualizado correctamente en {}".format(p_ip))
        except Exception as e:
            BaseError(3001, str(e))