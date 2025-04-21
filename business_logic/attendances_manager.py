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
import configparser
import string
from .models.attendance import Attendance
from .models.device import Device
from .shared_state import SharedState
from ..utils.errors import BaseError
from ..utils.file_manager import create_folder_and_return_path, find_root_directory
config = configparser.ConfigParser()
from datetime import datetime
import os
lock = eventlet.semaphore.Semaphore()

# Define the transformation mapping
config.read(os.path.join(find_root_directory(), 'config.ini'))

class AttendancesManagerBase(OperationManager):
    def __init__(self, state: SharedState):
        """
        Initializes the AttendancesManager instance.

        Args:
            state (SharedState): The shared state object used for managing application state.

        Attributes:
            attendances_count_devices (dict[str, dict[str, str]]): A dictionary to track attendance counts for devices.
            name_attendances_file (str): The name of the attendances file, retrieved from the 'Program_config' section of the configuration.

        Calls:
            super().__init__(state): Initializes the parent class with the provided shared state.
        """
        self.attendances_count_devices: dict[str, dict[str, str]] = {}
        # Get the value of name_attendances_file from the [Program_config] section
        self.name_attendances_file: str = config['Program_config']['name_attendances_file']
        super().__init__(state)

    def manage_devices_attendances(self, selected_ips: list[str]):
        """
        Manages the attendance records for a list of devices identified by their IPs.

        This method clears the current attendance count for all devices, then 
        processes each device in the provided list of IPs by invoking the 
        `manage_attendances_of_one_device` function for each device. The results 
        are stored in `self.attendances_count_devices`.

        Args:
            selected_ips (list[str]): A list of IP addresses representing the devices 
                                      whose attendance records need to be managed.

        Returns:
            dict: A dictionary containing the attendance count for each device.
        """
        self.attendances_count_devices.clear()
        super().manage_threads_to_devices(selected_ips=selected_ips, function=self.manage_attendances_of_one_device)
        return self.attendances_count_devices
    
    def manage_attendances_of_one_device(self, device: Device):
        """
        Manages the attendance records for a single device.

        This method is intended to be implemented by subclasses to handle
        the specific logic for managing attendance data from a given device.

        Args:
            device (Device): The device for which attendance records need to be managed.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Las subclases deberian implementar este error")

    def format_attendances(self, attendances: list[Attendance], id: int):
        """
        Formats a list of attendance records by setting their ID, formatting them, 
        and filtering out records that are either too old or in the future.

        Args:
            attendances (list[Attendance]): A list of Attendance objects to be formatted.
            id (int): The ID to be set for each attendance record.

        Returns:
            tuple: A tuple containing:
                - attendances_post_formatting (list[Attendance]): The list of formatted Attendance objects.
                - attendance_with_error (list[Attendance]): The list of Attendance objects 
                  that are either older than three months or in the future.
        """
        attendances_post_formatting: list[Attendance] = []
        attendance_with_error = []
        for attendance in attendances:
            attendance.set_id(id)
            attendance.format_attendance()
            if attendance.is_three_months_old() or attendance.is_in_the_future():
                #BaseError(2003, attendance, level="warning")
                attendance_with_error.append(attendance)
            attendances_post_formatting.append(attendance)
        if len(attendance_with_error) > 0:
            return attendances_post_formatting, attendance_with_error
        else:
            return attendances_post_formatting, []

    def manage_individual_attendances(self, device: Device, attendances: list[Attendance]):
        """
        Manages the attendance records for an individual device by saving them to specific folders.

        Args:
            device (Device): The device object containing information about the device, such as its district name,
                             model name, and IP address.
            attendances (list[Attendance]): A list of attendance records to be processed and saved.

        Functionality:
            - Creates a folder path based on the device's district name, model name, and point.
            - Generates a file name using the device's IP address and the current date.
            - Saves the attendance records to the generated folder path and file name.
            - Creates a backup folder path in the "ProgramData" directory and saves the attendance records there as well.
            - Handles any exceptions that occur during the process and logs them as critical errors.

        Raises:
            BaseError: If an exception occurs during the attendance management process, it is logged with an error code
                       and critical level.
        """
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
        """
        Manages the global attendance records by saving them to a specified file.

        Args:
            attendances (list[Attendance]): A list of Attendance objects to be managed and saved.

        Raises:
            BaseError: If an exception occurs during the process, it raises a BaseError
                       with error code 3000 and the exception message, marked as critical.

        Notes:
            - The method determines the root directory and constructs the file path
              using the `name_attendances_file` attribute.
            - The actual saving of attendance data is delegated to the `manage_attendance_saving` method.
        """
        try:
            folder_path: str = find_root_directory()
            file_name: str = f"{self.name_attendances_file}.txt"
            self.manage_attendance_saving(attendances, folder_path, file_name)
        except Exception as e:
            BaseError(3000, str(e), level="critical")

    def manage_attendance_saving(self, attendances: list[Attendance], folder_path: string, file_name: string):
        """
        Manages the saving of attendance records to a specified file.

        This method takes a list of attendance records, a folder path, and a file name,
        and saves the attendance records to the specified file. If an error occurs during
        the saving process, it raises a BaseError with an appropriate error code and message.

        Args:
            attendances (list[Attendance]): A list of attendance records to be saved.
            folder_path (str): The path to the folder where the file will be saved.
            file_name (str): The name of the file where the attendance records will be saved.

        Raises:
            BaseError: If an exception occurs during the saving process, a BaseError is raised
                       with error code 3001 and the exception message.
        """
        try:
            destiny_path: str = os.path.join(folder_path, file_name)
            # logging.debug(f'destiny_path: {destiny_path}')
            self.save_attendances_to_file(attendances, destiny_path)
        except Exception as e:
            BaseError(3001, str(e), level="critical")

    def save_attendances_to_file(self, attendances: list[Attendance], file):
        """
        Saves a list of attendance records to a specified file.

        Args:
            attendances (list[Attendance]): A list of Attendance objects to be saved.
            file (str): The file path where the attendance records will be appended.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            PermissionError: If there is no permission to write to the file.
            OSError: If an OS-related error occurs during file operations.
            Exception: For any other unexpected errors.
        """
        with lock:
            try:
                with open(file, 'a') as f:
                    for attendance in attendances:
                        f.write(f"{attendance.user_id} {attendance.timestamp_str} {attendance.id} {attendance.status}\n")
            except (FileNotFoundError, PermissionError, OSError) as e:
                raise e
            except Exception as e:
                raise e