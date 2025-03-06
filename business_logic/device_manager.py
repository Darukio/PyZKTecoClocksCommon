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

import logging
import eventlet
import os
import configparser
import time

config = configparser.ConfigParser()
from .connection_manager import ConnectionManager, ping_device
from ..utils.errors import ConnectionFailedError, OutdatedTimeError
from ..utils.file_manager import find_root_directory, load_from_file

def organize_device_info(line):
    """Parses a line of text and returns a dictionary with device details."""
    parts = line.strip().split(" - ")
    if len(parts) != 8:
        return None  # Invalid format, return None
    
    keys = ["district_name", "model_name", "point", "ip", "id", "communication", "battery", "active"]
    return dict(zip(keys, parts))

def get_device_info():
    """Loads device information from a file and returns a list of dictionaries."""
    file_path = os.path.join(find_root_directory(), 'info_devices.txt')
    return [device for data in load_from_file(file_path) if (device := organize_device_info(data))]

def network_operation_with_retry(op, ip, port, communication, max_attempts=3, from_service=False):
    config.read(os.path.join(find_root_directory(), 'config.ini'))
    max_attempts = int(config['Network_config']['retry_connection'])
    result = None
    try:
        conn_manager = ConnectionManager(ip, port, communication, from_service=from_service)
    except Exception as e:
        logging.error(str(e))
    
    for _ in range(max_attempts):
        try:
            logging.debug(f'{ip} CONECTANDO!')
            if not conn_manager.is_connected():
                start_time = time.time()
                conn_manager.connect()
                end_time = time.time()
                logging.debug(f'{ip} CONECTADO! {end_time-start_time:.2f}')
            if conn_manager.is_connected():
                logging.debug(f'{ip} OPERACION DE RED!')
                start_time = time.time()
                if hasattr(conn_manager, op):
                    func = getattr(conn_manager, op)
                    result = func()
                else:
                    raise AttributeError(f"La funcion '{op}' no existe en ConnectionManager")
                end_time = time.time()
                logging.debug(f'{ip} FINALIZANDO OPERACION DE RED! {end_time-start_time:.2f}')
                try:
                    conn_manager.end_connection()
                except Exception as e:
                    pass
                logging.debug(f'{ip} FINALIZADO!')
                break
        except OutdatedTimeError as e:
            logging.error(str(e))
            raise e
        except ConnectionRefusedError as e:
            conn_manager.reset_connection()
            if result:
                break
            error_message = f"Intento fallido {_ + 1} de {max_attempts} del dispositivo {ip} para la operacion {op}: {e.__cause__}"
            if _ + 1 == max_attempts:
                raise ConnectionFailedError(error_message) from e
            else:
                ConnectionFailedError(error_message)
        except Exception as e:
            logging.error(str(e))
            pass
                
    logging.debug(f'{ip} RESULTADO!')
    return result