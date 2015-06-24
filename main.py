
"""
Copyright (C) 2015 Yannik Marchand
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY Yannik Marchand ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Yannik Marchand BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation 
are those of the authors and should not be interpreted as representing
official policies, either expressed or implied, of Yannik Marchand.
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4 import QtGui, QtCore
from PyQt4.QtOpenGL import *
import os, sys

import byml, fmdl, sarc, yaz0

import datetime
now = datetime.datetime.now

color = 1

class CheckBox(QtGui.QCheckBox):
    def __init__(self,node):
        QtGui.QCheckBox.__init__(self)
        self.stateChanged.connect(self.changed)
        self.node = node

    def changed(self,state):
        self.node.changeValue(state==QtCore.Qt.Checked)

class LineEdit(QtGui.QLineEdit):
    def __init__(self,value,callback):
        QtGui.QLineEdit.__init__(self,str(value))
        self.callback = callback
        self.textChanged[str].connect(self.changed)

    def changed(self,text):
        if text:
            self.callback(self)

def FloatEdit(v,cb):
    edit = LineEdit(v,cb)
    edit.setValidator(QtGui.QDoubleValidator())
    return edit

def IntEdit(v,cb):
    edit = LineEdit(v,cb)
    edit.setValidator(QtGui.QIntValidator())
    return edit

def SettingName(oldName):
    if oldName == 'IsSnowCover':
        return 'Snow Covered'
    return oldName

class SettingsWidget(QtGui.QWidget):
    def __init__(self,parent):
        QtGui.QWidget.__init__(self,parent)
        layout = QtGui.QVBoxLayout(self)
        scroll = QtGui.QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        scrollContents = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(scrollContents)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        scroll.setWidget(scrollContents)

    def reset(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

    def showSettings(self,obj):
        self.current = obj
        self.config_lbl = QtGui.QLabel(obj.data['UnitConfigName'])
        self.config_lbl.setStyleSheet('font-size: 16px')
        self.layout.addWidget(self.config_lbl)

        lbl = QtGui.QLabel('Translate:')
        lbl.setStyleSheet('font-size: 14px')
        self.layout.addWidget(lbl)
        self.transx = FloatEdit(obj.posx,self.changed)
        self.transy = FloatEdit(obj.posy,self.changed)
        self.transz = FloatEdit(obj.posz,self.changed)
        self.layout.addWidget(self.transx)
        self.layout.addWidget(self.transy)
        self.layout.addWidget(self.transz)

        lbl = QtGui.QLabel('Rotate:')
        lbl.setStyleSheet('font-size: 14px')
        self.layout.addWidget(lbl)
        self.rotx = FloatEdit(obj.rotx,self.changed)
        self.roty = FloatEdit(obj.roty,self.changed)
        self.rotz = FloatEdit(obj.rotz,self.changed)
        self.layout.addWidget(self.rotx)
        self.layout.addWidget(self.roty)
        self.layout.addWidget(self.rotz)

        lbl = QtGui.QLabel('Scale:')
        lbl.setStyleSheet('font-size: 14px')
        self.layout.addWidget(lbl)
        self.sclx = FloatEdit(obj.sclx,self.changed)
        self.scly = FloatEdit(obj.scly,self.changed)
        self.sclz = FloatEdit(obj.sclz,self.changed)
        self.layout.addWidget(self.sclx)
        self.layout.addWidget(self.scly)
        self.layout.addWidget(self.sclz)

        for key in obj.data.subNodes():
            vnode = obj.data.getSubNode(key)
            if not key in ['Scale','Translate','Rotate','UnitConfig','Links','UnitConfigName',
                           'IsLinkDest','ModelSuffix','ModelName']:
                lbl = QtGui.QLabel(SettingName(key)+':')
                if isinstance(vnode,byml.FloatNode):
                    box = FloatEdit(obj.data[key],self.changed2)
                    box.node = vnode
                elif isinstance(vnode,byml.IntegerNode):
                    box = IntEdit(obj.data[key],self.changed2)
                    box.node = vnode
                elif isinstance(vnode,byml.BooleanNode):
                    box = CheckBox(vnode)
                    if obj.data[key]:
                        box.toggle()
                elif isinstance(vnode,byml.StringNode):
                    box = LineEdit(str(obj.data[key]),self.changed2)
                    box.node = vnode
                else:
                    box = QtGui.QLineEdit(str(obj.data[key]))
                    box.setEnabled(False)
                self.layout.addWidget(lbl)
                self.layout.addWidget(box)
                
            elif key == 'UnitConfigName':
                lbl = QtGui.QLabel(key+':')
                #box = LineEdit(str(obj.data['UnitConfigName']),self.configNameChanged)
                #box.node = vnode
                box = QtGui.QLineEdit(str(obj.data[key]))
                box.setEnabled(False)
                self.layout.addWidget(lbl)
                self.layout.addWidget(box)
                
            elif key == 'ModelName':
                lbl = QtGui.QLabel(key+':')
                if isinstance(vnode,byml.StringNode):
                    box = LineEdit(str(obj.data['ModelName']),self.modelNameChanged)
                    box.node = vnode
                else:
                    box = QtGui.QLineEdit(str(obj.data['ModelName']))
                    box.setEnabled(False)
                self.layout.addWidget(lbl)
                self.layout.addWidget(box)

    def changed(self,box):
        if self.transx.text() and self.transy.text() and self.transz.text() and self.rotx.text() and self.roty.text() and self.rotz.text() and self.sclx.text() and self.scly.text() and self.sclz.text():
            self.current.posx = float(self.transx.text())
            self.current.posy = float(self.transy.text())
            self.current.posz = float(self.transz.text())
            self.current.rotx = float(self.rotx.text())
            self.current.roty = float(self.roty.text())
            self.current.rotz = float(self.rotz.text())
            self.current.sclx = float(self.sclx.text())
            self.current.scly = float(self.scly.text())
            self.current.sclz = float(self.sclz.text())
            self.current.saveValues()
            window.glWidget.updateGL()

    def changed2(self,box):
        if box.text():
            box.node.changeValue(box.text())

    #def configNameChanged(self,box):
    #    if box.text():
    #        box.node.changeValue(box.text())
    #        self.config_lbl.setText(box.text())
    #        self.current.updateModel()

    def modelNameChanged(self,box):
        if box.text():
            box.node.changeValue(box.text())
            self.current.updateModel()

class LevelObject:
    def __init__(self,obj,dlist):
        global color
        self.data = obj
        self.color = (color/100/10.0,((color/10)%10)/10.0,(color%10)/10.0)
        color+=1
        self.list = dlist
        
        trans = obj['Translate']
        self.posx = trans['X']/100
        self.posy = trans['Y']/100
        self.posz = trans['Z']/100

        rot = obj['Rotate']
        self.rotx = rot['X']
        self.roty = rot['Y']
        self.rotz = rot['Z']

        scale = obj['Scale']
        self.sclx = scale['X']
        self.scly = scale['Y']
        self.sclz = scale['Z']

    def saveValues(self):
        obj = self.data
        trans = obj['Translate']
        if self.posx != trans['X']/100: trans.getSubNode('X').changeValue(self.posx*100)
        if self.posy != trans['Y']/100: trans.getSubNode('Y').changeValue(self.posy*100)
        if self.posz != trans['Z']/100: trans.getSubNode('Z').changeValue(self.posz*100)
            
        rot = obj['Rotate']
        if self.rotx != rot['X']: rot.getSubNode('X').changeValue(self.rotx)
        if self.roty != rot['Y']: rot.getSubNode('Y').changeValue(self.roty)
        if self.rotz != rot['Z']: rot.getSubNode('Z').changeValue(self.rotz)

        scale = obj['Scale']
        if self.sclx != scale['X']: scale.getSubNode('X').changeValue(self.sclx)
        if self.scly != scale['Y']: scale.getSubNode('Y').changeValue(self.scly)
        if self.sclz != scale['Z']: scale.getSubNode('Z').changeValue(self.sclz)

    def draw(self,pick):
        if pick:
            glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.posx,self.posy,self.posz)
        glRotatef(self.rotx,1.0,0.0,0.0)
        glRotatef(self.roty,0.0,1.0,0.0)
        glRotatef(self.rotz,0.0,0.0,1.0)
        #glScalef(self.sclx,self.scly,self.sclz)
        glCallList(self.list)
        glPopMatrix()

    def updateModel(self):
        model = self.data['ModelName']
        if not self.data['ModelName']:
            model = self.data['UnitConfigName']
        if not model in window.glWidget.cache:
            window.glWidget.cache[model] = window.glWidget.loadModel(model)
        self.list = window.glWidget.cache[model]
        window.glWidget.updateGL()

class LevelWidget(QGLWidget):

    objects = []
    cache = {}
    rotx = roty = rotz = 0
    posx = posy = 0
    posz = -300
    picked = None
    
    def __init__(self,parent):
        QGLWidget.__init__(self,parent)

    def reset(self):
        self.objects = []
        self.rotx = self.roty = self.rotz = 0
        self.posx = self.posy =  0
        self.posz = -300

    def pickObjects(self,x,y):
        self.paintGL(1)
        array = (GLuint * 1)(0)
        pixel = glReadPixels(x,self.height()-y,1,1,GL_RGB,GL_UNSIGNED_BYTE,array)
        r,g,b = [round(((array[0]>>(i*8))&0xFF)/255.0,1) for i in range(3)]
        self.picked = None
        window.settings.reset()
        for obj in self.objects:
            if obj.color == (r,g,b):
                self.picked = obj
                break
        if self.picked:
            window.settings.showSettings(self.picked)
        self.updateGL()

    def paintGL(self,pick=0):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.posx,self.posy,self.posz)
        glRotatef(self.rotx,1.0,0.0,0.0)
        glRotatef(self.roty,0.0,1.0,0.0)
        glRotatef(self.rotz,0.0,0.0,1.0)
        for obj in self.objects:
            if obj == self.picked:
                glColor3f(1.0,0.0,0.0)
            else:
                glColor3f(1.0,1.0,1.0)
            obj.draw(pick)

    def resizeGL(self,w,h):
        if h == 0:
            h = 1
            
        glViewport(0,0,w,h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0,float(w)/float(h),0.1,750.0)
        glMatrixMode(GL_MODELVIEW)

    def initializeGL(self):
        glClearColor(0.3,0.3,1.0,0.0)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_DEPTH_TEST)
        self.generateCubeList()

    def addObject(self,obj,modelName):
        if not modelName in self.cache:
            self.cache[modelName] = self.loadModel(modelName)
        lobj = LevelObject(obj,self.cache[modelName])
        self.objects.append(lobj)

    def loadModel(self,name):
        if not os.path.isfile(window.gamePath+'/ObjectData/'+name+'.szs'):
            return self.cubeList

        with open(window.gamePath+'/ObjectData/'+name+'.szs','rb') as f:
            data = f.read()

        sarchive = yaz0.decompress(data)
        if sarc.contains(sarchive,name+'.bfres'):
            bfres = sarc.extract(sarchive,name+'.bfres')
            model = fmdl.parse(bfres)
            return self.generateList(model)
        return self.cubeList

    def generateList(self,model):
        displayList = glGenLists(1)
        glNewList(displayList,GL_COMPILE)

        for polygon in model.shapes:

            rotation = polygon.rotation
            triangles = polygon.indices
            vertices = polygon.vertices
            
            glPushMatrix()
            glRotatef(rotation[0],1.0,0.0,0.0)
            glRotatef(rotation[1],0.0,1.0,0.0)
            glRotatef(rotation[2],0.0,0.0,1.0)

            glBegin(GL_TRIANGLES)
            for vertex in triangles:
                glVertex3f(*[vertices[vertex][i]/100 for i in range(3)])
            glEnd()

            glPushAttrib(GL_CURRENT_BIT)
            glColor3f(0.0,0.0,0.0)
            for triangle in [triangles[i*3:i*3+3] for i in range(len(triangles)/3)]:
                glBegin(GL_LINES)
                for vertex in triangle:
                    glVertex3f(*[vertices[vertex][i]/100 for i in range(3)])
                glEnd()
            glPopAttrib()

            glPopMatrix()
        
        glEndList()
        return displayList

    def generateCubeList(self):
        displayList = glGenLists(1)
        glNewList(displayList,GL_COMPILE)

        glBegin(GL_QUADS)
        self.drawCube()
        glEnd()

        glBegin(GL_LINES)
        glColor3f(0.0,0.0,0.0)
        self.drawCube()
        glEnd()

        glEndList()

        self.cubeList = displayList

    def drawCube(self):
        glVertex3f( 0.5, 0.5,-0.5)
        glVertex3f(-0.5, 0.5,-0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f( 0.5, 0.5, 0.5)

        glVertex3f( 0.5,-0.5, 0.5)
        glVertex3f(-0.5,-0.5, 0.5)
        glVertex3f(-0.5,-0.5,-0.5)
        glVertex3f( 0.5,-0.5,-0.5)
        
        glVertex3f( 0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(-0.5,-0.5, 0.5)
        glVertex3f( 0.5,-0.5, 0.5)

        glVertex3f( 0.5,-0.5,-0.5)
        glVertex3f(-0.5,-0.5,-0.5)
        glVertex3f(-0.5, 0.5,-0.5)
        glVertex3f( 0.5, 0.5,-0.5)
        
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5,-0.5)
        glVertex3f(-0.5,-0.5,-0.5)
        glVertex3f(-0.5,-0.5, 0.5)
        
        glVertex3f( 0.5, 0.5,-0.5)
        glVertex3f( 0.5, 0.5, 0.5)
        glVertex3f( 0.5,-0.5, 0.5)
        glVertex3f( 0.5,-0.5,-0.5)
    
    mousex = mousey = 0
    def mousePressEvent(self,event):
        if event.button() == 1:
            self.pickObjects(event.x(),event.y())

        self.mousex = event.x()
        self.mousey = event.y()

    def mouseMoveEvent(self,event):
        deltax = (event.x()-self.mousex)/2
        deltay = (event.y()-self.mousey)/2
        buttons = event.buttons()
        if buttons & QtCore.Qt.LeftButton:
            self.posx += deltax
            self.posy -= deltay
        if buttons & QtCore.Qt.RightButton:
            self.roty += deltax
            self.rotx += deltay
        self.mousex = event.x()
        self.mousey = event.y()
        self.updateGL()

class ChooseLevelDialog(QtGui.QDialog):
    def __init__(self,worldList):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle('Choose Level')
        self.currentLevel = None

        tree = QtGui.QTreeWidget()
        tree.setHeaderHidden(True)
        tree.currentItemChanged.connect(self.handleItemChange)
        tree.itemActivated.connect(self.handleItemActivated)
        
        nodes = []
        for world in worldList['WorldList'].subNodes():
            worldNode = QtGui.QTreeWidgetItem()
            worldNode.setText(0,'World '+str(world['WorldId']))
            for level in world['StageList'].subNodes():
                levelNode = QtGui.QTreeWidgetItem()
                levelNode.setData(0,QtCore.Qt.UserRole,level['StageName'])
                levelNode.setText(0,'Level '+str(level['CourseId'])+' ('+level['StageName']+')')
                worldNode.addChild(levelNode)
            nodes.append(worldNode)
        tree.addTopLevelItems(nodes)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)

        btn = self.buttonBox.addButton("Other file...",QtGui.QDialogButtonBox.ActionRole)
        btn.clicked.connect(self.openFile)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(tree)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.setMinimumWidth(340)
        self.setMinimumHeight(384)

    def openFile(self):
        fn = QtGui.QFileDialog.getOpenFileName(self,'Open Level','StageData','Level Archives (*.szs)')
        self.currentLevel = os.path.basename(str(fn))[:-8]
        if self.currentLevel:
            self.accept()

    def handleItemChange(self,current,previous):
        self.currentLevel = current.data(0,QtCore.Qt.UserRole).toString()
        if not self.currentLevel:
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)

    def handleItemActivated(self,item,column):
        self.currentLevel = item.data(0,QtCore.Qt.UserRole).toString()
        if self.currentLevel:
            self.accept()

class MainWindow(QtGui.QMainWindow):

    keyPresses = {0x1000020: 0}
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Super Mario 3D World")
        self.setGeometry(100,100,1080,720)

        self.setupMenu()
        
        self.qsettings = QtCore.QSettings("Kinnay","SM3DW Editor")
        self.gamePath = self.qsettings.value('gamePath').toPyObject()
        if not self.isValidGameFolder(self.gamePath):
            self.changeGamePath(True)

        self.loadStageList()
        self.levelSelect = ChooseLevelDialog(self.worldList)
        
        self.settings = SettingsWidget(self)
        self.setupGLScene()
        self.resizeWidgets()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateCamera)
        self.timer.start(30)

        self.show()

    def changeGamePath(self,disable=False):
        path = self.askGamePath()
        if path:
            self.qsettings.setValue('gamePath',path)
        else:
            if disable:
                self.openAction.setEnabled(False)
            QtGui.QMessageBox.warning(self,"Incomplete Folder","The folder you chose doesn't seem to contain the required files.")

    def askGamePath(self):
        QtGui.QMessageBox.information(self,'Game Path',"You're now going to be asked to pick a folder. Choose the folder that contains at least the StageData, ObjectData and SystemData folders of SM3DW. You can change this later in the settings menu.")
        folder = QtGui.QFileDialog.getExistingDirectory(self,"Choose Game Path")
        if not self.isValidGameFolder(folder):
            return None
        return folder

    def isValidGameFolder(self,folder):
        if not folder: return 0
        if not os.path.exists(folder+'\StageData'): return 0
        if not os.path.exists(folder+'\ObjectData'): return 0
        if not os.path.exists(folder+'\SystemData'): return 0
        if not os.path.isfile(folder+'\SystemData\StageList.szs'): return 0
        return 1

    def loadStageList(self):
        with open(self.gamePath+'/SystemData/StageList.szs','rb') as f:
            data = f.read()

        self.worldList = byml.BYML(sarc.extract(yaz0.decompress(data),'StageList.byml')).rootNode

    def showLevelDialog(self):
        if self.levelSelect.exec_():
            with open(self.gamePath+'/StageData/'+self.levelSelect.currentLevel+'Map1.szs','rb') as f:
                data = f.read()
            self.levelData = byml.BYML(sarc.extract(yaz0.decompress(data),self.levelSelect.currentLevel+'Map.byml'))
            self.loadLevel(self.levelData.rootNode)

    def loadLevel(self,levelData):
        stime = now()
        self.glWidget.reset()
        self.settings.reset()
        amount = len(levelData['ObjectList'])
        progress = QtGui.QProgressDialog(self)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setRange(0,amount)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setWindowTitle('Loading...')
        i = 0
        for obj in levelData['ObjectList'].subNodes():
            progress.setLabelText('Loading object '+str(i+1)+'/'+str(amount))
            progress.setValue(i)
            self.loadObject(obj)
            self.glWidget.updateGL()
            i+=1
        progress.setValue(i)
        self.saveAction.setEnabled(True)
        print now()-stime

    def loadObject(self,obj):
        modelName = obj['ModelName'] if obj['ModelName'] else obj['UnitConfigName']
        self.glWidget.addObject(obj,modelName)

    def setupMenu(self):
        self.openAction = QtGui.QAction("Open",self)
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.triggered.connect(self.showLevelDialog)

        self.saveAction = QtGui.QAction("Save",self)
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.triggered.connect(self.saveLevel)
        self.saveAction.setEnabled(False)

        pathAction = QtGui.QAction("Change Game Path",self)
        pathAction.setShortcut("Ctrl+G")
        pathAction.triggered.connect(self.changeGamePath)
        
        self.menubar = self.menuBar()
        fileMenu = self.menubar.addMenu("File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        settingsMenu = self.menubar.addMenu("Settings")
        settingsMenu.addAction(pathAction)

    def saveLevel(self):
        fn = QtGui.QFileDialog.getSaveFileName(self,'Save Level','StageData','Unpacked Levels (*.byml)')
        with open(fn,'wb') as f:
            self.levelData.saveChanges()
            f.write(self.levelData.data)

    def setupGLScene(self):
        self.glWidget = LevelWidget(self)
        self.glWidget.show()

    def resizeWidgets(self):
        self.glWidget.setGeometry(220,21,self.width(),self.height()-21)
        self.settings.setGeometry(0,21,220,self.height()-21)

    def resizeEvent(self,event):
        self.resizeWidgets()

    def updateCamera(self):
        spd = self.keyPresses[0x1000020]*2+1
        updateScene = False
        for key in self.keyPresses:
            if self.keyPresses[key]:
                if key == ord('I'): self.glWidget.rotx+=spd
                elif key == ord('K'): self.glWidget.rotx-=spd
                elif key == ord('O'): self.glWidget.roty+=spd
                elif key == ord('L'): self.glWidget.roty-=spd
                elif key == ord('P'): self.glWidget.rotz+=spd
                elif key == ord(';'): self.glWidget.rotz-=spd
                elif key == ord('A'): self.glWidget.posx-=spd
                elif key == ord('D'): self.glWidget.posx+=spd
                elif key == ord('S'): self.glWidget.posy-=spd
                elif key == ord('W'): self.glWidget.posy+=spd
                elif key == ord('Q'): self.glWidget.posz-=spd
                elif key == ord('E'): self.glWidget.posz+=spd
                updateScene = True

        if updateScene:
            self.glWidget.updateGL()

    def keyReleaseEvent(self,event):
        self.keyPresses[event.key()] = 0

    def keyPressEvent(self,event):
        self.keyPresses[event.key()] = 1

    def wheelEvent(self,event):
        self.glWidget.posz += event.delta()/15
        self.glWidget.updateGL()

def main():
    global window
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
