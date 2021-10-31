# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

class Playsoundy():
    Gst.init(None)

    def __init__(self, soundclip, *args, **kwargs):
        # super().__init__(*args, **kwargs)

        self.soundclip = soundclip

        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)

        self.player.props.uri = self.soundclip .uri

        
        # self.player.set_state(Gst.State.PLAYING)

        self.bus = self.player.get_bus()


        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

        # self.player.set_state(Gst.State.NULL)

    def play_pause(self):
        if self.soundclip.play_revealer.props.name == "soundclip-play":
            self.soundclip.play_revealer.set_reveal_child(False)
            self.soundclip.play_revealer.props.name = "soundclip-pause"
            self.player.set_state(Gst.State.NULL)
        else:
            self.soundclip.play_revealer.set_reveal_child(True)
            self.soundclip.play_revealer.props.name = "soundclip-play"
            self.player.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        # print(message.type)
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.soundclip.play_revealer.set_reveal_child(False)
            self.soundclip.play_revealer.props.name == "soundclip-play"
        elif message.type == Gst.MessageType.ERROR:
            self.soundclip.play_revealer.set_reveal_child(False)
            self.soundclip.play_revealer.props.name = "soundclip-play"
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)
            # self.button.set_label("Start")
        # elif message.type == Gst.MessageType.ASYNC_DONE:
        #     print(self.player.query_duration(Gst.Format.TIME)[1] / 1000000000)

def play(uri):
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst

    Gst.init(None)

    player = Gst.ElementFactory.make("playbin", "player")
    fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
    player.set_property("video-sink", fakesink)
    
    player.props.uri = uri

    player.set_state(Gst.State.PLAYING)
    # dur_int = player.query_duration(Gst.Format.TIME, None)[0]

    # print(dur_int)

    bus = player.get_bus()
    bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)

    player.set_state(Gst.State.NULL)





