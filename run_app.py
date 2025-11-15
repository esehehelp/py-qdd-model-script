import tkinter as tk
import matplotlib.pyplot as plt
from py_qdd_model.ui.main_window import MainWindow
from py_qdd_model.i18n import translator
from py_qdd_model.utils.config import settings

if __name__ == '__main__':
    # Set the language before creating any UI components
    translator.set_language(settings["language"]["lang"])
    
    plt.rcParams['font.family'] = 'Meiryo'
    root = tk.Tk()
    app = MainWindow(master=root)
    app.mainloop()
