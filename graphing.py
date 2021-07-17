from PyQt5.QtWidgets import QApplication
import pyqtgraph.examples
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import time
import math
import sys
import re

# pyqtgraph.examples.run()

# quit()
# import initExample ## Add path to library (just for examples; you do not need this)

"""
Data Types: 
Bulk: a:1,2,3,4,5,6,7,8
Stream: a:1,b:2,c:3,d:4

"""


token_splits = r"[;,\t]"
value_splits = r"[:=]"

testStrs = [
    'a=1;b=200;c=333;d=444',
    'a:1,b:2,c:3,d=4,e',
    'b=x,d=b,a=-1,e=-5',
    'a=1f,b=22f,c=3,d=4a,e=-5d',
    'dad = mad'
]

sines = [64, 67, 70, 73, 76, 80, 83, 86,
         88, 91, 94, 97, 100, 102, 105, 107,
         109, 111, 113, 115, 117, 119, 120, 122,
         123, 124, 125, 126, 127, 127, 128, 128,
         128, 128, 128, 127, 127, 126, 125, 124,
         123, 122, 120, 119, 117, 115, 113, 111,
         109, 107, 105, 102, 100, 97, 94, 91,
         88, 86, 83, 80, 76, 73, 70, 67,
         64, 61, 58, 55, 52, 48, 45, 42,
         40, 37, 34, 31, 28, 26, 23, 21,
         19, 17, 15, 13, 11, 9, 8, 6,
         5, 4, 3, 2, 1, 1, 0, 0,
         0, 0, 0, 1, 1, 2, 3, 4,
         5, 6, 8, 9, 11, 13, 15, 17,
         19, 21, 23, 26, 28, 31, 34, 37,
         40, 42, 45, 48, 52, 55, 58, 61, ]


plotTests = [
    'a:0,b:0,c:0',
    'a:1,b:0,c:5',
    'a:2,b:0,c:1',
    'a:3,b:0,c:5',
    'a:4,b:0,c:1',
    'a:5,b:0,c:5',
    'a:4,b:0,c:1',
    'a:3,b:0,c:0',
    'a:2,b:0,c:0',
    'a:1,b:0,c:0',
    'a:0,b:0,c:0',
]

bulkTest = [
    "a:1,2,3,4,5,6,7,8,9,10",
    "a:0,2,4,6,8,10,8,6,4,2",
    "a:1,2,3,4,5,6,7,8,9,10",
    "a:1,2,3,4,5,6,7,8,9,10",
            ]

plotTests = []
d = 0
for v in sines:
    d += 1
    st = f"a:{v},b:{-v+64},c:{20*math.sin(d/6.28)}"
    plotTests.append(st)



verbose = True
debug = True

def dprint(input, *args): # for debugging the program
    if debug:
        print(input, *args)


def vprint(input, *args): # verbose prints stuff to terminal 
    if verbose:
        print(input, *args)

TYPE_NONE = 0
TYPE_STREAM = 1 
TYPE_BULK = 2 

class graphWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent):
        super().__init__()
        self.graph_type = TYPE_NONE

        self.ptr = 0
        self.n_lines = 0
        self.previous_dict = {}
        self.current_dict = {}
        self.data_dict = {}
        self.curve_dict = {}
        self.started = False
        self.v_list = []

    def startLineGraph(self):
        print("Starting Line Graph")
        self.lineGraph = self.addPlot()
        self.graph_type = TYPE_STREAM

    def startStreamGraph(self, targets = ""):
        print("Starting Stream Graph")
        self.lineGraph = self.addPlot()
        self.graph_type = TYPE_STREAM
        self.targets = targets
        self.data_list = []


    def updateStreamGraph(self, input): 
        dprint('input: ' , str(input), type(input))


    def startBulkGraph(self, targets = ""): 
        self.graph_type = TYPE_BULK
        self.lineGraph = self.addPlot()
        self.targets = targets 
        self.data_list = []


    def updateBulkGraph(self, input):
        dprint('input: ' , str(input), type(input))
        
    def setKeys(self, keys=""):
        pass

    def update(self, input):
        if self.started == False:
            self.startLineGraph()
        self.parseLineData(input)
        self.updateLineData()
        self.updateLineGraph()

    def parseBulkData(self, input): 
        tokens = re.split(r'[:;=]', input)
        #print('tokens: ' , str(tokens), type(tokens))
        key = tokens[0]
        #print('key: ' , str(key), type(key))

        vals = tokens[-1]
        print('vals: ' , str(vals), type(vals))
        try:
            
            vals = re.split(r'[,]', vals)
            self.v_list = []
            for val in vals:
                try:
                    self.v_list.append(float(val))
                except Exception as E:
                    print(E)
            print('v_list: ' , str(self.v_list), type(self.v_list))
        except Exception as E:
            print(E) 
        if not self.started:
            self.startLineGraph()
        self.lineGraph.clear()
        self.lineGraph.plot(self.v_list)

    def parseLineData(self, input):
        tokens = re.split(token_splits, input)
        for token in tokens:
            if token:
                pairs = re.split(value_splits, token)
                if len(pairs) == 2:
                    try:
                        self.current_dict[pairs[0]] = float(pairs[1])
                    except:
                        pass
                else:
                    print("Wrong Pair Numbers, found: ", len(pairs))

    def addNewLine(self, key):
        self.n_lines += 1
        self.data_dict[key] = np.zeros(256)
        self.curve_dict[key] = self.lineGraph.plot(
            self.data_dict[key], pen=self.n_lines*2)
        label = pg.TextItem(key, color=self.n_lines*2,
                            anchor=(self.n_lines, -1))
        label.setTextWidth(25)
        self.lineGraph.addItem(label)
        # self.addItem(Label)

    def updateLineData(self):
        for key in self.current_dict.keys():
            if key not in self.data_dict.keys():
                self.addNewLine(key)
            self.data_dict[key][-1] = self.current_dict[key]
            self.data_dict[key] = np.roll(self.data_dict[key], -1)

    def testSingleBulk(self): 
        self.ptr += 1
        if (self.ptr > len(bulkTest)-1):
            self.ptr = 0
        print('self.ptr: ' , str(self.ptr), type(self.ptr))
        self.parseBulkData(bulkTest[self.ptr])


    def testSingleLine(self):
        if (self.ptr > len(plotTests)-1):
            self.ptr = 0
        self.parseLineData(plotTests[self.ptr])
        self.updateLineData()
        self.updateLineGraph()

    def testUpdate(self):
        self.startLineGraph()
        for line in plotTests:
            self.parseLineData(line)
            self.updateLineData()
            self.updateLineGraph()

    def updateLineGraph(self):
        for element in self.data_dict:
            self.curve_dict[element].setData(self.data_dict[element][:-1])
        self.ptr += 1


runExamples = 1
bulks = True

def exe():
    if not bulks: 
        app = QApplication(sys.argv)
        win = graphWidget(app)
        win.show()
        win.startLineGraph()
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(win.testSingleLine)
        timer.start((1/80)*1000)
        # win.testUpdate()
        status = app.exec_()
        sys.exit(status)
    else: 
        app = QApplication(sys.argv)
        win = graphWidget(app)
        win.show()
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(win.testSingleBulk)
        timer.start(1000)
        status = app.exec_()
        sys.exit(status)
        


        #status = app.exec_()
        #sys.exit(status)


if __name__ == '__main__':
    if runExamples:
        pyqtgraph.examples.run()
    else:
        exe()

    # def newTrace(self, key = ""):
    #     print("new trace:", key)
    #     self.key=[]
    #     self.valLists.append(self.key)

    # def updateData(self):
    #     #print("Val dict",self.valDict)
    #     for key in self.valDict:
    #         value = self.valDict[key]
    #         #print('key:' , str(key), type(key))
    #         #print('val:' , value, type(value))
    #         if key not in self.bigD:
    #             self.newTrace(key)
    #             self.bigD[key] = list()
    #         l = self.bigD[key]
    #         #print("l", l, type(l))
    #         #print("big d", self.bigD)
    #         self.bigD[key].append(self.valDict[key])

     #  def parseKeyVal(self, input):
#         #print("parsing")
#         tokens = re.split(token_splits, input)
#         #self.updateData()
#         for token in tokens:
#             if token:
#                 pairs = re.split(value_splits, token)
#                 #print("token", token)
#                 if len(pairs) > 1:
#                     try:
#                         self.valDict[pairs[0]] = [pairs[1]]
#                     except:
#                         pass
#         self.updateData()
    # def update(self):
    #     self.data1[:-1] = self.data1[1:]
    #     self.data2[:-1] = self.data2[1:]
    #     #print(self.valDict['a'])

    #     #self.data1 = np.append(self.data1, self.valDict)
    #     #self.data1[-1] = np.sin(self.ptr/2)
    #     #self.data1 = np.append(self.data1, self.valDict['a'])
    #     self.data1 = np.insert(self.data1, 1, self.valDict['a'])
    #     print(self.data1)
    #     self.data2[-1] = np.sin(self.ptr/1.9)
    #     self.curve2.setData(self.data2)
    #     self.curve1.setData(self.data1)
    #     self.ptr += 1

    # def start(self):
    #     pass

    # def close(self):
    #     pass

    # def test(self):
    #     print("test")
    #     for teststr in plotThese:
    #         self.parseKeyVal(teststr)
    #     print("Big D",self.bigD)
    #     listof = list(self.bigD.items())
    #     array = np.array(listof)
    #     print("array",array)


# # -*- coding: utf-8 -*-
# """
# Various methods of drawing scrolling plots.
# """
# import initExample ## Add path to library (just for examples; you do not need this)

# import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore, QtGui
# import numpy as np

# win = pg.GraphicsLayoutWidget(show=True)
# win.setWindowTitle('pyqtgraph example: Scrolling Plots')


# # 1) Simplest approach -- update data in the array such that plot appears to scroll
# #    In these examples, the array size is fixed.
# p1 = win.addPlot()
# p2 = win.addPlot()
# data1 = np.random.normal(size=300)
# curve1 = p1.plot(data1)
# curve2 = p2.plot(data1)
# ptr1 = 0
# def update1():
#     global data1, ptr1
#     data1[:-1] = data1[1:]  # shift data in the array one sample left
#                             # (see also: np.roll)
#     data1[-1] = np.random.normal()
#     curve1.setData(data1)

#     ptr1 += 1
#     curve2.setData(data1)
#     curve2.setPos(ptr1, 0)


# # 2) Allow data to accumulate. In these examples, the array doubles in length
# #    whenever it is full.
# win.nextRow()
# p3 = win.addPlot()
# p4 = win.addPlot()
# # Use automatic downsampling and clipping to reduce the drawing load
# p3.setDownsampling(mode='peak')
# p4.setDownsampling(mode='peak')
# p3.setClipToView(True)
# p4.setClipToView(True)
# p3.setRange(xRange=[-100, 0])
# p3.setLimits(xMax=0)
# curve3 = p3.plot()
# curve4 = p4.plot()

# data3 = np.empty(100)
# ptr3 = 0

# def update2():
#     global data3, ptr3
#     data3[ptr3] = np.random.normal()
#     ptr3 += 1
#     if ptr3 >= data3.shape[0]:
#         tmp = data3
#         data3 = np.empty(data3.shape[0] * 2)
#         data3[:tmp.shape[0]] = tmp
#     curve3.setData(data3[:ptr3])
#     curve3.setPos(-ptr3, 0)
#     curve4.setData(data3[:ptr3])


# # 3) Plot in chunks, adding one new plot curve for every 100 samples
# chunkSize = 100
# # Remove chunks after we have 10
# maxChunks = 10
# startTime = pg.ptime.time()
# win.nextRow()
# p5 = win.addPlot(colspan=2)
# p5.setLabel('bottom', 'Time', 's')
# p5.setXRange(-10, 0)
# curves = []
# data5 = np.empty((chunkSize+1,2))
# ptr5 = 0

# def update3():
#     global p5, data5, ptr5, curves
#     now = pg.ptime.time()
#     for c in curves:
#         c.setPos(-(now-startTime), 0)

#     i = ptr5 % chunkSize
#     if i == 0:
#         curve = p5.plot()
#         curves.append(curve)
#         last = data5[-1]
#         data5 = np.empty((chunkSize+1,2))
#         data5[0] = last
#         while len(curves) > maxChunks:
#             c = curves.pop(0)
#             p5.removeItem(c)
#     else:
#         curve = curves[-1]
#     data5[i+1,0] = now - startTime
#     data5[i+1,1] = np.random.normal()
#     curve.setData(x=data5[:i+2, 0], y=data5[:i+2, 1])
#     ptr5 += 1


# # update all plots
# def update():
#     update1()
#     update2()
#     update3()
# timer = pg.QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(50)

# if __name__ == '__main__':
#     pg.mkQApp().exec_()
