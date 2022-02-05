from random import randint
from PyQt5.QtGui import QFont, QPen, QColor
from PyQt5.QtWidgets import QApplication
from numpy.random import rand
import pyqtgraph.examples
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import time
import math
import sys
import re

from termcolor import cprint

from pyqtgraph.functions import intColor

"""Data Types: 
Single Value:
1
4
5

Array:
a:1,2,3,4,5,6,7,8
a:5,4,3,2,1,4,2,1

Key-Value: 
a:1,b:2,c:3,d:4
a:4,b:5,c:1,d:0
"""

DEBUG = True


def dprint(input, *args, color="", enabled=False):
    if DEBUG:
        print(input, *args)


class lineGraph(pg.PlotItem):
    def __init__(self, parent, maxLen=200, limits: str = None):
        super().__init__()
        self.setTitle("Plot")
        self._parent = parent
        self.lineDict = {}
        self.all_curves = {}
        self.total_len = maxLen
        self.lastColor = 0
        self.lastMaximum = None
        self.lastMinimum = None

        self.maximum: float = None
        self.minimum: float = None
        self.n_items = 0
        self.startTime = time.time()
        self.legend = pg.LegendItem(offset=(30, 30))
        self.legend.setParentItem(self)
        self.limits = limits

    def add_data(self, item: str):
        self.all_curves[item] = {}
        self.all_curves[item]['y'] = np.zeros(shape=self.total_len)
        self.all_curves[item]['x'] = np.zeros(shape=self.total_len)
        thisColor = intColor(self.lastColor)
        self.lastColor += 100
        self.lineDict[item] = self.plot(
            self.all_curves[item]['x'], self.all_curves[item]['y'], pen=thisColor)
        self.legend.addItem(self.lineDict[item], name=item)
        self.n_items = self.n_items + 1

    def update_data_array(self, update_dict):
        for item in update_dict:
            print(item)
            if item not in self.all_curves:
                self.add_data(item)
            self.all_curves[item]['y'] = np.asarray(update_dict[item])
            dprint('self.all_curves[item][y]: ', str(
                self.all_curves[item]['y']), type(self.all_curves[item]['y']))
            self.all_curves[item]['x'] = np.arange((len(update_dict[item])))
            dprint('self.all_curves[item][x]: ', str(
                self.all_curves[item]['x']), type(self.all_curves[item]['x']))
            self.lineDict[item].setData(
                self.all_curves[item]['x'], self.all_curves[item]['y'])
            max = np.max(self.all_curves[item]['y'])
            min = np.min(self.all_curves[item]['y'])
            if self.limits == "Total":
                if self.lastMaximum == None:
                    self.lastMaximum = max
                if self.lastMinimum == None:
                    self.lastMinimum = min
                if self.lastMinimum > min:
                    self.lastMinimum = min
                if self.lastMaximum < max:
                    self.lastMaximum = max
                self.setYRange(self.lastMinimum, self.lastMaximum)

    def update_data_kv(self, update_dict):
        timestamp = time.time() - self.startTime
        for item in update_dict:

            if item not in self.all_curves:
                self.add_data(item)
            self.all_curves[item]['y'][-1] = update_dict[item]
            self.all_curves[item]['x'][-1] = timestamp
            self.all_curves[item]['y'] = np.roll(self.all_curves[item]['y'], 1)
            self.all_curves[item]['x'] = np.roll(self.all_curves[item]['x'], 1)

            if self.limits == "Total":
                if self.lastMaximum == None:
                    self.lastMaximum = update_dict[item]
                if self.lastMinimum == None:
                    self.lastMinimum = update_dict[item]
                if update_dict[item] > self.lastMaximum:
                    self.lastMaximum = update_dict[item]
                    self.setYRange(self.lastMinimum, self.lastMaximum)
                if update_dict[item] < self.lastMinimum:
                    self.lastMinimum = update_dict[item]
                    self.setYRange(self.lastMinimum, self.lastMaximum)
            self.lineDict[item].setData(
                self.all_curves[item]['x'], self.all_curves[item]['y'])


class graphWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None, targets=None, maxLen=200):
        super().__init__()
        self.graph_type = None
        self.targets = None
        self.maxLen = maxLen
        self.n_lines = 0
        self.current_dict = {}
        self.str_buffer = ""
        self.started = False

    def updateData(self, u_dict: dict):
        if self.graph_type == 'key-value':
            self.graph.update_data_kv(u_dict)
        elif self.graph_type == 'array':
            self.graph.update_data_array(u_dict)

    def parse_array(self, input: str):  # example input = "a:1,2,3,4,5;b=5,4,3,2,1"
        input = input.replace("\n", "")
        input = input.replace(" ", "")
        # example tokens = ["a:1,2,3,4,5", "b:5,4,3,2,1"]
        tokens = re.split(r'[;|\t]', input)
        for token in tokens:
            # example sub_tokens = ["a", "1,2,3,4,5"]
            sub_tokens = re.split(r'[=:]', token)
            dprint("subTokens:", sub_tokens)
            if self.targets != None:
                if sub_tokens[0] not in self.targets:
                    dprint(f"Key: {sub_tokens[0]} not in target keys!")
                    continue
            if len(sub_tokens) > 1:  # subtokens could have a key and value
                vals = []
                # example values = ["1","2","3","4","5"]
                values = re.split(r'[,]', sub_tokens[1])
                for value in values:
                    try:
                        v = float(value)  # example v = 1
                        vals.append(v)
                    except:
                        pass
                # example vals = [1,2,3,4,5]
                self.current_dict[sub_tokens[0]] = vals
            else:
                dprint("Parse Error:", token)
        dprint("current dict:", self.current_dict)

    def parse_kv(self, input: str):
        input = input.replace(" ", "")
        tokens = re.split(r'[,;|\t]', input)
        for token in tokens:
            pairs = re.split(r'[:=]', token, 1)
            if len(pairs) > 1:
                if self.targets != None:
                    if pairs[0] not in self.targets:
                        print(f"Key: {tokens[0]} not in target keys!")
                        continue
                key = pairs[0].replace(" ", "")
                value = pairs[1].replace(" ", "")
                try:
                    self.current_dict[key] = float(value)
                except:
                    continue

    def update(self, input: str):
        if self.graph_type == None:
            dprint("ERROR: NO GRAPH STARTED")
            return
        dprint(self.graph_type)
        self.str_buffer = self.str_buffer + input
        if "\n" in self.str_buffer:
            if self.graph_type == "key-value":
                self.parse_kv(self.str_buffer)
            if self.graph_type == "array":
                self.parse_array(self.str_buffer)
            if self.graph_type == "paused":
                return
            self.str_buffer = ""
            self.updateData(self.current_dict)

    def pause(self):
        self.prev_type = self.graph_type
        dprint("Paused", self.prev_type)
        self.graph_type = "paused"

    def resume(self):
        if self.graph_type == "paused":
            dprint("Resuming", self.prev_type)
            self.graph_type = self.prev_type

    def clear_plot(self):
        dprint("clearing...")
        if self.graph_type != None:
            print("CLEARED")
            self.graph.all_curves = {}
            self.graph.lineDict = {}
            self.graph.clearPlots()

            self.removeItem(self.graph)
            self.graph = None

            self.targets = None
            self.graph_type = None

            self.current_dict = {}

    def add_kv_graph(self, targets: str = None, len=100, limits=None):
        print('self.type: ', str(self.graph_type), type(self.graph_type))
        if targets:
            targets = targets.replace(" ", "")
            self.targets = re.split(r'[,]', targets)
            dprint("TARGETS: ", targets)
        if self.graph_type == None:
            self.graph_type = 'key-value'
            self.graph = lineGraph(self, maxLen=len, limits=limits)
            self.addItem(self.graph)

    def add_array_graph(self, targets=None, len=100):
        print('self.type: ', str(self.graph_type), type(self.graph_type))
        if self.graph_type == None:
            dprint("Adding Array Graph:")
            self.graph_type = 'array'
            if targets:
                targets = targets.replace(" ", "")
                self.targets = re.split(r'[,]', targets)
                dprint("TARGETS: ", targets)
            else:
                targets = None
            self.graph = lineGraph(self, len)
            self.addItem(self.graph)


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
        self.numb_elements: int = 0
        self.str_buffer: str = ""
        self.limits = "Window"
        self.paused = False
        self.started = False
        self.plot = pg.PlotItem()

        self.elements = {}
        self.start_time: float = None
        self.separators = [',', ';', '\t', '\n', '|']
        self.assignment_operators = ['=', ':']
        self.prev_color = 0
        self.legend = pg.LegendItem(offset=(30, 30))
        self.legend.setParentItem(self.plot)
        self.addItem(self.plot)

    def begin(self, type="Key-Value", targets: list = None, max_points=100, limits="Window"):
        self.plot_type = type
        self.targets = targets
        self.max_points = max_points
        self.limits = limits
        self.started = True
        self.paused = False
        self.start_time = time.time()

    def pause(self):
        self.paused = True
        return

    def resume(self):
        self.paused = False

        return

    def reset(self):
        #self.elements = {}
        self.plot.clearPlots()
        self.elements = {}

        return

    def end(self):
        return

    def update(self, input: str):
        if not self.started or self.paused:
            return
        self.str_buffer += input
        if '\n' not in self.str_buffer:
            return

        if self.plot_type == 'Key-Value':
            self.parse_data_kv(self.str_buffer)
        elif self.plot_type == "Array":
            pass

        for element in self.elements:
            self.elements[element]['line'].setData(
                self.elements[element]['x'], self.elements[element]['y'])
        self.str_buffer = ""
        return

    def add_element(self, element_name: str):
        startTs = time.time() - self.start_time
        self.elements[element_name] = {}
        self.elements[element_name]['x'] = np.zeros(shape=self.max_points)
        self.elements[element_name]['x'].fill(startTs)

        self.elements[element_name]['y'] = np.zeros(shape=self.max_points)
        self.elements[element_name]['line'] = self.plot.plot(
            self.elements[element_name]['x'], self.elements[element_name]['y'], pen=intColor(self.prev_color))
        self.prev_color += 50
        self.legend.addItem(
            self.elements[element_name]['line'], name=element_name)
        return

    def parse_data_kv(self, input: str):
        tokens = char_split(input, self.separators)
        # print(tokens)
        timestamp = time.time() - self.start_time
        for token in tokens:
            if not str_contains_elements(token, self.assignment_operators):
                continue
            kv = char_split(token, self.assignment_operators)
            if len(kv) == 1:
                cprint(f"NO VALUE: {kv}", 'yellow')
                continue
            if self.targets and (kv[0] not in self.targets):
                cprint(f"NOT IN TARGETS: {kv}", 'yellow')
                continue
            # Convert to value

            key = kv[0]
            try:
                value: float = float(kv[1].replace(" ", "").replace("\t", ""))
            except ValueError:
                cprint(f"NOT A VALUE: {kv[1]}", 'yellow')
                continue

            if key not in self.elements:
                self.add_element(key)

            self.elements[key]['x'][-1] = timestamp
            self.elements[key]['y'][-1] = value
            self.elements[key]['x'] = np.roll(self.elements[key]['x'], 1)
            self.elements[key]['y'] = np.roll(self.elements[key]['y'], 1)


def _test_plot():
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
        start_time = time.time()
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
    # for arg in sys.argv[1:]:
    #     print("arg: ", arg)
    #     if arg == "-t":
    #         pyqtgraph.examples.run()
    #         quit()
    #     elif arg == '-h':
    #         print("HELP")
    #         quit()
    #     elif arg == '-b':
    #         test_graph('b')
    #         quit()
    # test_graph('h')
