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
import re
import logging
import sys

import eventlet
file_lock = eventlet.semaphore.Semaphore()

def load_from_file(file_path):
    """
    Reads the contents of a file and returns them as a list of stripped lines.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        list: A list of strings, where each string is a line from the file with leading
              and trailing whitespace removed.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If there is insufficient permission to read the file.
        OSError: If an OS-related error occurs while accessing the file.
        Exception: For any other unexpected errors.
    """
    content = []
    try:
        with open(file_path, 'r') as file:
            content = [line.strip() for line in file.readlines()] # Remove newlines
    except (FileNotFoundError, PermissionError, OSError) as e:
        raise e
    except Exception as e:
        raise e
    return content

def sanitize_folder_name(name):
    """
    Sanitizes a folder name by replacing invalid characters with a hyphen ('-').

    This function ensures that the folder name contains only alphanumeric characters,
    underscores ('_'), and hyphens ('-'). It also prevents multiple consecutive hyphens
    and removes any leading or trailing hyphens.

    Args:
        name (str): The original folder name to be sanitized.

    Returns:
        str: The sanitized folder name.
    """
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', name)  # Replace invalid characters
    sanitized = re.sub(r'-+', '-', sanitized)  # Prevent multiple consecutive '-'
    return sanitized.strip('-')  # Avoid leading or trailing '-'

def create_folder_and_return_path(*args, destination_path=None):
    """
    Creates a nested folder structure based on the provided folder names and returns the final path.
    Args:
        *args (str): Variable number of folder names to create in a nested structure.
        destination_path (str, optional): The base directory where the folders will be created.
            If not provided, the function will use the result of `find_root_directory()`.
    Returns:
        str: The full path to the final folder in the nested structure.
    Notes:
        - Folder names are sanitized using the `sanitize_folder_name` function before creation.
        - If a folder already exists, it will not be recreated.
        - Logs a debug message for each folder that is created.
    Raises:
        Any exceptions raised by `os.makedirs` or `os.path.join` will propagate.
    """
    if destination_path is None:
        # Base directory where folders will be stored
        destination_path = find_root_directory()
    
    for folder in args:
        sanitized_folder = sanitize_folder_name(folder.lower())  # Clean the folder name
        destination_path = os.path.join(destination_path, sanitized_folder)
        
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
            logging.debug(f'Se ha creado la carpeta {folder} en la ruta {destination_path}')
    
    return destination_path

def find_marker_directory(marker, current_path=os.path.abspath(os.path.dirname(__file__))):
    """
    Recursively searches for a directory containing a specific marker file, starting from the current path 
    and moving up the directory hierarchy.
    Args:
        marker (str): The name of the marker file to search for.
        current_path (str, optional): The starting directory path for the search. Defaults to the directory 
                                      of the current file.
    Returns:
        str or None: The path to the directory containing the marker file if found, otherwise None.
    Notes:
        - If the script is running in a frozen state (e.g., packaged with PyInstaller), the function searches 
          for the specified marker file.
        - If the script is not frozen, the function searches for a file named "main.py" instead of the marker.
    """
    if getattr(sys, 'frozen', False):
        while current_path != os.path.dirname(current_path):  # While not reaching the root of the file system
            if os.path.exists(os.path.join(current_path, marker)):
                return current_path
            current_path = os.path.dirname(current_path)
    else:
        while current_path != os.path.dirname(current_path):  # While not reaching the root of the file system
            if os.path.exists(os.path.join(current_path, "main.py")):
                return current_path
            current_path = os.path.dirname(current_path)
    
    return None

def find_root_directory():
    """
    Determines the root directory of the application.
    If the application is running in a frozen state (e.g., packaged with a tool like PyInstaller),
    the root directory is set to the directory containing the executable. Otherwise, it attempts
    to locate the directory containing a specific marker file (e.g., "main.py").
    Returns:
        str: The path to the root directory of the application, or None if the marker directory
        cannot be found.
    """
    path = None
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        marker = "main.py"
        path = find_marker_directory(marker)

    return path

def file_exists_in_folder(file_name, folder):
    """
    Checks if a file with the specified name exists in the given folder.

    Args:
        file_name (str): The name of the file to check for existence.
        folder (str): The path to the folder where the file is expected to be located.

    Returns:
        bool: True if the file exists in the folder, False otherwise.
    """
    from pathlib import Path
    # Create a Path object for the folder and file
    full_path: Path = Path(folder) / file_name
    return full_path.is_file()