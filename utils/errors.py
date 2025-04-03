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
    """Base class for errors with logging support."""
    def __init__(self, error_code, extra_info="", level="error"):
        self.code = error_code
        self.base_message = ERRORS.get(str(error_code), "Error desconocido")
        self.extra_info = extra_info
        self.message = self.__format_message()
        self.__log(level)
        super().__init__(self.message)

    def __format_message(self):
        """Formats the error message."""
        if self.extra_info:
            return f"{self.base_message} - {self.extra_info}"
        return self.base_message

    def __log(self, level):
        """Logs the error based on the specified level."""
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
        """Displays the error in a QMessageBox if a graphical interface is available."""
        QMessageBox.critical(parent, f"Error {self.code}", self.message)

    def show_message_box_html(self, parent=None):
        """Displays the error in a QMessageBox with HTML support."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(f"Error {self.code}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(self.message)
        msg_box.exec_()

class BaseErrorWithMessageBox(BaseError):
    """Base class for errors with logging and message box support."""

    def __init__(self, error_code, extra_info="", level="error", parent=None):
        super().__init__(error_code, extra_info, level)
        self.show_message_box(parent)

# Error and warning classes
class NetworkError(BaseError):
    def __init__(self, extra_info=""):
        super().__init__(1000, extra_info, level="warning")

class ConnectionFailedError(BaseError):
    def __init__(self, model_name="", point="", ip=""):
        super().__init__(1001, f'{model_name} - {point} - {ip}')

class OutdatedTimeError(Exception):
    def __init__(self, ip=""):
        super().__init__(ip)

class BatteryFailingError(BaseError):
    def __init__(self, model_name="", point="", ip=""):
        self.ip = ip
        super().__init__(2001, f'{model_name} - {point} - {ip}')

class AttendanceMismatchError(BaseError):
    def __init__(self, extra_info=""):
        super().__init__(2004, extra_info, level="warning")

class ObtainAttendancesError(BaseError):
    def __init__(self, ip=""):
        super().__init__(2005, ip)