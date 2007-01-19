############################################################################
##
## Copyright (C) 2006-2007 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################
################################################################################
# This file contains classes working with cell helper widgets, i.e. toolbar,
# resizer, etc.:
#   CellHelpers
#   CellResizer
#   CellResizerConfig
#   CellToolBar
################################################################################
from PyQt4 import QtCore, QtGui

################################################################################

class CellResizerConfig(object):
    """
    CellResizerConfig can be used to config different parameters of
    the CellResizer widget such as shape, mask, pixmap, color, size,
    and cursor. By default, it has a black, triangular shape of size
    25x25. In order to change the shape, we have to override this
    class

    """
    def __init__(self, size=25, color=QtGui.QColor(0,0,0)):
        """ CellResizerConfig(size: int, color: QColor) -> CellResizerConfig
        Create mask and pixmap of a triangular shape with the specifc size
        and color
        
        """
        self.size = size
        self.transparentColor = QtGui.QColor(QtCore.Qt.blue)
        self.image = QtGui.QImage(size,size,QtGui.QImage.Format_RGB32)
        for i in range(size):
            for j in range(size):
                if i+j<size-1:
                    self.image.setPixel(i, j, self.transparentColor.rgb())
                else:
                    if i+j==size-1 or i==size-1 or j==size-1:
                        self.image.setPixel(i, j,
                                            QtGui.QColor(QtCore.Qt.white).rgb())
                    else:
                        self.image.setPixel(i, j, color.rgb())
        self.pixmapVar = self.maskVar = self.cursorVar = None

    def pixmap(self):
        """ pixmap() -> QPixmap
        Return the pixmap of the resizer shape
        
        """
        if not self.pixmapVar:
            self.pixmapVar = QtGui.QPixmap.fromImage(self.image)
        return self.pixmapVar

    def mask(self):
        """ mask() -> QRegion
        Return only the region of the resizer that will be shown on screen
        
        """
        if not self.maskVar:
            mask = self.pixmap().createMaskFromColor(self.transparentColor)
            self.maskVar = QtGui.QRegion(mask)
        return self.maskVar

    def cursor(self):
        """ cursor() -> QCursor
        Return the cursor that will be shown inside the resizer
        
        """
        return QtGui.QCursor(QtCore.Qt.SizeFDiagCursor)

class CellResizer(QtGui.QLabel):
    """
    CellResizer is a customized shape SizeGrip that stays on top of
    the widget, moving this size grip will end up resizing the
    corresponding cell in the table. This is different from QSizeGrip
    because it allows overlapping on top of the widget

    """
    def __init__(self, sheet, config=CellResizerConfig(), parent=None):
        """ CellResizer(sheet: SpreadsheetSheet,
                        config: subclass of CellResizerConfig,
                        parent: QWidget) -> CellResizer
        Initialize the size grip with the default triangular shape
        
        """
        QtGui.QLabel.__init__(self,sheet)
        self.setMouseTracking(False)
        self.setFixedSize(config.size, config.size)
        self.setPixmap(config.pixmap())
        self.setMask(config.mask())
        self.setCursor(config.cursor())
        self.setStatusTip("Left/Right-click drag to resize the underlying"
                          "cell or the whole spreadsheet ")
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sheet = sheet
        self.config = config
        self.resizeAll = False
        self.dragging = False
        self.lastPos = None
        self.row = -1
        self.col = -1
        self.hide()


    def setDragging(self,b):        
        """ setDragging(b: boolean) -> None
        Set the resizer state to busy dragging
        
        """
        self.dragging = b

    def snapTo(self,row,col):
        """ snapTo(row, col) -> None
        Assign which row and column the resizer should be controlling
        
        """
        self.row = row
        self.col = col

    def adjustPosition(self, rect):
        """ adjustPosition(rect: QRect) -> None
        Adjust resizer position to be on the bottom-right corner of the cell
        
        """
        p = self.parent().mapFromGlobal(rect.topLeft())
        self.move(p.x()+rect.width()-self.width(),
                  p.y()+rect.height()-self.height())

    def mousePressEvent(self,e):
        """ mousePressEvent(e: QMouseEvent) -> None        
        Handle Qt mouse press event to track if we need to resize
        either left or right mouse button is clicked
        
        """
        if self.col>=0:
            if e.button()==QtCore.Qt.LeftButton:
                self.resizeAll = False
                self.dragging = True
                self.lastPos = QtCore.QPoint(e.globalX(),e.globalY())
            if e.button()==QtCore.Qt.RightButton and not self.sheet.fitToWindow:
                self.resizeAll = True
                self.dragging = True
                self.lastPos = QtCore.QPoint(e.globalX(),e.globalY())

    def mouseReleaseEvent(self,e):
        """ mouseReleaseEvent(e: QMouseEvent) -> None
        Handle Qt mouse release event to clean up all state
        
        """
        ctrl = e.modifiers()&QtCore.Qt.ControlModifier
        self.sheet.showHelpers(ctrl, self.row, self.col)
        if (e.button()==QtCore.Qt.LeftButton or
            e.button()==QtCore.Qt.RightButton):
            self.dragging = False

    def mouseMoveEvent(self,e):
        """ mouseMoveEvent(e: QMouseEvent) -> None        
        Interactively resize the corresponding column and row when the
        mouse moves
        
        """
        if self.dragging:
            hd = e.globalX() - self.lastPos.x()
            vd = e.globalY() - self.lastPos.y()
            self.lastPos.setX(e.globalX())
            self.lastPos.setY(e.globalY())
            hSize = self.sheet.columnWidth(self.col)
            vSize = self.sheet.rowHeight(self.row)
            fit = self.sheet.fitToWindow
            
            # All sections should have the same size (Right-Click)
            if self.resizeAll:
                # Resize the columnds first
                dS = int(hd / (self.col+1))
                mS = hd % (self.col+1)
                for i in range(self.sheet.columnCount()):                    
                    if i>self.col:
                        newValue = hSize+dS
                    else:
                        newValue = self.sheet.columnWidth(i)+dS+(i<mS)
                    self.sheet.setColumnWidth(i, newValue)
                # Then resize the rows
                dS = int(vd / (self.row+1))
                mS = vd % (self.row+1)
                for i in range(self.sheet.rowCount()):                    
                    if i>self.row:
                        newValue = vSize+dS
                    else:
                        newValue = self.sheet.rowHeight(i)+dS+(i<mS)
                    self.sheet.setRowHeight(i, newValue)

            # Only resize the corresponding column and row (Left-Click)
            else:
                self.sheet.setColumnWidth(self.col, hSize+hd)
                self.sheet.setRowHeight(self.row, vSize+vd)
            rect = self.sheet.getCellRect(self.row, self.col)
            rect.moveTo(self.sheet.viewport().mapToGlobal(rect.topLeft()))
            self.adjustPosition(rect)

class CellToolBar(QtGui.QToolBar):
    """
    CellToolBar is inherited from QToolBar with some functionalities
    for interacting with CellHelpers
    
    """
    def __init__(self, sheet):
        """ CellToolBar(sheet: SpreadsheetSheet) -> CellToolBar        
        Initialize the cell toolbar by calling the user-defined
        toolbar construction function
        
        """
        QtGui.QToolBar.__init__(self,sheet)
        self.setAutoFillBackground(True)
        self.sheet = sheet
        self.row = -1
        self.col = -1
        self.createToolBar()
    
    def createToolBar(self):
        """ createToolBar() -> None        
        A user-defined method for customizing the toolbar. This is
        going to be an empty method here for inherited classes to
        override.
        
        """
        pass

    def snapTo(self, row, col):
        """ snapTo(row, col) -> None
        Assign which row and column the toolbar should be snapped to
        
        """
        self.row = row
        self.col = col
        self.updateToolBar()

    def adjustPosition(self, rect):
        """ adjustPosition(rect: QRect) -> None
        Adjust the position of the toolbar to be top-left
        
        """
        self.adjustSize()
        p = self.parent().mapFromGlobal(rect.topLeft())
        self.move(p.x(), p.y())

    def updateToolBar(self):
        """ updateToolBar() -> None        
        This will get called when the toolbar widgets need to have
        their status updated. It sends out needUpdateStatus signal
        to let the widget have a change to update their own status
        
        """
        cellWidget = self.sheet.getCell(self.row, self.col)
        for action in self.actions():
            action.emit(QtCore.SIGNAL('needUpdateStatus'),
                        (self.sheet, self.row, self.col, cellWidget))

    def connectAction(self, action, widget):
        """ connectAction(action: QAction, widget: QWidget) -> None
        Connect actions to special slots of a widget
        
        """
        if hasattr(widget, 'updateStatus'):
            self.connect(action, QtCore.SIGNAL('needUpdateStatus'),
                         widget.updateStatus)
        if hasattr(widget, 'triggeredSlot'):
            self.connect(action, QtCore.SIGNAL('triggered()'),
                         widget.triggeredSlot)
        if hasattr(widget, 'toggledSlot'):
            self.connect(action, QtCore.SIGNAL('toggled(bool)'),
                         widget.toggledSlot)

    def appendAction(self, action):
        """ appendAction(action: QAction) -> QAction
        Setup and add action to the tool bar
        
        """
        action.toolBar = self
        self.addAction(action)
        self.connectAction(action, action)
        return action

    def appendWidget(self, widget):
        """ appendWidget(widget: QWidget) -> QAction
        Setup the widget as an action and add it to the tool bar

        """
        action = self.addWidget(widget)
        widget.toolBar = self
        action.toolBar = self
        self.connectAction(action, widget)
        return action

    def getSnappedWidget(self):
        """ getSnappedWidget() -> QWidget
        Return the widget being snapped by the toolbar
        
        """
        if self.row>=0 and self.col>=0:
            return self.sheet.getCell(self.row, self.col)
        else:
            return None

class CellHelpers(object):
    """
    CellHelpers is a container include CellResizer and CellToolbar
    that will shows up whenever the Ctrl key is hold down and the
    mouse hovers the cell.

    """
    def __init__(self, sheet, resizerInstance=None, toolBarInstance=None):
        """ CellHelpers(sheet: SpreadsheetSheet,
                        resizerInstance: CellResizer,
                        toolBarinstance: CellToolBar) -> CellHelpers
        Initialize with no tool bar and a cell resizer
        
        """
        self.sheet = sheet
        self.resizer = resizerInstance
        self.toolBar = toolBarInstance
        self.row = -1
        self.col = -1
        
    def snapTo(self, row, col):
        """ snapTo(row: int, col: int) -> None
        Assign the resizer and toolbar to the correct cell
        
        """
        if row>=0 and ((row!=self.row) or (col!=self.col)):
            self.hide()
            self.row = row
            self.col = col
            if self.resizer:
                self.resizer.snapTo(row,col)
            toolBar = self.sheet.getCellToolBar(row, col)
            if toolBar!=self.toolBar:
                if self.toolBar:
                    self.toolBar.hide()
                self.toolBar = toolBar
            if self.toolBar:
                self.toolBar.snapTo(row,col)
            self.adjustPosition()

    def adjustPosition(self):
        """ adjustPosition() -> None
        Adjust both the toolbar and the resizer
        
        """
        rect = self.sheet.getCellGlobalRect(self.row, self.col)
        if self.resizer:
            self.resizer.adjustPosition(rect)
        if self.toolBar:
            self.toolBar.adjustPosition(rect)

    def show(self):
        """ show() -> None
        An helper function derived from setVisible
        
        """
        self.setVisible(True)

    def hide(self):
        """ hide() -> None
        An helper function derived from setVisible
        
        """
        self.setVisible(False)

    def setVisible(self,b):
        """ setVisible(b: boolean) -> None
        Show/hide the cell helpers
        """
        if self.resizer:
            self.resizer.setVisible(b)
        if not b and self.resizer:
            self.resizer.setDragging(False)
        if self.toolBar:
            self.toolBar.setVisible(b)

    def isInteracting(self):
        """ isInteracting() -> boolean
        Check to see if the helper is in action with the resizer
        
        """
        if self.resizer:
            return self.resizer.dragging
        else:
            return False
