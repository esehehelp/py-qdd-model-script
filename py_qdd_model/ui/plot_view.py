import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ..utils.plotting import plot_surface

class PlotView:
    def __init__(self, master, fig=None):
        self.fig = fig or plt.Figure(figsize=(8,8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.ax = None

    def plot(self, X, Y, Z, xlabel, ylabel, zlabel, title):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        plot_surface(self.ax, X, Y, Z, xlabel, ylabel, zlabel, title)
        self.canvas.draw()

    def save_png(self, filepath: str):
        self.fig.savefig(filepath, dpi=300, facecolor='white')
