from pydantic import BaseModel, Field
from typing import List, Literal, Union, Dict, Any, Optional
from enum import Enum


# --- Base Component & Material Models ---

class BaseComponent(BaseModel):
    """A base model for all motor components, providing a name and type."""
    name: str = Field(..., description="Unique name for the component within the assembly.")
    component_type: str = Field(..., description="The type of the component.")


# --- Geometry & Arrangement Models ---

class RectangularMagnetGeometry(BaseModel):
    width: float = Field(..., gt=0, description="Magnet width in mm.")
    length: float = Field(..., gt=0, description="Magnet length in mm.")
    thickness: float = Field(..., gt=0, description="Magnet thickness in mm.")

class StatorGeometry(BaseModel):
    inner_radius: float = Field(..., ge=0)
    outer_radius: float = Field(..., gt=0)
    length: float = Field(..., gt=0)
    slot_number: int = Field(..., gt=0)
    # ... other slot geometry params

class RotorGeometry(BaseModel):
    inner_radius: float = Field(..., ge=0)
    outer_radius: float = Field(..., gt=0)
    length: float = Field(..., gt=0)


# --- Definable Components ---

class WindingComponent(BaseComponent):
    """Defines the properties of a winding set."""
    component_type: Literal["winding"] = "winding"
    material_key: str = Field(..., description="Key for the wire material (e.g., 'AWG20').")
    turns_per_coil: int = Field(..., gt=0)
    wiring_type: Literal['star', 'delta'] = "star"
    path_definition: Dict[str, Any] = Field(default_factory=dict, description="Defines how the winding is applied to a stator.")
    
    # --- Overridable Fields ---
    override_phase_resistance: Optional[float] = Field(None, ge=0)
    override_phase_inductance: Optional[float] = Field(None, ge=0)


class MagnetComponent(BaseComponent):
    """Defines the properties of a set of magnets."""
    component_type: Literal["magnet"] = "magnet"
    material_key: str = Field(..., description="Key for the magnet material (e.g., 'N42SH').")
    pole_pairs: int = Field(..., ge=1)
    geometry: Union[RectangularMagnetGeometry] # Can be extended with ArcMagnetGeometry etc.
    arrangement: Literal['surface', 'halbach', 'dual_halbach'] = "surface"


class StatorComponent(BaseComponent):
    """Defines a stator, which holds windings."""
    component_type: Literal["stator"] = "stator"
    material_key: str = Field(..., description="Key for the core material (e.g., '50H470').")
    geometry: StatorGeometry
    winding_ref: str = Field(..., description="Name of the WindingComponent used on this stator.")


class RotorComponent(BaseComponent):
    """Defines a rotor, which holds magnets."""
    component_type: Literal["rotor"] = "rotor"
    material_key: str = Field(..., description="Key for the rotor's structural material (e.g., 'S45C').")
    geometry: RotorGeometry
    magnet_ref: str = Field(..., description="Name of the MagnetComponent used on this rotor.")


# --- Top-Level Assembly Model ---

class Topology(BaseModel):
    """Defines the physical layout of the components."""
    layout_type: Literal['axial', 'radial'] = "radial"
    sequence: List[str] = Field(..., description="Ordered list of component names defining the assembly stack.")


class SimulationParams(BaseModel):
    """Parameters for running a simulation."""
    bus_voltage: float = Field(48.0, gt=0, description="Bus voltage for the simulation in Volts.")
    ambient_temperature: float = Field(25.0, description="Ambient temperature in Celsius.")


class MotorAssembly(BaseModel):
    """
    A comprehensive, component-based definition of a motor.
    This structure allows for flexible and complex motor topologies.
    """
    assembly_name: str = Field("My Motor Assembly", description="A user-defined name for the entire motor assembly.")
    description: str = Field("A custom motor assembly.", description="A brief description of the motor.")
    
    topology: Topology
    components: List[Union[StatorComponent, RotorComponent, WindingComponent, MagnetComponent]]
    
    simulation: SimulationParams = Field(default_factory=SimulationParams)

    # --- Global Overridable Fields ---
    override_kv: Optional[float] = Field(None, gt=0, description="Manually override the calculated motor velocity constant (RPM/V).")
    override_thermal_resistance: Optional[float] = Field(None, ge=0, description="Manually override the calculated thermal resistance.")

