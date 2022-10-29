# freeseer - vga/presentation capture software
#
#  Copyright (C) 2011, 2013  Free and Open Source Software Learning Centre
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
# http://github.com/Freeseer/freeseer/

'''
Desktop Source
--------------

A video input plugin that uses your desktop as the video source.

@author: Thanh Ha
'''
import logging
import sys

# GStreamer modules
import pygst
pygst.require("0.10")
import gst

# PyQt4 modules
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QDesktopWidget

# Freeseer modules
from freeseer.framework.plugin import IVideoInput
from freeseer.framework.area_selector import AreaSelector
from freeseer.framework.config import Config, options

# .freeseer-plugin custom modules
from . import widget

log = logging.getLogger(__name__)


class DesktopLinuxSrcConfig(Config):
    """Configuration settings for linux desktop video plugin."""

    # ximagesrc
    desktop = options.StringOption("Full")
    screen = options.IntegerOption(0)
    window = options.StringOption("")

    # Area Select
    start_x = options.IntegerOption(0)
    start_y = options.IntegerOption(0)
    end_x = options.IntegerOption(0)
    end_y = options.IntegerOption(0)


class DesktopLinuxSrc(IVideoInput):
    name = "Desktop Source"
    os = ["linux", "linux2", "win32", "cygwin"]
    CONFIG_CLASS = DesktopLinuxSrcConfig

    def get_videoinput_bin(self):
        """
        Return the video input object in gstreamer bin format.
        """
        bin = gst.Bin()  # Do not pass a name so that we can load this input more than once.

        videosrc = None

        if sys.platform.startswith("linux"):
            videosrc = gst.element_factory_make("ximagesrc", "videosrc")

            # Configure coordinates if we're not recording full desktop
            if self.config.desktop == "Area":
                videosrc.set_property("startx", self.config.start_x)
                videosrc.set_property("starty", self.config.start_y)
                videosrc.set_property("endx", self.config.end_x)
                videosrc.set_property("endy", self.config.end_y)
                log.debug('Recording Area start: %sx%s end: %sx%s',
                          self.config.start_x,
                          self.config.start_y,
                          self.config.end_x,
                          self.config.end_y)

            if self.config.desktop == "Window":
                videosrc.set_property("xname", self.config.window)

        elif sys.platform in ["win32", "cygwin"]:
            videosrc = gst.element_factory_make("dx9screencapsrc", "videosrc")

            # Configure coordinates if we're not recording full desktop
            if self.config.desktop == "Area":
                videosrc.set_property("x", self.config.start_x)
                videosrc.set_property("y", self.config.start_y)
                videosrc.set_property("width", self.config.end_x - self.config.start_x)
                videosrc.set_property("height", self.config.end_y - self.config.start_y)
                log.debug('Recording Area start: %sx%s end: %sx%s',
                          self.config.start_x,
                          self.config.start_y,
                          self.config.end_x,
                          self.config.end_y)

        bin.add(videosrc)

        colorspace = gst.element_factory_make("ffmpegcolorspace", "colorspace")
        bin.add(colorspace)
        videosrc.link(colorspace)

        # Setup ghost pad
        pad = colorspace.get_pad("src")
        ghostpad = gst.GhostPad("videosrc", pad)
        bin.add_pad(ghostpad)

        return bin

    def area_select(self):
        self.area_selector = AreaSelector(self)
        self.area_selector.show()
        self.gui.hide()
        self.gui.last_dialog.hide()
        self.widget.window().hide()

    def areaSelectEvent(self, start_x, start_y, end_x, end_y):
        if start_x <= end_x:
            self.config.start_x = start_x
            self.config.end_x = end_x
        else:
            self.config.start_x = end_x
            self.config.end_x = start_x

        if start_y <= end_y:
            self.config.start_y = start_y
            self.config.end_y = end_y
        else:
            self.config.start_y = end_y
            self.config.end_y = start_y

        self.config.save()
        log.debug('Area selector start: %sx%s end: %sx%s',
            self.config.start_x,
            self.config.start_y,
            self.config.end_x,
            self.config.end_y)
        # Automatically check the "Record Region" button.
        self.set_desktop_area()
        self.widget.areaButton.setChecked(True)
        self.widget.regionLabel.setText("{}x{} to {}x{}".format(
            self.config.start_x, self.config.start_y, self.config.end_x, self.config.end_y))

        self.gui.show()
        self.gui.last_dialog.show()
        self.widget.window().show()

    def get_widget(self):
        if self.widget is None:
            self.widget = widget.ConfigWidget()

        return self.widget

    def get_resolution_pixels(self):
        self.get_config()

        if self.config.desktop == "Full":
            app = QApplication.instance()
            screen_rect = app.desktop().screenGeometry()
            return screen_rect.width() * screen_rect.height()
        elif self.config.desktop == "Area":
            width = self.config.end_x - self.config.start_x
            height = self.config.end_y - self.config.start_y
            return width * height

    def __enable_connections(self):
        self.widget.connect(self.widget.desktopButton, SIGNAL('clicked()'), self.set_desktop_full)
        self.widget.connect(self.widget.areaButton, SIGNAL('clicked()'), self.set_desktop_area)
        self.widget.connect(self.widget.setAreaButton, SIGNAL('clicked()'), self.area_select)
        self.widget.connect(self.widget.screenSpinBox, SIGNAL('valueChanged(int)'), self.set_screen)

    def widget_load_config(self, plugman):
        self.get_config()

        if self.config.desktop == "Full":
            self.widget.desktopButton.setChecked(True)
        elif self.config.desktop == "Area":
            self.widget.areaButton.setChecked(True)

        # Try to detect how many screens the user has
        # minus 1 since we like to start count at 0
        max_screens = QDesktopWidget().screenCount()
        self.widget.screenSpinBox.setMaximum(max_screens - 1)

        self.widget.regionLabel.setText("{}x{} to {}x{}".format(
            self.config.start_x, self.config.start_y, self.config.end_x, self.config.end_y))

        # Finally enable connections
        self.__enable_connections()

    def set_screen(self, screen):
        self.config.screen = screen
        self.config.save()

    def set_desktop_full(self):
        self.config.desktop = "Full"
        self.config.save()
        self.gui.update_video_quality()

    def set_desktop_area(self):
        self.config.desktop = "Area"
        self.config.save()
        self.gui.update_video_quality()

    ###
    ### Translations
    ###
    def retranslate(self):
        self.widget.desktopLabel.setText(self.gui.app.translate('plugin-desktop', 'Record Desktop'))
        self.widget.areaLabel.setText(self.gui.app.translate('plugin-desktop', 'Record Region'))
        self.widget.screenLabel.setText(self.gui.app.translate('plugin-desktop', 'Screen'))
