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
from .device_manager import get_devices_info
from .models.device import Device
from .shared_state import SharedState
import concurrent
from concurrent.futures import ThreadPoolExecutor
from ..utils.errors import BaseError
from ..utils.system_utils import dump_all_thread_traces
config = configparser.ConfigParser()
from ..utils.file_manager import find_root_directory

class OperationManager:
    def __init__(self, state: SharedState):
        self.state: SharedState = state
        self.threads = []

    def manage_threads_to_devices(self, selected_ips: list[str], function: Callable):
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        threads_pool_max_size: int = int(config['Cpu_config']['threads_pool_max_size'])
        executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=threads_pool_max_size)
        all_devices: list[Device] = []
        try:
            all_devices = get_devices_info()
        except Exception as e:
            raise BaseError(3001, str(e))

        if len(all_devices) > 0:
            try:
                selected_devices: list[Device] = [device for device in all_devices if device.ip in selected_ips]

                # Set the total number of devices in the shared state
                self.state.set_total_devices(len(selected_devices))
                
                futures: list[ThreadPoolExecutor] = []
                for selected_device in selected_devices:
                    try:
                        futures.append(executor.submit(function, selected_device))
                    except Exception as e:
                        BaseError(3000, str(e), level="warning")

                #dump_all_thread_traces()

                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        dump_all_thread_traces()
                
            except Exception as e:
                BaseError(0000, str(e), level="critical")

            try:
                executor.shutdown(wait=True)
            except Exception as e:
                BaseError(3000, str(e), level="critical")