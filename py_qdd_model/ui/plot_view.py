import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ..utils.plotting import plot_surface
from ..utils.config import settings
from ..exceptions import FileOperationError

class PlotView:
    def __init__(self, master, fig=None):
        figsize = (settings.plot.figure_size_x, settings.plot.figure_size_y)
        dpi = settings.plot.display_dpi
        self.fig = fig or plt.Figure(figsize=figsize, dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.ax = None

    def plot(self, X, Y, Z, xlabel, ylabel, zlabel, title):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        downsample_factor = settings.plot.downsample_factor
        plot_surface(self.ax, X, Y, Z, xlabel, ylabel, zlabel, title, downsample_factor=downsample_factor)
        self.canvas.draw()

    def save_png(self, filepath: str):
        try:
            self.fig.savefig(filepath, dpi=settings.plot.save_dpi, facecolor='white')
        except IOError as e:
            raise FileOperationError(f"Failed to save PNG to {filepath}: {e}") from e
