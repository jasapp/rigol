"""
Rigol DP832A Control Library

Simple interface for controlling the Rigol DP832A power supply via USB TMC.
"""

import os
import time
from dataclasses import dataclass
from typing import Optional


DEFAULT_DEVICE = '/dev/usbtmc2'


@dataclass
class ChannelStatus:
    channel: int
    output: bool
    voltage_set: float
    current_set: float
    voltage: float
    current: float
    power: float


class RigolDP832A:
    """Control interface for Rigol DP832A power supply."""

    def __init__(self, device: str = DEFAULT_DEVICE):
        self.device = device
        self._verify_connection()

    def _verify_connection(self):
        """Verify we can talk to the device."""
        idn = self.query('*IDN?')
        if 'RIGOL' not in idn and 'DP8' not in idn:
            raise ConnectionError(f"Unexpected device response: {idn}")
        self.idn = idn

    def command(self, cmd: str) -> None:
        """Send a command (no response expected)."""
        fd = os.open(self.device, os.O_RDWR)
        try:
            os.write(fd, (cmd + '\n').encode())
            time.sleep(0.05)
        finally:
            os.close(fd)

    def query(self, cmd: str) -> str:
        """Send a command and read response."""
        fd = os.open(self.device, os.O_RDWR)
        try:
            os.write(fd, (cmd + '\n').encode())
            time.sleep(0.1)
            response = os.read(fd, 4096).decode('utf-8').strip()
            return response
        finally:
            os.close(fd)

    # Output control
    def output_on(self, channel: int) -> None:
        """Turn channel output on."""
        self.command(f':OUTP CH{channel},ON')

    def output_off(self, channel: int) -> None:
        """Turn channel output off."""
        self.command(f':OUTP CH{channel},OFF')

    def get_output(self, channel: int) -> bool:
        """Get output state."""
        return self.query(f':OUTP? CH{channel}') == 'ON'

    # Voltage control
    def set_voltage(self, channel: int, voltage: float) -> None:
        """Set channel voltage."""
        self.command(f':SOUR{channel}:VOLT {voltage}')

    def get_voltage_setpoint(self, channel: int) -> float:
        """Get voltage setpoint."""
        return float(self.query(f':SOUR{channel}:VOLT?'))

    def measure_voltage(self, channel: int) -> float:
        """Measure actual voltage."""
        return float(self.query(f':MEAS:VOLT? CH{channel}'))

    # Current control
    def set_current(self, channel: int, current: float) -> None:
        """Set channel current limit."""
        self.command(f':SOUR{channel}:CURR {current}')

    def get_current_setpoint(self, channel: int) -> float:
        """Get current setpoint."""
        return float(self.query(f':SOUR{channel}:CURR?'))

    def measure_current(self, channel: int) -> float:
        """Measure actual current."""
        return float(self.query(f':MEAS:CURR? CH{channel}'))

    # Power measurement
    def measure_power(self, channel: int) -> float:
        """Measure actual power."""
        return float(self.query(f':MEAS:POWE? CH{channel}'))

    # OVP/OCP protection
    def set_ovp(self, channel: int, voltage: float) -> None:
        """Set over-voltage protection."""
        self.command(f':OUTP:OVP:VAL CH{channel},{voltage}')
        self.command(f':OUTP:OVP CH{channel},ON')

    def set_ocp(self, channel: int, current: float) -> None:
        """Set over-current protection."""
        self.command(f':OUTP:OCP:VAL CH{channel},{current}')
        self.command(f':OUTP:OCP CH{channel},ON')

    # Convenience methods
    def status(self, channel: int) -> ChannelStatus:
        """Get full channel status."""
        return ChannelStatus(
            channel=channel,
            output=self.get_output(channel),
            voltage_set=self.get_voltage_setpoint(channel),
            current_set=self.get_current_setpoint(channel),
            voltage=self.measure_voltage(channel),
            current=self.measure_current(channel),
            power=self.measure_power(channel),
        )

    def all_off(self) -> None:
        """Turn all outputs off."""
        for ch in [1, 2, 3]:
            self.output_off(ch)

    def configure(self, channel: int, voltage: float, current: float,
                  output: bool = False) -> None:
        """Configure a channel (voltage, current, optionally enable)."""
        self.set_voltage(channel, voltage)
        self.set_current(channel, current)
        if output:
            self.output_on(channel)

    def __repr__(self) -> str:
        return f"RigolDP832A({self.device!r}) - {self.idn}"
