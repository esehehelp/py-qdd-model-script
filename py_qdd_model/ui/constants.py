# -*- coding: utf-8 -*- 

"""UI-related constants, organized by category."""

WINDOW_TITLE = 'QDDモーター特性モデリングツール'

class Plot:
    X_AXIS_LABEL = '電流 [A]'
    Y_AXIS_LABEL = '回転数 [RPM]'
    Z_AXIS_LABEL = 'グラフZ軸'
    PLOT_TITLE = 'QDDモーター特性マップ: {}'
    Z_AXIS_MAP = {
        '総合効率 [%]': 'efficiency',
        'トルク [Nm]': 'torque',
        '出力パワー [W]': 'output_power',
        '必要電圧 [V]': 'voltage',
        '全損失 [W]': 'total_loss'
    }

class Layout:
    PARAM_DEFS = {
        'モーター基本特性': {
            'kv': ('KV値 [rpm/V]', 100.0),
            'phase_resistance': ('一相あたり抵抗 (25℃) [Ohm]', 0.1),
            'phase_inductance': ('一相あたりインダクタンス [uH]', 100.0),
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

class Buttons:
    RUN = '計算＆プロット'
    LOAD_PRESET = 'プリセット読込'
    SAVE_PRESET = 'プリセット保存'
    SAVE_SUMMARY = 'サマリー保存'
    SAVE_PLOT = 'PNG保存'
    WINDING_CALC = '巻線計算'

class Dialog:
    class Title:
        INPUT_ERROR = '入力エラー'
        SAVE_COMPLETE = '保存完了'
        LOAD_COMPLETE = '読込完了'
        LOAD_ERROR = '読込エラー'
        SAVE_ERROR = '保存エラー'
        WARNING = '警告'
        ERROR = 'エラー'
        WINDING_CALC_COMPLETE = '巻線計算完了'
        WINDING_CALC_REF = '基準モーター'
        WINDING_CALC_INPUT = '入力'

    class Message:
        PARAMS_VALIDATION_FAILED = 'パラメータ検証に失敗しました:\n{}'
        PRESET_SAVED = 'プリセットを {} に保存しました。'
        PRESET_LOADED = 'プリセットを読み込みました。'
        PRESET_LOAD_FAILED = 'ファイルの読み込みに失敗しました。\n有効なJSONプリセットファイルを選択してください。\n\n詳細: {}'
        PLOT_SAVE_FAILED = 'グラフの保存に失敗しました:\n{}'
        SUMMARY_SAVE_FAILED = 'サマリーの保存に失敗しました:\n{}'
        PLOT_SAVED = 'グラフを {} に保存しました。'
        SUMMARY_SAVED = 'サマリーを {} に保存しました。'
        RUN_FIRST = '先に「計算＆プロット」を実行してください。'
        WINDING_CALC_MISSING_PARAMS = '計算の前に「KV値」と「ピーク電流」を設定してください。'
        WINDING_CALC_DENSITY_PROMPT = '目標とする電流密度 (A/mm²) を入力してください:'
        WINDING_CALC_USE_CUSTOM_REF = 'カスタムの基準モータープリセットを使用しますか？\n\n（「いいえ」を選択すると、デフォルトの\'medium\'プロファイルが使用されます。）'
        WINDING_CALC_LOAD_REF_ERROR = '基準ファイルの読み込みに失敗しました: {} '
        WINDING_CALC_KEY_ERROR = 'パラメータに必要なキーがありません: {} '
        WINDING_CALC_COMPLETE = (
            "計算基準: {}\n\n"
            "更新されたパラメータ:\n"
            "  - 一相あたり抵抗: {:.4f} Ohm\n"
            "  - 一相あたりインダクタンス: {:.2f} uH\n\n"
            "参考値:\n"
            "  - 推定ワイヤ直径: {:.3f} mm\n"
            "  - 推定全長: {:.2f} m"
        )

class FileDialog:
    JSON = ('JSONファイル', '*.json')
    PNG = ('PNG Image', '*.png')
    TXT = ('Text File', '*.txt')
    ALL = ('すべてのファイル', '*.*')

class SummaryReport:
    TITLE = "QDDモーター性能サマリー"
    PARAMS_HEADER = "使用したパラメータ:"