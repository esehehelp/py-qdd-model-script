from .base_loss import LossModel
import numpy as np

class DriverLossModel(LossModel):
    def __init__(self, on_resistance: float = 0.005, fixed_loss: float = 0.0):
        self.on_resistance = on_resistance
        self.fixed_loss = fixed_loss

    def calculate_loss(self, current: np.ndarray):
        conduction = (current ** 2) * self.on_resistance
        return conduction + self.fixed_loss
