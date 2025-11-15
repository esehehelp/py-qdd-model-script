# -*- coding: utf-8 -*-

"""
This module builds the UI constants dynamically based on the selected language.
It imports the translator function `t` and uses it to populate the data structures
that the UI components rely on.
"""

from ..i18n.translator import t

WINDOW_TITLE = t("WINDOW_TITLE")

class Plot:
    X_AXIS_LABEL = t("Plot.X_AXIS_LABEL")
    Y_AXIS_LABEL = t("Plot.Y_AXIS_LABEL")
    Z_AXIS_LABEL = t("Plot.Z_AXIS_LABEL")
    PLOT_TITLE = t("Plot.PLOT_TITLE")
    Z_AXIS_MAP = {
        t("Plot.Z_AXIS_MAP.efficiency"): "efficiency",
        t("Plot.Z_AXIS_MAP.torque"): "torque",
        t("Plot.Z_AXIS_MAP.output_power"): "output_power",
        t("Plot.Z_AXIS_MAP.voltage"): "voltage",
        t("Plot.Z_AXIS_MAP.total_loss"): "total_loss",
    }

class Layout:
    @staticmethod
    def get_param_defs():
        return {
            t("Layout.PARAM_DEFS.groups.general"): {
                'name': (t("Layout.PARAM_DEFS.labels.name"), "My Motor"),
                'description': (t("Layout.PARAM_DEFS.labels.description"), "A custom motor model."),
                'motor_type': (t("Layout.PARAM_DEFS.labels.motor_type"), 'inner_rotor', ['inner_rotor', 'outer_rotor', 'axial_flux']),
            },
            "electrical": {
                'kv': (t("Layout.PARAM_DEFS.labels.kv"), 100.0),
                'hysteresis_coeff': (t("Layout.PARAM_DEFS.labels.hysteresis_coeff"), 0.001),
                'eddy_current_coeff': (t("Layout.PARAM_DEFS.labels.eddy_current_coeff"), 1e-7),
            },
            "winding": {
                'phase_resistance': (t("Layout.PARAM_DEFS.labels.phase_resistance"), 0.1),
                'phase_inductance': (t("Layout.PARAM_DEFS.labels.phase_inductance"), 100.0),
                'wiring_type': (t("Layout.PARAM_DEFS.labels.wiring_type"), 'star', ['star', 'delta']),
                'continuous_current': (t("Layout.PARAM_DEFS.labels.continuous_current"), 10.0),
                'peak_current': (t("Layout.PARAM_DEFS.labels.peak_current"), 30.0),
                'wire_diameter': (t("Layout.PARAM_DEFS.labels.wire_diameter"), 0.5),
                'turns_per_coil': (t("Layout.PARAM_DEFS.labels.turns_per_coil"), 50),
            },
            "magnets": {
                'pole_pairs': (t("Layout.PARAM_DEFS.labels.pole_pairs"), 7),
                'use_halbach_array': (t("Layout.PARAM_DEFS.labels.use_halbach_array"), False),
                'magnet_width': (t("Layout.PARAM_DEFS.labels.magnet_width"), 10.0),
                'magnet_thickness': (t("Layout.PARAM_DEFS.labels.magnet_thickness"), 3.0),
                'magnet_length': (t("Layout.PARAM_DEFS.labels.magnet_length"), 20.0),
                'remanence_br': (t("Layout.PARAM_DEFS.labels.remanence_br"), 1.2),
            },
            "geometry": {
                'motor_outer_diameter': (t("Layout.PARAM_DEFS.labels.motor_outer_diameter"), 60.0),
                'motor_inner_diameter': (t("Layout.PARAM_DEFS.labels.motor_inner_diameter"), 30.0),
                'motor_length': (t("Layout.PARAM_DEFS.labels.motor_length"), 25.0),
                'slot_number': (t("Layout.PARAM_DEFS.labels.slot_number"), 12),
                'slot_depth': (t("Layout.PARAM_DEFS.labels.slot_depth"), 5.0),
                'slot_top_width': (t("Layout.PARAM_DEFS.labels.slot_top_width"), 2.0),
                'slot_bottom_width': (t("Layout.PARAM_DEFS.labels.slot_bottom_width"), 4.0),
            },
            "thermal": {
                'ambient_temperature': (t("Layout.PARAM_DEFS.labels.ambient_temperature"), 25.0),
                'thermal_resistance': (t("Layout.PARAM_DEFS.labels.thermal_resistance"), 2.0),
            },
            "driver": {
                'driver_on_resistance': (t("Layout.PARAM_DEFS.labels.driver_on_resistance"), 0.005),
                'driver_fixed_loss': (t("Layout.PARAM_DEFS.labels.driver_fixed_loss"), 2.0),
            },
            "gear": {
                'gear_ratio': (t("Layout.PARAM_DEFS.labels.gear_ratio"), 9.0),
                'gear_efficiency': (t("Layout.PARAM_DEFS.labels.gear_efficiency"), 0.95),
            },
            "simulation": {
                'bus_voltage': (t("Layout.PARAM_DEFS.labels.bus_voltage"), 48.0),
            }
        }
    SUMMARY_LAYOUT = {
        t("Layout.SUMMARY_LAYOUT.groups.peak"): [
            (t("Layout.SUMMARY_LAYOUT.labels.max_eff"), 'max_eff_val'),
            (t("Layout.SUMMARY_LAYOUT.labels.max_eff_point"), 'max_eff_point'),
            (t("Layout.SUMMARY_LAYOUT.labels.max_power"), 'max_power_val'),
            (t("Layout.SUMMARY_LAYOUT.labels.max_power_point"), 'max_power_point'),
            (t("Layout.SUMMARY_LAYOUT.labels.max_torque"), 'max_torque_val'),
            (t("Layout.SUMMARY_LAYOUT.labels.max_torque_point"), 'max_torque_point')
        ],
        t("Layout.SUMMARY_LAYOUT.groups.rated"): [
            (t("Layout.SUMMARY_LAYOUT.labels.rated_eff"), 'rated_eff_val'),
            (t("Layout.SUMMARY_LAYOUT.labels.rated_point"), 'rated_point')
        ],
        t("Layout.SUMMARY_LAYOUT.groups.envelope"): [
            (t("Layout.SUMMARY_LAYOUT.labels.max_rpm"), 'max_rpm_val'),
            (t("Layout.SUMMARY_LAYOUT.labels.max_current"), 'max_current_val')
        ]
    }

class Buttons:
    RUN = t("Buttons.RUN")
    LOAD_PRESET = t("Buttons.LOAD_PRESET")
    SAVE_PRESET = t("Buttons.SAVE_PRESET")
    SAVE_SUMMARY = t("Buttons.SAVE_SUMMARY")
    SAVE_PLOT = t("Buttons.SAVE_PLOT")
    WINDING_CALC = t("Buttons.WINDING_CALC")
    GENERATE_3D_MODEL = t("Buttons.GENERATE_3D_MODEL")
    EXPORT_CSV_FUSION = t("Buttons.EXPORT_CSV_FUSION")

class Dialog:
    class Title:
        INPUT_ERROR = t("Dialog.Title.INPUT_ERROR")
        SAVE_COMPLETE = t("Dialog.Title.SAVE_COMPLETE")
        LOAD_COMPLETE = t("Dialog.Title.LOAD_COMPLETE")
        LOAD_ERROR = t("Dialog.Title.LOAD_ERROR")
        SAVE_ERROR = t("Dialog.Title.SAVE_ERROR")
        WARNING = t("Dialog.Title.WARNING")
        ERROR = t("Dialog.Title.ERROR")
        WINDING_CALC_COMPLETE = t("Dialog.Title.WINDING_CALC_COMPLETE")
        WINDING_CALC_REF = t("Dialog.Title.WINDING_CALC_REF")
        WINDING_CALC_INPUT = t("Dialog.Title.WINDING_CALC_INPUT")

    class Message:
        PARAMS_VALIDATION_FAILED = t("Dialog.Message.PARAMS_VALIDATION_FAILED")
        PRESET_SAVED = t("Dialog.Message.PRESET_SAVED")
        PRESET_LOADED = t("Dialog.Message.PRESET_LOADED")
        PRESET_LOAD_FAILED = t("Dialog.Message.PRESET_LOAD_FAILED")
        PLOT_SAVE_FAILED = t("Dialog.Message.PLOT_SAVE_FAILED")
        SUMMARY_SAVE_FAILED = t("Dialog.Message.SUMMARY_SAVE_FAILED")
        PLOT_SAVED = t("Dialog.Message.PLOT_SAVED")
        SUMMARY_SAVED = t("Dialog.Message.SUMMARY_SAVED")
        RUN_FIRST = t("Dialog.Message.RUN_FIRST")
        WINDING_CALC_MISSING_PARAMS = t("Dialog.Message.WINDING_CALC_MISSING_PARAMS")
        WINDING_CALC_DENSITY_PROMPT = t("Dialog.Message.WINDING_CALC_DENSITY_PROMPT")
        WINDING_CALC_USE_CUSTOM_REF = t("Dialog.Message.WINDING_CALC_USE_CUSTOM_REF")
        WINDING_CALC_LOAD_REF_ERROR = t("Dialog.Message.WINDING_CALC_LOAD_REF_ERROR")
        WINDING_CALC_KEY_ERROR = t("Dialog.Message.WINDING_CALC_KEY_ERROR")
        WINDING_CALC_COMPLETE = t("Dialog.Message.WINDING_CALC_COMPLETE")

class FileDialog:
    JSON = (t("FileDialog.JSON"), '*.json')
    PNG = (t("FileDialog.PNG"), '*.png')
    TXT = (t("FileDialog.TXT"), '*.txt')
    ALL = (t("FileDialog.ALL"), '*.*')

class SummaryReport:
    TITLE = t("SummaryReport.TITLE")
    PARAMS_HEADER = t("SummaryReport.PARAMS_HEADER")
