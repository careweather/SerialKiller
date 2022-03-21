import time

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication
from pyqtgraph.functions import intColor
from sk_tools import *

def char_split(input: str, chars: list, keep_seps=False) -> list:
    r_list = []
    buff = ""
    for i in input:
        if i in chars:
            if keep_seps:
                buff += i
            r_list.append(buff)
            buff = ""
        else:
            buff += i
    if buff:
        r_list.append(buff)
    return r_list

def str_contains_elements(input: str, chars: list) -> bool:
    for i in input:
        if i in chars:
            return True
    return False


class Plot_Widget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent
        self.plot_type: str = None
        self.targets: list = None
        self.max_points: int = 100
        self.str_buffer: str = ""
        self.limits = "Window"
        self.paused = False
        self.started = False
        self.plot:pg.PlotItem = pg.PlotItem()
        self.elements = {}
        self.start_time: float = None
        self.separators = [',', ';', '\t', '\n', '|', ']']
        self.assignment_operators = ['=', ':']
        self.prev_color = 0
        self.max_value = 0
        self.min_value = 0

    def begin(self, type="Key-Value", targets: list = None, max_points=100, limits="Window"):
        if isinstance(targets, str):
            self.targets = targets.split(",")
        else:
            self.targets = targets

        self.prev_color = 0
        self.plot_type = type

        self.max_points = max_points
        self.limits = limits
        self.started = True
        self.paused = False
        
        self.start_time = time.perf_counter()
        self.legend = pg.LegendItem(offset=(30, 30))
        self.legend.setParentItem(self.plot)
        vprint("STARTING PLOT: ", self.plot_type, self.targets, self.max_points, self.limits)
        self.addItem(self.plot)

    def pause(self):
        vprint("Plot Paused")
        self.paused = True

    def resume(self):
        vprint("Plot Resumed")
        self.paused = False

    def reset(self):
        if not self.started:
            return
        vprint("Resetting Plot")
        self.prev_color = 0
        self.min_value = 0
        self.max_value =0

        self.legend.clear()
        self.str_buffer = ""
        self.plot.clearPlots()
        self.removeItem(self.plot)
        self.elements = {}
        self.started = False
        self.plot.enableAutoScale()

    def end(self): #TODO 
        return

    def update(self, input: str):
        if not self.started or self.paused:
            return
        self.str_buffer += input
        if '\n' not in self.str_buffer:
            return
        elements = self.str_buffer.split("\n", 1)
        if len(elements) > 1:
            self.str_buffer = elements[1]
        else:
            self.str_buffer = ""

        if self.plot_type == 'Key-Value':
            self.parse_data_kv(elements[0])

        elif self.plot_type == "Array": # TODO
            pass

        for element in self.elements:
            self.elements[element]['line'].setData(self.elements[element]['x'], self.elements[element]['y'])

        if self.limits == "Max":
            self.plot.setYRange(self.min_value, self.max_value)

    def add_element(self, element_name: str, start_value: float = 0):
        if not element_name:
            return
        startTs = time.perf_counter() - self.start_time
        self.elements[element_name] = {}
        self.elements[element_name]['x'] = np.zeros(shape=self.max_points)
        self.elements[element_name]['x'].fill(startTs)

        self.elements[element_name]['y'] = np.zeros(shape=self.max_points)
        self.elements[element_name]['y'].fill(start_value)
        self.elements[element_name]['line'] = self.plot.plot(
            self.elements[element_name]['x'], self.elements[element_name]['y'], pen=intColor(self.prev_color))
        self.prev_color += 50
        self.legend.addItem(self.elements[element_name]['line'], name=element_name)

    def parse_data_kv(self, input: str):
        input = input.replace("\r", "")
        tokens = char_split(input, self.separators)
        timestamp = time.perf_counter()- self.start_time
        for token in tokens:
            if not str_contains_elements(token, self.assignment_operators):
                continue
            kv = char_split(token, self.assignment_operators)
            if len(kv) == 1:
                #cprint(f"NO VALUE: {kv}", 'yellow')
                continue
            if self.targets and (kv[0] not in self.targets):
                continue

            key = kv[0]
            if not key:
                continue
            try:
                value: float = float(kv[1].replace(" ", "").replace("\t", ""))
            except ValueError:
                continue

            if key not in self.elements:
                self.add_element(key, value)

            self.elements[key]['x'][-1] = timestamp
            self.elements[key]['y'][-1] = value
            self.elements[key]['x'] = np.roll(self.elements[key]['x'], 1)
            self.elements[key]['y'] = np.roll(self.elements[key]['y'], 1)
            if value > self.max_value:
                self.max_value = value
            elif value < self.min_value:
                self.min_value = value


def _test_plot():
    import sys
    app = QApplication(sys.argv)
    plot = Plot_Widget()
    import math
    import random

    global indx_val
    indx_val = 0

    def update_kv():
        global indx_val
        test_str = f"A:{math.sin(indx_val/ 10) * 5 + random.random()},B:{round(random.random(),4)},c={random.randint(-2,5)}, d={math.cos(indx_val / 10) * 5}\n"
        indx_val = indx_val + 1
        start_time = time.perf_counter()
        plot.update(test_str)
        run_time = time.time() - start_time
        print(run_time)

    def pause_plot():
        if plot.paused:
            plot.reset()

            plot.resume()
        else:
            plot.pause()

    timer = pg.QtCore.QTimer()
    pauseTimer = pg.QtCore.QTimer()

    plot.begin(max_points=500)
    timer.timeout.connect(update_kv)
    pauseTimer.timeout.connect(pause_plot)
    pauseTimer.start(2000)
    app.processEvents()

    timer.start(10)
    plot.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    _test_plot()
