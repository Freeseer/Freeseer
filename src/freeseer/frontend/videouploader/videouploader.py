'''
Created on Oct 15, 2011

@author: jord
'''

from PyQt4 import QtGui, QtCore

from os import path

from UploaderWidget import UploaderMenuBar, UploaderWidget
from MinimalistCore import MinimalistCore

from freeseer.framework.core import FreeseerCore
from freeseer.framework.metadata import FreeseerMetadataLoader

def retranslateOnLanguageChange(klass):
    def changeEvent(self, event):
        super(klass, self).changeEvent(event)
        assert isinstance(event, QtCore.QEvent)
        
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()
    
    klass.changeEvent = changeEvent
    return klass



@retranslateOnLanguageChange
class UploaderApp(QtGui.QMainWindow):
    '''
    Video Uploader Main window
    '''
    USE_NATIVE_DIALOG = True
    
#    def __init__(self, parent = None, flags = QtCore.Qt.WindowFlags()):
#        QtGui.QMainWindow.__init__(self, parent, flags)
    def __init__(self, core=None):
        # validate arguments #
        if core is None:
            core = MinimalistCore(self)
        assert isinstance(core, FreeseerCore) or isinstance(core, MinimalistCore)
        
        # superclass #
        QtGui.QMainWindow.__init__(self, None)
        
        # define members #
        self.core = core
        self.mainWidget = None
        self.menubar = None
        
        metadataloader = FreeseerMetadataLoader(core.plugman)
        
        self.__initGui()
        self.mainWidget.fileselect.filemodel.setMetadataLoader(metadataloader)
        self.menubar.setMetadataLoader(metadataloader)
        self.__loadDefaults()
        self.__loadSettings()
        self.__initConnections()
        self.__doInitialActions()
    
    def __initGui(self):
        self.resize(560, 600)
        
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/freeseer/freeseer_logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        
        ## main window area ##       
        self.mainWidget = UploaderWidget(self)
        self.mainWidget.setObjectName("mainWidget")
        self.setCentralWidget(self.mainWidget)
        
        ## menubar ##
        self.menubar = UploaderMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        
        ## toolbar ##
        # it looks ugly, so it's left out.
#        self.toolbar = QtGui.QToolBar(self)
#        self.__initToolbar()
        
        self.retranslate()
    
    def __initToolbar(self):
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.menubar.actionUpload)
        toolbarspacer = QtGui.QWidget(self)
        spacerpolicy = QtGui.QSizePolicy()
        spacerpolicy.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        toolbarspacer.setSizePolicy(spacerpolicy)
        self.toolbar.addWidget(toolbarspacer)
        self.toolbar.addAction(self.menubar.actionClose)
        
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        self.addToolBarBreak(QtCore.Qt.TopToolBarArea)
    
    def __loadDefaults(self):
        abspath = path.expanduser("~/Videos")
        self.mainWidget.fileselect.lineEdit_filepath.setText(abspath)
        
    def __loadSettings(self):
        #self.core.config.videodir
        pass
    
    def __initConnections(self):
        self.menubar.actionClose.triggered.connect(self.close)
        self.mainWidget.buttonbar.rejected.connect(self.close)
        self.menubar.actionUpload.triggered.connect(self.upload)
        self.mainWidget.buttonbar.accepted.connect(self.upload)
        
        self.menubar.actionOpen_Directory.triggered.connect(self.browse)
        self.mainWidget.fileselect.browse.connect(self.browse)
        self.mainWidget.fileselect.goDirectory.connect(self.directoryChanged)
        
        self.mainWidget.fileselect._initConnections()
        self.menubar.actionSelect_All.triggered.connect(
                                self.mainWidget.fileselect.filemodel.checkAll)
        self.menubar.actionSelect_None.triggered.connect(
                                self.mainWidget.fileselect.filemodel.checkNone)
        self.menubar.actionInvert_Selection.triggered.connect(
                                self.mainWidget.fileselect.filemodel.checkInvert)
    
    @QtCore.pyqtSlot()
    def upload(self):
        QtGui.QMessageBox.critical(self, "", "Not yet implemented")
        success = False
        
        if success:
            self.close()
    
    def browse(self):
        oldpath = self.mainWidget.fileselect.directory
        def setPath(newpath):
            self.mainWidget.fileselect.directory = newpath
            if oldpath != newpath:
                self.directoryChanged()
        
        if UploaderApp.USE_NATIVE_DIALOG:
            newpath = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Open Directory"), 
                                                             oldpath,
                                                             QtGui.QFileDialog.ShowDirsOnly)
            setPath(newpath)
            
        else:
            dialog = QtGui.QFileDialog(self, self.tr("Open Directory"), oldpath)
            dialog.setModal(True)
            dialog.setOption(QtGui.QFileDialog.ShowDirsOnly)
            dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
            dialog.setFileMode(QtGui.QFileDialog.Directory)
            # TODO: set these to favourites.
            sideurls = dialog.sidebarUrls()
            sideurls.append(QtCore.QUrl("file://" + path.expanduser(self.core.config.videodir)))
            dialog.setSidebarUrls(sideurls)
            dialog.directoryEntered.connect(setPath)
            dialog.show()
    
    def directoryChanged(self):
        self.mainWidget.fileselect.filemodel.setDirectory(self.mainWidget.fileselect.directory)

    def __doInitialActions(self):
        self.directoryChanged()

    def retranslate(self):
        self.setWindowTitle(self.tr("Freeseer Video Uploader"))
  
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    main = UploaderApp()
    main.show()
    sys.exit(app.exec_())