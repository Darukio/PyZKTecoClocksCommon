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

import configparser
import os
from typing import Callable
import eventlet
from .device_manager import get_devices_info
from .models.device import Device
from .shared_state import SharedState
from ..utils.errors import BaseError
from ..utils.file_manager import find_root_directory

class OperationManager:
    def __init__(self, state: SharedState):
        """
        Initializes the OperationManager instance.

        Args:
            state (SharedState): The shared state object used to manage and share data across the application.

        Attributes:
            state (SharedState): Stores the shared state object.
            lock (eventlet.semaphore.Semaphore): A semaphore used to ensure thread-safe operations.
        """
        self.state: SharedState = state
        self.lock = eventlet.semaphore.Semaphore()

    def manage_threads_to_devices(self, selected_ips: list[str], function: Callable):
        """
        Manages the execution of a specified function across multiple devices using a thread pool.
        This method retrieves device information, filters the devices based on the provided IPs, 
        and executes the given function on each selected device using a green thread pool.
        Args:
            selected_ips (list[str]): A list of IP addresses representing the devices to be managed.
            function (Callable): The function to be executed on each selected device. 
                                 The function should accept a `Device` object as its argument.
        Raises:
            BaseError: 
                - If there is an issue retrieving device information (error code 3001).
                - If an exception occurs while spawning a thread for a device (error code 3000, warning level).
                - If a critical exception occurs during the thread pool management (error code 0000, critical level).
        Notes:
            - The maximum size of the thread pool is determined by the `threads_pool_max_size` 
              value in the `config.ini` file under the `Cpu_config` section.
            - The method updates the total number of devices being processed in the state object.
        """
        config = configparser.ConfigParser()
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        pool_max_size: int = int(config['Cpu_config']['threads_pool_max_size'])

        try:
            all_devices: list[Device] = get_devices_info()
        except Exception as e:
            raise BaseError(3001, str(e))

        if all_devices:
            try:
                selected_devices: list[Device] = [device for device in all_devices if device.ip in selected_ips]

                self.state.set_total_devices(len(selected_devices))

                pool = eventlet.GreenPool(size=pool_max_size)

                for selected_device in selected_devices:
                    try:
                        pool.spawn(function, selected_device)
                    except Exception as e:
                        BaseError(3000, str(e), level="warning")

                pool.waitall()
            except Exception as e:
                BaseError(0000, str(e), level="critical")