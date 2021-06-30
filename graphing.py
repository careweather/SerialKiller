

from PyQt5.QtWidgets import QApplication
import pyqtgraph.examples
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import time
import sys
# pyqtgraph.examples.run()

# quit()
# import initExample ## Add path to library (just for examples; you do not need this)


import re

token_splits = r"[;,\t]"
value_splits = r"[:=]"

testStrs = [
    'a=1;b=200;c=333;d=444',
    'a:1,b:2,c:3,d=4,e',
    'b=x,d=b,a=-1,e=-5',
    'a=1f,b=22f,c=3,d=4a,e=-5d',
    'dad = mad'
]

plotThese = [
    'a:0,b:2,c:0',
    'a:1,b:2,c:5',
    'a:2,b:2,c:1',
    'a:3,b:3,c:5',
    'a:4,b:3,c:1',
    'a:5,b:3,c:5',
    'a:4,b:2,c:1',
    'a:3,b:2,c:0',
    'a:2,b:2,c:0',
    'a:1,b:2,c:0',
    'a:0,b:2,c:0',
]

class graphWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent):
        super().__init__()
        self.plt1 = self.addPlot()
        #self.data1 = np.random.normal(size=100)
        #self.data2 = np.random.normal(size=100)
        self.data1 = np.zeros(shape= (100))
        self.data2 = np.zeros(shape=(100))
        self.curve1 = self.plt1.plot(self.data1)
        self.curve2 = self.plt1.plot(self.data2)
        self.ptr = 0

    def update(self): 
        print("updating!")
        self.data1[:-1] = self.data1[1:]
        self.data2[:-1] = self.data2[1:]
        #data1[-1] = np.random.normal()
        self.data1[-1] = np.sin(self.ptr/2)
        self.data2[-1] = np.sin(self.ptr/1.9)
        self.curve2.setData(self.data2)
        self.curve1.setData(self.data1)
        self.ptr += 1 

    def start(self):
        pass

    def close(self):
        pass
    def parseKeyVal(self, input):
        print("parsing")
        tokens = re.split(token_splits, input)
        for token in tokens: 
            if token:
                pairs = re.split(value_splits, token)
                #print("token", token)
                if len(pairs) > 1:
                    try:
                        self.valDict[pairs[0]] = pairs[1]
                    except:
                        pass
        self.updateLineGraph()

    def test(self):
        print("test")
        for teststr in plotThese:
            self.parseKeyVal(teststr)

runExamples = 1

def exe():
    app = QApplication(sys.argv)
    status = app.exec_()
    sys.exit(status)


if __name__ == '__main__':
    if runExamples:
        pyqtgraph.examples.run()
    else:
        exe()
    
    
# quit()
#!/usr/bin/python
# -*- coding: utf-8 -*-
# """
# Update a simple plot as rapidly as possible to measure speed.
# """

# ## Add path to library (just for examples; you do not need this)
# import initExample


# from pyqtgraph.Qt import QtGui, QtCore
# import numpy as np
# import pyqtgraph as pg
# from pyqtgraph.ptime import time
# app = pg.mkQApp("Plot Speed Test")

# p = pg.plot()
# p.setWindowTitle('pyqtgraph example: PlotSpeedTest')
# p.setRange(QtCore.QRectF(0, -10, 5000, 20)) 
# p.setLabel('bottom', 'Index', units='B')
# curve = p.plot()

# #curve.setFillBrush((0, 0, 100, 100))
# #curve.setFillLevel(0)

# #lr = pg.LinearRegionItem([100, 4900])
# #p.addItem(lr)

# data = np.random.normal(size=(50,5000))
# ptr = 0
# lastTime = time()
# fps = None
# def update():
#     global curve, data, ptr, p, lastTime, fps
#     curve.setData(data[ptr%10])
#     ptr += 1
#     now = time()
#     dt = now - lastTime
#     lastTime = now
#     if fps is None:
#         fps = 1.0/dt
#     else:
#         s = np.clip(dt*3., 0, 1)
#         fps = fps * (1-s) + (1.0/dt) * s
#     p.setTitle('%0.2f fps' % fps)
#     app.processEvents()  ## force complete redraw for every plot
# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(0)
    
# if __name__ == '__main__':
#     pg.mkQApp().exec_()
#