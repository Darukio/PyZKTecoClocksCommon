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

import threading
import logging
import os
from datetime import datetime
import time
import random
from typing import Callable
from .types import DeviceInfo
from ..connection.zk.attendance import Attendance as ZKAttendance
from .models.attendance import Attendance
from ..connection.zk.base import ZK, ZK_helper
import configparser
from ..utils.errors import AttendanceMismatchError, BaseError, NetworkError, ObtainAttendancesError, OutdatedTimeError
from ..utils.file_manager import find_root_directory

class ConnectionManager():
    conn = None

    def __init__(self, ip: str, port: int, communication: str):
        self.force_udp: bool = True if communication == 'UDP' else False
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(find_root_directory(), 'config.ini'))
        timeout = int(self.config['Network_config']['timeout'])
        self.zk: ZK = ZK(ip, port, timeout=timeout, ommit_ping=True, force_udp=self.force_udp)
        self.ip: str = ip
        self.port: str = port
        self.max_attempts = int(self.config['Network_config']['retry_connection'])

    def reset_connection(self):
        self.conn = None
        try:
            self.connect()
        except ConnectionRefusedError as e:
            raise e
    
    def is_connected(self):
        return self.conn is not None and self.conn.is_connect

    def connect(self):
        """Tries to connect to the device."""
        try:
            logging.info(f'Conectando al dispositivo {self.ip}...')
            self.conn = self.zk.connect()
            logging.info(f'Conectado exitosamente al dispositivo {self.ip}')
        except Exception as e:
            self.__handle_connection_error(e)
    
    def connect_with_retry(self):
        """Attempts to reconnect multiple times with retries."""
        for attempt in range(self.max_attempts):
            try:
                self.connect()
                    
                return self.conn
            except ConnectionRefusedError as e:
                if attempt == self.max_attempts - 1:
                    raise NetworkError(f"Maxima cantidad de reintentos para el dispositivo {self.ip}: {str(e)}") from e
                else:
                    error_message = f"Intento fallido {attempt + 1}/{self.max_attempts} del dispositivo {self.ip} para la operacion de conexion: {str(e)}"
                    NetworkError(error_message)
                    self.__exponential_backoff(attempt)
        raise BaseError(0000, "Codigo inalcanzable", level="critical")
    
    def __handle_connection_error(self, e):
        """Handles different types of connection errors."""
        if "TCP packet invalid" in str(e):
            raise ConnectionRefusedError("Error de paquete TCP invalido") from e
        elif "timed out" in str(e):
            raise ConnectionRefusedError("Error de tiempo de espera agotado") from e
        elif "[WinError 10040]" or "unpack" in str(e):
            raise ConnectionRefusedError("Error de tamaño del mensaje") from e
        elif "[WinError 10057]" in str(e) or "[WinError 10035]" in str(e) or "Instance is not connected." in str(e):
            raise ConnectionRefusedError("Dispositivo no conectado") from e
        logging.error(e)
        raise ConnectionRefusedError from e
    
    def disconnect(self):
        try:
            logging.info(f'Desconectando dispositivo {self.ip}...')
            self.conn.disconnect()
        except Exception as e:
            pass

    def __exponential_backoff(self, attempt: int):
        wait_time: int = min(2 ** attempt + random.uniform(0, 3), 30)
        time.sleep(wait_time)

    def __network_operation_wrapper(self, op: Callable, *args):
        """Wrapper to handle network operations with retry logic."""
        for attempt in range(self.max_attempts):
            try:
                # Check connection status before attempting operation
                if not self.is_connected():
                    self.reset_connection()

                # Attempt the network operation
                result = self.__execute_network_operation(op, *args)
                return result
            except ConnectionRefusedError as e:
                # Handle connection errors and retry logic
                if attempt == self.max_attempts - 1:
                    raise NetworkError(f"Maxima cantidad de reintentos para el dispositivo {self.ip}: {str(e)}") from e
                else:
                    error_message = f"Intento fallido {attempt + 1}/{self.max_attempts} del dispositivo {self.ip} para la operacion {op.__name__}: {str(e)}"
                    NetworkError(error_message)
                    self.__exponential_backoff(attempt)
        raise BaseError(0000, "Codigo inalcanzable", level="critical")

    def __execute_network_operation(self, op: Callable, *args):
        """Executes the network operation and handles any specific exceptions."""
        try:
            # Attempt the operation, passing the arguments if any
            if args:
                return op(*args)
            else:
                return op()

        except Exception as e:
            # Handle common network-related exceptions
            self.__handle_connection_error(e)

    def obtain_device_info(self):
        device_info: DeviceInfo = {
            "platform": None,
            "device_name": None,
            "firmware_version": None,
            "serial_number": None,
            "old_firmware": None,
            "attendance_count": None
        }

        try:
            device_info["platform"] = self.__network_operation_wrapper(self.conn.get_platform)
        except Exception as e:
            BaseError(1000, f"{self.ip} - Error obteniendo Platform: {str(e)}")
        try:
            device_info["device_name"] = self.__network_operation_wrapper(self.conn.get_device_name)
        except Exception as e:
            BaseError(1000, f"{self.ip} - Error obteniendo Device name: {str(e)}")
        try:
            device_info["firmware_version"] = self.__network_operation_wrapper(self.conn.get_firmware_version)
        except Exception as e:
            BaseError(1000, f"{self.ip} - Error obteniendo Firmware version: {str(e)}")
        try:
            device_info["serial_number"] = self.__network_operation_wrapper(self.conn.get_serialnumber)
        except Exception as e:
            BaseError(1000, f"{self.ip} - Error obteniendo Serial number: {str(e)}")
        try:
            device_info["old_firmware"] = self.__network_operation_wrapper(self.conn.get_firmware_version)
        except Exception as e:
            BaseError(1000, f"{self.ip} - Error obteniendo Old firmware: {str(e)}")
        try:
            device_info["attendance_count"] = self.__get_attendance_count()
        except Exception as e:
            BaseError(1000, f"{self.ip} - Error obteniendo Attendance count: {str(e)}")

        for key, value in device_info.items():
            logging.info(f"{self.ip} - {key}: {value}")
            if key is "old firmware":
                device_info.pop(key)

        return device_info
                            
    def update_time(self):
        try:
            zktime = self.__network_operation_wrapper(self.conn.get_time)
            logging.debug(f'{self.ip} - Dispositivo: {zktime} - Maquina local: {datetime.today()}')
            logging.info(f'Actualizando hora del dispositivo {self.ip}...')
            newtime = datetime.today()
            self.__network_operation_wrapper(self.conn.set_time, newtime)
            logging.info(f'Validando hora del dispositivo {self.ip}...')
            self.__validate_time(zktime)
        except NetworkError as e:
            raise NetworkError(f"Error al actualizar la hora del dispositivo {self.ip}") from e
        except OutdatedTimeError as e:
            raise OutdatedTimeError(self.ip) from e

        return

    def __validate_time(self, zktime: datetime):
        newtime = datetime.today()
        if (abs(zktime.hour - newtime.hour) > 0 or
        abs(zktime.minute - newtime.minute) >= 5 or
        zktime.day != newtime.day or
        zktime.month != newtime.month or
        zktime.year != newtime.year):
            raise OutdatedTimeError()
        
    def get_attendances(self):
        attendances: list[ZKAttendance] = []
        
        try:
            for attempt in range(self.max_attempts):
                try:
                    logging.info(f'Obteniendo marcaciones del dispositivo {self.ip}...')
                    attendances = self.__network_operation_wrapper(self.conn.get_attendance)
                    logging.debug(f'{self.ip} - Obtencion de marcaciones: {attendances}')
                    records = self.conn.records
                    logging.debug(f'{self.ip} - Longitud de marcaciones del dispositivo: {records}, Longitud de marcaciones obtenidas: {len(attendances)}')
                    if records != len(attendances):
                        error_message = f"Intento fallido {attempt + 1}/{self.max_attempts} del dispositivo {self.ip} para la operacion de get_attendance"
                        raise AttendanceMismatchError(error_message)

                    attendances = self.__network_operation_wrapper(self.conn.get_attendance)
                    new_records = self.conn.records
                    logging.debug(f'{self.ip} - Longitud de marcaciones de la conexion actual: {new_records}, Longitud de marcaciones de la ultima conexion: {records}')
                    if new_records != records:
                        error_message = f"Intento fallido {attempt + 1}/{self.max_attempts} del dispositivo {self.ip} para la operacion de get_attendance"
                        raise AttendanceMismatchError(error_message)
                    break
                except AttendanceMismatchError as e:
                    if attempt == self.max_attempts - 1:
                        raise AttendanceMismatchError(f"Maxima cantidad de reintentos para el dispositivo {self.ip}: {e.__cause__}") from e
                    else:
                        self.__exponential_backoff(attempt)

            parsed_attendances: list[Attendance] = []
            for attendance in attendances:
                timestamp: datetime = attendance.timestamp
                formatted_timestamp: str = timestamp.strftime("%d/%m/%Y %H:%M")
                parsed_attendance: Attendance = Attendance(user_id=attendance.user_id,
                                                    timestamp=formatted_timestamp,
                                                    status=attendance.status)
                parsed_attendances.append(parsed_attendance)
            return parsed_attendances
        except (NetworkError, AttendanceMismatchError) as e:
            raise ObtainAttendancesError(self.ip) from e
        except Exception as e:
            raise BaseError(0000, str(e), level="critical") from e
        
    def clear_attendances(self, clear_attendance: bool = False):
        if clear_attendance:
            logging.info(f'{self.ip} - Limpiando marcaciones...')
            try:
                self.__network_operation_wrapper(self.conn.clear_attendance)
            except NetworkError as e:
                raise NetworkError(f"Error al limpiar las marcaciones del dispositivo {self.ip}") from e
        
    def __get_attendance_count(self):
        try:
            attendances: list[ZKAttendance] = self.__network_operation_wrapper(self.conn.get_attendance)
            logging.info(f'{self.ip} - Obtencion de marcaciones: {attendances}')
            records: int = self.conn.records
            logging.debug(f'{self.ip} - Records: {str(records)}')
            return records
        except NetworkError as e:
            raise NetworkError(f"Error al obtener la cantidad de marcaciones del dispositivo {self.ip}") from e

    def restart_device(self):
        try:
            logging.info(f"Reiniciando dispositivo {self.ip}...")
            self.__network_operation_wrapper(self.conn.restart)
            return
        except NetworkError as e:
            raise NetworkError(f"Error al reiniciar el dispositivo {self.ip}") from e
        
    def update_device_name(self):
        try:
            device_name: str = self.__network_operation_wrapper(self.conn.get_device_name)
        except NetworkError as e:
            NetworkError(f'No se pudo obtener el nombre del dispositivo {self.ip}')
        if not device_name or device_name.isspace():
            try:
                serial_number: str = self.__network_operation_wrapper(self.conn.get_serialnumber)
                device_name = serial_number
                if serial_number == "5235702520030":
                    device_name = "MultiBio700/ID"
            except NetworkError as e:
                NetworkError(f'No se pudo obtener el numero de serie del dispositivo {self.ip}')
        if not device_name or device_name.isspace():
            raise BaseError(3000, f"Error al obtener el nombre del dispositivo {self.ip}: {str(e)}", level="warning")
        else:
            device_name = device_name.replace(" ", "")
        
        try:
            with open('info_devices.txt', 'r') as file:
                lines: list[str] = file.readlines()

            new_lines: list[str] = []
            for line in lines:
                parts: list[str] = line.strip().split(' - ')

                if parts[3] == self.ip:
                    if parts[1] != device_name:
                        logging.info(f'Reemplazando nombre del dispositivo {self.ip}... {parts[1]} por {device_name}')
                        parts[1] = device_name
                    else:
                        return device_name
                new_lines.append(' - '.join(parts) + '\n')

            with threading.Lock():
                with open('info_devices.txt', 'w') as file:
                    file.writelines(new_lines)
        except Exception as e:
            BaseError(3001, f"Error al reemplazar el nombre del dispositivo {self.ip}: {str(e)}", level="warning")
        
        return device_name

    def ping_device(self):
        try:
            config = configparser.ConfigParser()
            config.read(os.path.join(find_root_directory(), 'config.ini'))
            size_ping_test_connection: str = config['Network_config']['size_ping_test_connection']
            zk_helper: ZK_helper = ZK_helper(self.ip, self.port, size_ping_test_connection)
            return zk_helper.test_ping()
        except Exception as e:
            raise NetworkError(self.ip) from e