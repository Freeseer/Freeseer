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
WebM Output
-----------

An output plugin that records to webm format with vp8 encoding for the video
and Vorbis encoding for audio.

@author: Thanh Ha
'''

# GStreamer
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib

# Freeseer
from freeseer.framework.plugin import IOutput


class WebMOutput(IOutput):
    name = "WebM Output"
    os = ["linux", "linux2", "win32", "cygwin"]
    type = IOutput.BOTH
    recordto = IOutput.FILE
    extension = "webm"
    tags = None

    def get_output_bin(self, audio=True, video=True, metadata=None):
        bin = Gst.Bin()

        if metadata is not None:
            self.set_metadata(metadata)

        # Muxer
        muxer = Gst.ElementFactory.make("webmmux", "muxer")
        bin.add(muxer)

        filesink = Gst.ElementFactory.make('filesink', 'filesink')
        filesink.set_property('location', self.location)
        bin.add(filesink)

        #
        # Setup Audio Pipeline
        #
        if audio:

            #Create audio elements
            q1 = Gst.ElementFactory.make('queue', None)
            enc = Gst.ElementFactory.make('vorbisenc', None)
            q2 = Gst.ElementFactory.make('queue', None)
            audioconvert = Gst.ElementFactory.make("audioconvert", None)
            audiolevel = Gst.ElementFactory.make('level', None)
            audiolevel.set_property('interval', 20000000)

            #Setup metadata
            vorbistag = Gst.ElementFactory.make("vorbistag", None)
            #set tag merge mode to GST_TAG_MERGE_REPLACE
            merge_mode = Gst.TagMergeMode.__enum_values__[2]

            if metadata is not None:
                # Only set tag if metadata is set
                vorbistag.merge_tags(self.tags, merge_mode)
            vorbistag.set_tag_merge_mode(merge_mode)
            


            
            #Add the audio elements to the bin
            bin.add(q1)
            bin.add(audiolevel)
            bin.add(audioconvert)
            bin.add(enc)
            bin.add(vorbistag)
            bin.add(q2)

            #link the audio elements
            q1.link(audiolevel)
            audiolevel.link(audioconvert)
            audioconvert.link(enc)
            enc.link(vorbistag)
            vorbistag.link(q2)
            q2.link(muxer)

            # Setup ghost pads
            audiopad = q1.get_static_pad("sink")
            audio_ghostpad = Gst.GhostPad.new("audiosink", audiopad)
            bin.add_pad(audio_ghostpad)


        #
        # Setup Video Pipeline
        #
        if video:
            videoqueue = Gst.ElementFactory.make("queue", "videoqueue")
            bin.add(videoqueue)

            videocodec = Gst.ElementFactory.make("vp8enc", "videocodec")
            bin.add(videocodec)

            videopad = videoqueue.get_static_pad("sink")
            video_ghostpad = Gst.GhostPad.new("videosink", videopad)
            bin.add_pad(video_ghostpad)

            # Link Elements
            videoqueue.link(videocodec)
            videocodec.link(muxer)

        #
        # Link muxer to filesink
        #
        muxer.link(filesink)

        return bin

    def set_metadata(self, data):
        '''
        Populate global tag list variable with file metadata for
        vorbistag audio element
        '''
        self.tags = Gst.TagList.new_empty()
        merge_mode = Gst.TagMergeMode.__enum_values__[2]
        for tag in data.keys():
            if(Gst.tag_exists(tag)):
                if tag == "date":
                    s_date = data[tag].split("-")
                    Tag_date = GLib.Date() 
                    Tag_date.set_day(int(s_date[2]))
                    Tag_date.set_month(s_date[1])
                    Tag_date.set_year(int(s_date[0]))
                    self.tags.add_value(merge_mode, tag, Tag_date)
                else:
                    self.tags.add_value(merge_mode, tag, str(data[tag]))
            else:
                self.core.logger.log.debug("WARNING: Tag \"" + str(tag) + "\" is not registered with gstreamer.")
                pass
