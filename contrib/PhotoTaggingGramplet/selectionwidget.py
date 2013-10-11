#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013 Artem Glebov <artem.glebov@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id: $

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from __future__ import division

from gen.ggettext import sgettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import gobject

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Utils
from gen.display.name import displayer as name_displayer

#-------------------------------------------------------------------------
#
# Grabbers constants and routines
#
#-------------------------------------------------------------------------

GRABBER_INSIDE = 0
GRABBER_OUTSIDE = 1

MIN_CORNER_GRABBER = 20
MIN_SIDE_GRABBER = 20
MIN_GRABBER_PADDING = 10
MIN_SIDE_FOR_INSIDE_GRABBERS = (2 * (MIN_CORNER_GRABBER + MIN_GRABBER_PADDING) + 
                                MIN_SIDE_GRABBER)

INSIDE = 0
GRABBER_UPPER_LEFT = 1
GRABBER_UPPER = 2
GRABBER_UPPER_RIGHT = 3
GRABBER_RIGHT = 4
GRABBER_LOWER_RIGHT = 5
GRABBER_LOWER = 6
GRABBER_LOWER_LEFT = 7
GRABBER_LEFT = 8

def upper_left_grabber_inner(x1, y1, x2, y2):
    return (x1, y1, x1 + MIN_CORNER_GRABBER, y1 + MIN_CORNER_GRABBER)

def upper_grabber_inner(x1, y1, x2, y2):
    return (x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING, 
            y1, 
            x2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING,
            y1 + MIN_CORNER_GRABBER)

def upper_right_grabber_inner(x1, y1, x2, y2):
    return (x2 - MIN_CORNER_GRABBER, y1, x2, y1 + MIN_CORNER_GRABBER)

def right_grabber_inner(x1, y1, x2, y2):
    return (x2 - MIN_CORNER_GRABBER,
            y1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING,
            x2,
            y2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING)

def lower_right_grabber_inner(x1, y1, x2, y2):
    return (x2 - MIN_CORNER_GRABBER, y2 - MIN_CORNER_GRABBER, x2, y2)

def lower_grabber_inner(x1, y1, x2, y2):
    return (x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING, 
            y2 - MIN_CORNER_GRABBER, 
            x2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING,
            y2)

def lower_left_grabber_inner(x1, y1, x2, y2):
    return (x1, y2 - MIN_CORNER_GRABBER, x1 + MIN_CORNER_GRABBER, y2)

def left_grabber_inner(x1, y1, x2, y2):
    return (x1,
            y1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING,
            x1 + MIN_CORNER_GRABBER,
            y2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING)

# outer

def upper_left_grabber_outer(x1, y1, x2, y2):
    return (x1 - MIN_CORNER_GRABBER, y1 - MIN_CORNER_GRABBER, x1, y1)

def upper_grabber_outer(x1, y1, x2, y2):
    return (x1, y1 - MIN_CORNER_GRABBER, x2, y1)

def upper_right_grabber_outer(x1, y1, x2, y2):
    return (x2, y1 - MIN_CORNER_GRABBER, x2 + MIN_CORNER_GRABBER, y1)

def right_grabber_outer(x1, y1, x2, y2):
    return (x2, y1, x2 + MIN_CORNER_GRABBER, y2)

def lower_right_grabber_outer(x1, y1, x2, y2):
    return (x2, y2, x2 + MIN_CORNER_GRABBER, y2 + MIN_CORNER_GRABBER)

def lower_grabber_outer(x1, y1, x2, y2):
    return (x1, y2, x2, y2 + MIN_CORNER_GRABBER)

def lower_left_grabber_outer(x1, y1, x2, y2):
    return (x1 - MIN_CORNER_GRABBER, y2, x1, y2 + MIN_CORNER_GRABBER)

def left_grabber_outer(x1, y1, x2, y2):
    return (x1 - MIN_CORNER_GRABBER, y1, x1, y2)

# motion

def inside_moved(x1, y1, x2, y2, dx, dy):
    return (x1, y1, x2, y2)

def upper_left_moved(x1, y1, x2, y2, dx, dy):
    return (x1 + dx, y1 + dy, x2, y2)

def upper_moved(x1, y1, x2, y2, dx, dy):
    return (x1, y1 + dy, x2, y2)

def upper_right_moved(x1, y1, x2, y2, dx, dy):
    return (x1, y1 + dy, x2 + dx, y2)

def right_moved(x1, y1, x2, y2, dx, dy):
    return (x1, y1, x2 + dx, y2)

def lower_right_moved(x1, y1, x2, y2, dx, dy):
    return (x1, y1, x2 + dx, y2 + dy)

def lower_moved(x1, y1, x2, y2, dx, dy):
    return (x1, y1, x2, y2 + dy)

def lower_left_moved(x1, y1, x2, y2, dx, dy):
    return (x1 + dx, y1, x2, y2 + dy)

def left_moved(x1, y1, x2, y2, dx, dy):
    return (x1 + dx, y1, x2, y2)

# switching

GRABBERS = [INSIDE,
            GRABBER_UPPER_LEFT,
            GRABBER_UPPER,
            GRABBER_UPPER_RIGHT,
            GRABBER_RIGHT,
            GRABBER_LOWER_RIGHT,
            GRABBER_LOWER,
            GRABBER_LOWER_LEFT,
            GRABBER_LEFT]

INNER_GRABBERS = [None,
                  upper_left_grabber_inner,
                  upper_grabber_inner,
                  upper_right_grabber_inner,
                  right_grabber_inner,
                  lower_right_grabber_inner,
                  lower_grabber_inner,
                  lower_left_grabber_inner,
                  left_grabber_inner]

OUTER_GRABBERS = [None,
                  upper_left_grabber_outer,
                  upper_grabber_outer,
                  upper_right_grabber_outer,
                  right_grabber_outer,
                  lower_right_grabber_outer,
                  lower_grabber_outer,
                  lower_left_grabber_outer,
                  left_grabber_outer]

MOTION_FUNCTIONS = [inside_moved,
                    upper_left_moved,
                    upper_moved,
                    upper_right_moved,
                    right_moved,
                    lower_right_moved,
                    lower_moved,
                    lower_left_moved,
                    left_moved]

GRABBERS_SWITCH = [ 
  [INSIDE, INSIDE, INSIDE],
  [GRABBER_UPPER_RIGHT, GRABBER_LOWER_RIGHT, GRABBER_LOWER_LEFT],
  [GRABBER_UPPER, GRABBER_LOWER, GRABBER_LOWER],
  [GRABBER_UPPER_LEFT, GRABBER_LOWER_LEFT, GRABBER_UPPER_RIGHT],
  [GRABBER_LEFT, GRABBER_LEFT, GRABBER_RIGHT],
  [GRABBER_LOWER_LEFT, GRABBER_UPPER_LEFT, GRABBER_UPPER_RIGHT],
  [GRABBER_LOWER, GRABBER_UPPER, GRABBER_UPPER],
  [GRABBER_LOWER_RIGHT, GRABBER_UPPER_RIGHT, GRABBER_UPPER_LEFT],
  [GRABBER_RIGHT, GRABBER_RIGHT, GRABBER_LEFT]
]

# cursors

CURSOR_UPPER = gtk.gdk.Cursor(gtk.gdk.TOP_SIDE)
CURSOR_LOWER = gtk.gdk.Cursor(gtk.gdk.BOTTOM_SIDE)
CURSOR_LEFT = gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE)
CURSOR_RIGHT = gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)
CURSOR_UPPER_LEFT = gtk.gdk.Cursor(gtk.gdk.TOP_LEFT_CORNER)
CURSOR_UPPER_RIGHT = gtk.gdk.Cursor(gtk.gdk.TOP_RIGHT_CORNER)
CURSOR_LOWER_LEFT = gtk.gdk.Cursor(gtk.gdk.BOTTOM_LEFT_CORNER)
CURSOR_LOWER_RIGHT = gtk.gdk.Cursor(gtk.gdk.BOTTOM_RIGHT_CORNER)

CURSORS = [None,
           CURSOR_UPPER_LEFT,
           CURSOR_UPPER,
           CURSOR_UPPER_RIGHT,
           CURSOR_RIGHT,
           CURSOR_LOWER_RIGHT,
           CURSOR_LOWER,
           CURSOR_LOWER_LEFT,
           CURSOR_LEFT]

# helper functions

def grabber_position(rect):
    x1, y1, x2, y2 = rect
    if (x2 - x1 >= MIN_SIDE_FOR_INSIDE_GRABBERS and 
        y2 - y1 >= MIN_SIDE_FOR_INSIDE_GRABBERS):
        return GRABBER_INSIDE
    else:
        return GRABBER_OUTSIDE

def grabber_generators(rect):
    if grabber_position(rect) == GRABBER_INSIDE:
        return INNER_GRABBERS
    else:
        return OUTER_GRABBERS

def switch_grabber(grabber, x1, y1, x2, y2):
    switch_row = GRABBERS_SWITCH[grabber]
    if x1 > x2:
        if y1 > y2:
            return switch_row[1]
        else:
            return switch_row[0]
    else:
        if y1 > y2:
            return switch_row[2]
        else:
            return grabber

def can_grab(rect, x, y):
    """
    Checks if (x,y) lies within one of the grabbers of rect.
    """
    (x1, y1, x2, y2) = rect
    if (x2 - x1 >= MIN_SIDE_FOR_INSIDE_GRABBERS and 
        y2 - y1 >= MIN_SIDE_FOR_INSIDE_GRABBERS):
        # grabbers are inside
        if x < x1 or x > x2 or y < y1 or y > y2:
            return None
        for grabber in GRABBERS[1:]:
            grabber_area = INNER_GRABBERS[grabber](x1, y1, x2, y2)
            if inside_rect(grabber_area, x, y):
                return grabber
        return INSIDE
    else:
        # grabbers are outside
        if x1 <= x <= x2 and y1 <= y <= y2:
            return INSIDE
        for grabber in GRABBERS[1:]:
            grabber_area = OUTER_GRABBERS[grabber](x1, y1, x2, y2)
            if inside_rect(grabber_area, x, y):
                return grabber
        return None

#-------------------------------------------------------------------------
#
# PhotoTaggingGramplet
#
#-------------------------------------------------------------------------

RESIZE_RATIO = 1.5
MAX_ZOOM = 10
MIN_ZOOM = 0.05
MAX_SIZE = 2000
MIN_SIZE = 50
SHADING_OPACITY = 0.7
RADIUS = 5
MIN_SELECTION_SIZE = 10

THUMBNAIL_IMAGE_SIZE = (50, 50)

def scale_to_fit(orig_x, orig_y, target_x, target_y):
    orig_aspect = orig_x / orig_y
    target_aspect = target_x / target_y
    if orig_aspect > target_aspect:
        return target_x / orig_x
    else:
        return target_y / orig_y

def resize_keep_aspect(orig_x, orig_y, target_x, target_y):
    orig_aspect = orig_x / orig_y
    target_aspect = target_x / target_y
    if orig_aspect > target_aspect:
        return (target_x, target_x * orig_y // orig_x)
    else:
        return (target_y * orig_x // orig_y, target_y)

def order_coordinates(point1, point2):
    """
    Returns the rectangle (x1, y1, x2, y2) based on point1 and point2,
    such that x1 <= x2 and y1 <= y2.
    """
    x1 = min(point1[0], point2[0])
    x2 = max(point1[0], point2[0])
    y1 = min(point1[1], point2[1])
    y2 = max(point1[1], point2[1])
    return (x1, y1, x2, y2)

def inside_rect(rect, x, y):
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2

class Region(object):
    """
    Representation of a region of image that can be associated with
    a person.
    """

    def __init__(self, x1, y1, x2, y2):
        self.set_coords(x1, y1, x2, y2)
        self.person = None
        self.mediaref = None

    def coords(self):
        return (self.x1, self.y1, self.x2, self.y2)

    def set_coords(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def contains(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def contains_rect(self, other):
        return self.contains(other.x1, other.y1) and self.contains(other.x2, other.y2)

    def area(self):
        return abs(self.x1 - self.x2) * abs(self.y1 - self.y2)

    def intersects(self, other):
        # assumes that x1 <= x2 and y1 <= y2
        return not (self.x2 < other.x1 or self.x1 > other.x2 or
                    self.y2 < other.y1 or self.y1 > other.y2)

class SelectionWidget(gtk.ScrolledWindow):

    def __init__(self):
        self.loaded = False
        self.start_point_screen = None
        self.selection = None
        self.current = None
        self.in_region = None
        self.grabber = None
        self.regions = []
        self.translation = None
        self.pixbuf = None
        self.scaled_pixbuf = None
        self.scale = 1.0

        gtk.ScrolledWindow.__init__(self)
        self.add(self.build_gui())

    def build_gui(self):
        self.image = gtk.Image()
        self.image.set_has_tooltip(True)
        self.image.connect_after("expose-event", self.expose_handler)
        self.image.connect("query-tooltip", self.show_tooltip)

        self.event_box = gtk.EventBox()
        self.event_box.connect('button-press-event', self.button_press_event)
        self.event_box.connect('button-release-event', self.button_release_event)
        self.event_box.connect('motion-notify-event', self.motion_notify_event)
        self.event_box.connect('scroll-event', self.motion_scroll_event)
        self.event_box.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.event_box.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.event_box.add_events(gtk.gdk.POINTER_MOTION_MASK)

        self.event_box.add(self.image)

        self.viewport = gtk.Viewport()
        self.viewport.add(self.event_box)
        return self.viewport

    # ======================================================
    # field accessors
    # ======================================================

    def set_regions(self, regions):
        self.regions = regions

    def get_current(self):
        return self.current

    def set_current(self, region):
        self.current = region

    def get_selection(self):
        return self.selection

    # ======================================================
    # loading the image
    # ======================================================

    def load_image(self, image_path):
        self.start_point_screen = None
        self.selection = None
        self.in_region = None
        self.grabber_position = None
        self.grabber_to_draw = None

        try:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(image_path)
            self.original_image_size = (self.pixbuf.get_width(), self.pixbuf.get_height())

            viewport_size = self.viewport.get_allocation()
            self.scale = scale_to_fit(self.pixbuf.get_width(), self.pixbuf.get_height(), 
                                  viewport_size.width, viewport_size.height)
            self.rescale()
            self.loaded = True
        except (gobject.GError, OSError):
            self.show_missing()

    def show_missing(self):
        self.pixbuf = None
        self.image.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
        self.image.queue_draw()

    # ======================================================
    # utility functions for retrieving properties
    # ======================================================

    def is_image_loaded(self):
        return self.loaded

    def get_original_image_size(self):
        return self.original_image_size

    def get_scaled_image_size(self):
        unscaled_size = self.get_original_image_size()
        return (unscaled_size[0] * self.scale, unscaled_size[1] * self.scale)

    def get_viewport_size(self):
        rect = self.viewport.get_allocation()
        return (rect.width, rect.height)

    def get_used_screen_size(self):
        scaled_image_size = self.get_scaled_image_size()
        viewport_size = self.get_viewport_size()
        return (min(scaled_image_size[0], viewport_size[0]), 
                min(scaled_image_size[1], viewport_size[1]))

    # ======================================================
    # coordinate transformations
    # ======================================================

    def proportional_to_real(self, coord):
        """
        Translate proportional (ranging from 0 to 100) coordinates to image
        coordinates (in pixels).
        """
        w, h = self.original_image_size
        return (int(round(coord[0] * w / 100)), int(round(coord[1] * h / 100)))

    def real_to_proportional(self, coord):
        """
        Translate image coordinates (in pixels) to proportional (ranging
        from 0 to 100).
        """
        w, h = self.original_image_size
        return (int(round(coord[0] * 100 / w)), int(round(coord[1] * 100 / h)))

    def proportional_to_real_rect(self, rect):
        x1, y1, x2, y2 = rect
        return (self.proportional_to_real((x1, y1)) +
                self.proportional_to_real((x2, y2)))

    def real_to_proportional_rect(self, rect):
        x1, y1, x2, y2 = rect
        return (self.real_to_proportional((x1, y1)) +
                self.real_to_proportional((x2, y2)))

    def image_to_screen(self, coords):
        """
        Translate image coordinates to viewport coordinates using the current
        scale and viewport size.
        """
        viewport_rect = self.viewport.get_allocation()
        image_rect = self.scaled_size
        if image_rect[0] < viewport_rect.width:
            offset_x = (image_rect[0] - viewport_rect.width) / 2
        else:
            offset_x = 0.0
        if image_rect[1] < viewport_rect.height:
            offset_y = (image_rect[1] - viewport_rect.height) / 2
        else:
            offset_y = 0.0
        return (int(coords[0] * self.scale - offset_x), 
                int(coords[1] * self.scale - offset_y))

    def screen_to_image(self, coords):
        """
        Translate viewport coordinates to original (unscaled) image coordinates 
        using the current scale and viewport size.
        """
        viewport_rect = self.viewport.get_allocation()
        image_rect = self.scaled_size
        if image_rect[0] < viewport_rect.width:
            offset_x = (image_rect[0] - viewport_rect.width) / 2
        else:
            offset_x = 0.0
        if image_rect[1] < viewport_rect.height:
            offset_y = (image_rect[1] - viewport_rect.height) / 2
        else:
            offset_y = 0.0
        return (int((coords[0] + offset_x) / self.scale), 
                int((coords[1] + offset_y) / self.scale))

    def truncate_to_image_size(self, coords):
        x, y = coords
        (image_width, image_height) = self.get_original_image_size()
        x = max(x, 0)
        x = min(x, image_width)
        y = max(y, 0)
        y = min(y, image_height)
        return self.proportional_to_real(self.real_to_proportional((x, y)))

    def screen_to_truncated(self, coords):
        return self.truncate_to_image_size(self.screen_to_image(coords))

    def rect_image_to_screen(self, rect):
        x1, y1, x2, y2 = rect
        x1, y1 = self.image_to_screen((x1, y1))
        x2, y2 = self.image_to_screen((x2, y2))
        return (x1, y1, x2, y2)

    # ======================================================
    # drawing, refreshing and zooming the image
    # ======================================================

    def draw_selection(self):
        if not self.scaled_size:
            return

        w, h = self.scaled_size
        offset_x, offset_y = self.image_to_screen((0, 0))
        offset_x -= 1
        offset_y -= 1

        cr = self.image.window.cairo_create()

        if self.selection:
            x1, y1, x2, y2 = self.rect_image_to_screen(self.selection)

            # transparent shading
            self.draw_transparent_shading(cr, x1, y1, x2, y2, w, h, 
                                          offset_x, offset_y)

            # selection frame
            self.draw_selection_frame(cr, x1, y1, x2, y2)
        else:
            # selection frame
            for region in self.regions:
                x1, y1, x2, y2 = self.rect_image_to_screen(region.coords())
                self.draw_region_frame(cr, x1, y1, x2, y2)

        self.draw_grabber(cr)

    def draw_transparent_shading(self, cr, x1, y1, x2, y2, w, h, offset_x, offset_y):
        cr.set_source_rgba(1.0, 1.0, 1.0, SHADING_OPACITY)
        cr.rectangle(offset_x, offset_y, x1 - offset_x, y1 - offset_y)
        cr.rectangle(offset_x, y1, x1 - offset_x, y2 - y1)
        cr.rectangle(offset_x, y2, x1 - offset_x, h - y2 + offset_y)
        cr.rectangle(x1, y2 + 1, x2 - x1 + 1, h - y2 + offset_y)
        cr.rectangle(x2 + 1, y2 + 1, w - x2 + offset_x, h - y2 + offset_y)
        cr.rectangle(x2 + 1, y1, w - x2 + offset_x, y2 - y1 + 1)
        cr.rectangle(x2 + 1, offset_y, w - x2 + offset_x, y2 - offset_y)
        cr.rectangle(x1, offset_y, x2 - x1 + 1, y1 - offset_y)
        cr.fill()

    def draw_selection_frame(self, cr, x1, y1, x2, y2):
        self.draw_region_frame(cr, x1, y1, x2, y2)

    def draw_region_frame(self, cr, x1, y1, x2, y2):
        cr.set_source_rgb(1.0, 1.0, 1.0) # white
        cr.rectangle(x1, y1, x2 - x1, y2 - y1)
        cr.stroke()
        cr.set_source_rgb(0.0, 0.0, 1.0) # blue
        cr.rectangle(x1 - 2, y1 - 2, x2 - x1 + 4, y2 - y1 + 4)
        cr.stroke()

    def draw_grabber(self, cr):
        if self.current is not None and self.grabber is not None:
            selection_rect = self.rect_image_to_screen(self.selection)
            cr.set_source_rgb(1.0, 0, 0)
            if self.grabber_position is None:
                generators = grabber_generators(selection_rect)
            elif self.grabber_position == GRABBER_INSIDE:
                generators = INNER_GRABBERS
            else:
                generators = OUTER_GRABBERS
            if self.grabber_to_draw is not None:
                generator = generators[self.grabber_to_draw]
            else:
                generator = generators[self.grabber]
            if generator is not None:
                x1, y1, x2, y2 = generator(*selection_rect)
                cr.rectangle(x1, y1, x2 - x1, y2 - y1)
            cr.stroke()

    def refresh(self):
        self.image.queue_draw()

    def rescale(self):
        self.scaled_size = (int(self.original_image_size[0] * self.scale), 
                            int(self.original_image_size[1] * self.scale))
        self.scaled_image = self.pixbuf.scale_simple(self.scaled_size[0],
                                                     self.scaled_size[1],
                                                     gtk.gdk.INTERP_BILINEAR)
        self.image.set_from_pixbuf(self.scaled_image)
        self.image.set_size_request(*self.scaled_size)
        self.event_box.set_size_request(*self.scaled_size)

    def can_zoom_in(self):
        scaled_size = (self.original_image_size[0] * self.scale * RESIZE_RATIO,
                       self.original_image_size[1] * self.scale * RESIZE_RATIO)
        return scaled_size[0] < MAX_SIZE and scaled_size[1] < MAX_SIZE

    def can_zoom_out(self):
        scaled_size = (self.original_image_size[0] * self.scale * RESIZE_RATIO,
                       self.original_image_size[1] * self.scale * RESIZE_RATIO)
        return scaled_size[0] >= MIN_SIZE and scaled_size[1] >= MIN_SIZE

    def zoom_in(self):
        if self.can_zoom_in():
            self.scale *= RESIZE_RATIO
            self.rescale()
            self.emit("zoomed-in")

    def zoom_out(self):
        if self.can_zoom_out():
            self.scale /= RESIZE_RATIO
            self.rescale()
            self.emit("zoomed-out")

    def expose_handler(self, widget, event):
        if self.pixbuf:
            self.draw_selection()

    def select(self, region):
        self.current = region
        if self.current is not None:
            self.selection = self.current.coords()
        self.image.queue_draw()

    def clear_selection(self):
        self.current = None
        self.selection = None
        self.image.queue_draw()

    # ======================================================
    # managing regions
    # ======================================================

    def find_region(self, x, y):
        result = None
        for region in self.regions:
            if region.contains(x, y):
                if result is None or result.area() > region.area():
                    result = region
        return result

    # ======================================================
    # thumbnails
    # ======================================================

    def get_thumbnail(self, region, thumbnail_size):
        w = region.x2 - region.x1
        h = region.y2 - region.y1
        if w >= 1 and h >= 1:
            subpixbuf = self.pixbuf.subpixbuf(region.x1, region.y1, w, h)
            size = resize_keep_aspect(w, h, *thumbnail_size)
            return subpixbuf.scale_simple(size[0], size[1], 
                                          gtk.gdk.INTERP_BILINEAR)
        else:
            return None

    # ======================================================
    # mouse event handlers
    # ======================================================

    def button_press_event(self, obj, event):
        if not self.is_image_loaded():
            return
        if event.button == 1: # left button
            self.start_point_screen = (event.x, event.y)
            if self.current is not None and self.grabber is None:
                self.current = None
                self.selection = None
                self.refresh()
                self.emit("selection-cleared")
        elif event.button == 3: # right button
            # select a region, if clicked inside one
            click_point = self.screen_to_image((event.x, event.y))
            self.current = self.find_region(*click_point)
            self.selection = self.current.coords() if self.current is not None else None
            self.start_point_screen = None
            self.refresh()
            if self.current is not None:
                self.emit("region-selected")
                self.emit("right-button-clicked", event)
            else:
                self.emit("selection-cleared")
        return True # don't propagate the event further

    def button_release_event(self, obj, event):
        if not self.is_image_loaded():
            return
        if event.button == 1:
            if self.start_point_screen:
                if self.current is not None:
                    # a box is currently selected
                    if self.grabber is None:
                        # clicked outside of the grabbing area
                        self.current = None
                        self.selection = None
                        self.emit("selection-cleared")
                    elif self.grabber != INSIDE:
                        # clicked on one of the grabbers
                        dx, dy = (event.x - self.start_point_screen[0], 
                                  event.y - self.start_point_screen[1])
                        self.grabber_to_draw = self.modify_selection(dx, dy)
                        self.emit("region-modified")
                        self.current.set_coords(*self.selection)
                else:
                    # nothing is currently selected
                    if (abs(self.start_point_screen[0] - event.x) >= MIN_SELECTION_SIZE and
                        abs(self.start_point_screen[1] - event.y) >= MIN_SELECTION_SIZE):
                        # region selection
                        region = Region(*self.selection)
                        self.regions.append(region)
                        self.current = region
                        self.emit("region-created", event)
                    else:
                        # nothing selected, just a click
                        click_point = self.screen_to_image(self.start_point_screen)
                        self.current = self.find_region(*click_point)
                        self.selection = self.current.coords() if self.current is not None else None
                        self.emit("region-selected")

                self.start_point_screen = None
                self.refresh()

    def motion_notify_event(self, widget, event):
        if not self.is_image_loaded():
            return
        end_point_orig = self.screen_to_image((event.x, event.y))
        end_point = self.truncate_to_image_size(end_point_orig)
        if self.start_point_screen:
            # selection (mouse button pressed)
            if self.grabber is not None and self.grabber != INSIDE:
                # dragging the grabber
                dx, dy = (event.x - self.start_point_screen[0], 
                          event.y - self.start_point_screen[1])
                self.grabber_to_draw = self.modify_selection(dx, dy)
            else:
                # making new selection
                start_point = self.screen_to_truncated(self.start_point_screen)
                self.selection = order_coordinates(start_point, end_point)
        else:
            # motion (mouse button is not pressed)
            self.in_region = self.find_region(*end_point_orig)
            if self.current is not None:
                # a box is active, so check if the pointer is inside a grabber
                rect = self.rect_image_to_screen(self.current.coords())
                self.grabber = can_grab(rect, event.x, event.y)
                if self.grabber is not None:
                    self.grabber_to_draw = self.grabber
                    self.grabber_position = grabber_position(rect)
                    self.event_box.window.set_cursor(CURSORS[self.grabber])
                else:
                    self.grabber_to_draw = None
                    self.grabber_position = None
                    self.event_box.window.set_cursor(None)
            else:
                # nothing is active
                self.grabber = None
                self.grabber_to_draw = None
                self.grabber_position = None
                self.event_box.window.set_cursor(None)
        self.image.queue_draw()

    def motion_scroll_event(self, widget, event):
        if not self.is_image_loaded():
            return
        if event.direction == gtk.gdk.SCROLL_UP:
            self.zoom_in()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.zoom_out()

    # ======================================================
    # helpers for mouse event handlers
    # ======================================================

    def modify_selection(self, dx, dy):
        x1, y1, x2, y2 = self.rect_image_to_screen(self.current.coords())
        x1, y1, x2, y2 = MOTION_FUNCTIONS[self.grabber](x1, y1, x2, y2, dx, dy)
        (x1, y1) = self.screen_to_truncated((x1, y1))
        (x2, y2) = self.screen_to_truncated((x2, y2))
        grabber = switch_grabber(self.grabber, x1, y1, x2, y2)
        self.selection = order_coordinates((x1, y1), (x2, y2))
        return grabber

    # ======================================================
    # tooltips
    # ======================================================

    def show_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        if self.in_region:
            person = self.in_region.person
            if person:
                name = name_displayer.display(person)
            else:
                return False
            tooltip.set_text(name)
            return True
        else:
            return False

gobject.type_register(SelectionWidget)
gobject.signal_new("region-modified", SelectionWidget, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
gobject.signal_new("region-created", SelectionWidget, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, (gtk.gdk.Event,))
gobject.signal_new("region-selected", SelectionWidget, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
gobject.signal_new("selection-cleared", SelectionWidget, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
gobject.signal_new("right-button-clicked", SelectionWidget, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, (gtk.gdk.Event,))
gobject.signal_new("zoomed-in", SelectionWidget, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
gobject.signal_new("zoomed-out", SelectionWidget, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())
