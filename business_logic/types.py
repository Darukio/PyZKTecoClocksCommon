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

from typing import TypedDict, Optional

class DeviceInfo(TypedDict):
    """
    DeviceInfo is a TypedDict that represents information about a device.

    Attributes:
        platform (Optional[str]): The platform or operating system of the device.
        device_name (Optional[str]): The name of the device.
        firmware_version (Optional[str]): The current firmware version of the device.
        serial_number (Optional[str]): The serial number of the device.
        old_firmware (Optional[str]): The previous firmware version of the device, if applicable.
        attendance_count (Optional[int]): The number of attendance records stored on the device.
    """
    platform: Optional[str]
    device_name: Optional[str]
    firmware_version: Optional[str]
    serial_number: Optional[str]
    old_firmware: Optional[str]
    attendance_count: Optional[int]

class ConnectionInfo(TypedDict):
    """
    ConnectionInfo is a TypedDict that represents the connection details for a device.

    Attributes:
        connection_failed (Optional[bool]): Indicates whether the connection attempt failed. 
            True if the connection failed, False otherwise, or None if the status is unknown.
        device_info (Optional[DeviceInfo]): Contains information about the connected device, 
            or None if no device information is available.
    """
    connection_failed: Optional[bool]
    device_info: Optional[DeviceInfo]