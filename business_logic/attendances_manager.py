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

from .operation_manager import OperationManager
import configparser
import string
from .models.attendance import Attendance
from .models.device import Device
from .shared_state import SharedState
from ..utils.errors import BaseError
from ..utils.file_manager import create_folder_and_return_path, find_root_directory, save_attendances_to_file
config = configparser.ConfigParser()
from datetime import datetime
import os

# Define the transformation mapping
config.read(os.path.join(find_root_directory(), 'config.ini'))

class AttendancesManagerBase(OperationManager):
    def __init__(self, state: SharedState):
        self.attendances_count_devices: dict[str, dict[str, str]] = {}
        # Get the value of name_attendances_file from the [Program_config] section
        self.name_attendances_file: str = config['Program_config']['name_attendances_file']
        super().__init__(state)

    def manage_devices_attendances(self, selected_ips: list[str]):
        self.attendances_count_devices.clear()
        super().manage_threads_to_devices(selected_ips=selected_ips, function=self.manage_attendances_of_one_device)
        return self.attendances_count_devices
    
    def manage_attendances_of_one_device(self, device: Device):
        raise NotImplementedError("Las subclases deberian implementar este error")

    def format_attendances(self, attendances: list[Attendance], id: int):
        attendances_post_formatting: list[Attendance] = []
        for attendance in attendances:
            attendance.set_id(id)
            attendance.format_attendance()
            if attendance.is_three_months_old() or attendance.is_in_the_future():
                BaseError(2003, attendance, level="warning")
            attendances_post_formatting.append(attendance)
        return attendances_post_formatting

    def manage_individual_attendances(self, device: Device, attendances: list[Attendance]):
        try:
            # logging.debug(str(device))
            folder_path: str = create_folder_and_return_path('devices', device.district_name, device.model_name + "-" + device.point)
            new_time: datetime = datetime.today().date()
            date_string: str = new_time.strftime("%Y-%m-%d")
            file_name: str = device.ip + '_' + date_string + '_file.cro'
            self.manage_attendance_saving(attendances, folder_path, file_name)
            program_data_path = create_folder_and_return_path(device.district_name, device.model_name + "-" + device.point, destination_path=r"C:\\ProgramData\\Gestor Reloj de Asistencias Backup\\devices")
            self.manage_attendance_saving(attendances, program_data_path, file_name)
        except Exception as e:
            BaseError(3000, str(e), level="critical")

    def manage_global_attendances(self, attendances: list[Attendance]):
        try:
            folder_path: str = find_root_directory()
            file_name: str = f"{self.name_attendances_file}.txt"
            self.manage_attendance_saving(attendances, folder_path, file_name)
        except Exception as e:
            BaseError(3000, str(e), level="critical")

    def manage_attendance_saving(self, attendances: list[Attendance], folder_path: string, file_name: string):
        try:
            destiny_path: str = os.path.join(folder_path, file_name)
            # logging.debug(f'destiny_path: {destiny_path}')
            save_attendances_to_file(attendances, destiny_path)
        except Exception as e:
            BaseError(3001, str(e), level="critical")