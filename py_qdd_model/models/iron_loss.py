from .base_loss import LossModel
import numpy as np

class IronLossModel(LossModel):
    def __init__(self, hysteresis_coeff: float = 0.001, eddy_current_coeff: float = 1e-7):
        self.hysteresis_coeff = hysteresis_coeff
        self.eddy_current_coeff = eddy_current_coeff

    def calculate_loss(self, rpm: np.ndarray):
        return self.hysteresis_coeff * rpm + self.eddy_current_coeff * (rpm ** 2)
