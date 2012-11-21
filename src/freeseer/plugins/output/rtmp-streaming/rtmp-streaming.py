'''
freeseer - vga/presentation capture software

Copyright (C) 2011-2012  Free and Open Source Software Learning Centre
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

@author: Jonathan Shen
'''

import ConfigParser

import pygst
pygst.require("0.10")
import gst

from PyQt4 import QtGui, QtCore

from freeseer.framework.plugin import IOutput

class RTMPOutput(IOutput):
    name = "RTMP Streaming"
    type = IOutput.BOTH
    recordto = IOutput.STREAM
    tags = None
    
    # RTMP Streaming variables
    url = ""
    video_bitrate = 2400
    
	#@brief - RTMP Streaming plugin.
	# Structure for function was based primarily off the ogg function
	# Creates a bin to stream flv content to [self.url]
	# Bin has audio and video ghost sink pads 
	# Converts audio and video to flv with [flvmux] element
	# Streams flv content to [self.url]
	# TODO - Error handling - verify pad setup
    def get_output_bin(self, audio=True, video=True, metadata=None):
        bin = gst.Bin(self.name)
        
        if metadata is not None:
            self.set_metadata(metadata)
       
        # Muxer
        muxer = gst.element_factory_make("flvmux", "muxer")
        
        # Setup metadata
        # set tag merge mode to GST_TAG_MERGE_REPLACE
        merge_mode = gst.TagMergeMode.__enum_values__[2]
    
        muxer.merge_tags(self.tags, merge_mode)
        muxer.set_tag_merge_mode(merge_mode)
        
        bin.add(muxer)
        
        # RTMP sink
        #TODO - rtmpsink factory?
        rtmpsink = gst.element_factory_make('rtmpsink', 'rtmpsink')
        rtmpsink.set_property('location', self.url)
        bin.add(rtmpsink)
        
        #
        # Setup Audio Pipeline if Audio Recording is Enabled
        #
        if audio:
            audioqueue = gst.element_factory_make("queue", "audioqueue")
            bin.add(audioqueue)
            
            audioconvert = gst.element_factory_make("audioconvert", "audioconvert")
            bin.add(audioconvert)
            
            audiolevel = gst.element_factory_make('level', 'audiolevel')
            audiolevel.set_property('interval', 20000000)
            bin.add(audiolevel)
            
            # Setup ghost pads
            audiopad = audioqueue.get_pad("sink")
            audio_ghostpad = gst.GhostPad("audiosink", audiopad)
            bin.add_pad(audio_ghostpad)
            
            gst.element_link_many(audioqueue, audioconvert, audiolevel, muxer)
        
        
        #
        # Setup Video Pipeline
        #
        if video:
            videoqueue = gst.element_factory_make("queue", "videoqueue")
            bin.add(videoqueue)
            
            videocodec = gst.element_factory_make("x264enc", "videocodec")
            videocodec.set_property("bitrate", int(self.video_bitrate))
            bin.add(videocodec)
            
            # Setup ghost pads
            videopad = videoqueue.get_pad("sink")
            video_ghostpad = gst.GhostPad("videosink", videopad)
            bin.add_pad(video_ghostpad)
            
            gst.element_link_many(videoqueue, videocodec, muxer)
        
        #
        # Link muxer to rtmpsink
        #
        gst.element_link_many(muxer, rtmpsink)
        
        return bin
    
    def set_metadata(self, data):
        '''
        Populate global tag list variable with file metadata for
        vorbistag audio element
        '''
        self.tags = gst.TagList()

        for tag in data.keys():
            if(gst.tag_exists(tag)):
                self.tags[tag] = data[tag]
            else:
                #self.core.logger.log.debug("WARNING: Tag \"" + str(tag) + "\" is not registered with gstreamer.")
                pass
            
    def load_config(self, plugman):
        self.plugman = plugman
        
        try:
            self.url = self.plugman.plugmanc.readOptionFromPlugin(self.CATEGORY, self.get_config_name(), "Stream URL")
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            self.plugman.plugmanc.registerOptionFromPlugin(self.CATEGORY, self.get_config_name(), "Stream URL", self.url)
    
    def get_widget(self):
        if self.widget is None:
            self.widget = QtGui.QWidget()
            self.widget.setWindowTitle("RTMP Streaming Options")
            
            layout = QtGui.QFormLayout()
            self.widget.setLayout(layout)
            
            #
            # Stream URL
            #
            
            self.label_stream_url = QtGui.QLabel("Stream URL")
            self.lineedit_stream_url = QtGui.QLineEdit()
            layout.addRow(self.label_stream_url, self.lineedit_stream_url)

            self.lineedit_stream_url.textEdited.connect(self.set_stream_url)

        return self.widget

    def widget_load_config(self, plugman):
        self.load_config(plugman)
        
        self.lineedit_stream_url.setText(self.url)

    def set_stream_url(self, text):
        self.url = text
        self.plugman.plugmanc.registerOptionFromPlugin(self.CATEGORY, self.get_config_name(), "Stream URL", self.url)
        self.plugman.save()
        
    def get_properties(self):
        return ["StreamURL"]
    
    def get_property_value(self, property):
        if property == "StreamURL":
            return self.url
        else:
            return "There's no property with such name"
        
    def set_property_value(self, property, value):
        if property == "StreamURL":
            return self.set_stream_url(value)
        else:
            return "Error: There's no property with such name" 

