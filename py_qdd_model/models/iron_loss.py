from .base_loss import LossModel
import numpy as np

class IronLossModel(LossModel):
    """
    Generalized Steinmetz / frequency-dependent iron loss model.

    P_total(f, B) = k_g * f^beta * B^alpha + ke * f^2 * B^2 (optional separate eddy term)
    - kh, ke kept for compatibility, but kg/beta/alpha give more control.
    """
    def __init__(self,
                 kh: float = 0.001,
                 ke: float = 1e-7,
                 alpha: float = 2.0,
                 beta: float = 1.5,
                 kg: float = None,
                 pole_pairs: int = 1):
        # Backwards-compatible params: if kg is provided, use generalized form
        self.kh = kh
        self.ke = ke
        self.alpha = alpha
        self.beta = beta
        self.kg = kg
        self.pole_pairs = pole_pairs

    def calculate_loss(self, rpm: np.ndarray, Bmax: np.ndarray) -> np.ndarray:
        """
        rpm: shaft RPM array (same shape as Bmax)
        Bmax: array of same shape (T or normalized)
        Returns: iron loss in Watts (array)
        """
        # frequency (electrical) in Hz
        f = (rpm * self.pole_pairs) / 60.0
        f_safe = np.maximum(f, 1e-6)

        # If kg provided: generalized Steinmetz P = kg * f^beta * B^alpha
        if self.kg is not None:
            P_g = self.kg * (f_safe ** self.beta) * (np.abs(Bmax) ** self.alpha)
        else:
            # fallback: combine kh (hysteresis ~ f * B^alpha) and ke (eddy ~ f^2 * B^2)
            P_h = self.kh * f_safe * (np.abs(Bmax) ** self.alpha)
            P_e = self.ke * (f_safe ** 2) * (np.abs(Bmax) ** 2)
            P_g = P_h + P_e

        return P_g
