from .base_loss import LossModel
import numpy as np

class IronLossModel(LossModel):
    """
    鉄損モデル: Steinmetz式ベース
    - ヒステリシス損: kh * f * Bmax^α
    - 渦電流損: ke * f^2 * Bmax^2
    """
    def __init__(self, kh: float, ke: float, alpha: float, pole_pairs: int):
        self.kh = kh
        self.ke = ke
        self.alpha = alpha
        self.pole_pairs = pole_pairs

    def calculate_loss(self, rpm: np.ndarray, Bmax: np.ndarray) -> np.ndarray:
        f = (rpm * self.pole_pairs) / 60.0  # 電気角周波数(Hz)
        P_h = self.kh * f * (Bmax ** self.alpha)
        P_e = self.ke * (f ** 2) * (Bmax ** 2)
        return P_h + P_e