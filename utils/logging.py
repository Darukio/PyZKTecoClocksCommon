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
import logging
from .file_manager import *
import locale

locale.setlocale(locale.LC_TIME, "Spanish_Argentina.1252")  # Español de Argentina

def config_log(app_name):
    """
    Configures logging for the application.
    This function sets up logging to write debug and error logs to a specific folder structure.
    It creates a "logs" folder in the root directory of the project and organizes logs by month.
    Additionally, it attempts to copy the debug logs to a folder in "C:\\ProgramData" for centralized access.
    
    Args:
        app_name (str): The name of the application, used to name the log files.
    
    Behavior:
        - Creates a "logs" folder in the root directory of the project.
        - Creates a subfolder for the current month in the format "YYYY-MMM".
        - Writes debug logs to a file named "<app_name>_debug.log".
        - Writes error logs to a file named "<app_name>_error.log".
        - Attempts to copy the debug log to "C:\\ProgramData\\Gestor Reloj de Asistencias\\logs".
        - Configures the root logger to use the created handlers.
        - Removes duplicate handlers from the logger to prevent duplicate log entries.
    
    Raises:
        PermissionError: If the function cannot write to "C:\\ProgramData", a warning is logged instead.
    """
    logs_folder = os.path.join(find_root_directory(), 'logs')

    # Create the logs folder if it does not exist
    os.makedirs(logs_folder, exist_ok=True)

    current_date = datetime.today().date()
    date_string = current_date.strftime("%Y-%b")
    logs_month_folder = os.path.join(logs_folder, date_string)

    # Create the monthly logs folder if it does not exist
    os.makedirs(logs_month_folder, exist_ok=True)

    # ======= Root Logs ======= #
    debug_log_file = os.path.join(logs_month_folder, app_name + '_debug.log')
    error_log_file = os.path.join(logs_month_folder, app_name + '_error.log')

    debug_handler = logging.FileHandler(debug_log_file)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'))

    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # ======= Copy logs to ProgramData ======= #
    program_data_path = os.path.join(r"C:\\ProgramData\\Gestor Reloj de Asistencias\\logs", date_string)

    try:
        os.makedirs(program_data_path, exist_ok=True)

        debug_log_file_pd = os.path.join(program_data_path, app_name + '_debug.log')

        debug_handler_pd = logging.FileHandler(debug_log_file_pd)
        debug_handler_pd.setLevel(logging.DEBUG)
        debug_handler_pd.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'))

        # Get logger and remove duplicate handlers if they exist
        logger = logging.getLogger()
        logger.handlers.clear()  # 🔥 This prevents duplicate logs
        logger.setLevel(logging.DEBUG)
        
        # Add both handlers
        logger.addHandler(debug_handler)
        logger.addHandler(error_handler)
        logger.addHandler(debug_handler_pd)

    except PermissionError:
        logging.warning("Could not write to ProgramData.")