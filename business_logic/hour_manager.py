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

from ..utils.file_manager import find_root_directory

config = configparser.ConfigParser()
from .shared_state import SharedState
from ..utils.errors import BatteryFailingError, ConnectionFailedError, NetworkError, OutdatedTimeError
from .device_manager import get_device_info, network_operation_with_retry

def update_devices_time(selected_devices=None, from_service=False, emit_progress=None):
    device_info = []
    try:
        # Get all devices in a formatted list
        device_info = get_device_info()
    except Exception as e:
        logging.error(e)

    if device_info:
        gt = []
        active_devices = []
        config.read(os.path.join(find_root_directory(), 'config.ini'))
        coroutines_pool_max_size = int(config['Cpu_config']['coroutines_pool_max_size'])

        # Create a pool of green threads
        state = SharedState()
        pool = eventlet.GreenPool(coroutines_pool_max_size)
        
        if selected_devices:
            selected_ips = {device['ip'] for device in selected_devices}

            active_devices = [device for device in device_info if device['ip'] in selected_ips]
        elif from_service:
            active_devices = device_info

        # Set the total number of devices in the shared state
        state.set_total_devices(len(active_devices))
        
        for active_device in active_devices:
            try:
                gt.append(pool.spawn(update_device_time_single, active_device, from_service, emit_progress, state))
            except Exception as e:
                pass
            
        device_with_battery_failing = []
        device_error = {}
        for active_device, g in zip(active_devices, gt):
            logging.debug(f'Processing {active_device}')
            device_error[active_device['ip']] = { "connection failed": False, "battery failing": False }
            try:
                g.wait()
            except BatteryFailingError as e:
                logging.error(f"Error al actualizar la hora del dispositivo {e.ip}: {e} - {e.__cause__}")
                device_with_battery_failing.append(e.ip)
                device_error[active_device['ip']]["battery failing"] = True
            except NetworkError as e:
                device_error[active_device['ip']]["connection failed"] = True
            except Exception as e:
                logging.error(e, e.__cause__)

        logging.debug("Cantidad de dispositivos con fallos de pila: "+str(len(device_with_battery_failing)))
        if len(device_with_battery_failing) > 0:
            logging.debug("Dispositivos con fallos de pila: "+str(device_with_battery_failing))
            for ip in device_with_battery_failing:
                try:
                    update_battery_status(ip)
                except Exception as e:
                    logging.error(f"Error al actualizar el estado de bateria del dispositivo {e.ip}: {e}")

        logging.debug('TERMINE HORA!')
        return device_error

def update_device_time_single(info, from_service=False, emit_progress=None, state=None):
    try:
        network_operation_with_retry("update_time", ip=info['ip'], port=4370, communication=info['communication'], from_service=from_service)
    except ConnectionFailedError as e:
        raise NetworkError(info['model_name'], info['point'], info['ip'])
    except OutdatedTimeError as e:
        raise BatteryFailingError(info["model_name"], info["point"], info["ip"])
    except Exception as e:
        raise e
    finally:
        try:
            if state:
                # Update the number of processed devices and progress
                processed_devices = state.increment_processed_devices()
                if emit_progress:
                    progress = state.calculate_progress()
                    emit_progress(percent_progress=progress, device_progress=info["ip"], processed_devices=processed_devices, total_devices=state.get_total_devices())
                    logging.debug(f"processed_devices: {processed_devices}/{state.get_total_devices()}, progress: {progress}%")
        except Exception as e:
            logging.error(e)

    return

def update_battery_status(p_ip):
    with open('info_devices.txt', 'r') as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        parts = line.strip().split(' - ')
        ip = parts[3]
        if ip == p_ip:
            parts[6] = "False"
        new_lines.append(' - '.join(parts) + '\n')

    with open('info_devices.txt', 'w') as file:
        file.writelines(new_lines)

    logging.debug("Estado de bateria actualizado correctamente.")