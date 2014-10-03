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

import logging
import os
import re

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QInputDialog
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QMessageBox

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

from freeseer.framework.plugin import PluginManager, IOutput
from freeseer.frontend.qtcommon.FreeseerApp import FreeseerApp

from freeseer.frontend.qtcommon.AboutWidget import AboutWidget
from freeseer.frontend.configtool.AVWidget import AVWidget
from freeseer.frontend.configtool.ConfigToolWidget import ConfigToolWidget
from freeseer.frontend.configtool.GeneralWidget import GeneralWidget
from freeseer.frontend.configtool.PluginWidget import PluginWidget

log = logging.getLogger(__name__)


class ConfigToolApp(FreeseerApp):
    '''
    ConfigTool is used to tune settings used by the Freeseer Application
    '''

    def __init__(self, profile, config):
        FreeseerApp.__init__(self)

        # Load Config Stuff
        self.profile = profile
        self.config = config

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/freeseer/logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        # Initialize geometry, to be used for restoring window positioning.
        self.geometry = None

        self.mainWidget = ConfigToolWidget()
        self.setCentralWidget(self.mainWidget)

        self.currentWidget = None
        self.mainWidgetLayout = QtGui.QVBoxLayout()
        self.mainWidget.rightPanelWidget.setLayout(self.mainWidgetLayout)

        # Load all ConfigTool Widgets
        self.aboutWidget = AboutWidget()
        self.generalWidget = GeneralWidget()
        self.avWidget = AVWidget()
        self.pluginWidget = PluginWidget()

        self.plugman = PluginManager(profile)

        # XXX: Nasty hack to let our singleton plugins access the parent window
        #      for retranslate.
        for plugin in self.plugman.get_all_plugins():
            plugin.plugin_object.set_gui(self)

        # Custom Menu Items
        self.actionSaveProfile = QtGui.QAction(self)
        self.menuFile.insertAction(self.actionExit, self.actionSaveProfile)

        #
        # --- Language Related
        #
        # Fill in the langauges combobox and load the default language
        for language in self.languages:
            translator = QtCore.QTranslator()  # Create a translator to translate Language Display Text
            translator.load(":/languages/%s" % language)
            language_display_text = translator.translate("Translation", "Language Display Text")
            self.generalWidget.languageComboBox.addItem(language_display_text, language)

        # Load default language.
        actions = self.menuLanguage.actions()
        for action in actions:
            if action.data().toString() == self.config.default_language:
                action.setChecked(True)
                self.translate(action)
                break
        # --- End Language Related

        # connections
        self.connect(self.actionSaveProfile, QtCore.SIGNAL('triggered()'), self.show_save_profile_dialog)
        self.connect(self.mainWidget.closePushButton, QtCore.SIGNAL('clicked()'), self.close)
        self.connect(self.mainWidget.optionsTreeWidget, QtCore.SIGNAL('itemSelectionChanged()'), self.change_option)

        #
        # general tab connections
        #
        self.connect(self.generalWidget.languageComboBox, QtCore.SIGNAL('currentIndexChanged(int)'), self.set_default_language)
        self.connect(self.avWidget.fileDirPushButton, QtCore.SIGNAL('clicked()'), self.browse_video_directory)
        self.connect(self.avWidget.fileDirLineEdit, QtCore.SIGNAL('editingFinished()'), self.update_record_directory)
        self.connect(self.generalWidget.autoHideCheckBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_autohide)

        #
        # AV tab connections
        #
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_audiomixer_state)
        self.connect(self.avWidget.audioMixerComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_audiomixer)
        self.connect(self.avWidget.audioMixerSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_audio_mixer)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_videomixer_state)
        self.connect(self.avWidget.videoMixerComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_videomixer)
        self.connect(self.avWidget.videoMixerSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_video_mixer)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_record_to_file)
        self.connect(self.avWidget.fileComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_file_format)
        self.connect(self.avWidget.fileSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_file_format)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_record_to_stream)
        self.connect(self.avWidget.streamComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_stream_format)
        self.connect(self.avWidget.streamSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_stream_format)
        # GUI Disabling/Enabling Connections
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.audioMixerLabel.setEnabled)
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.audioMixerComboBox.setEnabled)
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.audioMixerSetupPushButton.setEnabled)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.videoMixerLabel.setEnabled)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.videoMixerComboBox.setEnabled)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.videoMixerSetupPushButton.setEnabled)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.fileLabel.setEnabled)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.fileComboBox.setEnabled)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.fileSetupPushButton.setEnabled)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.streamLabel.setEnabled)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.streamComboBox.setEnabled)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.streamSetupPushButton.setEnabled)

        self.retranslate()

        # Start off with displaying the General Settings
        items = self.mainWidget.optionsTreeWidget.findItems(self.generalString, QtCore.Qt.MatchExactly)
        if len(items) > 0:
            item = items[0]
            self.mainWidget.optionsTreeWidget.setCurrentItem(item)

    ###
    ### Translation
    ###

    def retranslate(self):
        self.setWindowTitle(self.app.translate("ConfigToolApp", "Freeseer ConfigTool"))

        #
        # Menu
        #
        self.saveProfileString = self.actionSaveProfile.setText(self.app.translate("ConfigToolApp", "Save Profile"))

        #
        # ConfigToolWidget
        #
        self.aboutString = self.app.translate("ConfigToolApp", "About")
        self.generalString = self.app.translate("ConfigToolApp", "General")
        self.avString = self.app.translate("ConfigToolApp", "Recording")
        self.pluginsString = self.app.translate("ConfigToolApp", "Plugins")
        self.audioInputString = self.app.translate("ConfigToolApp", "AudioInput")
        self.audioMixerString = self.app.translate("ConfigToolApp", "AudioMixer")
        self.videoInputString = self.app.translate("ConfigToolApp", "VideoInput")
        self.videoMixerString = self.app.translate("ConfigToolApp", "VideoMixer")
        self.outputString = self.app.translate("ConfigToolApp", "Output")

        self.mainWidget.optionsTreeWidget.topLevelItem(0).setText(0, self.generalString)
        self.mainWidget.optionsTreeWidget.topLevelItem(1).setText(0, self.avString)
        self.mainWidget.optionsTreeWidget.topLevelItem(2).setText(0, self.pluginsString)
        self.mainWidget.optionsTreeWidget.topLevelItem(3).setText(0, self.aboutString)
        self.mainWidget.closePushButton.setText(self.app.translate("ConfigToolApp", "Close"))
        # --- End ConfigToolWidget

        #
        # GeneralWidget
        #
        self.generalWidget.miscGroupBox.setTitle(self.app.translate("ConfigToolApp", "Miscellaneous"))
        self.generalWidget.languageLabel.setText(self.app.translate("ConfigToolApp", "Default Language"))
        self.generalWidget.autoHideCheckBox.setText(self.app.translate("ConfigToolApp", "Enable Auto-Hide"))
        # --- End GeneralWidget

        #
        # AV Widget
        #
        self.avWidget.title.setText(u"{0} {1} {2}".format(u'<h1>', self.app.translate("ConfigToolApp", "Recording"), u'</h1>'))

        self.avWidget.audioGroupBox.setTitle(self.app.translate("ConfigToolApp", "Audio Input"))
        self.avWidget.audioMixerLabel.setText(self.app.translate("ConfigToolApp", "Audio Mixer"))
        self.avWidget.audioMixerSetupPushButton.setToolTip(self.app.translate("ConfigToolApp", "Setup"))

        self.avWidget.videoGroupBox.setTitle(self.app.translate("ConfigToolApp", "Video Input"))
        self.avWidget.videoMixerLabel.setText(self.app.translate("ConfigToolApp", "Video Mixer"))
        self.avWidget.videoMixerSetupPushButton.setToolTip(self.app.translate("ConfigToolApp", "Setup"))

        self.avWidget.fileGroupBox.setTitle(self.app.translate("ConfigToolApp", "Record to File"))
        self.avWidget.fileDirLabel.setText(self.app.translate("ConfigToolApp", "Record Directory"))
        self.avWidget.fileDirPushButton.setText(u"{}...".format(self.app.translate("ConfigToolApp", "Browse")))
        self.avWidget.fileLabel.setText(self.app.translate("ConfigToolApp", "File Format"))
        self.avWidget.fileSetupPushButton.setToolTip(self.app.translate("ConfigToolApp", "Setup"))

        self.avWidget.streamGroupBox.setTitle(self.app.translate("ConfigToolApp", "Record to Stream"))
        self.avWidget.streamLabel.setText(self.app.translate("ConfigToolApp", "Stream Format"))
        self.avWidget.streamSetupPushButton.setToolTip(self.app.translate("ConfigToolApp", "Setup"))
        # --- End AV Widget

    ###
    ### Menu
    ###

    def show_save_profile_dialog(self):
        name, ok = QInputDialog().getText(self, "Save Profile", "Profile Name", QLineEdit.Normal)

        if ok:
            if re.match('^[\w-]+$', name):
                # TODO: This is a hack. Instead, there should be a option to
                # copy the current profile or something.
                pass
            else:
                QMessageBox.information(None, "Invalid name", "Invalid characters used. Only alphanumeric and dashes allowed.")

    ###
    ### General
    ###

    def change_option(self):
        option = self.mainWidget.optionsTreeWidget.currentItem().text(0)

        if self.currentWidget is not None:
            self.mainWidgetLayout.removeWidget(self.currentWidget)
            self.currentWidget.hide()

        if option == self.aboutString:
            self.load_about_widget()
        elif option == self.generalString:
            self.load_general_widget()
        elif option == self.avString:
            self.load_av_widget()
        elif option == self.pluginsString:
            self.load_plugins_widget()
        else:
            pass

    def load_about_widget(self):
        """Loads AboutWidget onto the configuration tool"""
        self.mainWidgetLayout.addWidget(self.aboutWidget)
        self.currentWidget = self.aboutWidget
        self.currentWidget.retranslate()
        self.currentWidget.show()

    def load_general_widget(self):
        self.mainWidgetLayout.addWidget(self.generalWidget)
        self.currentWidget = self.generalWidget
        self.currentWidget.show()

        # Load default language
        i = self.generalWidget.languageComboBox.findData(self.config.default_language)
        self.generalWidget.languageComboBox.setCurrentIndex(i)

        # Load Auto Hide Settings
        if self.config.auto_hide:
            self.generalWidget.autoHideCheckBox.setChecked(True)
        else:
            self.generalWidget.autoHideCheckBox.setChecked(False)

    def set_default_language(self, language):
        language_file = str(self.generalWidget.languageComboBox.itemData(language).toString())
        self.config.default_language = language_file
        self.config.save()

    def browse_video_directory(self):
        directory = self.avWidget.fileDirLineEdit.text()

        newDir = QtGui.QFileDialog.getExistingDirectory(self, "Select Video Directory", directory)
        if newDir == "":
            newDir = directory

        videodir = os.path.abspath(str(newDir))
        self.avWidget.fileDirLineEdit.setText(videodir)
        self.avWidget.fileDirLineEdit.emit(QtCore.SIGNAL("editingFinished()"))

    def update_record_directory(self):
        self.config.videodir = str(self.avWidget.fileDirLineEdit.text())
        self.config.save()

    def toggle_autohide(self, state):
        self.config.auto_hide = state
        self.config.save()

        # Make recordapp to update it's config
        # TODO: Surely there is a better way to do this

    ###
    ### AV Related
    ###

    def load_av_widget(self):
        self.mainWidgetLayout.addWidget(self.avWidget)
        self.currentWidget = self.avWidget
        self.currentWidget.show()

        #
        # Set up Audio
        #
        if self.config.enable_audio_recording:
            self.avWidget.audioGroupBox.setChecked(True)
        else:
            self.avWidget.audioGroupBox.setChecked(False)
            self.avWidget.audioMixerComboBox.setEnabled(False)
            self.avWidget.audioMixerSetupPushButton.setEnabled(False)

        n = 0  # Counter for finding Audio Mixer to set as current.
        self.avWidget.audioMixerComboBox.clear()
        plugins = self.plugman.get_audiomixer_plugins()
        for plugin in plugins:
            self.avWidget.audioMixerComboBox.addItem(plugin.plugin_object.get_name())
            if plugin.plugin_object.get_name() == self.config.audiomixer:
                self.avWidget.audioMixerComboBox.setCurrentIndex(n)
            n += 1

        #
        # Set up Video
        #
        if self.config.enable_video_recording:
            self.avWidget.videoGroupBox.setChecked(True)
        else:
            self.avWidget.videoGroupBox.setChecked(False)
            self.avWidget.videoMixerComboBox.setEnabled(False)
            self.avWidget.videoMixerSetupPushButton.setEnabled(False)

        n = 0  # Counter for finding Video Mixer to set as current.
        self.avWidget.videoMixerComboBox.clear()
        plugins = self.plugman.get_videomixer_plugins()
        for plugin in plugins:
            self.avWidget.videoMixerComboBox.addItem(plugin.plugin_object.get_name())
            if plugin.plugin_object.get_name() == self.config.videomixer:
                self.avWidget.videoMixerComboBox.setCurrentIndex(n)
            n += 1

        # Recording Directory Settings
        self.avWidget.fileDirLineEdit.setText(self.config.videodir)

        #
        # Set up File Format
        #
        if self.config.record_to_file:
            self.avWidget.fileGroupBox.setChecked(True)
        else:
            self.avWidget.fileGroupBox.setChecked(False)
            self.avWidget.fileComboBox.setEnabled(False)
            self.avWidget.fileSetupPushButton.setEnabled(False)

        n = 0  # Counter for finding File Format to set as current
        self.avWidget.fileComboBox.clear()
        plugins = self.plugman.get_output_plugins()
        for plugin in plugins:
            if plugin.plugin_object.get_recordto() == IOutput.FILE:
                self.avWidget.fileComboBox.addItem(plugin.plugin_object.get_name())
                if plugin.plugin_object.get_name() == self.config.record_to_file_plugin:
                    self.avWidget.fileComboBox.setCurrentIndex(n)
                n += 1

        #
        # Set up Stream Format
        #
        if self.config.record_to_stream:
            self.avWidget.streamGroupBox.setChecked(True)
        else:
            self.avWidget.streamGroupBox.setChecked(False)
            self.avWidget.streamComboBox.setEnabled(False)
            self.avWidget.streamSetupPushButton.setEnabled(False)

        n = 0  # Counter for finding Stream Format to set as current
        self.avWidget.streamComboBox.clear()
        plugins = self.plugman.get_output_plugins()
        for plugin in plugins:
            if plugin.plugin_object.get_recordto() == IOutput.STREAM:
                self.avWidget.streamComboBox.addItem(plugin.plugin_object.get_name())
                if plugin.plugin_object.get_name() == self.config.record_to_stream_plugin:
                    self.avWidget.streamComboBox.setCurrentIndex(n)
                n += 1

    def toggle_audiomixer_state(self, state):
        self.config.enable_audio_recording = state
        self.config.save()

    def change_audiomixer(self, audiomixer):
        self.config.audiomixer = audiomixer
        self.config.save()

    def setup_audio_mixer(self):
        mixer = str(self.avWidget.audioMixerComboBox.currentText())
        plugin = self.plugman.get_plugin_by_name(mixer, "AudioMixer")
        plugin.plugin_object.get_dialog()

    def toggle_videomixer_state(self, state):
        self.config.enable_video_recording = state
        self.config.save()

    def change_videomixer(self, videomixer):
        self.config.videomixer = videomixer
        self.config.save()

    def setup_video_mixer(self):
        mixer = str(self.avWidget.videoMixerComboBox.currentText())
        plugin = self.plugman.get_plugin_by_name(mixer, "VideoMixer")
        plugin.plugin_object.get_dialog()

    def toggle_record_to_file(self, state):
        self.config.record_to_file = state
        self.config.save()

    def change_file_format(self, format):
        self.config.record_to_file_plugin = format
        self.config.save()

    def setup_file_format(self):
        output = str(self.avWidget.fileComboBox.currentText())
        plugin = self.plugman.get_plugin_by_name(output, "Output")
        plugin.plugin_object.get_dialog()

    def toggle_record_to_stream(self, state):
        self.config.record_to_stream = state
        self.config.save()

    def change_stream_format(self, format):
        self.config.record_to_stream_plugin = format
        self.config.save()

    def setup_stream_format(self):
        output = str(self.avWidget.streamComboBox.currentText())
        plugin = self.plugman.get_plugin_by_name(output, "Output")
        plugin.plugin_object.get_dialog()

    ###
    ### Plugin Loader Related
    ###

    def load_plugins_widget(self):
        self.mainWidgetLayout.addWidget(self.pluginWidget)
        self.currentWidget = self.pluginWidget
        self.currentWidget.show()

        if (self.currentWidget.list.topLevelItem(0) is None):
            # Fill List

            # Audio Input Label
            QtGui.QTreeWidgetItem(self.currentWidget.list)
            self.currentWidget.list.topLevelItem(0).setText(0, "Audio Input")
            self.add_plugins_to_list("AudioInput", self.currentWidget.list.topLevelItem(0))

            # Audio Mixer Label
            QtGui.QTreeWidgetItem(self.currentWidget.list)
            self.currentWidget.list.topLevelItem(1).setText(0, "Audio Mixer")
            self.add_plugins_to_list("AudioMixer", self.currentWidget.list.topLevelItem(1))

            # Video Input Label
            QtGui.QTreeWidgetItem(self.currentWidget.list)
            self.currentWidget.list.topLevelItem(2).setText(0, "Video Input")
            self.add_plugins_to_list("VideoInput", self.currentWidget.list.topLevelItem(2))

            # Video Mixer Label
            QtGui.QTreeWidgetItem(self.currentWidget.list)
            self.currentWidget.list.topLevelItem(3).setText(0, "Video Mixer")
            self.add_plugins_to_list("VideoMixer", self.currentWidget.list.topLevelItem(3))

            # Output Label
            QtGui.QTreeWidgetItem(self.currentWidget.list)
            self.currentWidget.list.topLevelItem(4).setText(0, "Output")
            self.add_plugins_to_list("Output", self.currentWidget.list.topLevelItem(4))

            # Importer Label
            QtGui.QTreeWidgetItem(self.currentWidget.list)
            self.currentWidget.list.topLevelItem(5).setText(0, "Input")
            self.add_plugins_to_list("Importer", self.currentWidget.list.topLevelItem(5))

            self.currentWidget.list.expandAll()

    def add_plugins_to_list(self, plugin_type, parent):
        plugins = self.get_plugins(plugin_type)

        for i, plugin in enumerate(plugins):
            newItem = self.pluginWidget.getWidgetPlugin(plugin, plugin_type, self.plugman)
            parent.addChild(newItem)

    def get_plugins(self, plugin_type):
        """
        Returns a list of plugins of type

        Parameters:
            plugin_type - type of plugins to get

        Returns:
            list of plugins of type specified
        """
        plugins = []

        if plugin_type == "AudioInput":
            plugins = self.plugman.get_audioinput_plugins()
        elif plugin_type == "AudioMixer":
            plugins = self.plugman.get_audiomixer_plugins()
        elif plugin_type == "VideoInput":
            plugins = self.plugman.get_videoinput_plugins()
        elif plugin_type == "VideoMixer":
            plugins = self.plugman.get_videomixer_plugins()
        elif plugin_type == "Output":
            plugins = self.plugman.get_output_plugins()
        elif plugin_type == "Importer":
            plugins = self.plugman.get_importer_plugins()

        return plugins

    def show_plugin_widget_dialog(self, widget, name):
        """Shows the configuration dialog for a plugin."""
        self.dialog = QtGui.QDialog(self)

        self.dialog_layout = QtGui.QVBoxLayout()
        self.dialog_layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.dialog.setLayout(self.dialog_layout)
        self.dialog_layout.addWidget(widget)

        self.dialog.closeButton = QtGui.QPushButton("Close")
        self.dialog_layout.addWidget(self.dialog.closeButton)
        self.connect(self.dialog.closeButton, QtCore.SIGNAL('clicked()'), self.dialog.close)
        self.dialog.setWindowTitle(u'{} Setup'.format(name))
        self.dialog.setModal(True)
        self.dialog.show()

    def closeEvent(self, event):
        log.info('Exiting configtool...')
        self.geometry = self.saveGeometry()
        event.accept()
