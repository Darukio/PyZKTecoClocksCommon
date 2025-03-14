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
import os
from datetime import datetime
import threading
import eventlet
from ..connection.zk.base import ZK, ZK_helper
import configparser
config = configparser.ConfigParser()
from ..utils.errors import OutdatedTimeError
from ..utils.file_manager import find_root_directory

class ConnectionManager():
    conn = None
    from_service = False

    def __init__(self, ip, port, communication, from_service=False):
        self.force_udp = True if communication == 'UDP' else False
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        timeout=int(config['Network_config']['timeout'])
        if timeout is None:
            timeout = 15
        self.zk = ZK(ip, port, timeout=timeout, ommit_ping=True, force_udp=self.force_udp)
        self.ip = ip
        self.port = port
        self.communication = communication
        self.from_service = from_service

    def __tcp_operation(self, op, result):
        try:
            if hasattr(self.zk, op):
                func = getattr(self.zk, op)
                result['value'] = func()
            else:
                raise AttributeError(f"La funcion '{op}' no existe en el objeto")
        except Exception as e:
            result['exception'] = e

    def reset_connection(self):
        self.conn = None
    
    def is_connected(self):
        return self.conn is not None

    def connect(self):
        try:
            logging.info(f'Conectando al dispositivo {self.ip}...')
            if self.force_udp:
                self.conn = self.zk.connect()
            else:
                result = {}
                tcp_thread = threading.Thread(target=self.__tcp_operation, args=("connect", result))
                tcp_thread.start()
                tcp_thread.join()
                if 'exception' in result:
                    raise result['exception']
                self.conn = result.get('value')
            logging.info(f'Conectado exitosamente al dispositivo {self.ip}')
            logging.debug(f'{self.ip}: {self.conn}')
            try:
                logging.info(f'{self.ip} - Platform: {self.conn.get_platform()}')
                logging.info(f'{self.ip} - Device name: {self.conn.get_device_name()}')
                logging.info(f'{self.ip} - Firmware version: {self.conn.get_firmware_version()}')
                logging.info(f'{self.ip} - Old firmware: {self.conn.get_compat_old_firmware()}')
            except Exception as e:
                pass
        except Exception as e:
            if "TCP packet invalid" in str(e):
                raise ConnectionRefusedError("Error de paquete TCP inválido") from e
            elif "timed out" in str(e):
                raise ConnectionRefusedError("Error de tiempo de espera agotado") from e
            elif "[WinError 10040]" in str(e):
                raise ConnectionRefusedError("Error de tamaño de mensaje") from e
            elif "[WinError 10057]" in str(e):
                raise ConnectionRefusedError("Error de socket no conectado") from e
            raise ConnectionRefusedError from e
        eventlet.sleep(0)
        return self.conn
        
    def end_connection(self):
        try:
            """ ADD THREADING """
            logging.info(f'Desconectando dispositivo {self.ip}...')
            self.conn.disconnect()
        except Exception as e:
            logging.warning(e)
            raise ConnectionRefusedError from e
        eventlet.sleep(0)
        
    def update_time(self):
        try:
            if self.force_udp:
                zktime = self.conn.get_time()
            else:
                result = {}
                tcp_thread = threading.Thread(target=self.__tcp_operation, args=("get_time", result))
                tcp_thread.start()
                tcp_thread.join()
                if 'exception' in result:
                    raise result['exception']
                zktime = result.get('value')
            logging.debug(f'{self.ip} - Dispositivo: {zktime} - Maquina local: {datetime.today()}')
            eventlet.sleep(0)
        except Exception as e:
            raise ConnectionRefusedError from e

        try:
            logging.debug(f'Actualizando hora del dispositivo {self.ip}...')
            newtime = datetime.today()
            """ ADD THREADING """
            self.conn.set_time(newtime)
            eventlet.sleep(0)
        except Exception as e:
            raise ConnectionRefusedError from e

        try:
            logging.debug(f'Validando hora del dispositivo {self.ip}...')
            self.validate_time(zktime)
            eventlet.sleep(0)
        except OutdatedTimeError as e:
            raise OutdatedTimeError(self.ip) from e

        return

    def validate_time(self, zktime):
        newtime = datetime.today()
        if (abs(zktime.hour - newtime.hour) > 0 or
        abs(zktime.minute - newtime.minute) >= 5 or
        zktime.day != newtime.day or
        zktime.month != newtime.month or
        zktime.year != newtime.year):
            raise OutdatedTimeError()
        
    def get_attendances(self):
        attendances = []

        try:
            logging.info(f'Obteniendo marcaciones del dispositivo {self.ip}...')
            import time
            start_time = time.time()
            if self.force_udp:
                attendances = self.conn.get_attendance()
            else:
                result = {}
                tcp_thread = threading.Thread(target=self.__tcp_operation, args=("get_attendance", result))
                tcp_thread.start()
                tcp_thread.join()
                if 'exception' in result:
                    raise result['exception']
                attendances = result.get('value')
            logging.debug(f'{self.ip} - Obtencion de marcaciones: {attendances}')
            end_time = time.time()
            logging.debug(f'{self.ip} - Operacion de lectura de marcaciones - Tiempo de operacion: {end_time - start_time:.2f} s')
            records = self.conn.records
            logging.debug(f'{self.ip} - Longitud de marcaciones del dispositivo: {records}, Longitud de marcaciones obtenidas: {len(attendances)}')
            if records != len(attendances):
                raise Exception('Los registros de marcaciones no coinciden con la cantidad de marcaciones obtenidas')
            else:
                if self.force_udp:
                    self.conn.get_attendance()
                else:
                    result = {}
                    tcp_thread = threading.Thread(target=self.__tcp_operation, args=("get_attendance", result))
                    tcp_thread.start()
                    tcp_thread.join()
                    if 'exception' in result:
                        raise result['exception']
                new_records = self.conn.records
                logging.debug(f'{self.ip} - Longitud de marcaciones de la conexion actual: {new_records}, Longitud de marcaciones de la ultima conexion: {records}')
                if new_records != records:
                    raise Exception('Los registros de marcaciones no coinciden con la cantidad de marcaciones obtenidas')

                start_time_2 = time.time()
                config.read(os.path.join(find_root_directory(), 'config.ini'))
                # Determine the appropriate configuration based on the value of from_service
                config_key = 'clear_attendance_service' if self.from_service else 'clear_attendance'
                logging.debug(f'clear_attendance: {config['Device_config'][config_key]}')

                # Evaluate the selected configuration
                if eval(config['Device_config'][config_key]):
                    logging.debug(f'{self.ip} - Limpiando marcaciones...')
                    try:
                        end_time_2 = time.time()
                        logging.debug(f'{self.ip} - Operacion de limpieza de marcaciones - Tiempo de operacion: {end_time_2 - start_time_2:.2f} s')
                        if self.force_udp:
                            attendances = self.conn.clear_attendance()
                        else:
                            result = {}
                            tcp_thread = threading.Thread(target=self.__tcp_operation, args=("clear_attendance", result))
                            tcp_thread.start()
                            tcp_thread.join()
                            if 'exception' in result:
                                raise result['exception']
                        eventlet.sleep(0)
                    except Exception as e:
                        logging.error(f'{self.ip} - No se pudieron limpiar las marcaciones')
                        raise e

                return attendances
        except Exception as e:
            if "TCP packet invalid" in str(e):
                raise ConnectionRefusedError("Error de paquete TCP invalido") from e
            elif "timed out" in str(e):
                raise ConnectionRefusedError("Error de tiempo de espera agotado") from e
            elif "[WinError 10040]" in str(e):
                raise ConnectionRefusedError("Error de tamaño de mensaje") from e
            elif "[WinError 10057]" in str(e):
                raise ConnectionRefusedError("Error de socket no conectado") from e
            raise ConnectionRefusedError from e

    def get_attendance_count(self):
        try:
            if self.force_udp:
                attendances = self.conn.get_attendance()
            else:
                result = {}
                tcp_thread = threading.Thread(target=self.__tcp_operation, args=("get_attendance", result))
                tcp_thread.start()
                tcp_thread.join()
                if 'exception' in result:
                    raise result['exception']
                attendances = result.get('value')
            logging.debug(attendances)
            records = self.conn.records
            logging.debug(records)
            eventlet.sleep(0)
            return records
        except Exception as e:
            raise ConnectionRefusedError from e

    def restart_device(self):
        try:
            logging.info(f"Reiniciando dispositivo {self.ip}...")
            if self.force_udp:
                self.conn.restart()
            else:
                result = {}
                tcp_thread = threading.Thread(target=self.__tcp_operation, args=("restart", result))
                tcp_thread.start()
                tcp_thread.join()
                if 'exception' in result:
                    raise result['exception']
            return
        except Exception as e:
            if "TCP packet invalid" in str(e):
                raise ConnectionRefusedError("Error de paquete TCP inválido") from e
            elif "timed out" in str(e):
                raise ConnectionRefusedError("Error de tiempo de espera agotado") from e
            elif "[WinError 10040]" in str(e):
                raise ConnectionRefusedError("Error de tamaño de mensaje") from e
            elif "[WinError 10057]" in str(e):
                raise ConnectionRefusedError("Error de socket no conectado") from e
            raise ConnectionRefusedError from e
        
    def update_device_name(self):
        try:
            """ ADD THREADING """
            device_name = self.conn.get_device_name()
            device_name = device_name.replace(" ", "")
            if not device_name:
                try:
                    serial_number = self.conn.get_serialnumber()
                    device_name = serial_number
                    if serial_number == "5235702520030":
                        device_name = "MultiBio700/ID"
                except Exception as e:
                    logging.error(f"Error al obtener el nombre del dispositivo {self.ip}: {e}")
                    device_name = "NoName"
            try:
                with open('info_devices.txt', 'r') as file:
                    lines = file.readlines()

                new_lines = []
                for line in lines:
                    parts = line.strip().split(' - ')

                    if parts[3] == self.ip and parts[1] != device_name:
                        logging.debug(f'Reemplazando nombre del dispositivo {self.ip}... {parts[1]} por {device_name}')
                        parts[1] = device_name
                    new_lines.append(' - '.join(parts) + '\n')

                with open('info_devices.txt', 'w') as file:
                    file.writelines(new_lines)
            except Exception as e:
                logging.error(f"Error al reemplazar el nombre del dispositivo: {e}")
                raise e
            return device_name
        except Exception as e:
            pass

def ping_device(ip, port):
    try:
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        size_ping_test_connection = config['Network_config']['size_ping_test_connection']
        zk_helper = ZK_helper(ip, port, size_ping_test_connection)
        return zk_helper.test_ping()
    except Exception as e:
        raise ConnectionRefusedError from e