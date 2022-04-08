
import time

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication
from pyqtgraph.functions import intColor
from termcolor import cprint

from plot_widget import Plot_Widget


def _test_plot():
    import sys
    app = QApplication(sys.argv)
    plot = Plot_Widget()
    import math
    import random

    global indx_val
    indx_val = 0

    UPDATE_TYPE = "SA"

    def update_kv():
        global indx_val
        test_str = f"A:{round((math.sin(indx_val/ 10) * 5), 4)},"
        test_str += f"J,  " # Key with no value 
        test_str += f"B:{round(random.random(),4)},"
        test_str += "1234," # Value with no key 
        test_str += f"c {random.randint(-2,5)}, "
        test_str += f"d={math.cos(indx_val / 10) * 5}"
        indx_val = indx_val + 1
        start_time = time.perf_counter()
        plot.update(test_str + "\n")
        run_time = (time.perf_counter() - start_time) * 1000
        print(f"Input: <{test_str}>\tUpdate Time:{run_time}")

    def update_sa():
        test_str = "x:"
        for i in range(50):
            my_numb = random.random() * i
            test_str += f"{round(my_numb, 2)},"
        start_time = time.perf_counter()
        plot.update(test_str + "\n")
        run_time = (time.perf_counter() - start_time) * 1000
        print(f"Input: <{test_str}>\tUpdate Time:{run_time} ms")

    def pause_plot():
        if plot.paused:
            plot.reset()
            plot.resume()
        else:
            plot.pause()

    timer = pg.QtCore.QTimer()
    pauseTimer = pg.QtCore.QTimer()

    

    if UPDATE_TYPE == "SA":
        update_func = update_sa
        plot.begin("Single-Array", max_points=100, ref_lines=[0,1])

    else:
        update_func = update_kv
        plot.begin(max_points=50, targets=['A', 'B', 'c', 'd'], ref_lines=[5])



    timer.timeout.connect(update_func)
    #pauseTimer.timeout.connect(pause_plot)
    #pauseTimer.start(2000)
    app.processEvents()

    timer.start(50)
    plot.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    _test_plot()
