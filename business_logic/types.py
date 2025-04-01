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

from typing import TypedDict, Optional

class DeviceInfo(TypedDict):
    platform: Optional[str]
    device_name: Optional[str]
    firmware_version: Optional[str]
    serial_number: Optional[str]
    old_firmware: Optional[str]
    attendance_count: Optional[int]

class ConnectionInfo(TypedDict):
    connection_failed: Optional[bool]
    device_info: Optional[DeviceInfo]