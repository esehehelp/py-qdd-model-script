from .base_loss import LossModel
import numpy as np

class GearLossModel(LossModel):
    def __init__(self, gear_ratio: float = 1.0, gear_efficiency: float = 1.0):
        self.gear_ratio = gear_ratio
        self.gear_efficiency = gear_efficiency

    def calculate_loss(self, motor_output_power: np.ndarray):
        # motor_output_power はモーター軸出力（W）
        motor_output_power = np.asarray(motor_output_power)
        # 安全性：効率が1より大なら無効化
        invalid = (self.gear_efficiency >= 1.0) | (motor_output_power <= 0)
        gear_input_power = motor_output_power
        final_output_power = gear_input_power * self.gear_efficiency
        loss = gear_input_power - final_output_power
        loss = np.where(invalid, 0.0, loss)
        final_output_power = np.where(invalid, motor_output_power, final_output_power)
        return loss, final_output_power
