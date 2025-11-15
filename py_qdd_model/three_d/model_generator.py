import cadquery as cq
from pathlib import Path
from ..schema import MotorParams, MotorType, ElectricalParams, WindingParams, MagnetParams, GeometricParams, ThermalParams, DriverParams, GearParams, SimulationParams

def generate_motor_model(params: MotorParams, output_dir: Path):
    """
    Generates a 3D model of the motor based on MotorParams and exports it as a STEP file.
    Currently supports INNER_ROTOR type.
    """
    g = params.geometry
    length = g.motor_length

    # --- Stator and Rotor based on Motor Type ---
    if params.motor_type == MotorType.INNER_ROTOR:
        # Stator is the outer part with slots
        stator_outer_radius = g.motor_outer_diameter / 2
        stator_inner_radius = g.motor_outer_diameter / 2 - g.slot_depth
        
        stator_ring = cq.Workplane("XY").circle(stator_outer_radius).circle(stator_inner_radius).extrude(length)

        # Create a single trapezoidal slot sketch on the inner surface
        # This is a simplified representation, a more robust method would be to revolve a profile.
        slot_profile_inner = (
            cq.Workplane("XY")
            .moveTo(stator_inner_radius, -g.slot_top_width / 2)
            .lineTo(stator_inner_radius + g.slot_depth, -g.slot_bottom_width / 2)
            .lineTo(stator_inner_radius + g.slot_depth, g.slot_bottom_width / 2)
            .lineTo(stator_inner_radius, g.slot_top_width / 2)
            .close()
        )
        slots_to_cut = (
            cq.Workplane("XY")
            .polarArray(
                radius=0,
                angle=360,
                count=g.slot_number,
                startAngle=0,
            )
            .each(lambda loc: slot_profile_inner.val().located(loc))
        ).extrude(length)

        stator = stator_ring.cut(slots_to_cut)

        # Rotor is the simple inner cylinder
        rotor_radius = g.motor_inner_diameter / 2
        rotor = cq.Workplane("XY").circle(rotor_radius).extrude(length)

    elif params.motor_type == MotorType.OUTER_ROTOR:
        # Rotor is the outer ring
        rotor_outer_radius = g.motor_outer_diameter / 2
        # Assuming magnets are on the inside of the rotor, their thickness is part of the rotor.
        rotor_inner_radius = rotor_outer_radius - params.magnets.magnet_thickness
        rotor = cq.Workplane("XY").circle(rotor_outer_radius).circle(rotor_inner_radius).extrude(length)

        # Stator is the inner part with slots on the outside
        air_gap = 1.0 # mm, should be a parameter
        stator_outer_radius = rotor_inner_radius - air_gap
        stator_inner_radius = g.motor_inner_diameter / 2 # Shaft hole
        
        stator_ring = cq.Workplane("XY").circle(stator_outer_radius).circle(stator_inner_radius).extrude(length)

        # Create a single slot sketch on the outer surface
        slot_profile_outer = (
            cq.Workplane("XY")
            .moveTo(stator_outer_radius, -g.slot_top_width / 2)
            .lineTo(stator_outer_radius - g.slot_depth, -g.slot_bottom_width / 2)
            .lineTo(stator_outer_radius - g.slot_depth, g.slot_bottom_width / 2)
            .lineTo(stator_outer_radius, g.slot_top_width / 2)
            .close()
        )

        slots_to_cut = (
            cq.Workplane("XY")
            .polarArray(
                radius=0,
                angle=360,
                count=g.slot_number,
                startAngle=0
            )
            .each(lambda loc: slot_profile_outer.val().located(loc))
        ).extrude(length)
        
        stator = stator_ring.cut(slots_to_cut)

    elif params.motor_type == MotorType.AXIAL_FLUX:
        # Stator is a disk
        stator_outer_radius = g.motor_outer_diameter / 2
        stator_inner_radius = g.motor_inner_diameter / 2
        stator_thickness = length / 2 # Assuming two stators, or one stator and one rotor
        
        stator = cq.Workplane("XY").circle(stator_outer_radius).circle(stator_inner_radius).extrude(stator_thickness)

        # Rotor is also a disk
        rotor_outer_radius = g.motor_outer_diameter / 2
        rotor_inner_radius = g.motor_inner_diameter / 2
        rotor_thickness = length / 2 # Assuming one rotor
        
        rotor = cq.Workplane("XY").circle(rotor_outer_radius).circle(rotor_inner_radius).extrude(rotor_thickness)

        # For axial flux, we might want to position them axially
        # For simplicity, we'll just create them at the origin for now.
        # A more complex model would involve positioning and potentially slots/magnets on the faces.

    else:
        # Placeholder for other motor types (e.g., Axial)
        stator = cq.Workplane("XY").circle(g.motor_outer_diameter / 2).circle(g.motor_inner_diameter / 2).extrude(length)
        rotor = None # Explicitly set to None if not defined


    # --- Assembly ---
    assembly = cq.Assembly()
    assembly.add(stator, name="stator", color=cq.Color(0.5, 0.5, 0.5)) # gray
    if rotor is not None: # Check if rotor is defined
        assembly.add(rotor, name="rotor", color=cq.Color(0.2, 0.2, 0.2)) # darkgray

    # Define output path
    output_path = output_dir / f"{params.name.replace(' ', '_')}_model.step"

    # Export as STEP file
    try:
        assembly.save(str(output_path), "STEP")
        print(f"Generated STEP file: {output_path}")
    except Exception as e:
        print(f"Error: Failed to save the STEP file to {output_path}. Reason: {e}")
        # Re-raise the exception so the calling process knows something went wrong.
        raise


    return output_path

if __name__ == '__main__':
    # Example usage (for testing the module directly)
    
    test_params = MotorParams(
        name="Test Motor Detailed",
        description="A test motor for detailed 3D generation",
        motor_type="inner_rotor",
        electrical=ElectricalParams(kv=100.0),
        winding=WindingParams(phase_resistance=0.1, phase_inductance=100.0, wiring_type='star', continuous_current=10.0, peak_current=30.0, wire_diameter=0.5, turns_per_coil=50),
        magnets=MagnetParams(pole_pairs=7, use_halbach_array=False, magnet_width=10.0, magnet_thickness=3.0, magnet_length=20.0, remanence_br=1.2),
        geometry=GeometricParams(
            motor_outer_diameter=60.0, 
            motor_inner_diameter=30.0, 
            motor_length=25.0, 
            slot_number=12,
            slot_depth=8.0,
            slot_top_width=2.5,
            slot_bottom_width=5.0
        ),
        thermal=ThermalParams(ambient_temperature=25.0, thermal_resistance=2.0),
        driver=DriverParams(driver_on_resistance=0.005, driver_fixed_loss=2.0),
        gear=GearParams(gear_ratio=9.0, gear_efficiency=0.95),
        simulation=SimulationParams(bus_voltage=48.0)
    )

    output_dir = Path("./generated_models")
    output_dir.mkdir(exist_ok=True)

    generate_motor_model(test_params, output_dir)
