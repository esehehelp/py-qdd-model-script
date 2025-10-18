from .base_loss import LossModel
import numpy as np

class CopperLossModel(LossModel):
    def __init__(self, wiring_type: str = 'star'):
        self.wiring_type = wiring_type

    def calculate_loss(self, current: np.ndarray, phase_resistance: np.ndarray):
        """current: ndarray (A), phase_resistance: scalar or ndarray (Ohm)
        戻り値: ndarray (W)"""
        factor = 3 if self.wiring_type == 'star' else 1
        return factor * (current ** 2) * phase_resistance
