from pydantic import BaseModel, Field, field_validator
from typing import Literal

class MotorParams(BaseModel):
    kv: float = Field(..., gt=0)
    phase_resistance: float = Field(..., ge=0)
    phase_inductance: float = Field(..., ge=0)
    pole_pairs: int = Field(..., ge=1)
    wiring_type: Literal['star', 'delta'] = 'star'
    continuous_current: float = Field(..., ge=0)
    peak_current: float = Field(..., ge=0)

    ambient_temperature: float = 25.0
    thermal_resistance: float = 2.0

    hysteresis_coeff: float = 0.001
    eddy_current_coeff: float = 1e-7

    driver_on_resistance: float = 0.005
    driver_fixed_loss: float = 2.0

    gear_ratio: float = 9.0
    gear_efficiency: float = 0.95

    bus_voltage: float = 48.0

    @field_validator('gear_efficiency')
    def eff_between_0_and_1(cls, v):
        if not 0 < v <= 1:
            raise ValueError('gear_efficiency must be (0, 1].')
        return v

    @field_validator('peak_current')
    def peak_ge_continuous(cls, v, info):
        cont = info.data.get('continuous_current')
        if cont is not None and v < cont:
            raise ValueError('peak_current must be >= continuous_current')
        return v
