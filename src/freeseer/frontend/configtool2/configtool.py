#!/usr/bin/python
# -*- coding: utf-8 -*-

# freeseer - vga/presentation capture software
#
#  Copyright (C) 2011  Free and Open Source Software Learning Centre
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
# http://wiki.github.com/fosslc/freeseer/

from os import listdir;
from sys import *

from PyQt4 import QtGui, QtCore

from freeseer import project_info
from freeseer.framework.core import *

from configtoolui import *
from generalui import *
from pluginloader import *

__version__ = project_info.VERSION

class ConfigTool(QtGui.QDialog):
    '''
    ConfigTool is used to tune settings used by the Freeseer Application
    '''

    def __init__(self, core=None):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_ConfigTool()
        self.ui.setupUi(self)

        self.currentWidget = None
        self.mainWidgetLayout = QtGui.QVBoxLayout()
        self.ui.mainWidget.setLayout(self.mainWidgetLayout)
        
        # Load the General UI Widget
        self.generalWidget = QtGui.QWidget()
        self.generalui = Ui_General()
        self.generalui.setupUi(self.generalWidget)
        
        # Load Plugin Loader UI components
        self.pluginloaderWidget = QtGui.QWidget()
        self.pluginloader = Ui_PluginLoader()
        self.pluginloader.setupUi(self.pluginloaderWidget)

        # connections
        self.connect(self.ui.optionsWidget, QtCore.SIGNAL('itemSelectionChanged()'), self.change_option)
        self.connect(self.pluginloader.listWidget, QtCore.SIGNAL('itemChanged(QListWidgetItem *)'), self.set_plugin_state)

        # load core
        self.core = FreeseerCore()
        
        # get the config
        self.config = self.core.get_config()
        # get the plugin manager
        self.plugman = self.core.get_plugin_manager()
        
        # load active plugin widgets
        self.load_plugin_widgets()
        
        # Start off with displaying the General Settings
        items = self.ui.optionsWidget.findItems("General", QtCore.Qt.MatchExactly)
        if len(items) > 0:
            item = items[0]
            self.ui.optionsWidget.setCurrentItem(item)
        
    def change_option(self):
        option = self.ui.optionsWidget.currentItem().text(0)
        
        if self.currentWidget is not None:
            self.mainWidgetLayout.removeWidget(self.currentWidget)
            self.currentWidget.hide()
          
        if option == "General":
            self.load_general_widget()
        elif option == "Plugins":
            pass  
        elif option == "AudioInput":
            self.load_option_audioinput_plugins()
        elif option == "AudioMixer":
            self.load_option_audiomixer_plugins()
        elif option == "VideoInput":
            self.load_option_videoinput_plugins()
        elif option == "VideoMixer":
            self.load_option_videomixer_plugins()
        elif option == "Output":
            self.load_option_output_plugins()
        else:
            plugin_name = str(self.ui.optionsWidget.currentItem().text(0))
            plugin_category = str(self.ui.optionsWidget.currentItem().text(1))
            
            plugin = self.plugman.plugmanc.getPluginByName(plugin_name, plugin_category)
            self.show_plugin_widget(plugin)
        
    def load_general_widget(self):
        self.mainWidgetLayout.addWidget(self.generalWidget)
        self.currentWidget = self.generalWidget
        self.currentWidget.show()
        
        # Set up Audio
        if self.config.enable_audio_recoding == True:
            self.generalui.checkBoxAudioMixer.setChecked(True)
        else:
            self.generalui.checkBoxAudioMixer.setChecked(False)
            
        self.generalui.comboBoxAudioMixer.clear()
        plugins = self.plugman.plugmanc.getPluginsOfCategory("AudioMixer")
        for plugin in plugins:
            if plugin.is_activated:
                self.generalui.comboBoxAudioMixer.addItem(plugin.plugin_object.get_name())
        
        # Set up Video
        if self.config.enable_video_recoding == True:
            self.generalui.checkBoxVideoMixer.setChecked(True)
        else:
            self.generalui.checkBoxVideoMixer.setChecked(False)
            
        self.generalui.comboBoxVideoMixer.clear()
        plugins = self.plugman.plugmanc.getPluginsOfCategory("VideoMixer")
        for plugin in plugins:
            if plugin.is_activated:
                self.generalui.comboBoxVideoMixer.addItem(plugin.plugin_object.get_name())
        
        # Recording Directory Settings
        self.generalui.lineEditRecordDirectory.setText(self.config.videodir)
        
        # Load Auto Hide Settings
        if self.config.auto_hide == True:
            self.generalui.checkBoxAutoHide.setChecked(True)
        else:
            self.generalui.checkBoxAutoHide.setChecked(False)
        
    def load_plugin_list(self, plugin_type):
        self.pluginloader.listWidget.clear()
        for plugin in self.plugman.plugmanc.getPluginsOfCategory(plugin_type):
            item = QtGui.QListWidgetItem()
            item.setText(plugin.plugin_object.get_name())
            
            flags = QtCore.Qt.ItemFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setFlags(flags)
            
            if plugin.is_activated:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            
            self.pluginloader.listWidget.addItem(item)

    def load_option_audioinput_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("AudioInput")
            
    def load_option_audiomixer_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("AudioMixer")
        
    def load_option_videoinput_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("VideoInput")
            
    def load_option_videomixer_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("VideoMixer")
    
    def load_option_output_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()
        
        self.load_plugin_list("Output")

    def set_plugin_state(self, plugin):
        
        plugin_name = str(plugin.text())
        plugin_category = str(self.ui.optionsWidget.currentItem().text(0))
        
        if plugin.checkState() == 2:
            self.plugman.activate_plugin(plugin_name, plugin_category)
            self.add_plugin_widget(plugin_name, plugin_category)
        else:
            self.plugman.deactivate_plugin(plugin_name, plugin_category)
            self.del_plugin_widget(plugin_name)
    
    def load_plugin_widgets(self):
        categories = self.plugman.plugmanc.getCategories()
        for category in categories:
            plugins = self.plugman.plugmanc.getPluginsOfCategory(category)
            for plugin in plugins:
                if plugin.is_activated:
                    plugin_name = plugin.plugin_object.get_name()
                    self.add_plugin_widget(plugin_name, category)
    
    def add_plugin_widget(self, plugin_name, plugin_category):
        plugin = self.plugman.plugmanc.getPluginByName(plugin_name, plugin_category)
        if plugin.plugin_object.get_widget() is not None:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, plugin_name)
            item.setText(1, plugin_category)
            self.ui.optionsWidget.addTopLevelItem(item)
    
    def del_plugin_widget(self, plugin_name):
        items = self.ui.optionsWidget.findItems(plugin_name, QtCore.Qt.MatchExactly)
        if len(items) > 0:
            item = items[0]
            index = self.ui.optionsWidget.indexOfTopLevelItem(item)
            self.ui.optionsWidget.takeTopLevelItem(index)
        
    def show_plugin_widget(self, plugin):
        
        self.currentWidget = plugin.plugin_object.get_widget()
        if self.currentWidget is not None:
            self.mainWidgetLayout.addWidget(self.currentWidget)
            self.currentWidget.show()
