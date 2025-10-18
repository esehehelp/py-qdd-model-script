import tkinter as tk
import matplotlib.pyplot as plt
from py_qdd_model.ui.main_window import MainWindow

if __name__ == '__main__':
    plt.rcParams['font.family'] = 'Meiryo'
    root = tk.Tk()
    app = MainWindow(master=root)
    app.mainloop()
