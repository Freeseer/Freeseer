#!/usr/bin/python
# -*- coding: utf-8 -*-

# freeseer - vga/presentation capture software
#
#  Copyright (C) 2011, 2014  Free and Open Source Software Learning Centre
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

# PyQt modules
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QStringList
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAbstractItemView
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QCompleter
from PyQt4.QtGui import QDataWidgetMapper
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QHeaderView
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QSortFilterProxyModel
from PyQt4.QtGui import QTableView
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget

# Freeseer modules
from freeseer.framework.presentation import Presentation
from freeseer.frontend.qtcommon.FreeseerApp import FreeseerApp

# TalkEditor modules
from freeseer.frontend.talkeditor.CommandButtons import CommandButtons
from freeseer.frontend.talkeditor.TalkDetailsWidget import TalkDetailsWidget
from freeseer.frontend.talkeditor.ImportTalksWidget import ImportTalksWidget

log = logging.getLogger(__name__)


class TalkEditorApp(FreeseerApp):
    '''Freeseer talk database editor main gui class'''
    def __init__(self, config, db):
        FreeseerApp.__init__(self)

        self.config = config
        self.db = db

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
        self.mainLayout.setAlignment(Qt.AlignTop)

        # Add custom widgets
        self.commandButtons = CommandButtons()
        self.tableView = QTableView()
        self.tableView.setSortingEnabled(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.talkDetailsWidget = TalkDetailsWidget()
        self.importTalksWidget = ImportTalksWidget()
        self.mainLayout.addWidget(self.importTalksWidget)
        #self.mainLayout.addLayout(self.titleLayout)
        self.mainLayout.addWidget(self.commandButtons)
        self.mainLayout.addWidget(self.tableView)
        self.mainLayout.addWidget(self.talkDetailsWidget)
        self.mainLayout.addWidget(self.importTalksWidget)
        # --- End Layout

        # Initialize geometry, to be used for restoring window positioning.
        self.geometry = None

        #
        # Setup Menubar
        #
        self.actionExportCsv = QAction(self)
        self.actionExportCsv.setObjectName('actionExportCsv')
        self.actionRemoveAll = QAction(self)
        self.actionRemoveAll.setObjectName('actionRemoveAll')

        # Actions
        self.menuFile.insertAction(self.actionExit, self.actionExportCsv)
        self.menuFile.insertAction(self.actionExit, self.actionRemoveAll)
        # --- End Menubar

        #
        # TableView Connections
        #
        self.connect(self.tableView, SIGNAL('activated(const QModelIndex)'), self.talk_selected)
        self.connect(self.tableView, SIGNAL('selected(const QModelIndex)'), self.talk_selected)
        self.connect(self.tableView, SIGNAL('clicked(const QModelIndex)'), self.talk_selected)

        # Import Widget
        self.connect(self.importTalksWidget.csvRadioButton, SIGNAL('toggled(bool)'), self.toggle_import)
        self.connect(self.importTalksWidget.importButton, SIGNAL('clicked()'), self.import_talks)
        self.connect(self.importTalksWidget.cancelButton, SIGNAL('clicked()'), self.hide_import_talks_widget)
        self.importTalksWidget.setHidden(True)
        self.connect(self.importTalksWidget.csvFileSelectButton, SIGNAL('clicked()'), self.csv_file_select)
        self.connect(self.importTalksWidget.csvLineEdit, SIGNAL('returnPressed()'),
            self.importTalksWidget.importButton.click)
        self.connect(self.importTalksWidget.rssLineEdit, SIGNAL('returnPressed()'),
            self.importTalksWidget.importButton.click)
        self.connect(self.actionExportCsv, SIGNAL('triggered()'), self.export_talks_to_csv)
        self.connect(self.actionRemoveAll, SIGNAL('triggered()'), self.confirm_reset)

        # Command Buttons
        self.connect(self.commandButtons.addButton, SIGNAL('clicked()'), self.confirm_add)
        self.connect(self.commandButtons.removeButton, SIGNAL('clicked()'), self.remove_talk)
        self.connect(self.commandButtons.removeAllButton, SIGNAL('clicked()'), self.confirm_reset)
        self.connect(self.commandButtons.importButton, SIGNAL('clicked()'), self.show_import_talks_widget)
        self.connect(self.commandButtons.exportButton, SIGNAL('clicked()'), self.export_talks_to_csv)
        self.connect(self.commandButtons.searchButton, SIGNAL('clicked()'), self.search_talks)
        self.connect(self.commandButtons.searchLineEdit, SIGNAL('textEdited(QString)'), self.search_talks)
        self.connect(self.commandButtons.searchLineEdit, SIGNAL('returnPressed()'), self.search_talks)

        # Talk Details Buttons
        self.connect(self.talkDetailsWidget.saveButton, SIGNAL('clicked()'), self.add_or_update_talk)

        # Talk Details Widget
        self.connect(self.talkDetailsWidget.titleLineEdit, SIGNAL('textEdited(const QString)'), self.enable_save)
        self.connect(self.talkDetailsWidget.presenterLineEdit, SIGNAL('textEdited(const QString)'), self.enable_save)
        self.connect(self.talkDetailsWidget.categoryLineEdit, SIGNAL('textEdited(const QString)'), self.enable_save)
        self.connect(self.talkDetailsWidget.eventLineEdit, SIGNAL('textEdited(const QString)'), self.enable_save)
        self.connect(self.talkDetailsWidget.roomLineEdit, SIGNAL('textEdited(const QString)'), self.enable_save)
        self.connect(self.talkDetailsWidget.descriptionTextEdit, SIGNAL('modificationChanged(bool)'), self.enable_save)
        self.connect(self.talkDetailsWidget.dateEdit, SIGNAL('dateChanged(const QDate)'), self.enable_save)
        self.connect(self.talkDetailsWidget.timeEdit, SIGNAL('timeChanged(const QTime)'), self.enable_save)

        # Load default language
        actions = self.menuLanguage.actions()
        for action in actions:
            if action.data().toString() == self.config.default_language:
                action.setChecked(True)
                self.translate(action)
                break

        # Load Talk Database
        self.load_presentations_model()

        # Setup Autocompletion
        self.update_autocomple_fields()

        self.talkDetailsWidget.saveButton.setEnabled(False)

        # Select first item
        #self.tableView.setCurrentIndex(self.proxy.index(0,0))
        #self.talk_selected(self.proxy.index(0,0))

    #
    # Translation
    #
    def retranslate(self):
        self.setWindowTitle(self.app.translate("TalkEditorApp", "Freeseer Talk Editor"))

        #
        # Reusable Strings
        #
        self.confirmDBClearTitleString = self.app.translate("TalkEditorApp", "Remove All Talks from Database")
        self.confirmDBClearQuestionString = self.app.translate("TalkEditorApp",
                                                               "Are you sure you want to clear the DB?")
        self.confirmTalkDetailsClearTitleString = self.app.translate("TalkEditorApp", "Unsaved Data")
        self.confirmTalkDetailsClearQuestionString = self.app.translate("TalkEditorApp",
                                                                        "Unsaved talk details will be lost. Continue?")
        # --- End Reusable Strings

        #
        # Menubar
        #
        self.actionExportCsv.setText(self.app.translate("TalkEditorApp", "&Export to CSV"))
        self.actionRemoveAll.setText(self.app.translate("TalkEditorApp", "&Remove All Talks"))

        # --- End Menubar

        #
        # TalkDetailsWidget
        #
        self.talkDetailsWidget.titleLabel.setText(self.app.translate("TalkEditorApp", "Title"))
        self.talkDetailsWidget.presenterLabel.setText(self.app.translate("TalkEditorApp", "Presenter"))
        self.talkDetailsWidget.categoryLabel.setText(self.app.translate("TalkEditorApp", "Category"))
        self.talkDetailsWidget.eventLabel.setText(self.app.translate("TalkEditorApp", "Event"))
        self.talkDetailsWidget.roomLabel.setText(self.app.translate("TalkEditorApp", "Room"))
        self.talkDetailsWidget.dateLabel.setText(self.app.translate("TalkEditorApp", "Date"))
        self.talkDetailsWidget.timeLabel.setText(self.app.translate("TalkEditorApp", "Time"))
        # --- End TalkDetailsWidget

        #
        # Import Talks Widget Translations
        #
        self.importTalksWidget.rssRadioButton.setText(self.app.translate("TalkEditorApp", "RSS URL"))
        self.importTalksWidget.csvRadioButton.setText(self.app.translate("TalkEditorApp", "CSV File"))
        self.importTalksWidget.importButton.setText(self.app.translate("TalkEditorApp", "Import"))
        # --- End Talks Widget Translations

        #
        # Command Button Translations\
        #
        self.commandButtons.importButton.setText(self.app.translate("TalkEditorApp", "Import"))
        self.commandButtons.exportButton.setText(self.app.translate("TalkEditorApp", "Export"))
        self.commandButtons.addButton.setText(self.app.translate("TalkEditorApp", "Add New Talk"))
        self.commandButtons.removeButton.setText(self.app.translate("TalkEditorApp", "Remove"))
        self.commandButtons.removeAllButton.setText(self.app.translate("TalkEditorApp", "Remove All"))
        # --- End Command Butotn Translations

        #
        # Search Widget Translations
        #
        self.commandButtons.searchButton.setText(self.app.translate("TalkEditorApp", "Search"))
        # --- End Command Button Translations

    def load_presentations_model(self):
        # Load Presentation Model
        self.presentationModel = self.db.get_presentations_model()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.presentationModel)
        self.tableView.setModel(self.proxy)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # Fill table whitespace.
        self.tableView.horizontalHeader().setStretchLastSection(False)
        self.tableView.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        # Hide the ID field
        self.tableView.setColumnHidden(0, True)

        # Map data to widgets
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.proxy)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.addMapping(self.talkDetailsWidget.titleLineEdit, 1)
        self.mapper.addMapping(self.talkDetailsWidget.presenterLineEdit, 2)
        self.mapper.addMapping(self.talkDetailsWidget.categoryLineEdit, 4)
        self.mapper.addMapping(self.talkDetailsWidget.eventLineEdit, 5)
        self.mapper.addMapping(self.talkDetailsWidget.roomLineEdit, 6)
        self.mapper.addMapping(self.talkDetailsWidget.descriptionTextEdit, 3)
        self.mapper.addMapping(self.talkDetailsWidget.dateEdit, 7)
        self.mapper.addMapping(self.talkDetailsWidget.timeEdit, 8)

        # Load StringLists
        self.titleList = QStringList(self.db.get_string_list("Title"))
        #self.speakerList = QStringList(self.db.get_speaker_list())
        #self.categoryList = QStringList(self.db.get_category_list())
        #self.eventList = QStringList(self.db.get_event_list())
        #self.roomList = QStringList(self.db.get_room_list())

        #Disble input
        self.talkDetailsWidget.disable_input_fields()

    def search_talks(self):
        # The default value is 0. If the value is -1, the keys will be read from all columns.
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterFixedString(self.commandButtons.searchLineEdit.text())

    def talk_selected(self, model):
        self.mapper.setCurrentIndex(model.row())
        self.talkDetailsWidget.enable_input_fields()
        self.talkDetailsWidget.saveButton.setEnabled(False)

    def toggle_import(self):
        if self.importTalksWidget.csvRadioButton.isChecked():
            self.importTalksWidget.csvLineEdit.setEnabled(True)
            self.importTalksWidget.csvFileSelectButton.setEnabled(True)
            self.importTalksWidget.rssLineEdit.setEnabled(False)
        else:
            self.importTalksWidget.csvLineEdit.setEnabled(False)
            self.importTalksWidget.csvFileSelectButton.setEnabled(False)
            self.importTalksWidget.rssLineEdit.setEnabled(True)

    def show_import_talks_widget(self):
        self.commandButtons.setHidden(True)
        self.tableView.setHidden(True)
        self.talkDetailsWidget.setHidden(True)
        self.importTalksWidget.setHidden(False)

    def hide_import_talks_widget(self):
        self.commandButtons.setHidden(False)
        self.tableView.setHidden(False)
        self.talkDetailsWidget.setHidden(False)
        self.importTalksWidget.setHidden(True)

    def add_or_update_talk(self):
        """Adds or updates a talk using data from the input fields

        If there is a talk selected, it updates that talk by calling update_talk
        Otherwise, it adds a new talk to the database by calling add_talk
        """
        selected_talk = self.tableView.currentIndex()
        if selected_talk.row() >= 0:  # The tableView index begins at 0 and is -1 by default
            self.update_talk(selected_talk)
        else:
            self.add_talk()

    def update_talk(self, selected_talk):
        """Updates the currently selected talk using data from the input fields"""
        presentation = self.create_presentation()

        selected_row = selected_talk.row()
        selected_column = selected_talk.column()
        talk_id = selected_talk.sibling(selected_row, 0).data().toString()

        self.db.update_presentation(talk_id, presentation)

        self.presentationModel.select()

        self.tableView.selectRow(selected_row)
        self.tableView.setCurrentIndex(self.proxy.index(selected_row, selected_column))
        self.mapper.setCurrentIndex(selected_row)

        self.talkDetailsWidget.saveButton.setEnabled(False)

    def add_talk(self):
        presentation = self.create_presentation()

        # Do not add talks if they are empty strings
        if (len(presentation.title) == 0):
            return
        self.db.insert_presentation(presentation)

        # Update Model, Refreshes TableView
        self.presentationModel.select()

        # Select Last Row
        self.tableView.selectRow(self.presentationModel.rowCount() - 1)
        self.tableView.setCurrentIndex(self.proxy.index(self.proxy.rowCount() - 1, 0))
        self.talk_selected(self.proxy.index(self.proxy.rowCount() - 1, 0))

        self.update_autocomple_fields()
        self.talkDetailsWidget.disable_input_fields()

    def create_presentation(self):
        """Creates and returns an instance of Presentation using data from the input fields"""
        date = self.talkDetailsWidget.dateEdit.date()
        time = self.talkDetailsWidget.timeEdit.time()
        return Presentation(
            unicode(self.talkDetailsWidget.titleLineEdit.text()).strip(),
            unicode(self.talkDetailsWidget.presenterLineEdit.text()).strip(),
            unicode(self.talkDetailsWidget.descriptionTextEdit.toPlainText()).strip(),
            unicode(self.talkDetailsWidget.categoryLineEdit.text()).strip(),
            unicode(self.talkDetailsWidget.eventLineEdit.text()).strip(),
            unicode(self.talkDetailsWidget.roomLineEdit.text()).strip(),
            unicode(date.toString(Qt.ISODate)),
            unicode(time.toString(Qt.ISODate)))

    def confirm_add(self):
        """Requests confirmation before clearing fields for a new talk."""
        if self.are_fields_enabled() and self.unsaved_details_exist():
            confirm = QMessageBox.question(self,
                                           self.confirmTalkDetailsClearTitleString,
                                           self.confirmTalkDetailsClearQuestionString,
                                           QMessageBox.Yes,
                                           QMessageBox.No)

            if confirm == QMessageBox.Yes:
                self.clear_talk_details_widget()
        else:
            self.clear_talk_details_widget()

    def clear_talk_details_widget(self):
        self.talkDetailsWidget.saveButton.setEnabled(True)
        self.talkDetailsWidget.enable_input_fields()
        self.talkDetailsWidget.titleLineEdit.clear()
        self.talkDetailsWidget.presenterLineEdit.clear()
        self.talkDetailsWidget.descriptionTextEdit.clear()
        self.talkDetailsWidget.categoryLineEdit.clear()
        #self.talkDetailsWidget.eventLineEdit.clear()
        #self.talkDetailsWidget.roomLineEdit.clear()

        self.presentationModel.select()

        self.talkDetailsWidget.saveButton.setEnabled(False)

    def remove_talk(self):
        try:
            rows_selected = self.tableView.selectionModel().selectedRows()
        except:
            return

        # Reversed because rows in list change position once row is removed
        for row in reversed(rows_selected):
            self.presentationModel.removeRow(row.row())

    def load_talk(self):
        try:
            self.tableView.currentIndex().row()
        except:
            return

        self.mapper.addMapping(self.talkDetailsWidget.roomLineEdit, 6)
        self.presentationModel.select()

    def reset(self):
        self.db.clear_database()
        self.presentationModel.select()

    def confirm_reset(self):
        """Presents a confirmation dialog to ask the user if they are sure they wish to remove the talk database.
        If Yes call the reset() function"""
        confirm = QMessageBox.question(self,
                                       self.confirmDBClearTitleString,
                                       self.confirmDBClearQuestionString,
                                       QMessageBox.Yes |
                                       QMessageBox.No,
                                       QMessageBox.No)

        if confirm == QMessageBox.Yes:
            self.reset()

    def add_talks_from_rss(self):
        rss_url = unicode(self.importTalksWidget.rssLineEdit.text())
        if rss_url:
            self.db.add_talks_from_rss(rss_url)
            self.presentationModel.select()
            self.hide_import_talks_widget()
        else:
            error = QMessageBox()
            error.setText("Please enter a RSS URL")
            error.exec_()

    def closeEvent(self, event):
        log.info('Exiting talk database editor...')
        self.geometry = self.saveGeometry()
        event.accept()

    def csv_file_select(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Select file', "", "*.csv")
        if fname:
            self.importTalksWidget.csvLineEdit.setText(fname)

    def add_talks_from_csv(self):
        fname = self.importTalksWidget.csvLineEdit.text()

        if fname:
            self.db.add_talks_from_csv(fname)
            self.presentationModel.select()
            self.hide_import_talks_widget()
        else:
            error = QMessageBox()
            error.setText("Please select a file")
            error.exec_()

    def import_talks(self):
        if self.importTalksWidget.csvRadioButton.isChecked():
            self.add_talks_from_csv()
        else:
            self.add_talks_from_rss()

        self.update_autocomple_fields()

    def export_talks_to_csv(self):
        fname = QFileDialog.getSaveFileName(self, 'Select file', "", "*.csv")
        if fname:
            self.db.export_talks_to_csv(fname)

    def update_autocomple_fields(self):
        self.titleList = QStringList(self.db.get_string_list("Title"))
        self.speakerList = QStringList(self.db.get_string_list("Speaker"))
        self.categoryList = QStringList(self.db.get_string_list("Category"))
        self.eventList = QStringList(self.db.get_string_list("Event"))
        self.roomList = QStringList(self.db.get_string_list("Room"))

        self.titleCompleter = QCompleter(self.titleList)
        self.titleCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        self.speakerCompleter = QCompleter(self.speakerList)
        self.speakerCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        self.categoryCompleter = QCompleter(self.categoryList)
        self.categoryCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        self.eventCompleter = QCompleter(self.eventList)
        self.eventCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        self.roomCompleter = QCompleter(self.roomList)
        self.roomCompleter.setCaseSensitivity(Qt.CaseInsensitive)

        self.talkDetailsWidget.titleLineEdit.setCompleter(self.titleCompleter)
        self.talkDetailsWidget.presenterLineEdit.setCompleter(self.speakerCompleter)
        self.talkDetailsWidget.categoryLineEdit.setCompleter(self.categoryCompleter)
        self.talkDetailsWidget.eventLineEdit.setCompleter(self.eventCompleter)
        self.talkDetailsWidget.roomLineEdit.setCompleter(self.roomCompleter)

    def are_fields_enabled(self):
        return (self.talkDetailsWidget.titleLineEdit.isEnabled() and
                self.talkDetailsWidget.presenterLineEdit.isEnabled() and
                self.talkDetailsWidget.categoryLineEdit.isEnabled() and
                self.talkDetailsWidget.eventLineEdit.isEnabled() and
                self.talkDetailsWidget.roomLineEdit.isEnabled() and
                self.talkDetailsWidget.dateEdit.isEnabled() and
                self.talkDetailsWidget.timeEdit.isEnabled())

    def unsaved_details_exist(self):
        """Checks if changes have been made to new/existing talk details

        Looks for text in the input fields and check the enabled state of the Save Talk button
        If the Save Talk button is enabled, the input fields contain modified values
        """
        return (self.talkDetailsWidget.saveButton.isEnabled() and
                (self.talkDetailsWidget.titleLineEdit.text() or
                self.talkDetailsWidget.presenterLineEdit.text() or
                self.talkDetailsWidget.categoryLineEdit.text() or
                self.talkDetailsWidget.descriptionTextEdit.toPlainText()))

    def enable_save(self):
        self.talkDetailsWidget.saveButton.setEnabled(True)
