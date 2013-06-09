#!/usr/bin/python
# -*- coding: utf-8 -*-

# freeseer - vga/presentation capture software
#
#  Copyright (C) 2011-2013  Free and Open Source Software Learning Centre
#  http://fosslc.org
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

# For support, questions, suggestions or any other inquiries, visit:
# http://wiki.github.com/Freeseer/freeseer/

# python-libs
import logging
import sys

# PyQt modules
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QAbstractItemView
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QDataWidgetMapper
from PyQt4.QtGui import QFont
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QTableView
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

# Freeseer modules
from freeseer import settings, __version__
from freeseer.framework.config import Config
from freeseer.framework.database import QtDBConnector
from freeseer.framework.presentation import Presentation
from freeseer.frontend.qtcommon.FreeseerApp import FreeseerApp
from freeseer.frontend.qtcommon.Resource import resource_rc

# TalkEditor modules
from CommandButtons import CommandButtons
from TalkDetailsWidget import TalkDetailsWidget

log = logging.getLogger(__name__)
        
class TalkEditorApp(FreeseerApp):
    '''
    Freeseer talk database editor main gui class
    '''
    def __init__(self, backButton=False):
        FreeseerApp.__init__(self)
        
        icon = QIcon()
        icon.addPixmap(QPixmap(':/freeseer/logo.png'), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)
        self.resize(960, 600)
        
        #
        # Setup Layout
        #
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        # Add the Title Row (Use BOLD / Big Font)
        self.titleLayout = QHBoxLayout()
        self.talkEditorLabel = QLabel('Talk Editor')
        font = QFont('Helvetica', 24, QFont.Bold)
        self.talkEditorLabel.setFont(font)
        self.titleLayout.addWidget(self.talkEditorLabel)
        self.backButton = QPushButton('Back to Recorder')
        if backButton: # Only show the back button if requested by caller
            self.titleLayout.addWidget(self.backButton)
        self.titleLayout.addStretch()

        # Add custom widgets
        self.commandButtons = CommandButtons()
        self.tableView = QTableView()
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.talkDetailsWidget = TalkDetailsWidget()
        
        # 
        self.mainLayout.addLayout(self.titleLayout)
        self.mainLayout.addSpacing(10)
        self.mainLayout.addWidget(self.commandButtons)
        self.mainLayout.addWidget(self.tableView)
        self.mainLayout.addWidget(self.talkDetailsWidget)
        # --- End Layout
        
        # Initialize geometry, to be used for restoring window positioning.
        self.geometry = None

        # Load backends
        self.config = Config(settings.configdir)
        self.db = QtDBConnector(settings.configdir)
        
        #
        # Setup Menubar
        #
        self.actionExportCsv = QAction(self)
        self.actionExportCsv.setObjectName('actionExportCsv')
        
        # Actions
        self.menuFile.insertAction(self.actionExit, self.actionExportCsv)
        # --- End Menubar
        
        #
        # Talk Editor Connections
        #

        self.connect(self.tableView, SIGNAL('activated(const QModelIndex)'), self.talk_selected)

        # Add Talk Widget
        # self.connect(self.addTalkWidget.addButton, QtCore.SIGNAL('clicked()'), self.add_talk)
        # self.connect(self.addTalkWidget.cancelButton, QtCore.SIGNAL('clicked()'), self.hide_add_talk_widget)
        # self.addTalkWidget.setHidden(True)
        
        # Editor Widget
        # self.connect(self.editorWidget.rssLineEdit, QtCore.SIGNAL('returnPressed()'), self.editorWidget.rssPushButton.click)
        # self.connect(self.editorWidget.rssPushButton, QtCore.SIGNAL('clicked()'), self.add_talks_from_rss)
        # self.connect(self.editorWidget.addButton, QtCore.SIGNAL('clicked()'), self.show_add_talk_widget)
        # self.connect(self.editorWidget.removeButton, QtCore.SIGNAL('clicked()'), self.remove_talk)
        # self.connect(self.editorWidget.clearButton, QtCore.SIGNAL('clicked()'), self.confirm_reset)
        # self.connect(self.editorWidget.closeButton, QtCore.SIGNAL('clicked()'), self.close)
        
        # CSV Widget
        # self.connect(self.editorWidget.csvFileSelectButton, QtCore.SIGNAL('clicked()'), self.csv_file_select)
        # self.connect(self.editorWidget.csvPushButton, QtCore.SIGNAL('clicked()'), self.add_talks_from_csv)
        # self.connect(self.actionExportCsv, QtCore.SIGNAL('triggered()'), self.export_talks_to_csv)

        # Load default language
        actions = self.menuLanguage.actions()
        for action in actions:
            if action.data().toString() == self.config.default_language:
                action.setChecked(True)
                self.translate(action)
                break
        self.load_presentations_model()

    ###
    ### Translation
    ###
    def retranslate(self):
        self.setWindowTitle(self.app.translate("TalkEditorApp", "Freeseer Talk Editor"))
        
        #
        # Reusable Strings
        #
        self.confirmDBClearTitleString = self.app.translate("TalkEditorApp", "Clear Database")
        self.confirmDBClearQuestionString = self.app.translate("TalkEditorApp", "Are you sure you want to clear the DB?")
        # --- End Reusable Strings
        
        #
        # Menubar
        #
        self.actionExportCsv.setText(self.app.translate("TalkEditorApp", "&Export to CSV"))
        # --- End Menubar
        
        #
        # AddTalkWidget
        #
        # self.addTalkWidget.addTalkGroupBox.setTitle(self.app.translate("TalkEditorApp", "Add Talk"))
        # self.addTalkWidget.titleLabel.setText(self.app.translate("TalkEditorApp", "Title"))
        # self.addTalkWidget.presenterLabel.setText(self.app.translate("TalkEditorApp", "Presenter"))
        # self.addTalkWidget.eventLabel.setText(self.app.translate("TalkEditorApp", "Event"))
        # self.addTalkWidget.roomLabel.setText(self.app.translate("TalkEditorApp", "Room"))
        # self.addTalkWidget.dateLabel.setText(self.app.translate("TalkEditorApp", "Date"))
        # self.addTalkWidget.timeLabel.setText(self.app.translate("TalkEditorApp", "Time"))
        # self.addTalkWidget.addButton.setText(self.app.translate("TalkEditorApp", "Add"))
        # self.addTalkWidget.cancelButton.setText(self.app.translate("TalkEditorApp", "Cancel"))
        # --- End AddTalkWidget
        
        #
        # EditorWidget
        #
        # self.editorWidget.rssLabel.setText(self.app.translate("TalkEditorApp", "URL"))
        # self.editorWidget.rssPushButton.setText(self.app.translate("TalkEditorApp", "Load talks from RSS"))
        # self.editorWidget.csvLabel.setText(self.app.translate("TalkEditorApp", "File"))
        # self.editorWidget.csvPushButton.setText(self.app.translate("TalkEditorApp", "Load talks from CSV"))
        # self.editorWidget.addButton.setText(self.app.translate("TalkEditorApp", "Add"))
        # self.editorWidget.removeButton.setText(self.app.translate("TalkEditorApp", "Remove"))
        # self.editorWidget.clearButton.setText(self.app.translate("TalkEditorApp", "Clear"))
        # self.editorWidget.closeButton.setText(self.app.translate("TalkEditorApp", "Close"))
        # --- End EditorWidget
    
    def load_presentations_model(self):
        # Load Presentation Model
        self.presentationModel = self.db.get_presentations_model()
        self.tableView.setModel(self.presentationModel)

        # Hide the ID field
        self.tableView.setColumnHidden(0, True)

        # Map data to widgets
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.presentationModel)
        self.mapper.addMapping(self.talkDetailsWidget.titleLineEdit, 1)
        self.mapper.addMapping(self.talkDetailsWidget.presenterLineEdit, 2)
        self.mapper.addMapping(self.talkDetailsWidget.categoryLineEdit, 4)
        self.mapper.addMapping(self.talkDetailsWidget.eventLineEdit, 5)
        self.mapper.addMapping(self.talkDetailsWidget.roomLineEdit, 6)
        self.mapper.addMapping(self.talkDetailsWidget.descriptionTextEdit, 3)
    
    def talk_selected(self, model):
        self.mapper.setCurrentIndex(model.row())

    def show_add_talk_widget(self):
        self.editorWidget.setHidden(True)
        self.addTalkWidget.setHidden(False)
        
    def hide_add_talk_widget(self):
        self.editorWidget.setHidden(False)
        self.addTalkWidget.setHidden(True)
    
    def add_talk(self):
        date = self.addTalkWidget.dateEdit.date()
        time = self.addTalkWidget.timeEdit.time()
        datetime = QtCore.QDateTime(date, time)
        presentation = Presentation(unicode(self.addTalkWidget.titleLineEdit.text()),
                                    unicode(self.addTalkWidget.presenterLineEdit.text()),
                                    "", # description
                                    "", # level
                                    unicode(self.addTalkWidget.eventLineEdit.text()),
                                    unicode(self.addTalkWidget.roomLineEdit.text()),
                                    unicode(datetime.toString(QtCore.Qt.ISODate)))
        
        # Do not add talks if they are empty strings
        if (len(presentation.title) == 0): return

        self.db.insert_presentation(presentation)

        # cleanup
        self.addTalkWidget.titleLineEdit.clear()
        self.addTalkWidget.presenterLineEdit.clear()

        self.presentationModel.select()
        
        self.hide_add_talk_widget()

    def remove_talk(self):
        try:
            row_clicked = self.editorWidget.editor.currentIndex().row()
        except:
            return
        
        self.presentationModel.removeRow(row_clicked)
        self.presentationModel.select()
        
    def reset(self):
        self.db.clear_database()
        self.presentationModel.select()
        
    def confirm_reset(self):
        """
        Presents a confirmation dialog to ask the user if they are sure they
        wish to remove the talk database.
        
        If Yes call the reset() function.
        """
        confirm = QtGui.QMessageBox.question(self,
                    self.confirmDBClearTitleString,
                    self.confirmDBClearQuestionString,
                    QtGui.QMessageBox.Yes | 
                    QtGui.QMessageBox.No,
                    QtGui.QMessageBox.No)
        
        if confirm == QtGui.QMessageBox.Yes:
            self.reset()
            
    def add_talks_from_rss(self):
        rss_url = unicode(self.editorWidget.rssLineEdit.text())
        self.db.add_talks_from_rss(rss_url)
        self.presentationModel.select()

    def closeEvent(self, event):
        log.info('Exiting talk database editor...')
        self.geometry = self.saveGeometry()
        event.accept()
    
    def csv_file_select(self):
        dirpath = str(self.editorWidget.csvLineEdit.text())
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Select file', "", "*.csv")
        if fname:
            self.editorWidget.csvLineEdit.setText(fname)    
    
    def add_talks_from_csv(self):
        fname = self.editorWidget.csvLineEdit.text()
        
        if fname:
            self.db.add_talks_from_csv(fname)
            self.presentationModel.select()
    
    def export_talks_to_csv(self):
        dirpath = str(self.editorWidget.csvLineEdit.text())
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Select file', "", "*.csv")
        if fname:
            self.db.export_talks_to_csv(fname)
