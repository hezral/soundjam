# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import gi

gi.require_version('Handy', '1')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Granite', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Handy, Gtk, GObject, Gio, Granite, Gdk, cairo, PangoCairo, Pango, GLib

import math

class CircularProgressBar(Gtk.Bin):
    '''Ported from https://github.com/phastmike/vala-circular-progress-bar'''
    MIN_D = 80
    font = "Inter"
    line_cap = cairo.LineCap.BUTT

    _line_width = 1
    _percentage = 0.0
    _center_fill_color = "#adadad"
    _radius_fill_color = "#d3d3d3"
    _progress_fill_color = "#4a90d9"

    center_filled = GObject.Property(type=bool, default=False)
    radius_filled = GObject.Property(type=bool, default=False)
    font = GObject.Property(type=str, default="Inter")
    line_cap = GObject.Property(type=cairo.LineCap, default=cairo.LineCap.BUTT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        drawing_area = Gtk.DrawingArea()
        drawing_area.set_size_request(300, 300)
        drawing_area.props.expand = True
        drawing_area.props.halign = self.props.valign = Gtk.Align.FILL

        drawing_area.connect("draw", self.draw)
        self.connect("notify", self.on_notify)

        self.add(drawing_area)

    def on_notify(self, *args):
        self.queue_draw()

    @GObject.Property(type=str)
    def center_fill_color(self):
        '''Center pad fill color (Check Gdk.RGBA parse method)'''
        return self._center_fill_color

    @center_fill_color.setter
    def center_fill_color(self, value):
        color = Gdk.RGBA()
        if color.parse(value):
            self._center_fill_color = value

    @GObject.Property(type=str)
    def radius_fill_color(self):
        '''The circular pad fill color (Check GdkRGBA parse method)'''
        return self._radius_fill_color

    @radius_fill_color.setter
    def radius_fill_color(self, value):
        color = Gdk.RGBA()
        if color.parse(value):
            self._radius_fill_color = value

    @GObject.Property(type=str)
    def progress_fill_color(self):
        '''Progress line color (Check GdkRGBA parse method)'''
        return self._progress_fill_color

    @progress_fill_color.setter
    def progress_fill_color(self, value):
        color = Gdk.RGBA()
        if color.parse(value):
            self._progress_fill_color= value

    @GObject.Property(type=int)
    def line_width(self):
        '''The circle radius line width'''
        return self._line_width

    @line_width.setter
    def line_width(self, value):
        if value < 0:
            self._line_width = 0
        else:
            self._line_width = value

    @GObject.Property(type=float)
    def percentage(self):
        '''The percentage value [0.0 ... 1.0]'''
        return self._percentage

    @percentage.setter
    def percentage(self, value):
        if value > 1.0:
            self._percentage = 1.0
        elif value < 0.0:
            self._percentage = 0.0
        else:
            self._percentage = float(value)

    def calculate_radius(self):
        return int(min(self.get_allocated_width() / 2, self.get_allocated_height() / 2) - 1)

    def calculate_diameter(self):
        return int(2 * self.calculate_radius())

    def do_get_request_mode(self):
        return Gtk.SizeRequestMode.CONSTANT_SIZE

    def do_get_preferred_width(self):
        d = self.calculate_diameter()
        min_w = self.MIN_D
        if d > self.MIN_D:
            natural_w = d
        else:
            natural_w = self.MIN_D
        return min_w, natural_w

    def do_get_preferred_height(self):
        d = self.calculate_diameter()
        min_h = self.MIN_D
        if d > self.MIN_D:
            natural_h = d
        else:
            natural_h = self.MIN_D
        return min_h, natural_h

    # def do_size_allocate(self, allocation):
    #     super().size_allocate(allocation)

    def draw(self, widget, cr):

        cr.save()

        color = Gdk.RGBA()

        center_x = self.get_allocated_width() / 2
        center_y = self.get_allocated_height() / 2
        radius =  self.calculate_radius()

        if radius - self.line_width < 0:
            delta = 0
            self.set_property("line_width", radius)
        else:
            delta = radius - (self.line_width / 2)

        color = Gdk.RGBA()

        cr.set_line_cap(self.line_cap)
        cr.set_line_width(self.line_width)

        # Center Fill
        if self.center_filled:
            cr.arc(center_x, center_y, delta, 0, 2 * math.pi)
            color.parse(self.center_fill_color)
            Gdk.cairo_set_source_rgba(cr, color)
            cr.fill()

        # Radius Fill
        if self.radius_filled:
            cr.arc(center_x, center_y, delta, 0, 2 * math.pi)
            color.parse(self.radius_fill_color)
            Gdk.cairo_set_source_rgba(cr, color)
            cr.stroke()

        # Progress/Percentage Fill
        if self.percentage > 0:
            color.parse(self.progress_fill_color)
            Gdk.cairo_set_source_rgba(cr, color)

            if self.line_width == 0:
                cr.move_to(center_x, center_y)
                cr.arc(center_x, center_y, delta+1, 1.5 * math.pi, (1.5 + self.percentage * 2 ) * math.pi)
                cr.fill()
            else:
                cr.arc(center_x, center_y, delta, 1.5 * math.pi, (1.5 + self.percentage * 2 ) * math.pi)
                cr.stroke()

        # Textual information
        context = self.get_style_context()
        context.save()
        context.add_class(Gtk.STYLE_CLASS_TROUGH)
        color = context.get_color(context.get_state())
        Gdk.cairo_set_source_rgba(cr, color)

        # Percentage
        layout = PangoCairo.create_layout(cr)
        layout.set_text("{0}".format(int(self.percentage * 100.0)), -1)
        desc = Pango.FontDescription.from_string(self.font + " 24")
        layout.set_font_description(desc)
        PangoCairo.update_layout(cr, layout)
        w, h = layout.get_size() 
        cr.move_to(center_x - ((w / Pango.SCALE) / 2), center_y - 27 )
        PangoCairo.show_layout(cr, layout)

        # Units indicator ('PERCENT')
        layout.set_text("PERCENT", -1)
        desc = Pango.FontDescription.from_string(self.font + " 8")
        layout.set_font_description(desc)
        PangoCairo.update_layout(cr, layout)
        w, h = layout.get_size()
        cr.move_to(center_x - ((w / Pango.SCALE) / 2), center_y + 13)
        PangoCairo.show_layout(cr, layout)

        context.restore()
        cr.restore()

        # return self.draw(cr)

class Demo(Handy.ApplicationWindow):
    Handy.init()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.header = self.generate_headerbar()

        self.progr_adj = Gtk.Adjustment()
        self.progr_adj.props.upper = 1
        self.progr_adj.props.step_increment = 0.01
        self.progr_adj.props.page_increment = 10

        self.linew_adj = Gtk.Adjustment()
        self.linew_adj.props.upper = 100
        self.linew_adj.props.value = 1
        self.linew_adj.props.step_increment = 1
        self.linew_adj.props.page_increment = 10

        self.demo_settings = self.generate_demo_ui_settings()

        self.circularprogressbar = CircularProgressBar()
        self.circularprogressbar.props.margin = 6

        color = Gdk.RGBA()
        color.parse(str(self.circularprogressbar.center_fill_color))
        self.colorbutton1.set_rgba(color)
  
        color.parse(str(self.circularprogressbar.radius_fill_color))
        self.colorbutton1.set_rgba(color)

        color.parse(str(self.circularprogressbar.progress_fill_color))
        self.colorbutton3.set_rgba(color)

        self.button_center_filled.bind_property("active", self.circularprogressbar, "center_filled", GObject.BindingFlags.DEFAULT)
        self.button_radius_filled.bind_property("active", self.circularprogressbar, "radius_filled", GObject.BindingFlags.DEFAULT)

        self.colorbutton1.connect("color-set", self.on_color_set)
        self.colorbutton2.connect("color-set", self.on_color_set)
        self.colorbutton3.connect("color-set", self.on_color_set)

        self.button_cap.connect("toggled", self.on_toggled)

        self.s_progr.connect("value-changed", self.on_value_changed)
        self.s_linew.connect("value-changed", self.on_value_changed)

        main_grid = Gtk.Grid()
        main_grid.props.expand = True
        main_grid.attach(self.header, 0, 0, 1, 1)
        main_grid.attach(self.circularprogressbar, 0, 1, 1, 1)
        main_grid.attach(self.demo_settings, 0, 2, 1, 1)

        self.add(main_grid)
        self.props.name = "main"
        # self.set_size_request(640, 500)
        self.show_all()
        self.set_keep_above(True)

        self.connect("configure-event", self.on_configure_event)
        self.connect("destroy", Gtk.main_quit)

    def generate_headerbar(self):
        header = Handy.HeaderBar()
        header.props.name = "main"
        header.props.hexpand = True
        header.props.spacing = 0
        header.props.has_subtitle = False
        header.props.show_close_button = True
        header.props.decoration_layout = "close:"
        header.get_style_context().add_class(Gtk.STYLE_CLASS_FLAT)
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
        start_view.attach(start_overlay, 0, 0, 1, 1)
        return start_view

    def convert_color_component_to_string(self, color_component):
        return "{0}".format(str(float(color_component * 255)))

    def convert_rgba_to_webcolor(self, c):
        red   = self.convert_color_component_to_string(c.red)
        green = self.convert_color_component_to_string(c.green)
        blue  = self.convert_color_component_to_string(c.blue)
        return "#" + red + green + blue

    def generate_demo_ui_settings(self):

        grid = Gtk.Grid()
        grid.props.visible = True
        grid.props.can_focus = False
        grid.props.halign = Gtk.Align.FILL
        grid.props.valign = Gtk.Align.END
        grid.props.border_width = 6
        grid.props.row_spacing = 6
        grid.props.column_spacing = 6

        box = Gtk.Grid()
        box.props.hexpand = False
        box.props.visible = True
        box.props.can_focus = False
        box.props.halign = Gtk.Align.CENTER
        box.props.border_width = 6
        box.props.row_spacing = 6
        box.props.column_spacing = 6

        labelc = Gtk.Label()
        labelc.props.hexpand = True
        labelc.props.can_focus = False
        labelc.props.label = "<b> W x H </b>"
        labelc.props.use_markup = True
        box.attach(labelc, 0, 0, 1, 1)
                  
        self.pbar_w = Gtk.Label()
        self.pbar_w.props.hexpand = True
        self.pbar_w.props.can_focus = False
        self.pbar_w.props.label = "80"
        self.pbar_w.props.use_markup = True
        box.attach(self.pbar_w, 1, 0, 1, 1)

        self.pbar_h = Gtk.Label()
        self.pbar_h .props.hexpand = True
        self.pbar_h .props.can_focus = False
        self.pbar_h .props.label = "80"
        self.pbar_h .props.use_markup = True
        box.attach(self.pbar_h, 2, 0, 1, 1)

        grid.attach(box, 0, 0, 2, 1)

        box0 = Gtk.Grid()
        box0.props.hexpand = True
        box0.props.visible = True
        box0.props.can_focus = False
        box0.props.halign = Gtk.Align.FILL
        box0.props.border_width = 6
        box0.props.row_spacing = 6
        box0.props.column_spacing = 6

        self.s_linew = Gtk.Scale()
        self.s_linew.props.name = "s_linew"
        self.s_linew.props.visible = True
        self.s_linew.props.can_focus = True
        self.s_linew.props.hexpand = True
        self.s_linew.props.adjustment = self.linew_adj
        self.s_linew.props.round_digits = 1
        self.s_linew.props.digits = 0
        self.s_linew.props.value_pos = Gtk.PositionType.BOTTOM
        box0.attach(self.s_linew, 1, 0, 2, 1)

        labela = Gtk.Label()
        labela.props.visible = True
        labela.props.can_focus = False
        labela.props.halign = Gtk.Align.START
        labela.props.valign = Gtk.Align.CENTER
        labela.props.label = "Line Width"
        box0.attach(labela, 0, 0, 1, 1)

        grid.attach(box0, 0, 1, 1, 1)

        box1 = Gtk.Grid()
        box1.props.hexpand = True
        box1.props.visible = True
        box1.props.can_focus = False
        box1.props.halign = Gtk.Align.FILL
        box1.props.border_width = 6
        box1.props.row_spacing = 6
        box1.props.column_spacing = 6

        self.s_progr = Gtk.Scale()
        self.s_progr.props.name = "s_progr"
        self.s_progr.props.visible = True
        self.s_progr.props.can_focus = True
        self.s_progr.props.hexpand = True
        self.s_progr.props.adjustment = self.progr_adj
        self.s_progr.props.round_digits = 1
        self.s_progr.props.digits = 2
        self.s_progr.props.value_pos = Gtk.PositionType.BOTTOM
        box1.attach(self.s_progr, 1, 1, 2, 1) 

        labelb = Gtk.Label()
        labelb.props.visible = True
        labelb.props.can_focus = False
        labelb.props.halign = Gtk.Align.START
        labelb.props.valign = Gtk.Align.CENTER
        labelb.props.label = "Percentage"
        box1.attach(labelb, 0, 1, 1, 1)

        grid.attach(box1, 0, 2, 1, 1)


        box2 = Gtk.Grid()
        box2.props.hexpand = True
        box2.props.visible = True
        box2.props.can_focus = False
        box2.props.halign = Gtk.Align.FILL
        box2.props.border_width = 6
        box2.props.row_spacing = 6
        box2.props.column_spacing = 6

        label1 = Gtk.Label()
        label1.props.hexpand = True
        label1.props.can_focus = False
        label1.props.label = "Center"
        box2.attach(label1, 0, 0, 1, 1)

        label2 = Gtk.Label()
        label2.props.hexpand = True
        label2.props.can_focus = False
        label2.props.label = "Radius"
        box2.attach(label2, 1, 0, 1, 1)

        label3 = Gtk.Label()
        label3.props.hexpand = True
        label3.props.can_focus = False
        label3.props.label = "Progress"
        box2.attach(label3, 2, 0, 1, 1)

        self.button_center_filled = Gtk.ToggleButton()
        self.button_center_filled.props.name = "button_center_filled"
        self.button_center_filled.props.label = "Fill"
        self.button_center_filled.props.hexpand = True
        self.button_center_filled.props.can_focus = True
        self.button_center_filled.props.receives_default = True
        box2.attach(self.button_center_filled, 0, 1, 1, 1)

        self.button_radius_filled = Gtk.ToggleButton()
        self.button_radius_filled.props.name = "button_radius_filled"
        self.button_radius_filled.props.label = "Fill"
        self.button_radius_filled.props.hexpand = True
        self.button_radius_filled.props.can_focus = True
        self.button_radius_filled.props.receives_default = True
        box2.attach(self.button_radius_filled, 1, 1, 1, 1)

        self.button_cap = Gtk.ToggleButton()
        self.button_cap.props.name = "button_cap"
        self.button_cap.props.label = "LineCap"
        self.button_cap.props.hexpand = True
        self.button_cap.props.can_focus = True
        self.button_cap.props.receives_default = True
        box2.attach(self.button_cap, 2, 1, 1, 1)

        self.colorbutton1 = Gtk.ColorButton()
        self.colorbutton1.props.name = "colorbutton1"
        self.colorbutton1.props.hexpand = True
        self.colorbutton1.props.can_focus = True
        self.colorbutton1.props.receives_default = True
        box2.attach(self.colorbutton1, 0, 2, 1, 1)
                
        self.colorbutton2 = Gtk.ColorButton()
        self.colorbutton2.props.name = "colorbutton2"
        self.colorbutton2.props.hexpand = True
        self.colorbutton2.props.can_focus = True
        self.colorbutton2.props.receives_default = True
        box2.attach(self.colorbutton2, 1, 2, 1, 1)

        self.colorbutton3 = Gtk.ColorButton()
        self.colorbutton3.props.name = "colorbutton3"
        self.colorbutton3.props.hexpand = True
        self.colorbutton3.props.can_focus = True
        self.colorbutton3.props.receives_default = True
        box2.attach(self.colorbutton3, 2, 2, 1, 1)

        grid.attach(box2, 0, 3, 2, 1)




        return grid

    def on_color_set(self, colorbutton):
        c = colorbutton.get_rgba()
        if colorbutton.props.name == "colorbutton1":
            self.circularprogressbar.set_property("center_fill_color", c.to_string())
        elif colorbutton.props.name == "colorbutton2":
            self.circularprogressbar.set_property("radius_fill_color", c.to_string())
        elif colorbutton.props.name == "colorbutton3":
            self.circularprogressbar.set_property("progress_fill_color", c.to_string())
        colorbutton.set_tooltip_text(self.convert_rgba_to_webcolor(c))

    def on_toggled(self, togglebutton):
        if togglebutton.props.name == "button_cap":
            if self.circularprogressbar.line_cap == cairo.LineCap.ROUND:
                self.circularprogressbar.set_property("line_cap", cairo.LineCap.BUTT)
            else:
                self.circularprogressbar.set_property("line_cap", cairo.LineCap.ROUND)
            # togglebutton.set_tooltip_text (self.circularprogressbar.line_cap.to_string())

    def on_value_changed(self, scale):
        if scale.props.name == "s_progr":
            self.circularprogressbar.set_property("percentage", scale.get_value())
        if scale.props.name == "s_linew":
            self.circularprogressbar.set_property("line_width", scale.get_value())

    def on_configure_event(self, window, event):
        w = self.circularprogressbar.get_allocated_width()
        h = self.circularprogressbar.get_allocated_height()

        wstr = "{0}".format(w)
        hstr = "{0}".format(h)

        # // The lowest is the indicator of the size
        # // because the widget keeps the aspect ratio

        if w > h:
            hstr = "<b><u>" + hstr + "</u></b>"
        elif h > w:
            wstr = "<b><u>" + wstr + "</u></b>"
        else:
            wstr = "<b><u>" + wstr + "</u></b>"
            hstr = "<b><u>" + hstr + "</u></b>"

        self.pbar_w.set_markup(wstr)
        self.pbar_h.set_markup(hstr)

        self.linew_adj.set_upper(float(min(w, h) / 2))

        return False

class HoldButton(Gtk.Button):

    GObject.signal_new("held", Gtk.Button, GObject.SIGNAL_RUN_LAST, GObject.TYPE_BOOLEAN, [GObject.TYPE_PYOBJECT])

    def __init__(self, label=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect("button-press-event", self.h_pressed)
        self.connect("clicked", self.h_clicked)
        self.connect("held", self.on_held)
        self.timeout_id = None
        self.props.label = label
        self.props.expand = False
        self.props.halign = Gtk.Align.CENTER

    def on_held(self, *args):
        print("held")

    def h_clicked(self, *args):
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        else:
            self.stop_emission_by_name("clicked")

    def h_pressed(self, *args):
        self.timeout_id = GLib.timeout_add(750, self.h_timeout, None)

    def h_timeout(self, *args):
        self.timeout_id = None
        self.emit("held", None)
        return False

def main():
    app = Demo()
    Gtk.main()
        
if __name__ == "__main__":    
    main()


