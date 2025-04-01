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

from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
import configparser

def load_attendance_status_config():
    """
    Loads the attendance status configuration from a 'config.ini' file and 
    populates the global dictionary `attendance_status_dictionary` with the 
    status mappings.

    The configuration file is expected to have an 'Attendance_status' section 
    with the following keys:
    - 'status_fingerprint'
    - 'status_face'
    - 'status_card'

    The dictionary `attendance_status_dictionary` will map specific status 
    codes to their corresponding configuration values:
    - 1: Fingerprint status
    - 15: Face status
    - 0, 2, 4: Card status

    Raises:
        Exception: If there is an error reading the configuration file or 
        accessing the required keys.
    """
    try:
        config = configparser.ConfigParser()
        from ...utils.file_manager import find_root_directory
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        global attendance_status_dictionary
        attendance_status_dictionary = {
            1: config['Attendance_status']['status_fingerprint'],
            15: config['Attendance_status']['status_face'],
            0: config['Attendance_status']['status_card'],
            2: config['Attendance_status']['status_card'],
            4: config['Attendance_status']['status_card'],
        }
    except Exception as e:
        raise e

class Attendance():
    """
    A class to represent an attendance record.
    Attributes:
    -----------
    user_id : int
        The ID of the user.
    timestamp : str
        The timestamp of the attendance in the format "%d/%m/%Y %H:%M".
    timestamp_str : datetime
        The preformatted timestamp as a datetime object.
    id : int
        The ID of the attendance record.
    status : int
        The status of the attendance.
    Methods:
    --------
    set_id(id: int):
        Sets the ID of the attendance record.
    __str__():
        Returns a string representation of the attendance record.
    __repr__():
        Returns a string representation of the attendance record.
    format_attendance():
        Formats the attendance record by zero-padding the user ID and mapping the status using a dictionary.
    mapping_dictionary(number):
        Applies the transformation according to the dictionary.
    is_three_months_old():
        Checks if the attendance record is older than three months.
    is_in_the_future():
        Checks if the attendance record is in the future.
    """
    def __init__(self, user_id: int = None, timestamp: str | datetime = None, id: int = None, status: int = None):
        """
        Initialize an Attendance object.

        Args:
            user_id (int, optional): The ID of the user. Defaults to None.
            timestamp (str, optional): The timestamp of the attendance in the format "%d/%m/%Y %H:%M". Defaults to None.
            id (int, optional): The ID of the attendance record. Defaults to None.
            status (int, optional): The status of the attendance. Defaults to None.
        """
        try:
            load_attendance_status_config()
            self.user_id: int = user_id
            if isinstance(timestamp, datetime):
                self.timestamp_str = timestamp
                self.timestamp: str = timestamp.strftime("%d/%m/%Y %H:%M")
            else:
                self.timestamp: str = timestamp
                self.timestamp_str: datetime = datetime.strptime(timestamp, "%d/%m/%Y %H:%M") if timestamp else None
            self.id: int = id
            self.status: int = status
        except Exception as e:
            import logging
            logging.error(e)

    def set_id(self, id: int):
        """
        Sets the ID for the instance.

        Args:
            id (int): The ID to be set.
        """
        self.id = id

    def __str__(self):
        """
        Returns a string representation of the Attendance object.

        Returns:
            str: A string in the format 'Attendance: {user_id} - {timestamp} - {id} - {status}'.
        """
        return f'Attendance: {self.user_id} - {self.timestamp} - {self.id} - {self.status}'
    
    def __repr__(self):
        """
        Returns a string representation of the Attendance object.

        Returns:
            str: A string in the format 'Attendance: {user_id} - {timestamp} - {id} - {status}'.
        """
        return f'Attendance: {self.user_id} - {self.timestamp} - {self.id} - {self.status}'

    def format_attendance(self):
        """
        Formats the attendance data by ensuring the user_id is a zero-padded string of length 9
        and mapping the status to its corresponding value using the mapping_dictionary method.
        Raises:
            ImportError: If the BaseError module cannot be imported.
            BaseError: If there is an error during the formatting process, with error code 3000.
        Attributes:
            user_id (str): The user ID, zero-padded to 9 characters.
            status (int): The mapped status value.
        """
        try:
            from ...utils.errors import BaseError
        except ImportError as e:
            raise e
        
        try:
            self.user_id = str(self.user_id).zfill(9)
            self.status: int = self.mapping_dictionary(int(self.status))
        except Exception as e:
            BaseError(3000, f'Error formateando la marcacion: {str(e)}')

    def mapping_dictionary(self, number):
        """
        Maps a given number to its corresponding attendance status.

        Args:
            number (int): The status code to be mapped.

        Returns:
            str: The corresponding attendance status.

        Raises:
            ValueError: If the status code is not specified in the dictionary.
        """
        # If the number is in the dictionary, return the transformed value
        if number in attendance_status_dictionary:
            return attendance_status_dictionary[number]
        # Optional: Handle unspecified cases
        else:
            raise ValueError(f"Unspecified status code: {number}")
            
    def is_three_months_old(self):
        """
        Check if the timestamp is at least three months old.

        This method compares the preformatted timestamp with the current date minus three months.
        
        Returns:
            bool: True if the timestamp is at least three months old, False otherwise.
        """
        now = datetime.now()
        three_months_ago = now - relativedelta(months=3)
        return self.timestamp_str and self.timestamp_str <= three_months_ago

    def is_in_the_future(self):
        """
        Check if the timestamp is in the future.

        Returns:
            bool: True if the timestamp is in the future, False otherwise.
        """
        now = datetime.now()
        return self.timestamp_str and self.timestamp_str > now
