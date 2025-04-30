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

import re
import logging
import os
from datetime import datetime
import time
import random
from typing import Callable

import eventlet
from .types import DeviceInfo
from .models.attendance import Attendance
from ..connection.zk.base import ZK, ZK_helper
import configparser
from ..utils.errors import AttendanceMismatchError, BaseError, NetworkError, ObtainAttendancesError, OutdatedTimeError
from ..utils.file_manager import find_root_directory

class ConnectionManager():
    conn = None

    def __init__(self, ip: str, port: int, communication: str):
        """
        Initializes the ConnectionManager instance.

        Args:
            ip (str): The IP address of the device to connect to.
            port (int): The port number to use for the connection.
            communication (str): The communication protocol to use ('UDP' or other).

        Attributes:
            force_udp (bool): Indicates whether to force UDP communication.
            config (ConfigParser): Configuration parser for reading settings from 'config.ini'.
            timeout (int): Timeout value for the connection, read from the configuration file.
            zk (ZK): Instance of the ZK class for managing the connection.
            ip (str): The IP address of the device.
            port (str): The port number of the device.
            max_attempts (int): Maximum number of retry attempts for the connection, read from the configuration file.
            lock (Semaphore): Semaphore lock to manage concurrent access.
        """
        self.force_udp: bool = True if communication == 'UDP' else False
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(find_root_directory(), 'config.ini'))
        self.timeout = int(self.config['Network_config']['timeout'])
        self.zk: ZK = ZK(ip, port, timeout=self.timeout, ommit_ping=True, force_udp=self.force_udp)
        self.ip: str = ip
        self.port: str = port
        self.max_attempts = int(self.config['Network_config']['retry_connection'])
        self.lock = eventlet.semaphore.Semaphore()

    def reset_connection(self):
        """
        Resets the current connection by disconnecting and reinitializing it.

        This method first disconnects the existing connection and sets the 
        connection object to None. It then attempts to establish a new connection. 
        If the connection attempt fails due to a ConnectionRefusedError, the 
        exception is raised.

        Raises:
            ConnectionRefusedError: If the connection attempt is refused.
        """
        self.disconnect()
        self.conn = None
        try:
            self.connect()
        except ConnectionRefusedError as e:
            raise e
    
    def is_connected(self):
        """
        Check if the connection is established.

        Returns:
            (bool): True if the connection object (`self.conn`) is not None 
                  and the connection is active (`self.conn.is_connect`), 
                  otherwise False.
        """
        return self.conn is not None and self.conn.is_connect

    def connect(self):
        """
        Establishes a connection to the device using the provided IP address.

        This method attempts to connect to the device by executing a network operation.
        If the connection is successful, a log message is recorded indicating the success.
        If the connection is refused, a `ConnectionRefusedError` is raised.

        Raises:
            ConnectionRefusedError: If the connection to the device is refused.
        """
        try:
            logging.info(f'Conectando al dispositivo {self.ip}...')
            self.conn = self.__execute_network_operation(self.zk.connect)
            logging.info(f'Conectado exitosamente al dispositivo {self.ip}')
        except ConnectionRefusedError as e:
            raise e
    
    def connect_with_retry(self):
        """
        Attempts to establish a connection with retries using exponential backoff.
        This method tries to connect to a device multiple times, as specified by
        `self.max_attempts`. If the connection fails due to a `ConnectionRefusedError`,
        it retries the connection after waiting for a period determined by an
        exponential backoff strategy. If all attempts fail, a `NetworkError` is raised.

        Raises:
            NetworkError: If the maximum number of connection attempts is reached
                          without success.
            BaseError: If the code reaches an unreachable state (should not occur).

        Returns:
            (object): The established connection object (`self.conn`) if successful.
        """
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
        """
        Handles connection errors by analyzing the exception message and raising a 
        more specific ConnectionRefusedError with a descriptive message.

        Args:
            e (Exception): The exception object containing details about the connection error.

        Raises:
            ConnectionRefusedError: Raised with a specific error message based on the 
                                content of the exception message. Possible reasons include:
                                
                - "TCP packet invalid": Indicates an invalid TCP packet.
                - "timed out": Indicates a timeout error.
                - "[WinError 10040]" or "unpack": Indicates an error in message reception or sending.
                - "[WinError 10057]", "[WinError 10035]", or "Instance is not connected.": 
                  Indicates that the device is not connected.
            ConnectionRefusedError: A generic connection error if no specific case matches.
        """
        if "TCP packet invalid" in str(e):
            raise ConnectionRefusedError("Error de paquete TCP invalido") from e
        elif "timed out" in str(e):
            raise ConnectionRefusedError("Error de tiempo de espera agotado") from e
        elif "[WinError 10040]" in str(e) or "unpack" in str(e):
            raise ConnectionRefusedError("Error de recepcion/envio del mensaje") from e
        elif "[WinError 10057]" in str(e) or "[WinError 10035]" in str(e) or "Instance is not connected." in str(e):
            raise ConnectionRefusedError("Dispositivo no conectado") from e
        logging.error(e)
        raise ConnectionRefusedError from e
    
    def disconnect(self):
        """
        Disconnects the device from the current connection.

        This method attempts to disconnect the device associated with the given
        IP address. If an exception occurs during the disconnection process,
        it is silently ignored.

        Logs:
            Logs an informational message indicating the disconnection attempt.

        Exceptions:
            Any exceptions raised during the disconnection process are caught
            and ignored.
        """
        try:
            logging.info(f'Desconectando dispositivo {self.ip}...')
            self.conn.disconnect()
        except Exception as e:
            pass

    def __exponential_backoff(self, attempt: int):
        """
        Implements an exponential backoff strategy for retrying operations.

        Args:
            attempt (int): The current retry attempt number (starting from 0).

        Behavior:
            - Calculates a wait time using an exponential backoff formula: 2^attempt + random jitter.
            - The random jitter is a uniform value between 0 and 3 to introduce randomness.
            - Caps the maximum wait time at 30 seconds.
            - Pauses execution for the calculated wait time.

        Note:
            This method is intended to be used internally for managing retry delays.
        """
        wait_time: int = min(2 ** attempt + random.uniform(0, 3), 30)
        time.sleep(wait_time)

    def __network_operation_wrapper(self, op: Callable, *args):
        """
        A wrapper method to handle network operations with retry logic.

        This method attempts to execute a given network operation multiple times, 
        handling connection errors and retrying with exponential backoff if necessary.

        Args:
            op (Callable): The network operation to be executed.
            *args: Additional arguments to be passed to the network operation.

        Returns:
            (Any): The result of the network operation if successful.

        Raises:
            NetworkError: If the maximum number of retry attempts is reached or 
                          if a connection error occurs.
            BaseError: If an unreachable code path is executed (critical error).
        """
        for attempt in range(self.max_attempts):
            try:
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

    def __execute_network_operation(self, op: callable, *args):
        """
        Executes a network operation with a specified timeout and handles potential errors.
        This method wraps the execution of a callable operation (`op`) with a timeout mechanism
        using `eventlet.timeout.Timeout`. If the operation exceeds the allowed time, a 
        `ConnectionRefusedError` is raised. Any other exceptions are handled by the 
        `__handle_connection_error` method.

        Args:
            op (callable): The operation to execute. This should be a callable object.
            *args: Optional arguments to pass to the callable operation.

        Raises:
            ConnectionRefusedError: If the operation exceeds the maximum allowed time.
            Exception: Any other exceptions raised by the operation are handled internally.

        Logs:
            Logs the execution time of the operation in seconds.

        Note:
            The timeout is calculated as the configured `self.timeout` value plus an additional
            5 seconds.
        """
        from eventlet.timeout import Timeout
        timeout = self.timeout + 5
        start_time = time.time()

        try:
            with Timeout(timeout):
                result = op(*args) if args else op()
                end_time = time.time()
                return result

        except Timeout:
            end_time = time.time()
            raise ConnectionRefusedError(
                f"La operacion '{op.__name__}' supero el tiempo maximo de {timeout} segundos"
            )

        except Exception as e:
            end_time = time.time()
            self.__handle_connection_error(e)

        finally:
            elapsed_time = end_time - start_time
            logging.debug(
                f"{self.ip} - Tiempo de ejecucion de la operacion '{op.__name__}': {elapsed_time:.2f} segundos"
            )

    def obtain_device_info(self):
        """
        Obtains device information by performing network operations and retrieving
        various attributes of the connected device.

        Returns:
            (dict): A dictionary containing the following device information:

                - platform (str or None): The platform of the device.
                - device_name (str or None): The name of the device.
                - firmware_version (str or None): The firmware version of the device.
                - serial_number (str or None): The serial number of the device.
                - old_firmware (str or None): The old firmware version of the device.
                - attendance_count (int or None): The attendance count stored in the device.

        Logs:
            Logs each retrieved device information attribute along with the device's IP address.
            If an error occurs during retrieval, logs an error message with the IP address
            and the specific attribute that failed.

        Raises:
            BaseError: If any network operation fails, a BaseError is raised with an error code
            and a descriptive message.

        Note:
            The "old_firmware" key is removed from the returned dictionary before it is returned.
        """
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
            if key == "old firmware":
                device_info.pop(key)

        return device_info
                            
    def update_time(self):
        """
        Updates the time on the connected device to match the local machine's time.
        This method retrieves the current time from the device, logs the operation,
        and then updates the device's time to match the local machine's time. After
        updating, it validates the time to ensure synchronization.

        Raises:
            NetworkError: If there is a network-related issue during the operation.
            OutdatedTimeError: If the device's time is outdated and cannot be updated.
            
        Returns:
            None
        """
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
        """
        Validates the provided datetime object against the current system time.

        This method checks if the provided `zktime` is outdated by comparing it
        to the current system time (`datetime.today()`). The validation fails if:
        
        - The hour difference is greater than 0.
        - The minute difference is 5 or more.
        - The day, month, or year do not match.

        If any of these conditions are met, an `OutdatedTimeError` is raised.

        Args:
            zktime (datetime): The datetime object to validate.

        Raises:
            OutdatedTimeError: If the provided `zktime` is considered outdated.
        """
        newtime = datetime.today()
        if (abs(zktime.hour - newtime.hour) > 0 or
        abs(zktime.minute - newtime.minute) >= 5 or
        zktime.day != newtime.day or
        zktime.month != newtime.month or
        zktime.year != newtime.year):
            raise OutdatedTimeError()
        
    def get_attendances(self):
        """
        Retrieves attendance records from a device, ensuring data consistency and handling retries.
        This method attempts to fetch attendance records from a connected device. It performs
        multiple retries in case of mismatched data or network issues, using an exponential backoff
        strategy between attempts. The retrieved records are parsed into `Attendance` objects before
        being returned.

        Returns:
            (list[Attendance]): A list of parsed attendance records.

        Raises:
            AttendanceMismatchError: If the maximum number of retry attempts is reached due to
                                     mismatched attendance data.
            ObtainAttendancesError: If there is a network issue or an attendance mismatch error occurs.
            BaseError: For any other unexpected errors, with a critical error level.
        """
        attendances: list = []
        
        try:
            for attempt in range(self.max_attempts):
                try:
                    logging.info(f'Obteniendo marcaciones del dispositivo {self.ip}...')
                    attendances = self.__network_operation_wrapper(self.conn.get_attendance)
                    #logging.debug(f'{self.ip} - Obtencion de marcaciones: {attendances}')
                    records = self.conn.records
                    logging.debug(f'{self.ip} - Longitud de marcaciones del dispositivo: {records}, Longitud de marcaciones obtenidas: {len(attendances)}')
                    if records != len(attendances):
                        error_message = f"Intento fallido {attempt + 1}/{self.max_attempts} del dispositivo {self.ip} para la operacion de get_attendance"
                        raise AttendanceMismatchError(error_message)
                                    
                    """
                    attendances = self.__network_operation_wrapper(self.conn.get_attendance)
                    new_records = self.conn.records
                    logging.debug(f'{self.ip} - Longitud de marcaciones de la conexion actual: {new_records}, Longitud de marcaciones de la ultima conexion: {records}')
                    if new_records != records:
                        error_message = f"Intento fallido {attempt + 1}/{self.max_attempts} del dispositivo {self.ip} para la operacion de get_attendance"
                        raise AttendanceMismatchError(error_message)
                    """
                    break
                except AttendanceMismatchError as e:
                    if attempt == self.max_attempts - 1:
                        raise AttendanceMismatchError(f"Maxima cantidad de reintentos para el dispositivo {self.ip}") from e
                    else:
                        self.__exponential_backoff(attempt)

            parsed_attendances: list[Attendance] = []
            for attendance in attendances:
                parsed_attendance: Attendance = Attendance(user_id=attendance.user_id,
                                                    timestamp=attendance.timestamp,
                                                    status=attendance.status)
                parsed_attendances.append(parsed_attendance)
            return parsed_attendances
        except (NetworkError, AttendanceMismatchError) as e:
            raise ObtainAttendancesError(self.ip) from e
        except Exception as e:
            raise BaseError(0000, str(e), level="critical") from e
        
    def clear_attendances(self, clear_attendance: bool = False):
        """
        Clears attendance records from the device if the `clear_attendance` flag is set to True.

        Args:
            clear_attendance (bool): A flag indicating whether to clear attendance records. 
                                     If True, the attendance records will be cleared.

        Raises:
            NetworkError: If there is an issue during the network operation to clear attendance records.
        """
        if clear_attendance:
            logging.info(f'{self.ip} - Limpiando marcaciones...')
            try:
                self.__network_operation_wrapper(self.conn.clear_attendance)
            except NetworkError as e:
                raise NetworkError(f"Error al limpiar las marcaciones del dispositivo {self.ip}") from e
        
    def __get_attendance_count(self):
        """
        Retrieves the count of attendance records from the connected device.

        This method uses a network operation wrapper to fetch attendance data
        and then retrieves the total number of records from the device connection.

        Returns:
            (int): The total number of attendance records.

        Raises:
            NetworkError: If there is an issue retrieving the attendance count
                          from the device.
        """
        try:
            self.__network_operation_wrapper(self.conn.get_attendance)
            #logging.info(f'{self.ip} - Obtencion de marcaciones: {attendances}')
            records: int = self.conn.records
            logging.debug(f'{self.ip} - Records: {str(records)}')
            return records
        except NetworkError as e:
            raise NetworkError(f"Error al obtener la cantidad de marcaciones del dispositivo {self.ip}") from e

    def restart_device(self):
        """
        Restarts the device associated with the current connection.

        This method attempts to restart the device by invoking the `restart` 
        method on the connection object. If a network-related error occurs 
        during the operation, it raises a `NetworkError` with additional 
        context about the failure.

        Raises:
            NetworkError: If there is an issue restarting the device due to 
                          network-related problems.
        """
        try:
            logging.info(f"Reiniciando dispositivo {self.ip}...")
            self.__network_operation_wrapper(self.conn.restart)
            return
        except NetworkError as e:
            raise NetworkError(f"Error al reiniciar el dispositivo {self.ip}") from e
        
    def update_device_name(self):
        """
        Updates the device name associated with the current connection.
        This method attempts to retrieve the device name from the connected device.
        If the device name cannot be retrieved or is invalid, it falls back to using
        the device's serial number. If the serial number matches a specific value,
        it assigns a predefined name. The updated device name is then stored in a
        shared file (`info_devices.txt`), replacing the old name if necessary.

        Raises:
            BaseError: If the device name or serial number cannot be retrieved, or
                       if there is an error updating the shared file.

        Returns:
            (str): The updated device name.

        Exceptions:
            NetworkError: Raised internally when network operations fail.
            BaseError: Raised when there are issues with retrieving or updating
              the device name.

        Notes:
            - The method ensures that the device name contains only alphanumeric
              characters, spaces, slashes, or hyphens.
            - The method uses a lock to ensure thread-safe access to the shared file.

        Logging:
            - Logs a message when replacing the device name in the shared file.
        """
        try:
            device_name: str = self.__network_operation_wrapper(self.conn.get_device_name)
            device_name = re.sub(r'[^A-Za-z0-9\s/\-]', '', device_name)
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
            with open(os.path.join(find_root_directory(), 'info_devices.txt'), 'r') as file:
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

            with self.lock:
                with open(os.path.join(find_root_directory(), 'info_devices.txt'), 'w') as file:
                    file.writelines(new_lines)
        except Exception as e:
            BaseError(3001, f"Error al reemplazar el nombre del dispositivo {self.ip}: {str(e)}", level="warning")
        
        return device_name

    def ping_device(self):
        """
        Attempts to ping the device to test network connectivity.

        This method reads the network configuration from a 'config.ini' file, 
        initializes a ZK_helper instance with the device's IP, port, and 
        the size of the ping test connection, and performs a ping test.

        Returns:
            (bool): True if the ping test is successful, False otherwise.

        Raises:
            NetworkError: If there is an issue with the network connectivity 
                          or if any exception occurs during the ping test.
        """
        try:
            config = configparser.ConfigParser()
            config.read(os.path.join(find_root_directory(), 'config.ini'))
            size_ping_test_connection: str = config['Network_config']['size_ping_test_connection']
            zk_helper: ZK_helper = ZK_helper(self.ip, self.port, size_ping_test_connection)
            return zk_helper.test_ping()
        except Exception as e:
            raise NetworkError(self.ip) from e