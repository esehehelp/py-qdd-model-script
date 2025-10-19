# -*- coding: utf-8 -*-
import numpy as np

class PhysicsConstants:
    """
    Defines physical constants used in the motor model.
    """
    # Temperature coefficient for copper resistance change. Units: 1/°C
    COPPER_TEMP_COEFF = 0.00393
    
    # Conversion factor from Revolutions Per Minute (RPM) to Radians per Second.
    RPM_TO_RAD_PER_SEC = (2 * np.pi) / 60
    
    # Conversion factor from Radians per Second to Revolutions Per Minute (RPM).
    RAD_PER_SEC_TO_RPM = 60 / (2 * np.pi)
    
    # Reference temperature for material properties (e.g., resistance, magnets). Units: °C
    REFERENCE_TEMPERATURE = 25.0

class ModelDefaults:
    """
    Defines default values for the motor analysis model.
    """
    # Maximum number of iterations for the thermal convergence loop.
    MAX_ITERATIONS = 50
    
    # Under-relaxation factor for thermal calculation. (0 < relax <= 1).
    # Lower values increase stability but slow down convergence.
    RELAXATION_FACTOR = 0.4
    
    # Convergence threshold for temperature change between iterations. Units: °C
    CONVERGENCE_THRESHOLD = 0.05
    
    # Fallback maximum RPM if it cannot be calculated from motor parameters.
    FALLBACK_MAX_RPM = 5000