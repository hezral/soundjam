# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import sys
import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Granite', '1.0')
from gi.repository import Gtk, Gio, Granite, Gdk

from .window import soundjamWindow
from .utils import HelperUtils

class Application(Gtk.Application):

    granite_settings = Granite.Settings.get_default()
    gtk_settings = Gtk.Settings.get_default()
    gio_settings = Gio.Settings(schema_id="com.github.hezral.soundjam")
    utils = HelperUtils()

    main_window = None

    def __init__(self):
        super().__init__(application_id='com.github.hezral.soundjam',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        prefers_color_scheme = self.granite_settings.get_prefers_color_scheme()
        self.gtk_settings.set_property("gtk-application-prefer-dark-theme", prefers_color_scheme)
        self.granite_settings.connect("notify::prefers-color-scheme", self.on_prefers_color_scheme)

        provider = Gtk.CssProvider()        
        provider.load_from_path(os.path.join(os.path.dirname(__file__), "data", "application.css"))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.icon_theme = Gtk.IconTheme.get_default()
        self.icon_theme.prepend_search_path(os.path.join(os.path.dirname(__file__), "data", "icons"))

        if "io.elementary.stylesheet" not in self.gtk_settings.props.gtk_theme_name:
            self.gtk_settings.set_property("gtk-theme-name", "io.elementary.stylesheet.blueberry")

    def do_activate(self):
        if not self.main_window:
            self.main_window = soundjamWindow(application=self)
        self.main_window.present()

    def on_prefers_color_scheme(self, *args):
        prefers_color_scheme = self.granite_settings.get_prefers_color_scheme()
        self.gtk_settings.set_property("gtk-application-prefer-dark-theme", prefers_color_scheme)


def main(version):
    app = Application()
    return app.run(sys.argv)
