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
    import sys
    import threading
    import traceback
    import logging
    # Obtiene los frames de todos los hilos activos
    frames = sys._current_frames()
    for thread in threading.enumerate():
        logging.debug(f"Thread {thread.name} (ID: {thread.ident}): {thread.is_alive()}")
        frame = frames.get(thread.ident)
        if frame:
            traceback.print_stack(frame)
        logging.debug("-" * 50)

def get_parent_process(pid):
    """
    Get the parent process of a given process.

    Args:
        pid (int): PID of the process.

    Returns:
        psutil.Process: Parent process object or None if it doesn't exist.
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
    Get a list of child processes of a given process.

    Args:
        pid (int): PID of the process.

    Returns:
        list: List of psutil.Process objects representing the children.
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
    Check if the process has administrator privileges.
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
    Relaunch the script with administrator privileges if necessary.
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
    logging.info("Cerrando instancia duplicada...")
    sys.exit(0)  # Exit the script if a duplicate is found