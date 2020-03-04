import os
import logging

from PyQt5 import QtGui, QtCore, QtWidgets

logger = logging.getLogger()

class MsgTextEdit(QtWidgets.QTextEdit):
    """
    Override the QTextEdit for auto completion of tags and runs.
    Also, the very first character we type into the message box is used as a trigger to kick off other events.
    For example, to get the current run, clear the tags (after the timeout) etc
    """
    tagCompleted = QtCore.pyqtSignal(str)
    firstCharacter = QtCore.pyqtSignal()

    def __init__(self,*args):
        QtWidgets.QTextEdit.__init__(self,*args)
        self.completer = None
        self.firstCharacterDone = False

    def setCompleter(self, completer):
        if self.completer:
            self.disconnect(self.completer, 0, self, 0)
        if not completer:
            return
        completer.setWidget(self)
        completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer = completer
        self.completer.highlighted.connect(self.highlighted)

    def resetFirstCharacterDone(self):
        self.firstCharacterDone = False

    def __onlyOneMatch__(self, completionPrefix):
        if self.completer:
            matches = [x for x in self.completer.getTags() if x.startswith(completionPrefix)]
            if len(matches) == 1:
                return True, matches[0]
        return False, None

    def highlighted(self, completion):
        logger.debug("Highlight completion %s", completion)
        tuc = self.textUnderCursor()
        if completion.startswith(tuc):
            remaining_text = completion[len(tuc):] + " "
            tc = self.textCursor()
            tc.insertText(remaining_text)
            self.tagCompleted.emit(completion)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def tagUnderCursor(self):
        tc = self.textCursor()
        while tc.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor):
            selectedText = tc.selectedText()
            if selectedText.startswith(" #"):
                return selectedText[2:]
            if selectedText.startswith(" "):
                return None
        selectedText = tc.selectedText()
        if selectedText.startswith("#"):
            return selectedText[2:]
        return None

    def focusInEvent(self, event):
        if self.completer:
            self.completer.setWidget(self);
        QtWidgets.QTextEdit.focusInEvent(self, event)


    def keyPressEvent(self, event):
        if not self.firstCharacterDone and len(event.text()) > 0:
            self.firstCharacterDone = True
            self.firstCharacter.emit()

        inCompletionMode = False
        tagundercursor = self.tagUnderCursor()
        if tagundercursor != None and " " not in tagundercursor and "\t" not in tagundercursor:
            inCompletionMode = True

        if not inCompletionMode:
            super(MsgTextEdit, self).keyPressEvent(event)
            return

        #logger.debug("Key press event %s", event.key())
        if self.completer and self.completer.popup() and self.completer.popup().isVisible():
            # If the popup is active, allow navigation keys.
            if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab):
                event.ignore()
                return

        if inCompletionMode:
            if event.key() == QtCore.Qt.Key_Space:
                #logger.debug("Spacebar. Resetting the completion mode.")
                mtc = self.textUnderCursor()
                logger.debug("Need to add %s to the list of tags", mtc)
                super(MsgTextEdit, self).keyPressEvent(event)
                self.tagCompleted.emit(mtc)
                inCompletionMode = False
                return

            mtc = self.textUnderCursor() + event.text()
            # We auto complete only if the key pressed is an alphabetic character.
            if len(event.text()) > 0 and len(mtc) > 2:
                match, matched = self.__onlyOneMatch__(mtc)
                if match:
                    self.completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
                    if (matched != self.completer.completionPrefix()):
                        self.completer.setCompletionPrefix(matched)
                    self.completer.complete()
                    return

        if event.key() == QtCore.Qt.Key_Tab:
            logger.debug("Tab pressed")
            words = self.completer.getTags()
            completionPrefix = self.textUnderCursor()
            match, matched = self.__onlyOneMatch__(completionPrefix)
            if match:
                self.completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
                if (matched != self.completer.completionPrefix()):
                    self.completer.setCompletionPrefix(matched)
                self.completer.complete()
                # self.completer.insertText.emit(self.completer.currentCompletion())
                return
            else:
                self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
                if (completionPrefix != self.completer.completionPrefix()):
                    self.completer.setCompletionPrefix(completionPrefix)
                self.completer.complete()
                return

        super(MsgTextEdit, self).keyPressEvent(event)
        return
