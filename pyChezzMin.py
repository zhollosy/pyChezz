"""
    Vector Figures:  https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces
"""

import sys
import os
import json
import getpass
from time import gmtime, strftime
from PyQt4 import QtGui, QtCore, QtSvg, uic

scriptPath = os.path.dirname(__file__)
uifile = scriptPath + "/pyChezzMinUI.ui"
form_class = uic.loadUiType(uifile)[0]


class QPointFEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QtCore.QPointF):
            return [obj.x(), obj.y()]
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

# https://stackoverflow.com/questions/2597278/python-load-variables-in-a-dict-into-namespace
class Bunch(object):
    '''convert dict to attribute
    darkFigures = Bunch(self.darkFigures)
    darkFigures.darkKing
    '''
    def __init__(self, adict):
        self.__dict__.update(adict)

# Snapping - http://www.walletfox.com/course/qgraphicsitemsnaptogrid.php
class myGraphicsSvgItem(QtSvg.QGraphicsSvgItem):
    def __init__(self, parent=None, limitRect=None, cursorShape=QtCore.Qt.OpenHandCursor):
        QtSvg.QGraphicsSvgItem.__init__(self, parent)
        if cursorShape:
            self.cursorShape = cursorShape
        if limitRect:
            self.limitRect = QtCore.QRectF(limitRect)
        self.setCursor(cursorShape)

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemPositionChange:
            # print self.objectName(), '  <-- moved'
            new_value = value.toPointF()
            self.setCursor(QtCore.Qt.ClosedHandCursor)

            if not self.limitRect.contains(new_value):
                new_value.setX(min(self.limitRect.right(), max(new_value.x(), self.limitRect.left())))
                new_value.setY(min(self.limitRect.bottom(), max(new_value.y(), self.limitRect.top())))
                # print new_value, '  <---- NOT Contains'
                value = QtCore.QVariant(new_value)
            return QtGui.QGraphicsItem.itemChange(self, change, value)
        if change == QtGui.QGraphicsItem.ItemPositionHasChanged:
            self.setCursor(self.cursorShape)

        return QtGui.QGraphicsItem.itemChange(self, change, value)


class pyChezzWin(QtGui.QWidget, form_class):
    """ GUI class for chess using minimal number of widgets, no AI, on intuitive surface """
    __widgetInst__ = None
    __build__ = 056
    def __init__(self, app = None):
        if not self.__widgetInst__:
            __widgetInst__ = app
            super(pyChezzWin, self).__init__()
            self.setupUi(self)
            self.interactiveBoardView = QtGui.QGraphicsView(self)
            self.scene = QtGui.QGraphicsScene(self.interactiveBoardView)

            self.firstShow = True
            self.baseViewRect = QtCore.QRect()

            # figures, icons and fields
            self.fields = {}
            self.snapPoints = []
            self.icons = {}
            self.figures = {}
            self.darkFigures = {"darkKing": self.figureInfo(name='darkKing', startField='E8'),
                                "darkQueen": self.figureInfo(name='darkQueen', startField='D8'),
                                "darkBishop1": self.figureInfo(name='darkBishop1', startField='C8'),
                                "darkBishop2": self.figureInfo(name='darkBishop2', startField='F8'),
                                "darkKnight1": self.figureInfo(name='darkKnight1', startField='B8'),
                                "darkKnight2": self.figureInfo(name='darkKnight2', startField='G8'),
                                "darkRook1": self.figureInfo(name='darkRook1', startField='A8'),
                                "darkRook2": self.figureInfo(name='darkRook2', startField='H8'),
                                "darkPawn1": self.figureInfo(name='darkPawn1', startField='A7'),
                                "darkPawn2": self.figureInfo(name='darkPawn2', startField='B7'),
                                "darkPawn3": self.figureInfo(name='darkPawn3', startField='C7'),
                                "darkPawn4": self.figureInfo(name='darkPawn4', startField='D7'),
                                "darkPawn5": self.figureInfo(name='darkPawn5', startField='E7'),
                                "darkPawn6": self.figureInfo(name='darkPawn6', startField='F7'),
                                "darkPawn7": self.figureInfo(name='darkPawn7', startField='G7'),
                                "darkPawn8": self.figureInfo(name='darkPawn8', startField='H7')}
            self.lightFigures = {"lightKing": self.figureInfo(name='lightKing', startField='E1'),
                                 "lightQueen": self.figureInfo(name='lightQueen', startField='D1'),
                                 "lightBishop1": self.figureInfo(name='lightBishop1', startField='C1'),
                                 "lightBishop2": self.figureInfo(name='lightBishop2', startField='F1'),
                                 "lightKnight1": self.figureInfo(name='lightKnight1', startField='B1'),
                                 "lightKnight2": self.figureInfo(name='lightKnight2', startField='G1'),
                                 "lightRook1": self.figureInfo(name='lightRook1', startField='A1'),
                                 "lightRook2": self.figureInfo(name='lightRook2', startField='H1'),
                                 "lightPawn1": self.figureInfo(name='lightPawn1', startField='A2'),
                                 "lightPawn2": self.figureInfo(name='lightPawn2', startField='B2'),
                                 "lightPawn3": self.figureInfo(name='lightPawn3', startField='C2'),
                                 "lightPawn4": self.figureInfo(name='lightPawn4', startField='D2'),
                                 "lightPawn5": self.figureInfo(name='lightPawn5', startField='E2'),
                                 "lightPawn6": self.figureInfo(name='lightPawn6', startField='F2'),
                                 "lightPawn7": self.figureInfo(name='lightPawn7', startField='G2'),
                                 "lightPawn8": self.figureInfo(name='lightPawn8', startField='H2')}

            # Connections
            QtCore.QObject.connect(self.verticalSlider, QtCore.SIGNAL("valueChanged(int)"), self.valueHandlerSlider)
            QtCore.QObject.connect(self.btnOpen, QtCore.SIGNAL("clicked()"), self.btnOpen_Clicked)
            QtCore.QObject.connect(self.btnSave, QtCore.SIGNAL("clicked()"), self.btnSave_Clicked)
            QtCore.QObject.connect(self.scene, QtCore.SIGNAL("clicked()"), self.btnOpen_Clicked)
            # self.resizeEvent = self.alignTable
            self.showEvent = self.initOnFirstShow

            # game
            self.myLogFile = ''
            self.myFigColor = 'light'
            # TODO: place common data-variables into the gameData dict! Replace references in the code!
            # self.gameStarted = False
            self.opponentName = 'OPPONENT'
            self.gameData = {}
            self.setWhoAmI('')
            self.setOpponentName('OPPONENT')
            self.setGameStarted(False)
            self.gameData['users'] = {'OPPONENT': 'dark'}


    def setWhoAmI(self, name=None):
        self.gameData['whoAmI'] = name
        print "I\'am: ", name

    def getWhoAmI(self):
        return self.gameData['whoAmI']

    def setOpponentName(self, name=None):
        self.gameData['opponentName'] = name

    def getOpponentName(self):
        return self.gameData['opponentName']

    def setGameStarted(self, state=True):
        self.gameData['gameStarted'] = state

    def getGameStarted(self):
        return self.gameData['gameStarted']

    def figureInfo(self, name='', startField=''):
        """ Store parameters of a chess figure """
        infDict = {}
        infDict['name'] = name
        infDict['isLight'] = False
        infDict['isDark'] = False
        infDict['imageFile'] = ''
        infDict['startField'] = startField
        infDict['currentField'] = ''
        infDict['currentPos'] = QtCore.QPointF()
        infDict['graphicsItem'] = QtSvg.QGraphicsSvgItem()
        return infDict

    def initOnFirstShow(self, null):
        if self.firstShow:
            self.setFixedSize(self.size())
            self.frmIndicatorYOU.hide()
            self.initializeBoard()
            self.alignTable(self)
            self.drawFigures()
            self.drawIcons()
            self.baseViewRect = self.interactiveBoardView.geometry()
            self.collectSnapPoints()
            self.enableFigures(self.darkFigures, state=False)
            self.enableFigures(self.lightFigures, state=False)
            self.interactiveBoardView.setCursor(QtCore.Qt.OpenHandCursor)
            self.firstShow = False
            print "Shown!!!"
            # print "view + scene ---> ", self.interactiveBoardView.rect(), self.interactiveBoardView.sceneRect()

    def btnOpen_Clicked(self):
        self.openDataFile()

    def btnSave_Clicked(self):
        self.saveNewDataFile()
        self.setGameStarted()

    def valueHandlerSlider(self, value):
        # FIXME: users data recognition must be fixed !!!!
        if self.gameData['users'].keys().count(getpass.getuser()):
            if value:
                # opponent turn
                #self.interactiveBoardView.setEnabled(False)
                self.enableFigures(self.darkFigures, state=False)
                self.enableFigures(self.lightFigures, state=False)
                self.frmIndicatorME.hide()
                self.frmIndicatorYOU.show()
                self.saveChezzMinData()
            else:
                # my turn
                # self.interactiveBoardView.setEnabled(True)
                self.enableFigures(self.darkFigures)
                self.enableFigures(self.lightFigures)
                self.frmIndicatorME.show()
                self.frmIndicatorYOU.hide()
                self.loadChezzMinData()

    def saveNewDataFile(self):
        # openfile = QtGui.QFileDialog.getOpenFileName(self, filter='*.czz')
        openfile = QtGui.QFileDialog.getSaveFileName(self, filter='*.czz')

        # dialog success
        if openfile != '':
            # existing file
            if os.path.isfile(openfile):
                msgBox = QtGui.QMessageBox()
                msgBox.setText("Over write is forbiden!");
                msgBox.exec_();
                return self.saveNewDataFile()
            # new file will be created
            else:
                open(openfile, 'w')
                self.myLogFile = openfile
                self.saveChezzMinData()
                file_info = QtCore.QFileInfo(openfile)
                self.btnOpen.setText(file_info.fileName())
                return True
        else:
            return False

    def openDataFile(self):
        # openfile = QtGui.QFileDialog.getOpenFileName(self, filter='*.czz')
        openfile = QtGui.QFileDialog.getOpenFileName(self, filter='*.czz')

        # dialog success
        if os.path.isfile(openfile):
            f = open(openfile, 'r')
            self.myLogFile = openfile
            file_info = QtCore.QFileInfo(openfile)
            self.btnOpen.setText(file_info.fileName())
            self.initGame()
            self.loadChezzMinData()
            self.setGameStarted()
            return True
        else:
            return False

    def alignTable(self, null):
        if self.baseViewRect.width() > 0:
            targetRect = self.interactiveBoardView.geometry()
            xForm = QtGui.QMatrix()
            width_ratio = float(targetRect.width()) / self.baseViewRect.width()
            height_ratio = float(targetRect.height()) / self.baseViewRect.height()
            xForm.scale(width_ratio, height_ratio)
            self.interactiveBoardView.setMatrix(xForm)

        # self.interactiveBoardView.fitInView(QtCore.QRectF(0, 0, targetRect.width(), targetRect.height()))

    def initializeBoard(self):
        self.interactiveBoardView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.interactiveBoardView.setStyleSheet("background-color: transparent;")
        self.interactiveBoardView.setFrameShape(QtGui.QFrame.NoFrame)
        self.interactiveBoardView.setObjectName("interactiveTable")
        self.interactiveBoardView.setScene(self.scene)
        self.interactiveBoardView.setInteractive(True)
        self.interactiveBoardView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.interactiveBoardView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.verticalSlider.setEnabled(False)
        self.pebleOppLight.setVisible(False)
        self.pebleMyDark.setVisible(False)
        self.setWhoAmI(getpass.getuser())
        self.gameData['users'][self.getWhoAmI()] = 'light'
        print 'Users: ', self.gameData['users']

        # fit sceneRect
        targetRect = self.frmOpponentPark.geometry()
        targetRect.setBottom(self.frmMyPark.geometry().bottom())
        self.interactiveBoardView.setGeometry(targetRect)
        self.interactiveBoardView.setSceneRect(0, 0, targetRect.width(), targetRect.height())

        # collecting field widgets from UI file
        for row in range(1, 9):
            for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                fld = eval('self.field%s%s' % (col, row))
                self.fields['%s%s' % (col, row)] = fld   # self.fields['A1'] = self.fieldA1

    def startNewGame(self):
        if self.saveChezzMinData():
            self.initGame()

    def initGame(self, state=True):
        self.setGameStarted(state)
        self.icons['rotateIcon'].setVisible(False)
        self.icons['goIcon'].setVisible(False)
        self.enableFigures(self.darkFigures)
        self.enableFigures(self.lightFigures)
        self.btnSave.setVisible(False)
        self.verticalSlider.setEnabled(True)
        # whois next !!
        print 'Game Started!!!'

    def rotateBoard(self):
        boardRect = self.interactiveBoardView.frameRect()
        goIconRect = self.icons["goIcon"].boundingRect()

        if self.myFigColor.find('light') == 0:
            self.interactiveBoardView.rotate(180)

            pos = QtCore.QPointF(boardRect.width()/2 + goIconRect.width()/2, boardRect.height()/2 - 60)
            self.icons["goIcon"].setPos(pos)
            self.icons["goIcon"].rotate(180)

            for key, fig in self.figures.iteritems():
                fig.rotate(180)
                fig.moveBy(1.5, 2)

            self.pebleOppLight.setVisible(True)
            self.pebleOppDark.setVisible(False)
            self.pebleMyLight.setVisible(False)
            self.pebleMyDark.setVisible(True)
            self.myFigColor = 'dark'
        else:
            self.interactiveBoardView.rotate(-180)

            pos = QtCore.QPointF(boardRect.width()/2 - goIconRect.width()/2, boardRect.height()/2+60)
            self.icons["goIcon"].setPos(pos)
            self.icons["goIcon"].rotate(180)

            for key, fig in self.figures.iteritems():
                fig.rotate(180)
                fig.moveBy(-1.5, -2)

            self.pebleOppLight.setVisible(False)
            self.pebleOppDark.setVisible(True)
            self.pebleMyLight.setVisible(True)
            self.pebleMyDark.setVisible(False)
            self.myFigColor = 'light'

        # self.users['dark'], self.users['light'] = (self.users['light'], self.users['dark'])
        # self.users[self.users.keys()[0]], self.users[self.users.keys()[1]] = (self.users.values()[1], self.users.values()[0])
        self.gameData['users'][self.gameData['users'].keys()[0]], self.gameData['users'][self.gameData['users'].keys()[1]] =\
            (self.gameData['users'].values()[1], self.gameData['users'].values()[0])
        print  'Users: ', self.gameData['users']


    def drawFigures(self):
        imagesPath = os.path.dirname(__file__) + "/images/"
        limitRect = self.interactiveBoardView.frameRect()

        self.figures["darkKing"] = myGraphicsSvgItem(imagesPath + "kdt.svg", limitRect=limitRect)
        self.figures["darkQueen"] = myGraphicsSvgItem(imagesPath + "qdt.svg", limitRect=limitRect)
        self.figures["darkBishop1"] = myGraphicsSvgItem(imagesPath + "bdt.svg", limitRect=limitRect)
        self.figures["darkBishop2"] = myGraphicsSvgItem(imagesPath + "bdt.svg", limitRect=limitRect)
        self.figures["darkKnight1"] = myGraphicsSvgItem(imagesPath + "ndt.svg", limitRect=limitRect)
        self.figures["darkKnight2"] = myGraphicsSvgItem(imagesPath + "ndt.svg", limitRect=limitRect)
        self.figures["darkRook1"] = myGraphicsSvgItem(imagesPath + "rdt.svg", limitRect=limitRect)
        self.figures["darkRook2"] = myGraphicsSvgItem(imagesPath + "rdt.svg", limitRect=limitRect)
        self.figures["darkPawn1"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn1"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn2"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn3"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn4"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn5"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn6"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn7"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)
        self.figures["darkPawn8"] = myGraphicsSvgItem(imagesPath + "pdt.svg", limitRect=limitRect)

        self.figures["lightKing"] = myGraphicsSvgItem(imagesPath + "klt.svg", limitRect=limitRect)
        self.figures["lightQueen"] = myGraphicsSvgItem(imagesPath + "qlt.svg", limitRect=limitRect)
        self.figures["lightBishop1"] = myGraphicsSvgItem(imagesPath + "blt.svg", limitRect=limitRect)
        self.figures["lightBishop2"] = myGraphicsSvgItem(imagesPath + "blt.svg", limitRect=limitRect)
        self.figures["lightKnight1"] = myGraphicsSvgItem(imagesPath + "nlt.svg", limitRect=limitRect)
        self.figures["lightKnight2"] = myGraphicsSvgItem(imagesPath + "nlt.svg", limitRect=limitRect)
        self.figures["lightRook1"] = myGraphicsSvgItem(imagesPath + "rlt.svg", limitRect=limitRect)
        self.figures["lightRook2"] = myGraphicsSvgItem(imagesPath + "rlt.svg", limitRect=limitRect)
        self.figures["lightPawn1"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn1"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn2"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn3"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn4"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn5"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn6"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn7"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)
        self.figures["lightPawn8"] = myGraphicsSvgItem(imagesPath + "plt.svg", limitRect=limitRect)

        for key, fig in self.figures.iteritems():
            fig.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
            fig.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
            fig.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges, True)
            fig.setTransformOriginPoint(-fig.boundingRect().width()-4, -fig.boundingRect().height()-4)
            fig.setScale(0.7)
            # fig.setScale(-0.7)
            fig.setObjectName(key)
            self.scene.addItem(fig)

        # place figures to initial pos
        for fig, figInf in self.darkFigures.iteritems():
            self.moveFigureToField(fig, figInf['startField'])
            figInf['currentField'] = figInf['startField']
        for fig, figInf in self.lightFigures.iteritems():
            self.moveFigureToField(fig, figInf['startField'])
            figInf['currentField'] = figInf['startField']
            # print "%s - %s" % (fig, figInf['startField'])

    def drawIcons(self):
        imagesPath = os.path.dirname(__file__) + "/images/"
        limitRect = self.interactiveBoardView.frameRect()

        # rotateIcon
        self.icons["rotateIcon"] = myGraphicsSvgItem(imagesPath + "rotate_square.svg", cursorShape=QtCore.Qt.PointingHandCursor)
        self.icons["rotateIcon"].setObjectName('rotateIcon')
        self.scene.addItem(self.icons["rotateIcon"])
        iconRect = self.icons["rotateIcon"].boundingRect()
        self.icons["rotateIcon"].setPos(QtCore.QPointF(limitRect.bottomRight()/2) - iconRect.bottomRight()/2)

        # goIcon
        self.icons["goIcon"] = myGraphicsSvgItem(imagesPath + "GO.svg", cursorShape=QtCore.Qt.PointingHandCursor)
        self.icons["goIcon"].setObjectName('goIcon')
        self.scene.addItem(self.icons["goIcon"])
        iconRect = self.icons["goIcon"].boundingRect()
        self.icons["goIcon"].setPos(QtCore.QPointF(limitRect.width()/2 - iconRect.width()/2, limitRect.height()/2+60))

    def mousePressEvent(self, QMouseEvent):
        posGlobal = self.mapToGlobal(QMouseEvent.pos())
        posLocal = self.interactiveBoardView.mapFromGlobal(posGlobal)
        item = self.interactiveBoardView.itemAt(posLocal)
        if item is not None:
            if str(item.objectName()).find('rotateIcon') == 0:
                self.rotateBoard()
            if str(item.objectName()).find('goIcon') == 0:
                self.startNewGame()
            print "Pressed: ", item.objectName()

    def enableFigures(self, figures, state=True):
        for fig in figures:
            self.figures[fig].setFlag(QtGui.QGraphicsItem.ItemIsSelectable, state)
            self.figures[fig].setFlag(QtGui.QGraphicsItem.ItemIsMovable, state)

    def placeIcon(self, iconName, iconPos):
        pass

    def removeIcon(self, iconName):
        pass

    def moveFigureToField(self, figName, fldName):
        fig = self.figures[figName]
        fldCoordGlobal = self.getFieldCenter(fldName)
        fldCoordLocal = self.interactiveBoardView.mapFromGlobal(fldCoordGlobal)
        fig.setPos(QtCore.QPointF(fldCoordLocal))

    def moveFigureToPos(self, figName, pos):
        fig = self.figures[figName]
        fig.setPos(pos)

    def getFieldCenter(self, fldName):
        fld = self.fields[fldName]
        fldCenterOffset = QtCore.QPoint(fld.geometry().center()) - fld.pos()
        return fld.mapToGlobal(fldCenterOffset)

    def collectSnapPoints(self):
        self.snapPoints = []
        for key, fld in self.fields.iteritems():
            fldCoordGlobal = self.getFieldCenter(key)
            fldCoordLocal = self.interactiveBoardView.mapFromGlobal(fldCoordGlobal)
            self.snapPoints.append(fldCoordLocal)

        rectOpp = self.frmOpponentPark.geometry()
        rectSpace = QtCore.QPoint(rectOpp.width()/9, rectOpp.height()/3)
        for i in range(rectSpace.x(), 8*rectSpace.x(), rectSpace.x()):
            for j in range(rectSpace.y(), rectSpace.y()*3, rectSpace.y()):
                boardCoordGlob = self.frmOpponentPark.mapToGlobal(QtCore.QPoint(i, j))
                fldCoordLocal = self.interactiveBoardView.mapFromGlobal(boardCoordGlob)
                self.snapPoints.append(fldCoordLocal)
        rectMy = self.frmMyPark.geometry()
        # TODO: Complete collecting parking points for snap
        # print self.snapPoints

    def saveChezzMinData(self):
        if self.myLogFile:
            self.gameDataexport_dict = {}
            figPlaces = {}
            for key, item in self.figures.iteritems():
                figPlaces[str(item.objectName())] = (item.pos().x(), item.pos().y())

            time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

            self.gameData['fileDataType'] = ('pyChezzMin', 'v0.1.%s' % self.__build__, '?????@gmail.com')
            self.gameData['gameStarted'] = time if 'gameStarted' not in self.gameData else self.gameData['gameStarted']
            self.gameData['figPlaces'] = figPlaces
            self.gameData['whoIsNext'] = (self.gameData['whoAmI'], self.gameData['opponentName'])[self.verticalSlider.value()]

            json_data = json.dumps(self.gameData, sort_keys=True, indent=4, separators=(',', ': '))
            try:
                with open(self.myLogFile, "w") as log:
                    log.write(json_data)
            finally:
                print "Saved!"
                return True
        else:
            return self.saveNewDataFile()


    def loadChezzMinData(self):
        json_data = {}
        # if log file written and has data
        if self.myLogFile and int(os.stat(self.myLogFile).st_size):
            try:
                with open(self.myLogFile, "r") as log:
                    json_data = json.loads(log.read())
            except:
                print "Cannot read data file!"
            else:
                # loaded and check if the user is part of the game
                if self.getWhoAmI() in json_data['users'].keys():
                    self.gameData = json_data
                    mySavedColor = [col for per, col in json_data['users'].iteritems() if per == self.getWhoAmI()][0]
                    if mySavedColor != self.myFigColor: # flip the board if necessary
                        self.rotateBoard()
                        print 'rotated on load'
                    self.myFigColor = mySavedColor
                    # self.setGameStarted()

                    # turnIndex = ('ME', 'OPPONENT').index(json_data['whoIsNext'])
                    turnIndex = (self.getWhoAmI(), self.getOpponentName()).index(json_data['whoIsNext'])
                    # self.verticalSlider.setValue(turnIndex)

                    for key, value in json_data['figPlaces'].iteritems():
                        self.moveFigureToPos(key, QtCore.QPointF(value[0], value[1]))
                    print "Loaded!"
                else:
                    print "You are not parted in this game!"
        print 'Loaded: ', json_data

def main():

    app = QtGui.QApplication(sys.argv)
    if pyChezzWin.__widgetInst__ is None:
        t = pyChezzWin(app=app)
        t.setWindowIcon(QtGui.QIcon(os.path.dirname(__file__) + "/images/pyChezz.svg"))
    else:
        t = pyChezzWin.__widgetInst__
    t.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

