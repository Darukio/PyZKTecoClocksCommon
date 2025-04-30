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

class Device:
    def __init__(self, district_name: str = None, 
                 model_name: str = None, point: str = None, 
                 ip: str = None, id: str = None, 
                 communication: str = None, 
                 battery_failing: str = False,
                 active: str = False):
        """
        Initializes a Device object with the specified attributes.

        Args:
            district_name (str, optional): The name of the district where the device is located. Defaults to None.
            model_name (str, optional): The model name of the device. Defaults to None.
            point (str, optional): The point or location identifier of the device. Defaults to None.
            ip (str, optional): The IP address of the device. Defaults to None.
            id (str, optional): The unique identifier of the device. Defaults to None.
            communication (str, optional): The communication protocol used by the device. 
                Must be one of ['TCP', 'UDP', 'RS232', 'RS485']. Raises ValueError if invalid. Defaults to None.
            battery_failing (str, optional): Indicates if the device's battery is failing. 
                Interpreted as True if the value is one of ['true', '1', 'yes', 'verdadero', 'si'] (case-insensitive). Defaults to False.
            active (str, optional): Indicates if the device is active. 
                Interpreted as True if the value is one of ['true', '1', 'yes', 'verdadero', 'si'] (case-insensitive). Defaults to False.

        Raises:
            ValueError: If the communication protocol is not one of ['TCP', 'UDP', 'RS232', 'RS485'].
        """
        self.district_name: str = district_name
        self.model_name: str = model_name
        self.point: str = point
        self.ip: str = ip
        self.id: int = int(id) if id is not None else None
        if communication not in ['TCP', 'UDP', 'RS232', 'RS485']:
            raise ValueError('Tipo de protocolo de comunicacion no valido "{}" en el dispositivo {}'.format(communication, ip))
        self.communication: str = communication
        self.battery_failing: bool = battery_failing.lower() in ['true', '1', 'yes', 'verdadero', 'si']
        self.active: bool = active.lower() in ['true', '1', 'yes', 'verdadero', 'si']

    def __str__(self):
        """
        Returns a string representation of the Device object.

        The string includes the district name, model name, point, IP address, 
        device ID, communication status, battery failing status, and active status.

        Returns:
            (str): A formatted string containing the device's details.
        """
        return f'Device: {self.district_name} - {self.model_name} - {self.point} - {self.ip} - {self.id} - {self.communication} - {self.battery_failing} - {self.active}'
    
    def __repr__(self):
        """
        Returns a string representation of the Device object.

        The string includes the district name, model name, point, IP address, 
        device ID, communication status, battery status, and active status.

        Returns:
            (str): A formatted string representing the device.
        """
        return f'Device: {self.district_name} - {self.model_name} - {self.point} - {self.ip} - {self.id} - {self.communication} - {self.battery_failing} - {self.active}'