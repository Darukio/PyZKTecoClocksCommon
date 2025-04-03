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
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except WindowsError:
        return False
