from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal
from enum import Enum


class MotorType(str, Enum):
    """Defines the type of motor architecture."""
    INNER_ROTOR = "inner_rotor"
    OUTER_ROTOR = "outer_rotor"
    AXIAL_FLUX = "axial_flux"


class WindingParams(BaseModel):
    """Parameters related to the motor windings."""
    phase_resistance: float = Field(..., ge=0, description="Phase resistance in Ohms.")
    phase_inductance: float = Field(..., ge=0, description="Phase inductance in Henrys.")
    wiring_type: Literal['star', 'delta'] = Field("star", description="Winding configuration.")
    continuous_current: float = Field(..., ge=0, description="Continuous current rating in Amps.")
    peak_current: float = Field(..., ge=0, description="Peak current rating in Amps.")
    wire_diameter: float = Field(..., gt=0, description="Diameter of the enamel wire in mm.")
    turns_per_coil: int = Field(..., gt=0, description="Number of turns per coil.")

    @field_validator('peak_current')
    def peak_ge_continuous(cls, v, info):
        cont = info.data.get('continuous_current')
        if cont is not None and v < cont:
            raise ValueError('peak_current must be >= continuous_current')
        return v


class MagnetParams(BaseModel):
    """Parameters related to the magnets."""
    pole_pairs: int = Field(..., ge=1, description="Number of magnet pole pairs.")
    use_halbach_array: bool = Field(False, description="Whether a Halbach array is used.")
    magnet_width: float = Field(..., gt=0, description="Width of the magnet in mm.")
    magnet_thickness: float = Field(..., gt=0, description="Thickness of the magnet in mm.")
    magnet_length: float = Field(..., gt=0, description="Length of the magnet in mm.")
    remanence_br: float = Field(..., gt=0, description="Magnetic remanence (Br) in Tesla.")


class GeometricParams(BaseModel):
    """Parameters related to the motor's physical dimensions."""
    motor_outer_diameter: float = Field(..., gt=0, description="Outer diameter of the motor in mm.")
    motor_inner_diameter: float = Field(..., gt=0, description="Inner diameter of the motor in mm.")
    motor_length: float = Field(..., gt=0, description="Axial length of the motor in mm.")
    slot_number: int = Field(..., gt=0, description="Number of stator slots.")
    slot_depth: float = Field(5.0, gt=0, description="Depth of the stator slots in mm.")
    slot_top_width: float = Field(2.0, gt=0, description="Width of the slot opening in mm.")
    slot_bottom_width: float = Field(4.0, gt=0, description="Width of the slot bottom in mm.")

    @model_validator(mode='after')
    def check_diameters(self) -> 'GeometricParams':
        if self.motor_outer_diameter <= self.motor_inner_diameter:
            raise ValueError('motor_outer_diameter must be greater than motor_inner_diameter')
        return self


class ElectricalParams(BaseModel):
    """Core electrical parameters of the motor."""
    kv: float = Field(..., gt=0, description="Motor velocity constant in RPM/V.")
    hysteresis_coeff: float = Field(0.001, ge=0, description="Hysteresis loss coefficient.")
    eddy_current_coeff: float = Field(1e-7, ge=0, description="Eddy current loss coefficient.")


class ThermalParams(BaseModel):
    """Thermal properties of the motor."""
    ambient_temperature: float = Field(25.0, description="Ambient temperature in Celsius.")
    thermal_resistance: float = Field(2.0, ge=0, description="Thermal resistance from windings to case in C/W.")


class DriverParams(BaseModel):
    """Parameters for the motor driver/ESC."""
    driver_on_resistance: float = Field(0.005, ge=0, description="On-resistance of the driver FETs in Ohms.")
    driver_fixed_loss: float = Field(2.0, ge=0, description="Fixed power loss in the driver in Watts.")


class GearParams(BaseModel):
    """Parameters for the gearbox, if any."""
    gear_ratio: float = Field(1.0, gt=0, description="Gear ratio. 1.0 for direct drive.")
    gear_efficiency: float = Field(1.0, description="Efficiency of the gearbox.")

    @field_validator('gear_efficiency')
    def eff_between_0_and_1(cls, v):
        if not 0 < v <= 1:
            raise ValueError('gear_efficiency must be (0, 1].')
        return v


class SimulationParams(BaseModel):
    """Parameters for running a simulation."""
    bus_voltage: float = Field(48.0, gt=0, description="Bus voltage for the simulation in Volts.")


class MotorParams(BaseModel):
    """A comprehensive container for all motor-related parameters."""
    name: str = Field("My Motor", description="A user-defined name for the motor model.")
    description: str = Field("A custom motor model.", description="A brief description of the motor.")
    motor_type: MotorType = Field(MotorType.INNER_ROTOR, description="The architecture of the motor.")

    electrical: ElectricalParams = Field(..., description="Core electrical parameters.")
    winding: WindingParams = Field(..., description="Winding parameters.")
    magnets: MagnetParams = Field(..., description="Magnet parameters.")
    geometry: GeometricParams = Field(..., description="Physical dimensions.")
    thermal: ThermalParams = Field(..., description="Thermal properties.")
    driver: DriverParams = Field(..., description="Motor driver parameters.")
    gear: GearParams = Field(..., description="Gearbox parameters.")
    simulation: SimulationParams = Field(..., description="Simulation settings.")


# --- Application Settings Models ---

class WindowSettings(BaseModel):
    initial_size: str = "1280x900"

class LayoutSettings(BaseModel):
    main_padding: int = 10
    widget_pady: int = 8
    button_padx: int = 4
    combobox_width: int = 20

class PlotSettings(BaseModel):
    figure_size_x: int = 8
    figure_size_y: int = 8
    display_dpi: int = 100
    save_dpi: int = 300
    downsample_factor: int = Field(3, ge=1)

class AnalysisSettings(BaseModel):
    grid_points: int = Field(50, ge=10)
    rpm_safety_margin: float = Field(1.1, gt=0)

class LanguageSettings(BaseModel):
    lang: Literal["jp", "en"] = "jp"

class AppSettings(BaseModel):
    """A comprehensive container for all application settings."""
    window: WindowSettings = Field(default_factory=WindowSettings)
    layout: LayoutSettings = Field(default_factory=LayoutSettings)
    plot: PlotSettings = Field(default_factory=PlotSettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    language: LanguageSettings = Field(default_factory=LanguageSettings)
