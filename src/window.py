# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

from inspect import currentframe, getframeinfo

import os
import time

import gi
gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
gi.require_version('Granite', '1.0')
from gi.repository import Gtk, Handy, GLib, Gdk, Granite, Pango, Gio, GdkPixbuf, cairo

from .custom_widgets import HoldButton
from .playsoundy import Playsoundy, play
from .utils import HelperUtils

class soundjamWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'soundjamWindow'

    Handy.init()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = self.props.application

        self.header = self.generate_headerbar()
        self.start_view = self.generate_start_view()
        self.soundboard_view = self.generate_soundboard_view()
        self.settings_view = self.generate_settings_view()

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.props.expand = True
        # self.scrolled_window.props.hscrollbar_policy = Gtk.PolicyType.NEVER 
        self.scrolled_window.add(self.soundboard_view)
        self.vadjustment = self.scrolled_window.props.vadjustment
        self.vadjustment.connect("notify::value", self.on_scroll)

        self.stack = Gtk.Stack()
        self.stack.add_named(self.start_view, "start-view")
        self.stack.add_named(self.scrolled_window, "soundboard-view")
        # self.stack.add_named(self.settings_view, "settings-view")

        overlay = Gtk.Overlay()
        overlay.add(self.stack)
        overlay.add_overlay(self.header)

        grid = Gtk.Grid()
        grid.props.expand = True
        # grid.attach(self.stack, 0, 0, 1, 1)
        # grid.attach(self.header, 0, 0, 1, 1)
        grid.attach(overlay, 0, 0, 1, 1)

        self.add(grid)
        self.props.name = "main"
        self.props.default_width = 800
        self.props.default_height = 490
        # self.set_size_request(640, 500)
        geometry = Gdk.Geometry()
        # setattr(geometry, 'base_height', 450)
        # setattr(geometry, 'base_width', 800)
        # self.set_geometry_hints(None, geometry, Gdk.WindowHints.BASE_SIZE)
        setattr(geometry, 'min_width', 280)
        setattr(geometry, 'min_height', 280)
        self.set_geometry_hints(None, geometry, Gdk.WindowHints.MIN_SIZE)
        # setattr(geometry, 'max_height', 1080)
        # setattr(geometry, 'max_width', 1888)
        # self.set_geometry_hints(None, geometry, Gdk.WindowHints.MAX_SIZE)
        # setattr(geometry, 'height_inc', 100)
        # setattr(geometry, 'width_inc', 100)
        # self.set_geometry_hints(None, geometry, Gdk.WindowHints.RESIZE_INC)
        self.show_all()

        self.drag_and_drop_setup(self)
        self.drag_and_grab_setup(self.soundboard_view)

        self.add_to_soundboard(data=None)

    def on_scroll(self, vadjustment, value):
        if vadjustment.props.value > 0.8 * (vadjustment.props.upper - vadjustment.props.page_size):
            self.header.get_style_context().add_class("hidden")
            self.header.set_visible(False)
            self.soundboard_view.props.margin_top = 20
        else:
            self.header.get_style_context().remove_class("hidden")
            self.header.set_visible(True)
            self.soundboard_view.props.margin_top = 60

    def generate_headerbar(self):

        self.spinbutton = Gtk.SpinButton().new_with_range(min=1, max=10, step=1)
        self.spinbutton.props.can_focus = False

        header = Handy.HeaderBar()
        header.props.name = "main"
        header.props.halign = Gtk.Align.FILL
        header.props.valign = Gtk.Align.START
        header.props.hexpand = True
        header.props.spacing = 0
        header.props.has_subtitle = False
        header.props.show_close_button = True
        header.props.decoration_layout = "close:"
        header.pack_end(self.spinbutton)
        return header

    def generate_start_view(self):
        icon = Gtk.Image().new_from_icon_name("io.elementary.music", Gtk.IconSize.DIALOG)
        start_overlay = Gtk.Overlay()
        start_overlay.props.name = "stack"
        start_overlay.props.expand = True
        start_overlay.props.valign = start_overlay.props.halign = Gtk.Align.FILL
        start_overlay.add(icon)

        start_view = Gtk.Grid()
        start_view.props.can_focus = True
        start_view.props.row_spacing = 2
        start_view.attach(start_overlay, 0, 1, 1, 1)
        return start_view

    def generate_soundboard_view(self):
        soundboard = Gtk.FlowBox()
        soundboard.props.name = "soundboard"
        soundboard.props.expand = True
        soundboard.props.homogeneous = True
        soundboard.props.row_spacing = 20
        soundboard.props.column_spacing = 20
        soundboard.props.max_children_per_line = 10
        soundboard.props.min_children_per_line = 1
        soundboard.props.margin_top = 60
        soundboard.props.margin_left = 20
        soundboard.props.margin_right = 20
        soundboard.props.margin_bottom = 20
        soundboard.props.valign = Gtk.Align.START
        soundboard.props.halign = Gtk.Align.FILL
        soundboard.props.selection_mode = Gtk.SelectionMode.NONE
        soundboard.connect("child-activated", self.on_flowboxchild_activated)
        return soundboard

    def generate_settings_view(self):
        settings = Gtk.Grid()
        settings.props.name = "settings"
        settings.props.expand = True
        settings.props.halign = Gtk.Align.CENTER
        settings.props.no_show_all = True
        return settings

    def drag_and_drop_setup(self, widget):
        widget.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        widget.drag_dest_add_uri_targets()
        widget.connect("drag_data_received", self.on_drag_data_received)
        # widget.connect("drag_drop", self.on_drag_drop)

    def drag_and_grab_setup(self, widget):
        widget.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.COPY)
        widget.drag_source_add_uri_targets()
        widget.connect("drag_end", self.on_drag_data_grabbed)

    def on_drag_drop(self, *args):
        print(locals())

    def on_drag_data_received(self, widget, context, x, y, data, info, timestamp):
        Gtk.drag_finish(context, True, False, timestamp) 
        self.add_to_soundboard(data)
        self.stack.set_visible_child(self.scrolled_window)
        print("on_drag_data_received")

    def on_drag_data_grabbed(self, widget, drag_context):
        uris = []
        for child in widget.get_selected_children():
            # child.get_children()[0].icon_grid.hide()
            # child.get_children()[0].icon_label.hide()
            # child.get_children()[0].poof_revealer.set_reveal_child(True)
            # child.get_children()[0].poof.on_show()
            # self.on_soundclip_removed(child)
            # GLib.timeout_add(1000, self.on_soundclip_removed, child)
            child.destroy()
            # if child.get_children()[0].uri != None:
            #     uris.append(child.get_children()[0].uri)
        # print(uris)
        # self.off_select_mode()

    @HelperUtils.run_async
    def add_to_soundboard(self, data):
        if data is not None:
            for child in self.soundboard_view.get_children():
                print(child.get_children()[0].props.name)
                if child.get_children()[0].props.name == "placeholders":
                    child.destroy()
            target = data.get_target()
            # print(str(target))
            if str(target) == "text/uri-list":
                uris = data.get_uris()
                for uri in uris:
                    path, hostname = GLib.filename_from_uri(uri)
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            mime_type, val = Gio.content_type_guess(path, data=None)
                            if "audio" in mime_type:
                                GLib.idle_add(self.add_soundclip, uri)
                                time.sleep(0.05)
                                print("add_to_soundboard")
        else:
            for i in range(12):
                grid = Gtk.Grid()
                grid.props.expand = True
                grid.set_size_request(160, 120)
                # grid.get_style_context().add_class("clip-containers")
                eventbox = Gtk.EventBox()
                eventbox.props.name = "placeholders"
                eventbox.props.expand = True
                eventbox.set_size_request(160, 120)
                # eventbox.get_style_context().add_class("clip-containers")
                eventbox.add(grid)
                eventbox.connect("enter-notify-event", self.on_hover_enter)
                eventbox.connect("leave-notify-event", self.on_hover_leave)
                self.soundboard_view.add(eventbox)
                self.soundboard_view.show_all()
                self.stack.set_visible_child(self.scrolled_window)

    def add_soundclip(self, uri):
        try:
            duplicate = [child for child in self.soundboard_view.get_children() if child.get_children()[0].uri == uri][0]
        except:
            self.soundboard_view.add(SoundClip(uri))
        self.soundboard_view.show_all()
        # self.scrolled_window.show_all()

    def on_hover_enter(self, eventbox, eventcrossing):
        # eventbox.get_style_context().add_class("hover")
        eventbox.get_style_context().add_class("clip-containers")

    def on_hover_leave(self, eventbox, eventcrossing):
        eventbox.get_style_context().remove_class("clip-containers")
        # eventbox.get_style_context().remove_class("hover")


    def on_flowboxchild_activated(self, flowbox, flowboxchild):
        # if self.soundboard_view.props.selection_mode == Gtk.SelectionMode.NONE:
        flowboxchild.get_children()[0].player.play_pause()

    def on_select_mode(self):
        if self.soundboard_view.props.selection_mode == Gtk.SelectionMode.NONE and len(self.soundboard_view.get_selected_children()) == 0:
            self.soundboard_view.props.selection_mode = Gtk.SelectionMode.MULTIPLE

            for child in self.soundboard_view.get_children():
                if child.is_selected():
                    child.select_revealer.set_reveal_child(True)

            # self.soundboard_view.connect("button-press-event", self.on_clicked)
            self.soundboard_view.disconnect_by_func(self.on_flowboxchild_activated)

        elif self.soundboard_view.props.selection_mode == Gtk.SelectionMode.MULTIPLE and len(self.soundboard_view.get_selected_children()) == 0:
            self.soundboard_view.props.selection_mode = Gtk.SelectionMode.NONE

            # for child in self.soundboard_view.get_children():
                # child.get_children()[0].connect("button-press-event", child.get_children()[0].on_mouse_clicked)
                # child.get_children()[0].connect("key-press-event", child.get_children()[0].on_keyboard_pressed)

            self.soundboard_view.connect("child-activated", self.on_flowboxchild_activated)
            # self.soundboard_view.disconnect_by_func(self.on_clicked)

            self.soundboard_view.unselect_all()

    def on_clicked(self, eventbox, eventbutton):
        import datetime
        if eventbutton.type.value_name == "GDK_2BUTTON_PRESS":
            self.off_select_mode()

    def off_select_mode(self):
        for child in self.soundboard_view.get_children():
            child.get_children()[0].connect("button-press-event", child.get_children()[0].on_mouse_clicked)
            child.get_children()[0].select_revealer.set_reveal_child(False)

        # self.soundboard_view.disconnect_by_func(self.on_flowboxchild_activated)
        self.soundboard_view.disconnect_by_func(self.on_clicked)
        self.soundboard_view.unselect_all()
        self.soundboard_view.props.selection_mode = Gtk.SelectionMode.NONE

class SoundClip(Gtk.EventBox):
    def __init__(self, uri, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uri = uri
        self.player = Playsoundy(self)

        path, hostname = GLib.filename_from_uri(uri)

        filename = os.path.splitext(os.path.basename(path))[0]

        select = Gtk.Button(image=Gtk.Image().new_from_icon_name("process-completed", Gtk.IconSize.LARGE_TOOLBAR))
        select.props.name = "soundclip-select"
        select.props.can_focus = False
        select.connect("clicked", self.on_select_button)
        select.get_style_context().add_class("soundclip-select")
        self.select_revealer = Gtk.Revealer()
        self.select_revealer.props.can_focus = False
        self.select_revealer.props.halign = Gtk.Align.END
        self.select_revealer.props.valign = Gtk.Align.START
        self.select_revealer.props.hexpand = True
        self.select_revealer.props.margin_top = 4
        self.select_revealer.props.margin_right = 20
        self.select_revealer.props.transition_duration = 250
        self.select_revealer.props.transition_type = Gtk.RevealerTransitionType.CROSSFADE
        self.select_revealer.add(select)

        play_icon = Gtk.Image().new_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        play_icon.props.name = "soundclip-play"
        play_icon.props.margin_left = 2
        play = Gtk.Box()
        play.props.name = "soundclip-play"
        play.props.can_focus = False
        play.props.height_request = play.props.width_request = 48
        play.get_style_context().add_class("play")
        play_button_container = Gtk.Overlay()
        play_button_container.add(play)
        play_button_container.add_overlay(play_icon)
        self.play_revealer = Gtk.Revealer()
        self.play_revealer.props.can_focus = False
        self.play_revealer.props.halign = Gtk.Align.CENTER
        self.play_revealer.props.valign = Gtk.Align.CENTER
        self.play_revealer.props.vexpand = True
        self.play_revealer.props.margin_bottom = 30
        self.play_revealer.props.transition_duration = 250
        self.play_revealer.props.transition_type = Gtk.RevealerTransitionType.CROSSFADE
        self.play_revealer.add(play_button_container)

        self.icon_image = Gtk.Image().new_from_icon_name("io.elementary.music", Gtk.IconSize.DIALOG)
        self.icon_image.set_pixel_size(96)
        self.icon_image.props.can_focus = False

        self.icon_label = ItemLabel(filename)
        self.icon_label.props.can_focus = False

        grid = Gtk.Grid()
        grid.props.can_focus = False
        grid.props.margin = 6
        grid.props.row_spacing = 4
        grid.props.expand = True
        grid.props.halign = Gtk.Align.CENTER
        grid.props.valign = Gtk.Align.START
        grid.attach(self.icon_image, 0, 0, 1, 1)
        grid.attach(self.icon_label, 0, 1, 1, 1)
        grid.set_size_request(128, 128)

        overlay_grid = Gtk.Grid()
        overlay_grid.props.can_focus = False
        overlay_grid.attach(self.select_revealer, 0, 0, 1, 1)
        overlay_grid.attach(self.play_revealer, 0, 0, 1, 1)

        overlay = Gtk.Overlay()
        overlay.props.can_focus = False
        overlay.add(grid)
        overlay.add_overlay(overlay_grid)

        self.add(overlay)
        self.props.can_focus = False
        self.props.name = filename

        self.connect("enter-notify-event", self.on_enter_notify)
        self.connect("leave-notify-event", self.on_leave_notify)
        # self.connect("button-press-event", self.on_mouse_clicked)
        # self.connect("key-press-event", self.on_keyboard_pressed)

    # def on_keyboard_pressed(self, *args):
    #     print(locals())
    #     # self.player.play_pause()

    # def on_mouse_clicked(self, eventbox, eventbutton):
    #     if eventbutton.button == 1:
    #         self.player.play_pause()

    def on_enter_notify(self, widget, eventcrossing):
        self.select_revealer.set_reveal_child(True)

    def on_leave_notify(self, widget, eventcrossing):
        if not self.get_parent().is_selected():
            self.select_revealer.set_reveal_child(False)

    def on_select_button(self, button):
        # print(button.props.name, "triggered at line: {0}, code_context: {1}".format(getframeinfo(currentframe()).lineno, getframeinfo(currentframe()).code_context))
        if not self.get_parent().is_selected():
            self.get_toplevel().on_select_mode()
            self.get_toplevel().soundboard_view.select_child(self.get_parent())
        else:
            self.get_toplevel().soundboard_view.unselect_child(self.get_parent())
            self.get_toplevel().on_select_mode()

class ItemLabel(Gtk.Label):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.props.label = filename
        self.props.wrap_mode = Pango.WrapMode.CHAR
        self.props.max_width_chars = 16
        self.props.wrap = True
        self.props.hexpand = True
        self.props.justify = Gtk.Justification.CENTER
        self.props.lines = 2
        self.props.ellipsize = Pango.EllipsizeMode.END

class CompositedGrid(Gtk.Grid):
    ''' Ported from
    https://github.com/ricotz/plank/blob/master/lib/Widgets/CompositedWindow.vala
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app_paintable = True
        self.double_buffered = False
        self.connect("draw", self.draw)

    def draw(self, widget, cairo_context):
        cairo_context.save()
        cairo_context.set_operator(cairo.Operator.CLEAR)
        cairo_context.paint()
        cairo_context.restore()
        
        return Gdk.EVENT_STOP

class PoofItem(Gtk.Grid):
    ''' Ported from
    https://github.com/ricotz/plank/blob/master/lib/Widgets/PoofWindow.vala
    '''

    RUN_LENGTH = 300 * 1000

    poof_image = None
    poof_size = None
    poof_frames = None
    
    start_time = 0
    frame_time = 0
    
    animation_timer_id = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        import math
        
        self.poof_image = GdkPixbuf.Pixbuf.new_from_file(os.path.join(os.path.dirname(__file__), "data", "poof.svg"))
        self.poof_size = self.poof_image.props.width
        self.poof_frames = math.floor(self.poof_image.props.height / self.poof_size)

        self.set_size_request(self.poof_size, self.poof_size)

        drawing_area = Gtk.DrawingArea()
        drawing_area.props.expand = True
        drawing_area.connect("draw", self.draw)

        self.attach(drawing_area, 0, 0, 1, 1)
        self.props.can_focus = False

    def draw(self, drawing_area, cairo_context):
        cairo_context.set_operator(cairo.Operator.SOURCE)
        Gdk.cairo_set_source_pixbuf(cairo_context, self.poof_image, 0, -self.poof_size * (self.poof_frames * (self.frame_time - self.start_time) / float(self.RUN_LENGTH)))
        cairo_context.paint()

        # cairo_context.save()
        # cairo_context.set_operator(cairo.Operator.CLEAR)
        # cairo_context.paint()
        # cairo_context.restore()

        return Gdk.EVENT_STOP

    def on_show(self):
        if self.animation_timer_id > 0:
            GLib.Source.remove(self.animation_timer_id)

        if self.poof_image is None and self.poof_frames > 0:
            return
        
        self.start_time = GLib.get_monotonic_time()
        self.frame_time = self.start_time

        self.show()
        self.animation_timer_id = GLib.timeout_add(30, self.animate, None)

    def animate(self, data):
        self.frame_time = GLib.get_monotonic_time()
            
        if self.frame_time - self.start_time <= self.RUN_LENGTH:
            self.queue_draw()
            return True
        
        self.animation_timer_id = 0
        self.hide()
        return False