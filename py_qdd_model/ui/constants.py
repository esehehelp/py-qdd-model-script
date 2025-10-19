# -*- coding: utf-8 -*-

# Window Title
WINDOW_TITLE = 'QDDモーター特性モデリングツール'

# Plotting
X_AXIS_LABEL = '電流 [A]'
Y_AXIS_LABEL = '回転数 [RPM]'
PLOT_TITLE = 'QDDモーター特性マップ: {}'

# Plot Z-Axis Options
Z_AXIS_MAP = {
    '総合効率 [%]': 'efficiency',
    'トルク [Nm]': 'torque',
    '出力パワー [W]': 'output_power',
    '必要電圧 [V]': 'voltage',
    '全損失 [W]': 'total_loss'
}

# Summary Panel Layout
SUMMARY_LAYOUT = {
    'ピーク性能': [
        ('最大総合効率', 'max_eff_val'),
        ('└ 回転数/電流/トルク', 'max_eff_point'),
        ('最大出力パワー', 'max_power_val'),
        ('└ 回転数/電流/トルク', 'max_power_point'),
        ('最大トルク', 'max_torque_val'),
        ('└ 回転数/電流', 'max_torque_point')
    ],
    '定格動作時 (連続電流)': [
        ('最大効率', 'rated_eff_val'),
        ('└ 回転数/トルク/パワー', 'rated_point')
    ],
    '動作領域': [
        ('最大回転数 (電圧制限下)', 'max_rpm_val'),
        ('最大電流 (電圧制限下)', 'max_current_val')
    ]
}

# Parameter Panel Layout
PARAM_DEFS = {
    'モーター基本特性': {
        'kv': ('KV値 [rpm/V]', 100.0),
        'phase_resistance': ('一相あたり抵抗 (25℃) [Ohm]', 0.1),
        'phase_inductance': ('一相あたりインダクタンス [H]', 0.0001),
        'pole_pairs': ('極対数', 7),
        'wiring_type': ('配線方式', 'star', ['star','delta']),
        'continuous_current': ('連続電流 [A]', 10.0),
        'peak_current': ('ピーク電流 [A]', 30.0)
    },
    '熱モデル': {
        'ambient_temperature': ('周囲温度 [°C]', 25.0),
        'thermal_resistance': ('モーター熱抵抗 [°C/W]', 2.0)
    },
    '鉄損モデル': {
        'hysteresis_coeff': ('ヒステリシス係数 [W/rpm]', 0.001),
        'eddy_current_coeff': ('渦電流係数 [W/rpm^2]', 1e-7)
    },
    'ドライバ損失モデル': {
        'driver_on_resistance': ('ドライバON抵抗 [Ohm]', 0.005),
        'driver_fixed_loss': ('ドライバ固定損失 [W]', 2.0)
    },
    'ギア損失モデル': {
        'gear_ratio': ('減速比', 9.0),
        'gear_efficiency': ('ギア効率', 0.95)
    },
    '動作条件': {
        'bus_voltage': ('バス電圧 [V]', 48.0)
    }
}

# Button Labels
RUN_BUTTON = '計算＆プロット'
LOAD_PRESET_BUTTON = 'プリセット読込'
SAVE_PRESET_BUTTON = 'プリセット保存'
SAVE_SUMMARY_BUTTON = 'サマリー保存'
SAVE_PLOT_BUTTON = 'PNG保存'

# Labels
Z_AXIS_LABEL = 'グラフZ軸'

# Dialog Titles
INPUT_ERROR_TITLE = '入力エラー'
SAVE_COMPLETE_TITLE = '保存完了'
LOAD_COMPLETE_TITLE = '読込完了'
LOAD_ERROR_TITLE = '読込エラー'
SAVE_ERROR_TITLE = '保存エラー'
WARNING_TITLE = '警告'

# Dialog Messages
PARAMS_VALIDATION_FAILED_MSG = 'パラメータ検証に失敗しました:\n{}'
PRESET_SAVED_MSG = 'プリセットを {} に保存しました。'
PRESET_LOADED_MSG = 'プリセットを読み込みました。'
PRESET_LOAD_FAILED_MSG = 'ファイルの読み込みに失敗しました。\n有効なJSONプリセットファイルを選択してください。\n\n詳細: {}'
PLOT_SAVE_FAILED_MSG = 'グラフの保存に失敗しました:\n{}'
SUMMARY_SAVE_FAILED_MSG = 'サマリーの保存に失敗しました:\n{}'
PLOT_SAVED_MSG = 'グラフを {} に保存しました。'
SUMMARY_SAVED_MSG = 'サマリーを {} に保存しました。'
RUN_FIRST_MSG = '先に「計算＆プロット」を実行してください。'

# File Dialog
JSON_FILE_TYPE = ('JSONファイル', '*.json')
PNG_FILE_TYPE = ('PNG Image', '*.png')
TXT_FILE_TYPE = ('Text File', '*.txt')
ALL_FILES_TYPE = ('すべてのファイル', '*.*')

# Summary Report
SUMMARY_TITLE = "QDDモーター性能サマリー"
SUMMARY_PARAMS_HEADER = "使用したパラメータ:"