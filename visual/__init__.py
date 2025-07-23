from .read import read
from matplotlib import animation

def visualize(path, save_path):
    gcode = read(path, no_travel=True)
    writer = animation.FFMpegWriter(fps=10, extra_args=["-crf", "0"], bitrate=1000000)
    # matplotlib is silly and interval=0 is ABSOLUTELY UNACCEPTABLE
    gcode.animated('b', save_file=save_path, show=False, interval=0.000000000000000001, writer=writer, frames=100)
