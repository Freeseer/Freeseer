'''
freeseer - vga/presentation capture software

Copyright (C) 2013  Free and Open Source Software Learning Centre
http://fosslc.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

For support, questions, suggestions or any other inquiries, visit:
http://wiki.github.com/Freeseer/freeseer/

@author: Aaron Brubacher
'''

import ConfigParser
import pygst
pygst.require('0.10')
import gst
from PyQt4 import QtGui, QtCore

from freeseer.framework.plugin import IAudioMixer

class MultiAudio(IAudioMixer):
    name = 'Multiple Audio Inputs'
    os = ['linux', 'linux2', 'win32', 'cygwin', 'darwin']
    input1 = None
    input2 = None
    widget = None
    
    def get_audiomixer_bin(self):
        mixerbin = gst.Bin()
        
        audiomixer = gst.element_factory_make('adder', 'audiomixer')
        mixerbin.add(audiomixer)
        
        # ghost pads
        sinkpad1 = audiomixer.get_pad('sink%d')
        sink_ghostpad1 = gst.GhostPad('sink1', sinkpad1)
        mixerbin.add_pad(sink_ghostpad1)
        
        sinkpad2 = audiomixer.get_pad('sink%d')
        sink_ghostpad2 = gst.GhostPad('sink2', sinkpad2)
        mixerbin.add_pad(sink_ghostpad2)
        
        srcpad = audiomixer.get_pad('src')
        src_ghostpad = gst.GhostPad('src', srcpad)
        mixerbin.add_pad(src_ghostpad)
        
        return mixerbin

    def get_inputs(self):
        inputs = [(self.input1, 0), (self.input2, 1)]
        return inputs
    
    def load_inputs(self, player, mixer, inputs):
        input1 = inputs[0]
        player.add(input1)
        input1.link(mixer)
        
        input2 = inputs[1]
        player.add(input2)
        input2.link(mixer)
        
    def load_config(self, plugman):
        self.plugman = plugman
        
        try:
            self.input1 = self.plugman.get_plugin_option(self.CATEGORY, self.get_config_name(), 'Audio Input 1')
            self.input2 = self.plugman.get_plugin_option(self.CATEGORY, self.get_config_name(), 'Audio Input 2')
        except ConfigParser.NoSectionError:
            self.plugman.set_plugin_option(self.CATEGORY, self.get_config_name(), 'Audio Input 1', self.input1)
            self.plugman.set_plugin_option(self.CATEGORY, self.get_config_name(), 'Audio Input 2', self.input2)
        
    def get_widget(self):
        if self.widget is None:
            self.widget = QtGui.QWidget()
            layout = QtGui.QGridLayout()
            self.widget.setLayout(layout)
            
            self.source1_label = QtGui.QLabel('Source 1')
            self.source1_combobox = QtGui.QComboBox()
            self.source1_combobox.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
            self.source1_button = QtGui.QPushButton("Setup") 
            layout.addWidget(self.source1_label, 0, 0)
            layout.addWidget(self.source1_combobox, 0, 1)
            layout.addWidget(self.source1_button, 0, 2)
            self.widget.connect(self.source1_combobox, QtCore.SIGNAL('currentIndexChanged(const QString&)'), self.set_input1)
            self.widget.connect(self.source1_button, QtCore.SIGNAL('clicked()'), self.source1_setup)
            
            self.source2_label = QtGui.QLabel('Source 2')
            self.source2_combobox = QtGui.QComboBox()
            self.source2_combobox.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
            self.source2_button = QtGui.QPushButton("Setup") 
            layout.addWidget(self.source2_label, 1, 0)
            layout.addWidget(self.source2_combobox, 1, 1)
            layout.addWidget(self.source2_button, 1, 2)
            self.widget.connect(self.source2_combobox, QtCore.SIGNAL('currentIndexChanged(const QString&)'), self.set_input2)
            self.widget.connect(self.source2_button, QtCore.SIGNAL('clicked()'), self.source2_setup)
        return self.widget
    
    def widget_load_config(self, plugman):
        self.load_config(plugman)
        
        plugins = self.plugman.get_audioinput_plugins()
        self.widget.disconnect(self.source1_combobox, QtCore.SIGNAL('currentIndexChanged(const QString&)'), self.set_input1)
        self.widget.disconnect(self.source2_combobox, QtCore.SIGNAL('currentIndexChanged(const QString&)'), self.set_input2)
        self.source1_combobox.clear()
        self.source2_combobox.clear()
        for i, source in enumerate(plugins):
            name = source.plugin_object.get_name()
            self.source1_combobox.addItem(name)
            if self.input1 == name:
                self.source1_combobox.setCurrentIndex(i)
            self.source2_combobox.addItem(name)
            if self.input2 == name:
                self.source2_combobox.setCurrentIndex(i)
        self.widget.connect(self.source1_combobox, QtCore.SIGNAL('currentIndexChanged(const QString&)'), self.set_input1)
        self.widget.connect(self.source2_combobox, QtCore.SIGNAL('currentIndexChanged(const QString&)'), self.set_input2)
        
    def source1_setup(self):
        plugin_name = str(self.source1_combobox.currentText())
        plugin = self.plugman.get_plugin_by_name(plugin_name, "AudioInput")
        plugin.plugin_object.set_instance(0)
        plugin.plugin_object.get_dialog()
        
    def source2_setup(self):
        plugin_name = str(self.source2_combobox.currentText())
        plugin = self.plugman.get_plugin_by_name(plugin_name, "AudioInput")
        plugin.plugin_object.set_instance(1)
        plugin.plugin_object.get_dialog()
        
    def set_input1(self, input1):
        self.input1 = input1
        self.plugman.set_plugin_option(self.CATEGORY, self.get_config_name(), 'Audio Input 1', self.input1)
        
    def set_input2(self, input2):
        self.input2 = input2
        self.plugman.set_plugin_option(self.CATEGORY, self.get_config_name(), 'Audio Input 2', self.input2)
