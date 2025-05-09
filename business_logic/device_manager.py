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

import logging
import os
import configparser
config = configparser.ConfigParser()
from ..utils.file_manager import find_root_directory, load_from_file
from .models.device import Device
from ..utils.errors import BaseError

def organize_devices_info(line: str):
    """
    Parses a line of text containing device information and organizes it into a Device object.

    Args:
        line (str): A string containing device information in the format:
                    "district_name - model_name - point - ip - id - communication - battery_failing - active".

    Returns:
        (Device): An instance of the Device class populated with the parsed information, or
                None if the input line does not conform to the expected format.
    """
    parts: list[str] = line.strip().split(" - ")
    if len(parts) != 8:
        return None  # Invalid format, return None
    return Device(
        district_name=parts[0],
        model_name=parts[1],
        point=parts[2],
        ip=parts[3],
        id=parts[4],
        communication=parts[5],
        battery_failing=parts[6],
        active=parts[7]
    )

def get_devices_info():
    """
    Retrieves information about devices from a specified file.

    This function reads device data from a file named 'info_devices.txt' located
    in the root directory of the project. It processes the data to organize
    device information and returns a list of devices.

    Returns:
        (list[str]): A list of organized device information.

    Raises:
        BaseError: If an error occurs during file loading or data processing,
                   a BaseError with code 3001 is raised, including the error
                   message and a critical severity level.
    """
    file_path: str = os.path.join(find_root_directory(), 'info_devices.txt')
    devices: list[str] = []
    try:
        devices = [device for data in load_from_file(file_path) if (device := organize_devices_info(data))]
    except Exception as e:
        raise BaseError(3001, str(e), level="critical")
    return devices

def activate_all_devices():
    """
    Activates all devices by updating their status in the 'info_devices.txt' file.
    This function reads the 'info_devices.txt' file, modifies the status of each device
    to "True", and writes the updated information back to the file. The file is expected
    to be located in the root directory of the project.
    
    The file format is expected to have lines where each line contains device information
    separated by ' - ', and the status is located at the 8th position (index 7).

    Raises:
        BaseError: If an exception occurs during file operations, a BaseError with code 3001
                   and the exception message is raised.
    """
    try:
        with open(os.path.join(find_root_directory(), 'info_devices.txt'), 'r') as file:
            lines: list[str] = file.readlines()

        new_lines: list[str] = []
        for line in lines:
            parts: list[str] = line.strip().split(' - ')
            parts[7] = "True"
            new_lines.append(' - '.join(parts) + '\n')

        with open(os.path.join(find_root_directory(), 'info_devices.txt'), 'w') as file:
            file.writelines(new_lines)

        logging.debug("Estado activo actualizado correctamente")
    except Exception as e:
        BaseError(3001, str(e))