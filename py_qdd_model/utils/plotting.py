import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_surface(ax, X, Y, Z, xlabel='I', ylabel='RPM', zlabel='Z', title='', downsample_factor: int = 1):
    surf = ax.plot_surface(X, Y, Z, cmap='plasma', rstride=downsample_factor, cstride=downsample_factor, alpha=0.9, antialiased=True, linewidth=0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    ax.set_title(title, pad=20)
    return surf
