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

import json
import logging
import os
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from .file_manager import find_marker_directory

# Load errors from JSON
with open(os.path.join(find_marker_directory("json"), "json", "errors.json"), encoding="utf-8") as f:
    ERRORS: dict[str, str] = json.load(f)

class BaseError(Exception):
    def __init__(self, error_code, extra_info="", level="error"):
        """
        Initializes an instance of the error class with the specified error code, 
        additional information, and logging level.

        Args:
            error_code (int or str): The code representing the specific error.
            extra_info (str, optional): Additional information to provide context 
                about the error. Defaults to an empty string.
            level (str, optional): The logging level for the error. Defaults to "error".

        Attributes:
            code (int or str): The error code.
            base_message (str): The base error message retrieved from the ERRORS dictionary.
            extra_info (str): Additional context information about the error.
            message (str): The formatted error message combining base_message and extra_info.

        Raises:
            Exception: The base class exception is initialized with the formatted message.
        """
        self.code = error_code
        self.base_message = ERRORS.get(str(error_code), "Error desconocido")
        self.extra_info = extra_info
        self.message = self.__format_message()
        self.__log(level)
        super().__init__(self.message)

    def __format_message(self):
        """
        Formats the error message by appending additional information if available.

        Returns:
            str: The formatted error message. If `extra_info` is provided, it appends
            it to the `base_message` separated by " - ". Otherwise, it returns the
            `base_message` alone.
        """
        if self.extra_info:
            return f"{self.base_message} - {self.extra_info}"
        return self.base_message

    def __log(self, level):
        """
        Logs an error message along with additional details such as cause, context, 
        and traceback at the specified logging level.
        Args:
            level (str): The logging level to use. Can be "warning", "critical", or any other 
                         value for default error logging.
        Behavior:
            - Constructs a log message using the error code and message.
            - Logs the message at the specified level:
                - "warning" logs with `logging.warning`.
                - "critical" logs with `logging.critical`.
                - Any other value logs with `logging.error`.
            - Collects additional details about the error, including:
                - `__cause__`: The cause of the exception, if available.
                - `__context__`: The context of the exception, if available.
                - `__traceback__`: The traceback of the exception, if available.
            - Filters out empty or whitespace-only details.
            - Appends the additional details to the log message and logs it at the debug level 
              if any details are present.
        """
        log_message = f"[{self.code}] {self.message}"
        
        if level == "warning":
            logging.warning(log_message)
        elif level == "critical":
            logging.critical(log_message)
        else:
            logging.error(log_message)

        log_details: list[str] = [
            str(self.__cause__) if self.__cause__ else "",
            str(self.__context__) if self.__context__ else "",
            str(self.__traceback__) if self.__traceback__ else ""
        ]
        log_details: list[str] = [detail for detail in log_details if detail and detail.strip()]  # Filter out empty values

        if len(log_details) > 0:
            log_message += " - " + " ".join(log_details)
            logging.debug(log_message)

    def show_message_box(self, parent=None):
        """
        Displays a critical error message box with the error code and message.

        Args:
            parent (QWidget, optional): The parent widget for the message box. Defaults to None.
        """
        QMessageBox.critical(parent, f"Error {self.code}", self.message)

    def show_message_box_html(self, parent=None):
        """
        Displays an error message in a QMessageBox with HTML formatting.

        Args:
            parent (QWidget, optional): The parent widget for the QMessageBox. Defaults to None.

        Attributes:
            code (int): The error code to display in the message box title.
            message (str): The error message to display in the message box body.
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(f"Error {self.code}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(self.message)
        msg_box.exec_()

class BaseErrorWithMessageBox(BaseError):
    def __init__(self, error_code, extra_info="", level="error", parent=None):
        """
        Initializes the error handling instance.

        Args:
            error_code (str): The code representing the specific error.
            extra_info (str, optional): Additional information about the error. Defaults to an empty string.
            level (str, optional): The severity level of the error (e.g., "error", "warning"). Defaults to "error".
            parent (object, optional): The parent object for the error message box, if applicable. Defaults to None.
        """
        super().__init__(error_code, extra_info, level)
        self.show_message_box(parent)

# Error and warning classes
class NetworkError(BaseError):
    def __init__(self, extra_info=""):
        """
        Initializes the error instance with a specific error code, extra information, 
        and a warning level.

        Args:
            extra_info (str, optional): Additional information about the error. 
                                        Defaults to an empty string.
        """
        super().__init__(1000, extra_info, level="warning")

class ConnectionFailedError(BaseError):
    def __init__(self, model_name="", point="", ip=""):
        """
        Initializes an instance of the error with a specific model name, point, and IP address.

        Args:
            model_name (str, optional): The name of the model associated with the error. Defaults to an empty string.
            point (str, optional): The specific point or location related to the error. Defaults to an empty string.
            ip (str, optional): The IP address associated with the error. Defaults to an empty string.
        """
        super().__init__(1001, f'{model_name} - {point} - {ip}')

class OutdatedTimeError(Exception):
    def __init__(self, ip=""):
        """
        Initializes the instance with the specified IP address.

        Args:
            ip (str, optional): The IP address to associate with the instance. Defaults to an empty string.
        """
        super().__init__(ip)

class BatteryFailingError(BaseError):
    def __init__(self, model_name="", point="", ip=""):
        """
        Initializes an instance of the class with the specified model name, point, and IP address.

        Args:
            model_name (str, optional): The name of the model. Defaults to an empty string.
            point (str, optional): A specific point or identifier. Defaults to an empty string.
            ip (str, optional): The IP address associated with the instance. Defaults to an empty string.
        """
        self.ip = ip
        super().__init__(2001, f'{model_name} - {point} - {ip}')

class AttendanceMismatchError(BaseError):
    def __init__(self, extra_info=""):
        """
        Initializes the error instance with a specific error code, extra information, 
        and a warning level.

        Args:
            extra_info (str, optional): Additional information about the error. 
                                        Defaults to an empty string.
        """
        super().__init__(2004, extra_info, level="warning")

class ObtainAttendancesError(BaseError):
    def __init__(self, ip=""):
        """
        Initializes the error instance with a specific IP address.

        Args:
            ip (str, optional): The IP address associated with the error. Defaults to an empty string.
        """
        super().__init__(2005, ip)