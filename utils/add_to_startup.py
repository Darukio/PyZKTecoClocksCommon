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

import os
import winreg
import logging
from .file_manager import find_root_directory

def add_to_startup(app_name):
    """
    Adds the specified application to the Windows startup registry, ensuring it starts automatically
    when the user logs in.
    Args:
        app_name (str): The name of the application (without the .exe extension) to be added to startup.
    Raises:
        FileNotFoundError: If the executable file for the application cannot be found.
        PermissionError: If the function lacks the necessary permissions to modify the registry.
        OSError: If there is an issue accessing or modifying the Windows registry.
    Notes:
        - This function modifies the Windows registry under the current user's context.
        - The executable file path is constructed by appending ".exe" to the application name and 
          combining it with the root directory path returned by `find_root_directory()`.
        - Ensure that the `find_root_directory()` function is implemented and returns the correct path.
    """
    # Path to the executable you want to start automatically
    executable_path = os.path.join(find_root_directory(), app_name + ".exe")
    #logging.debug(f'executable_path: {executable_path}')

    # Open the registry key where startup programs are stored
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)
    
    # Set the registry value to start your application at startup
    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, executable_path)
    
    # Close the registry key
    winreg.CloseKey(key)

def remove_from_startup(app_name):
    """
    Removes an application from the Windows startup registry.
    This function attempts to delete the specified application's entry
    from the Windows registry key responsible for managing startup programs.
    If the entry does not exist or the registry key cannot be accessed, 
    the function will log the error and exit gracefully.
    Args:
        app_name (str): The name of the application to remove from startup.
    Notes:
        - This function requires access to the Windows registry and should
          be run with appropriate permissions.
        - The `winreg` module is used to interact with the Windows registry.
        - Errors are logged using the `logging` module.
    """
    # Try to open the registry key where startup programs are stored
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)
        #logging.debug(f'key: {key}')
    except FileNotFoundError as e:
        logging.error(e)
        # If the key does not exist, exit the function
        return

    # Try to delete the startup entry if it exists
    try:
        winreg.DeleteValue(key, app_name)
    except FileNotFoundError as e:
        # If the entry does not exist, we can also exit the function
        logging.error(e)
    
    # Close the registry key
    winreg.CloseKey(key)

def is_startup_entry_exists(app_name):
    """
    Checks if a startup entry exists for the given application name in the Windows registry.

    Args:
        app_name (str): The name of the application to check in the Windows startup registry.

    Returns:
        bool: True if the startup entry exists, False otherwise.

    Notes:
        - This function accesses the Windows registry under the current user's context.
        - It specifically checks the 'Run' key in 'HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run'.
        - If the specified application name is not found or an error occurs while accessing the registry, 
          the function returns False.
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except WindowsError:
        return False
