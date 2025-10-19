import numpy as np
from typing import Dict, Tuple, Optional, Any
import numpy.typing as npt
from ..schema import MotorParams

class ResultsAnalyzer:
    def __init__(self, params: MotorParams, results: Dict[str, npt.NDArray], current_range: npt.NDArray) -> None:
        self.p = params
        self.r = results
        self.current_range = current_range
        self.valid_mask = self.r['voltage'] <= self.p.bus_voltage

    def _get_summary_point(self, key: str) -> Tuple[Optional[float], Optional[Tuple[int, int]]]:
        if not np.any(self.valid_mask):
            return None, None
        
        data = np.where(self.valid_mask, self.r[key], np.nan)
        if not np.any(~np.isnan(data)):
            return None, None
            
        idx = np.nanargmax(data)
        coords: Tuple[int, int] = np.unravel_index(idx, data.shape) # type: ignore
        val = data[coords]
        return val, coords

    def calculate_summary(self) -> Dict[str, str]:
        summary: Dict[str, str] = {}

        # 1. Peak Efficiency
        max_eff, eff_coords = self._get_summary_point('efficiency')
        if max_eff is not None and eff_coords is not None:
            summary['max_eff_val'] = f'{max_eff*100:.1f} %'
            summary['max_eff_point'] = f"{self.r['rpm'][eff_coords]:.0f} RPM / {self.r['current'][eff_coords]:.1f} A / {self.r['torque'][eff_coords]:.2f} Nm"

        # 2. Max Output Power
        max_power, power_coords = self._get_summary_point('output_power')
        if max_power is not None and power_coords is not None:
            summary['max_power_val'] = f'{max_power:.1f} W'
            summary['max_power_point'] = f"{self.r['rpm'][power_coords]:.0f} RPM / {self.r['current'][power_coords]:.1f} A / {self.r['torque'][power_coords]:.2f} Nm"

        # 3. Max Torque
        max_torque, torque_coords = self._get_summary_point('torque')
        if max_torque is not None and torque_coords is not None:
            summary['max_torque_val'] = f'{max_torque:.2f} Nm'
            summary['max_torque_point'] = f"{self.r['rpm'][torque_coords]:.0f} RPM / {self.r['current'][torque_coords]:.1f} A"

        # 4. Rated (Continuous) Operation
        cont_idx = np.argmin(np.abs(self.current_range - self.p.continuous_current))
        rated_mask = self.valid_mask[:, cont_idx]
        rated_eff = np.where(rated_mask, self.r['efficiency'][:, cont_idx], np.nan)
        if np.any(~np.isnan(rated_eff)):
            rated_idx = np.nanargmax(rated_eff)
            summary['rated_eff_val'] = f'{rated_eff[rated_idx]*100:.1f} %'
            summary['rated_point'] = f"{self.r['rpm'][rated_idx, cont_idx]:.0f} RPM / {self.r['torque'][rated_idx, cont_idx]:.2f} Nm / {self.r['output_power'][rated_idx, cont_idx]:.1f} W"

        # 5. Operating Envelope
        if np.any(self.valid_mask):
            max_rpm = np.max(self.r['rpm'][self.valid_mask])
            max_current = np.max(self.r['current'][self.valid_mask])
            summary['max_rpm_val'] = f'{max_rpm:.0f} RPM'
            summary['max_current_val'] = f'{max_current:.1f} A'
        
        return summary