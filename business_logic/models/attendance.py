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

from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
import configparser
config = configparser.ConfigParser()
from ...utils.file_manager import find_root_directory
config.read(os.path.join(find_root_directory(), 'config.ini'))

def load_attendance_status_config():
    """
    Loads the attendance status configuration into a global dictionary.

    This function initializes the `attendance_status_dictionary` global variable
    with mappings of status codes to their corresponding configuration values
    from the `config` dictionary. The status codes represent different methods
    of attendance (e.g., fingerprint, face, card).

    Global Variables:
        attendance_status_dictionary (dict): A dictionary mapping status codes
            to their respective attendance status configuration values.

    Raises:
        Exception: Propagates any exception that occurs during the loading
            of the configuration.
    """
    try:
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
    
load_attendance_status_config()

class Attendance():
    def __init__(self, user_id = None, timestamp = None, id = None, status = None):
        """
        Initializes an instance of the attendance model.

        Args:
            user_id (Optional[Any]): The unique identifier for the user. Defaults to None.
            timestamp (Optional[datetime]): The timestamp of the attendance record. Defaults to None.
            id (Optional[Any]): The unique identifier for the attendance record. Defaults to None.
            status (Optional[Any]): The status of the attendance record. Defaults to None.

        Attributes:
            user_id (Any): The unique identifier for the user.
            timestamp (datetime): The timestamp of the attendance record.
            timestamp_str (str): The formatted string representation of the timestamp.
            id (Any): The unique identifier for the attendance record.
            status (Any): The status of the attendance record.

        Raises:
            Exception: Logs an error if an exception occurs during initialization.
        """
        import logging
        try:
            self.user_id = user_id
            self.timestamp = timestamp
            self.timestamp_str: str = timestamp.strftime("%d/%m/%Y %H:%M")
            self.id = id
            self.status = status
        except Exception as e:
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
            (str): A string in the format 'Attendance: {user_id} - {timestamp} - {id} - {status}'.
        """
        return f'Attendance: {self.user_id} - {self.timestamp} - {self.id} - {self.status}'
    
    def __repr__(self):
        """
        Returns a string representation of the Attendance object.

        Returns:
            (str): A string in the format 'Attendance: {user_id} - {timestamp} - {id} - {status}'.
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
            (str): The corresponding attendance status.

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
            (bool): True if the timestamp is at least three months old, False otherwise.
        """
        now = datetime.now()
        three_months_ago = now - relativedelta(months=3)
        return self.timestamp and self.timestamp <= three_months_ago

    def is_in_the_future(self):
        """
        Check if the timestamp is in the future.

        Returns:
            (bool): True if the timestamp is in the future, False otherwise.
        """
        now = datetime.now()
        return self.timestamp and self.timestamp > now