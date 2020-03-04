import sys
import os
from time import time, localtime, strftime
import logging

from PyQt5 import QtGui, QtCore, QtWidgets

plogger = logging.getLogger()

class TagCompleter(QtWidgets.QCompleter):
    insertText = QtCore.pyqtSignal(str)
    def __init__(self, tags, parent=None):
        plogger.debug("Autocompleter with tags %s", tags)
        self.tags = tags
        self.completion_model = QtCore.QStringListModel(self.tags)
        QtWidgets.QCompleter.__init__(self, parent)
        self.setModel(self.completion_model)
        #self.connect(self, QtCore.SIGNAL("activated(const QString&)"), self.changeCompletion)

    def changeCompletion(self, completion):
        plogger.debug("Find completion")
        if completion.find("(") != -1:
            completion = completion[:completion.find("(")]
        print(completion)
        self.insertText.emit(completion)

    def getTags(self):
        return self.tags

    def setTags(self, tags):
        self.tags = tags
        self.completion_model.setStringList(self.tags)
