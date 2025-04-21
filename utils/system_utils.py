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

from .errors import BaseError
from .logging import logging
import ctypes
import subprocess
import sys
import os
import psutil

def dump_all_thread_traces():
    """
    Dumps the stack traces of all active threads for debugging purposes.

    This function retrieves the current stack frames of all active threads
    and logs their details, including thread name, ID, and whether the thread
    is alive. It also prints the stack trace of each thread to help diagnose
    issues such as deadlocks or unexpected behavior in multithreaded applications.

    Note:
        This function uses `sys._current_frames()`, which is considered a private
        API and may not be available or behave consistently across Python versions.

    Logging:
        - Logs the thread name, ID, and alive status using the `logging` module.
        - Logs a separator line ("-" * 50) after each thread's stack trace.

    Dependencies:
        - `sys`: Used to retrieve the current frames of all threads.
        - `threading`: Used to enumerate all active threads.
        - `traceback`: Used to print the stack trace of each thread.
        - `logging`: Used for logging thread details and separators.

    Example:
        Call this function when debugging a multithreaded application to inspect
        the state of all threads:
        
        ```
        dump_all_thread_traces()
        ```
    """
    import sys
    import threading
    import traceback
    import logging

    frames = sys._current_frames()
    for thread in threading.enumerate():
        logging.debug(f"Thread {thread.name} (ID: {thread.ident}): {thread.is_alive()}")
        frame = frames.get(thread.ident)
        if frame:
            traceback.print_stack(frame)
        logging.debug("-" * 50)

def get_parent_process(pid):
    """
    Retrieves the parent process of a given process ID (PID).

    Args:
        pid (int): The process ID of the target process.

    Returns:
        psutil.Process or None: The parent process object if found, 
        or None if the process does not exist or an error occurs.

    Logs:
        Logs an error message if the process with the given PID does not exist.

    Raises:
        BaseError: If an unexpected exception occurs, it raises a BaseError 
        with an error code and the exception message.
    """
    try:
        process = psutil.Process(pid)
        return process.parent()
    except psutil.NoSuchProcess:
        logging.error(f"No existen procesos con el pid {pid}")
        return None
    except Exception as e:
        BaseError(0000, str(e))
    
def get_child_processes(pid):
    """
    Retrieves the child processes of a given process ID (PID).

    Args:
        pid (int): The process ID of the parent process.

    Returns:
        list: A list of `psutil.Process` objects representing the child processes.
              Returns an empty list if no child processes are found or if the parent
              process does not exist.

    Raises:
        psutil.NoSuchProcess: If the process with the given PID does not exist.
        Exception: For any other unexpected errors, logs the error and raises a BaseError.

    Note:
        This function uses the `psutil` library to interact with system processes.
    """
    try:
        process = psutil.Process(pid)
        return process.children()
    except psutil.NoSuchProcess:
        logging.error(f"No existen procesos con el pid {pid}")
        return []
    except Exception as e:
        BaseError(0000, str(e))

def is_user_admin():
    """
    Checks if the current user has administrative privileges.

    Returns:
        bool: True if the user has administrative privileges, False otherwise.

    Logs:
        Logs an error message if an exception occurs while checking privileges.

    Exceptions:
        Handles any exceptions that occur during the privilege check and logs the error.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logging.error(f"Error obteniendo los privilegios: {str(e)}")
        return False
    except Exception as e:
        BaseError(0000, str(e))

def run_as_admin():
    """
    Ensures the script is running with administrator privileges. If the current user is not an 
    administrator, the script restarts itself with elevated permissions.
    Behavior:
    - If the script is an executable (.exe), it uses the Windows ShellExecuteW API to relaunch 
      the script with administrator privileges.
    - If the script is a Python file, it uses PowerShell to relaunch the script with elevated 
      permissions using the `pythonw` interpreter.
    Steps:
    1. Checks if the current user has administrator privileges using the `is_user_admin` function.
    2. If not an administrator:
       - Constructs the command to relaunch the script with its current arguments.
       - Restarts the script with elevated privileges.
       - Terminates the original process.
    Note:
    - This function is specific to Windows environments.
    - The `is_user_admin` function must be implemented elsewhere in the codebase.
    - The `sys` and `ctypes` modules are used for handling script execution and privilege elevation.
    Raises:
        SystemExit: Terminates the original process after relaunching with elevated privileges.
    """
    if not is_user_admin():
        # The script is not running as administrator, so we restart it with elevated privileges
        script = sys.argv[0]
        params = " ".join(sys.argv[1:])

        #logging.debug("script: "+script + " " + params)

        # Run the script with elevated permissions
        if script.endswith(".exe"):  # If it's an .exe file
            # Re-run the script with administrator permissions
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        else:  # If it's a Python script
            subprocess.run(['powershell', 'Start-Process', 'pythonw', '-ArgumentList', f'"{script}" {params}', '-Verb', 'RunAs'])
        sys.exit(0)  # Terminate the original process

def verify_duplicated_instance(script_name):
    """
    Checks if there is another instance of the given script already running.
    Args:
        script_name (str): The full path or name of the script to check for duplicate instances.
    Returns:
        bool: True if a duplicate instance of the script is found, False otherwise.
    This function iterates over all active processes and checks if the given script is already
    running. It considers the following:
    - The process name should match 'python.exe' or 'pythonw.exe' (for Python scripts).
    - The script name should appear in the command line arguments of the process.
    - The process should not be the current process, its parent process, or any of its child processes.
    If a duplicate instance is found, it logs the command line of the duplicate process and returns True.
    Otherwise, it returns False.
    Exceptions:
        - Handles `psutil.NoSuchProcess`, `psutil.AccessDenied`, and `psutil.ZombieProcess` exceptions
          gracefully by ignoring them.
        - Logs any other unexpected exceptions using a custom `BaseError` handler.
    """
    # Get the script name without the full path
    script_basename = os.path.basename(script_name)
    
    # Iterate over all active processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Ignore processes of other programs that are not the current script
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'pythonw.exe':
                # Check if the script instance is already running
                if script_basename in proc.info['cmdline']:
                    if proc.info['pid'] != os.getpid():
                        # If we find another instance that is not the current one
                        logging.info(f"Instancia duplicada encontrada: {proc.info['cmdline']}")
                        return True
            if proc.info['name'] == script_basename:
                if (
                    proc.info['pid'] != os.getpid()  # Not the current process
                    and proc.info['pid'] != get_parent_process(os.getpid()).pid  # Not the parent process
                    and proc.info['pid'] not in [p.pid for p in get_child_processes(os.getpid())]  # Not a child process
                ):
                    # If we find another instance that is not the current one and is not related
                    logging.info(f"Instancia duplicada encontrada: {proc.info['cmdline']}")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            BaseError(0000, str(e))
    
    # If we don't find a duplicate instance, return False
    return False

def exit_duplicated_instance():
    """
    Terminates the script if a duplicate instance is detected.

    This function logs a message indicating that a duplicate instance
    of the script is being closed and then exits the program with a
    status code of 0.

    Usage:
        Call this function when you need to ensure that only one instance
        of the script is running at a time.

    Note:
        Ensure proper logging configuration is set up before calling this
        function to capture the log message.
    """
    logging.info("Cerrando instancia duplicada...")
    sys.exit(0)  # Exit the script if a duplicate is found