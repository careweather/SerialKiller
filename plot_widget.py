import time

import numpy as np
import pyqtgraph as pg
import PyQt5.QtCore
from pyqtgraph.functions import intColor
from termcolor import cprint
from sk_tools import vprint


def char_split(input: str, chars: list, keep_seps=False) -> list:
    r_list = []
    buff = ""
    for i in input:
        if i in chars:
            if keep_seps:
                buff += i
            if buff:
                r_list.append(buff)
            buff = ""
        else:
            buff += i
    if buff:
        r_list.append(buff)
    return r_list

def str_get_number(input: str):
    try:
        result = float(input)
        return result
    except ValueError:
        return None


class Plot_Widget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent
        self.plot_type: str = None
        #self.targets: list = None
        self.targets = {}
        self.max_points: int = 100
        self.str_buffer: str = ""
        self.limits = []
        self.paused = False
        self.started = False
        self.plot: pg.PlotItem = pg.PlotItem()
        self.elements = {}
        self.start_time: float = None
        self.separators = [',', ';', '\t', '\n', '|', ']', '[', ' ', '=', ':']
        self.prev_color = 0
        #self.setMinimumHeight(0)


    def begin(self, type="Key-Value", targets: list = None, max_points=100, limits: list = [], separators: list = None, ref_lines: list = None):
        if separators:
            self.separators = separators


        self.targets = {}
        if isinstance(targets, str):
            targetList = char_split(targets, [','])
            for item in targetList:
                item: str 
                if "*" in item: 
                    itemtokens = item.split("*")
                    if len(itemtokens) > 1:
                        self.targets[itemtokens[0]] = {'m': str_get_number(itemtokens[1])}
                if "/" in item: 
                    itemtokens = item.split("/")
                    if len(itemtokens) > 1:
                        self.targets[itemtokens[0]] = {'m': 1.00 / str_get_number(itemtokens[1])}

                else: 
                    self.targets[item] = {"m": 1}
        else:
            self.targets = targets

        vprint("TARGETS: ", self.targets)

        if ref_lines:
            if isinstance(ref_lines, (float, int)):
                ref_lines = [ref_lines]
            for line in ref_lines:
                self.plot.addLine(y=line)
                #self.plot.addLine(y=line, pen=pg.mkPen(style=PyQt5.QtCore.Qt.DashLine))

        self.prev_color = 0
        self.plot_type = type

        self.max_points = int(max_points)
        self.limits = limits
        self.started = True
        self.paused = False
        self.elements = {}

        self.start_time = time.perf_counter()
        self.legend = pg.LegendItem(offset=(30, 30))
        self.legend.setParentItem(self.plot)
        vprint(f"[PLOT] STARTING {self.plot_type}\n\ttarget:\t{self.targets}\n\tlen:\t{self.max_points}\n\tseps:\t{self.separators}\n\tlines:\t{ref_lines}", color="green")
        vprint(f"\tlimits: {self.limits}", color="green")

        
        self.addItem(self.plot)

        #self.plot.min

        #self.plot.setMinimumHeight(100.0)

        #size = self.plot.minimumSize()
        #print(size.height(), size.width(), self.plot.height(), self.plot.width(), self.height(), self.width())

    def pause(self):
        vprint("[PLOT] Paused")
        self.paused = True

    def resume(self):
        vprint("[PLOT] Resumed")
        self.paused = False

    def reset(self):
        if not self.started:
            return
        vprint("[PLOT] Reset")
        self.prev_color = 0
        self.legend.clear()
        self.str_buffer = ""
        self.plot.clearPlots()

        self.removeItem(self.plot)

        self.plot: pg.PlotItem = pg.PlotItem()

        self.elements = {}
        self.started = False
        #self.plot.enableAutoScale()

    def end(self):  # TODO
        self.reset() 
        return

    def update(self, input: str, wait_for_newline=True):
        if not self.started or self.paused:
            return
        self.str_buffer += input
        if '\n' not in self.str_buffer and wait_for_newline:
            return

        lines = self.str_buffer.split("\n")
        if len(lines) > 1:
            self.str_buffer = lines.pop(-1)  # Last part did not have a newline
        else:
            self.str_buffer = ""

        for line in lines:
            line = line.replace("\r", '')
            if not line:
                continue
            if self.plot_type == 'Key-Value':
                self.parse_data_key_value(line)
            elif self.plot_type == "Single-Array":
                self.parse_data_single_array(line)
            elif self.plot_type == 'Single-Value':
                self.parse_data_single_value(line)
            elif self.plot_type == "Key-Array":
                self.parse_data_key_array(line)

        for element in self.elements:
            self.elements[element]['line'].setData(self.elements[element]['x'], self.elements[element]['y'])

        if self.limits:
            if len(self.limits) == 2:
                self.plot: pg.PlotItem
                self.plot.setYRange(self.limits[0], self.limits[1])

    def add_element(self, element_name: str, start_x: float = 0, start_y: float = 0):
        if not element_name:
            return

        mval = 1
        if element_name in self.targets:
            mval = self.targets[element_name]['m']
        startTs = time.perf_counter() - self.start_time
        self.elements[element_name] = {}
        self.elements[element_name]['m'] = mval
        #self.elements[element_name]['x'] = np.zeros(shape=self.max_points)
        self.elements[element_name]['x'] = np.empty(shape=self.max_points)
        self.elements[element_name]['x'].fill(start_x)

        #self.elements[element_name]['y'] = np.empty(shape=self.max_points)
        self.elements[element_name]['y'] = np.zeros(shape=self.max_points)
        self.elements[element_name]['y'].fill(start_y)
        self.elements[element_name]['line'] = self.plot.plot(self.elements[element_name]['x'], self.elements[element_name]['y'], pen=intColor(self.prev_color))
        self.prev_color += 50
        self.legend.addItem(self.elements[element_name]['line'], name=element_name)

    def parse_data_single_value(self, input: str):
        timestamp = time.perf_counter() - self.start_time
        tokens = char_split(input, self.separators)
        value = None

        vprint(f"\n[PLOT SV] TOKENS: {tokens}", color="cyan")

        for token in tokens:
            value = str_get_number(token)
            if value:
                break

        if value == None:
            return

        if "a" not in self.elements:
            self.add_element("a", time.perf_counter() - self.start_time, value)

        vprint(f"[PLOT SV] VALUES: {tokens}", color="green")
        self.elements["a"]['x'][-1] = timestamp
        self.elements["a"]['y'][-1] = value
        self.elements["a"]['x'] = np.roll(self.elements["a"]['x'], 1)
        self.elements["a"]['y'] = np.roll(self.elements["a"]['y'], 1)

    def parse_data_key_value(self, input: str):
        tokens = char_split(input, self.separators)
        vprint(f"\n[PLOT KV] TOKENS: {tokens}", color='yellow', end="\t")  # Debug
        timestamp = time.perf_counter() - self.start_time
        prev_key: str = None
        while tokens:
            token = tokens.pop(0)
            if not token:
                continue
            if not prev_key:
                if self.targets:
                    if token in self.targets:
                        prev_key = token
                else:
                    prev_key = token
                    if str_get_number(token) != None:
                        continue
                continue
            else:
                value = str_get_number(token)
                if value == None:
                    continue

            vprint(f"\n[PLOT KV] PAIR: {prev_key}:{value}", color='green', sep='=', end="\t")  # Debug

            if prev_key not in self.elements:
                self.add_element(prev_key, time.perf_counter() - self.start_time, value)

            self.elements[prev_key]['x'][-1] = timestamp
            self.elements[prev_key]['y'][-1] = value * self.elements[prev_key]['m']
            self.elements[prev_key]['x'] = np.roll(self.elements[prev_key]['x'], 1)
            self.elements[prev_key]['y'] = np.roll(self.elements[prev_key]['y'], 1)


            prev_key = None
        vprint("\n")  # Debug

    def parse_data_single_array(self, input: str):
        tokens = char_split(input, self.separators)
        vprint(f"\n[PLOT SA] TOKENS: {tokens}", color='yellow', end="\t")  # Debug
        index = 0

        if len(tokens < 10):
            return
        for token in tokens:
            value = str_get_number(token)
            if value == None:
                return
                continue
            if index > self.max_points - 1:
                return
            if "a" not in self.elements:
                self.add_element("a", 0, value)

            self.elements['a']['x'][index] = index
            self.elements['a']['y'][index] = value
            index += 1

        self.elements['a']['x'] = self.elements['a']['x'][0:index]
        self.elements['a']['y'] = self.elements['a']['y'][0:index]

    def parse_data_key_array(self, input: str):
        input = input.replace(" ", "")
        elems = char_split(input, [':', '='])

        if len(elems) < 2:
            vprint("[PLOT KA] BAD:", elems, color='yellow')
            return
        name = elems[0]
        tokens = char_split(elems[1], self.separators)
        vprint(tokens, color='yellow')
        index = 0
        for token in tokens:
            value = str_get_number(token)
            if value == None:
                continue
            if index > self.max_points - 1:
                return
            if name not in self.elements:
                self.add_element(name, 0, value)

            self.elements[name]['x'][index] = index
            self.elements[name]['y'][index] = value
            index += 1

        self.elements[name]['x'] = self.elements[name]['x'][0:index]
        self.elements[name]['y'] = self.elements[name]['y'][0:index]



if __name__ == '__main__':
    from test_plot_widget import _test_plot
    _test_plot()
