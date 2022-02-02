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

def dprint(input, *args, color = "", enabled = False): 
    if DEBUG: 
        print(input, *args)
    
class lineGraph(pg.PlotItem): 
    def __init__(self, parent, maxLen = 200):
        super().__init__()
        self.setTitle("Plot")
        self._parent = parent
        self.lineDict = {}
        self.all_curves = {}
        self.total_len = maxLen
        self.lastColor = 0
        self.lastMaximum = None
        self.lastMinimum = None
        self.n_items = 0
        self.startTime = time.time()
        self.legend = pg.LegendItem(offset=(30,30))
        self.legend.setParentItem(self)
        
    def add_data(self, item: str):
        self.all_curves[item] = {}
        self.all_curves[item]['y'] = np.zeros(shape = self.total_len)
        self.all_curves[item]['x'] = np.zeros(shape = self.total_len)
        thisColor = intColor(self.lastColor)
        self.lastColor += 100
        self.lineDict[item]= self.plot(self.all_curves[item]['x'],self.all_curves[item]['y'], pen=thisColor)
        self.legend.addItem(self.lineDict[item], name=item)
        self.n_items = self.n_items + 1 

    def update_data_array(self, update_dict): 
        for item in update_dict: 
            print(item)
            if item not in self.all_curves: 
                self.add_data(item)
            self.all_curves[item]['y'] = np.asarray(update_dict[item])
            dprint('self.all_curves[item][y]: ' , str(self.all_curves[item]['y']), type(self.all_curves[item]['y']))
            self.all_curves[item]['x'] = np.arange((len(update_dict[item])))
            dprint('self.all_curves[item][x]: ' , str(self.all_curves[item]['x']), type(self.all_curves[item]['x']))
            self.lineDict[item].setData(self.all_curves[item]['x'], self.all_curves[item]['y'])
            max = np.max(self.all_curves[item]['y'])
            min = np.min(self.all_curves[item]['y'])
            if self.lastMaximum == None: 
                self.lastMaximum = max 
            if self.lastMinimum == None: 
                self.lastMinimum = min
            if self.lastMinimum > min: 
                self.lastMinimum = min
            if self.lastMaximum < max: 
                self.lastMaximum = max 
            self.setYRange(self.lastMinimum, self.lastMaximum)
            #print(max)

    def update_data_kv(self, update_dict):
        timestamp = time.time() - self.startTime
        for item in update_dict:
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
            if item not in self.all_curves: 
                self.add_data(item)
            self.all_curves[item]['y'][-1] = update_dict[item]
            self.all_curves[item]['x'][-1] = timestamp
            self.all_curves[item]['y'] = np.roll(self.all_curves[item]['y'], 1)
            self.all_curves[item]['x'] = np.roll(self.all_curves[item]['x'], 1)
            self.lineDict[item].setData(self.all_curves[item]['x'], self.all_curves[item]['y'])
           
    
class graphWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent = None, targets = None, maxLen = 200):
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

    def parse_array(self, input:str):               #example input = "a:1,2,3,4,5;b=5,4,3,2,1"
        input = input.replace("\n", "")
        input = input.replace(" ", "")
        tokens = re.split(r'[;|\t]', input)         #example tokens = ["a:1,2,3,4,5", "b:5,4,3,2,1"]
        for token in tokens: 
            sub_tokens = re.split(r'[=:]', token)   #example sub_tokens = ["a", "1,2,3,4,5"]
            dprint("subTokens:", sub_tokens)
            if self.targets != None: 
                if sub_tokens[0] not in self.targets: 
                    dprint(f"Key: {sub_tokens[0]} not in target keys!")
                    continue
            if len(sub_tokens) > 1: #subtokens could have a key and value 
                vals = []
                values = re.split(r'[,]', sub_tokens[1]) #example values = ["1","2","3","4","5"]
                for value in values: 
                    try: 
                        v = float(value) #example v = 1
                        vals.append(v)
                    except: 
                        pass 
                self.current_dict[sub_tokens[0]] = vals #example vals = [1,2,3,4,5]
            else: 
                dprint("Parse Error:", token)
        dprint("current dict:", self.current_dict) 

    def parse_kv(self, input:str): 
        input = input.replace(" ", "")
        tokens = re.split(r'[,;|\t]', input)
        for token in tokens:
            pairs = re.split(r'[:=]', token, 1)
            if len(pairs)> 1:
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
                
    def update(self, input:str): 
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
            
    def add_kv_graph(self, targets:str = None, len = 100): 
        print('self.type: ' , str(self.graph_type), type(self.graph_type))
        if targets: 
            targets = targets.replace(" ", "")
            self.targets = re.split(r'[,]', targets)
            dprint("TARGETS: ", targets)
        if self.graph_type == None:
            self.graph_type = 'key-value'
            self.graph = lineGraph(self, maxLen=len)
            self.addItem(self.graph)

    def add_array_graph(self, targets = None, len = 100): 
        print('self.type: ' , str(self.graph_type), type(self.graph_type))
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

sine_val = 0
def test_graph(graph_type = 'h'):
    import random
    import math

    test_dict = {}
    print("RUNNING GRAPH TEST", graph_type)
    app = QApplication(sys.argv)
    win = graphWidget()

    def update_array(): 
        rand1 = random.randint(0,3)
        rand2 = random.randint(0,4)
        test_val = f"a:1,2,{rand1 + rand2},4,{rand1*rand2}; b=5,4,{rand1*2},2,1\n"
        win.update(test_val)
        
    def update_test(): 
        global sine_val
        sine_val = sine_val + .1 
        noise = random.uniform(-.6,.6)
        nF = math.sin(sine_val*noise)*.1
        test_dict['x'] = 1+ math.sin(sine_val)
        test_dict['s'] = (1 + math.sin(sine_val)) + (noise*nF)
        win.updateData(test_dict)
    
    timer = pg.QtCore.QTimer()
    if graph_type == 'b': 
        win.add_array_graph()
        timer.timeout.connect(update_array)
    else: 
        win.add_kv_graph()
        timer.timeout.connect(update_test)
        app.processEvents()

    timer.start(100)
    win.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    for arg in sys.argv[1:]: 
        print("arg: ", arg)
        if arg == "-t": 
            pyqtgraph.examples.run()
            quit()
        elif arg == '-h': 
            print("HELP")
            quit()
        elif arg == '-b': 
            test_graph('b')
            quit()
    test_graph('h')

