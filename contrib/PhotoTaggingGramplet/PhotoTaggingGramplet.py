#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011 Nick Hall
#           (C) 2011 Doug Blank <doug.blank@gmail.com>
#           (C) 2013  Artem Glebov <artem.glebov@gmail.com>
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

import os
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
from config import config
from gen.db import DbTxn
from gen.display.name import displayer as name_displayer
from gen.plug import Gramplet
from gen.lib import MediaRef, Person
from gui.editors.editperson import EditPerson
from gui.selectors import SelectorFactory

#-------------------------------------------------------------------------
#
# computer vision modules
#
#-------------------------------------------------------------------------
try:
    import cv
    computer_vision_available = True
except ImportError:
    computer_vision_available = False

#-------------------------------------------------------------------------
#
# configuration
#
#-------------------------------------------------------------------------

GRAMPLET_CONFIG_NAME = "phototagginggramplet"
CONFIG = config.register_manager(GRAMPLET_CONFIG_NAME)
CONFIG.register("detection.box_size", (50,50))
CONFIG.load()
CONFIG.save()

MIN_FACE_SIZE = CONFIG.get("detection.box_size")

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
DETECTED_REGION_PADDING = 10
MIN_SELECTION_SIZE = 10

MIN_CORNER_GRABBER = 50
MIN_SIDE_GRABBER = 50
MIN_GRABBER_PADDING = 20
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

path, filename = os.path.split(__file__)
HAARCASCADE_PATH = os.path.join(path, 'haarcascade_frontalface_alt.xml')

CURSOR_UPPER = gtk.gdk.Cursor(gtk.gdk.TOP_SIDE)
CURSOR_LOWER = gtk.gdk.Cursor(gtk.gdk.BOTTOM_SIDE)
CURSOR_LEFT = gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE)
CURSOR_RIGHT = gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)
CURSOR_UPPER_LEFT = gtk.gdk.Cursor(gtk.gdk.TOP_LEFT_CORNER)
CURSOR_UPPER_RIGHT = gtk.gdk.Cursor(gtk.gdk.TOP_RIGHT_CORNER)
CURSOR_LOWER_LEFT = gtk.gdk.Cursor(gtk.gdk.BOTTOM_LEFT_CORNER)
CURSOR_LOWER_RIGHT = gtk.gdk.Cursor(gtk.gdk.BOTTOM_RIGHT_CORNER)

CURSORS = [None, CURSOR_UPPER_LEFT, CURSOR_UPPER, CURSOR_UPPER_RIGHT,
           CURSOR_RIGHT, CURSOR_LOWER_RIGHT, CURSOR_LOWER, CURSOR_LOWER_LEFT,
           CURSOR_LEFT]

def resize_keep_aspect(orig_x, orig_y, target_x, target_y):
    orig_aspect = orig_x / orig_y
    target_aspect = target_x / target_y
    if orig_aspect > target_aspect:
        return (target_x, target_x * orig_y // orig_x)
    else:
        return (target_y * orig_x // orig_y, target_y)

def scale_to_fit(orig_x, orig_y, target_x, target_y):
    orig_aspect = orig_x / orig_y
    target_aspect = target_x / target_y
    if orig_aspect > target_aspect:
        return target_x / orig_x
    else:
        return target_y / orig_y

def order_coordinates(point1, point2):
    x1 = min(point1[0], point2[0])
    x2 = max(point1[0], point2[0])
    y1 = min(point1[1], point2[1])
    y2 = max(point1[1], point2[1])
    return (x1, y1, x2, y2)

def can_grab(rect, x, y):
    (x1, y1, x2, y2) = rect
    if (x2 - x1 >= MIN_SIDE_FOR_INSIDE_GRABBERS and 
        y2 - y1 >= MIN_SIDE_FOR_INSIDE_GRABBERS):
        # grabbers are inside
        if x < x1 or x > x2 or y < y1 or y > y2:
            return None
        elif y1 <= y <= y1 + MIN_CORNER_GRABBER: # upper grabbers
            if x1 <= x <= x1 + MIN_CORNER_GRABBER:
                return GRABBER_UPPER_LEFT
            elif (x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING <= x and 
                  x <= x2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING):
                return GRABBER_UPPER
            elif x2 - MIN_CORNER_GRABBER <= x <= x2:
                return GRABBER_UPPER_RIGHT
            else:
                return INSIDE
        elif y2 - MIN_CORNER_GRABBER <= y <= y2: # lower grabbers
            if x1 <= x <= x1 + MIN_CORNER_GRABBER:
                return GRABBER_LOWER_LEFT
            elif (x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING <= x and 
                  x <= x2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING):
                return GRABBER_LOWER
            elif x2 - MIN_CORNER_GRABBER <= x <= x2:
                return GRABBER_LOWER_RIGHT
            else:
                return INSIDE
        elif (y1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING <= y and
              y <= y2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING):
            # middle grabbers (left and right side)
            if x1 <= x <= x1 + MIN_CORNER_GRABBER:
                return GRABBER_LEFT
            elif x2 - MIN_CORNER_GRABBER <= x <= x2:
                return GRABBER_RIGHT
            else:
                return INSIDE
        else:
            return INSIDE
    else:
        # grabbers are outside
        if x1 <= x <= x2 and y1 <= y <= y2:
            return INSIDE
        elif y1 - MIN_CORNER_GRABBER <= y <= y1: # upper grabbers
            if x1 - MIN_CORNER_GRABBER <= x <= x1:
                return GRABBER_UPPER_LEFT
            elif x1 <= x <= x2:
                return GRABBER_UPPER
            elif x2 <= x <= x2 + MIN_CORNER_GRABBER:
                return GRABBER_UPPER_RIGHT
            else:
                return None
        elif y2 <= y <= y2 + MIN_CORNER_GRABBER: # lower grabbers
            if x1 - MIN_CORNER_GRABBER <= x <= x1:
                return GRABBER_LOWER_LEFT
            elif x1 <= x <= x2:
                return GRABBER_LOWER
            elif x2 <= x <= x2 + MIN_CORNER_GRABBER:
                return GRABBER_LOWER_RIGHT
            else:
                return None
        elif y1 <= y <= y2:
            if x1 - MIN_CORNER_GRABBER <= x <= x1:
                return GRABBER_LEFT
            elif x2 <= x <= x2 + MIN_CORNER_GRABBER:
                return GRABBER_RIGHT
            else:
                return None
        else:
            return None

class Region(object):

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

class PhotoTaggingGramplet(Gramplet):

    def init(self):
        self.loaded = False
        self.pixbuf = None
        self.current = None
        self.scaled_pixbuf = None
        self.scale = 1.0

        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
        self.top.show_all()

    def on_save(self):
        CONFIG.save()

    # ======================================================
    # building the GUI
    # ======================================================

    def build_gui(self):
        """
        Build the GUI interface.
        """
        self.top = gtk.VBox()

        hpaned = gtk.HPaned()

        button_panel = gtk.HBox()

        self.button_index = gtk.ToolButton(gtk.STOCK_INDEX)
        self.button_add = gtk.ToolButton(gtk.STOCK_ADD)
        self.button_del = gtk.ToolButton(gtk.STOCK_REMOVE)
        self.button_clear = gtk.ToolButton(gtk.STOCK_CLEAR)
        self.button_edit = gtk.ToolButton(gtk.STOCK_EDIT)
        self.button_zoom_in = gtk.ToolButton(gtk.STOCK_ZOOM_IN)
        self.button_zoom_out = gtk.ToolButton(gtk.STOCK_ZOOM_OUT)
        self.button_detect = gtk.ToolButton(gtk.STOCK_EXECUTE)

        self.button_index.connect("clicked", self.sel_person_clicked)
        self.button_add.connect("clicked", self.add_person_clicked)
        self.button_del.connect("clicked", self.clear_ref_clicked)
        self.button_clear.connect("clicked", self.del_region_clicked)
        self.button_edit.connect("clicked", self.edit_person_clicked)
        self.button_zoom_in.connect("clicked", self.zoom_in_clicked)
        self.button_zoom_out.connect("clicked", self.zoom_out_clicked)
        self.button_detect.connect("clicked", self.detect_faces_clicked)

        button_panel.pack_start(self.button_index, expand=False, fill=False, padding=5)
        button_panel.pack_start(self.button_add, expand=False, fill=False, padding=5)
        button_panel.pack_start(self.button_del, expand=False, fill=False, padding=5)
        button_panel.pack_start(self.button_clear, expand=False, fill=False, padding=5)
        button_panel.pack_start(self.button_edit, expand=False, fill=False, padding=5)
        button_panel.pack_start(self.button_zoom_in, expand=False, fill=False, padding=5)
        button_panel.pack_start(self.button_zoom_out, expand=False, fill=False, padding=5)
        button_panel.pack_start(self.button_detect, expand=False, fill=False, padding=5)

        tooltips = gtk.Tooltips()
        self.button_index.set_tooltip(tooltips, "Select Person", None)
        self.button_add.set_tooltip(tooltips, "Add Person", None)
        self.button_del.set_tooltip(tooltips, "Clear Reference", None)
        self.button_clear.set_tooltip(tooltips, "Remove Selection", None)
        self.button_edit.set_tooltip(tooltips, "Edit referenced Person", None)
        self.button_zoom_in.set_tooltip(tooltips, "Zoom In", None)
        self.button_zoom_out.set_tooltip(tooltips, "Zoom Out", None)

        if computer_vision_available:
            self.button_detect.set_tooltip(tooltips, "Detect faces", None)
        else:
            self.button_detect.set_tooltip(tooltips, "Detect faces (cv module required)", None)

        self.enable_buttons()

        self.top.pack_start(button_panel, expand=False, fill=True, padding=5)

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

        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.add(self.viewport)
        self.scrolled_window.set_size_request(200, -1)

        hpaned.pack1(self.scrolled_window, resize=True, shrink=False)

        self.treestore = gtk.TreeStore(int, str)

        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_size_request(400, -1)
        self.treeview.connect("cursor-changed", self.cursor_changed)
        self.treeview.connect("row-activated", self.row_activated)
        self.column1 = gtk.TreeViewColumn(_(''))
        self.column2 = gtk.TreeViewColumn(_('Person'))
        self.treeview.append_column(self.column1)
        self.treeview.append_column(self.column2)

        self.cell1 = gtk.CellRendererText()
        self.cell2 = gtk.CellRendererText()
        self.column1.pack_start(self.cell1, True)
        self.column1.add_attribute(self.cell1, 'text', 0)
        self.column2.pack_start(self.cell2, True)
        self.column2.add_attribute(self.cell2, 'text', 1)

        self.treeview.set_search_column(0)
        self.column1.set_sort_column_id(0)
        self.column2.set_sort_column_id(1)

        hpaned.pack2(self.treeview, resize=False, shrink=False)

        self.top.pack_start(hpaned, expand=True, fill=True)

        return self.top

    # ======================================================
    # gramplet event handlers
    # ======================================================

    def db_changed(self):
        self.dbstate.db.connect('media-update', self.update)
        self.connect_signal('Media', self.update)

    def main(self):
        self.loaded = False
        self.start_point_screen = None
        self.selection = None
        self.current = None
        self.in_region = None
        self.grabber = None
        self.regions = []
        self.translation = None
        self.pixbuf = None
        media = self.get_current_object()
        self.top.hide()
        if media and media.mime.startswith("image"):
            self.load_image(media)
        else:
            self.pixbuf = None
            self.image.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
            self.image.queue_draw()
        self.refresh_list()
        self.enable_buttons()
        self.top.show()

    def expose_handler(self, widget, event):
        if self.pixbuf:
            self.draw_selection()

    # ======================================================
    # loading the image
    # ======================================================

    def load_image(self, media):
        self.start_point_screen = None
        self.selection = None
        self.in_region = None

        image_path = Utils.media_path_full(self.dbstate.db, media.get_path())
        try:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(image_path)
            self.original_image_size = (self.pixbuf.get_width(), self.pixbuf.get_height())

            viewport_size = self.viewport.get_allocation()
            self.scale = scale_to_fit(self.pixbuf.get_width(), self.pixbuf.get_height(), 
                                  viewport_size.width, viewport_size.height)
            self.rescale()
            self.retrieve_backrefs()
            self.loaded = True
        except (gobject.GError, OSError):
            self.pixbuf = None
            self.image.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)

    def retrieve_backrefs(self):
        """
        Finds the media references pointing to the current image
        """
        backrefs = self.dbstate.db.find_backlink_handles(self.get_current_handle())
        for (reftype, ref) in backrefs:
            if reftype == "Person":
                person = self.dbstate.db.get_person_from_handle(ref)
                name = person.get_primary_name()
                gallery = person.get_media_list()
                for mediaref in gallery:
                    referenced_handles = mediaref.get_referenced_handles()
                    if len(referenced_handles) == 1:
                        handle_type, handle = referenced_handles[0]
                        if handle_type == "MediaObject" and handle == self.get_current_handle():
                            rect = mediaref.get_rectangle()
                            if rect is None:
                                rect = (0, 0, 100, 100)
                            coords = self.proportional_to_real_rect(rect)
                            region = Region(*coords)
                            region.person = person
                            region.mediaref = mediaref
                            self.regions.append(region)

    # ======================================================
    # utility functions for retrieving properties
    # ======================================================

    def is_image_loaded(self):
        return self.loaded

    def get_current_handle(self):
        return self.get_active('Media')

    def get_current_object(self):
        return self.dbstate.db.get_object_from_handle(self.get_current_handle())

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
        return (min(scaled_image_size[0], viewport_size[0]), min(scaled_image_size[1], viewport_size[1]))

    # ======================================================
    # coordinate transformations
    # ======================================================

    def proportional_to_real(self, coord):
        """
        Translate proportional (ranging from 0 to 100) coordinates to image coordinates (in pixels).
        """
        w, h = self.original_image_size
        return map ((lambda x : int(round(x / 100))), (coord[0] * w, coord[1] * h))

    def real_to_proportional(self, coord):
        """
        Translate image coordinates (in pixels) to proportional (ranging from 0 to 100).
        """
        w, h = self.original_image_size
        return map ((lambda x : int(round(x * 100))), (coord[0] / w, coord[1] / h))

    def proportional_to_real_rect(self, rect):
        return self.proportional_to_real(rect[0:2]) + self.proportional_to_real(rect[2:4])

    def real_to_proportional_rect(self, rect):
        return self.real_to_proportional(rect[0:2]) + self.real_to_proportional(rect[2:4])

    def image_to_screen(self, coords):
        """
        Translate image coordinates to viewport coordinates using the current scale and viewport size.
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
        return (int(coords[0] * self.scale - offset_x), int(coords[1] * self.scale - offset_y))

    def screen_to_image(self, coords):
        """
        Translate viewport coordinates to original (unscaled) image coordinates using the current scale
        and viewport size.
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
        return (int((coords[0] + offset_x) / self.scale), int((coords[1] + offset_y) / self.scale))

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
            x1, y1, x2, y2 = self.rect_image_to_screen(self.selection)
            cr.set_source_rgb(1.0, 0, 0)
            if (x2 - x1 >= MIN_SIDE_FOR_INSIDE_GRABBERS and
                y2 - y1 >= MIN_SIDE_FOR_INSIDE_GRABBERS):
                if self.grabber == GRABBER_UPPER_LEFT:
                    cr.rectangle(x1,
                                 y1,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_UPPER:
                    cr.rectangle(x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING,
                                 y1,
                                 x2 - x1 - 2 * (MIN_CORNER_GRABBER + MIN_GRABBER_PADDING),
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_UPPER_RIGHT:
                    cr.rectangle(x2 - MIN_CORNER_GRABBER,
                                 y1,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_RIGHT:
                    cr.rectangle(x2 - MIN_CORNER_GRABBER,
                                 y1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING,
                                 MIN_CORNER_GRABBER,
                                 y2 - y1 - 2 * (MIN_CORNER_GRABBER + MIN_GRABBER_PADDING))
                elif self.grabber == GRABBER_LOWER_RIGHT:
                    cr.rectangle(x2 - MIN_CORNER_GRABBER,
                                 y2 - MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_LOWER:
                    cr.rectangle(x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING,
                                 y2 - MIN_CORNER_GRABBER,
                                 x2 - x1 - 2 * (MIN_CORNER_GRABBER + MIN_GRABBER_PADDING),
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_LOWER_LEFT:
                    cr.rectangle(x1,
                                 y2 - MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_LEFT:
                    cr.rectangle(x1,
                                 y1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING, 
                                 MIN_CORNER_GRABBER, 
                                 y2 - y1 - 2 * (MIN_CORNER_GRABBER + MIN_GRABBER_PADDING))
                else:
                    assert False # this case should never be reached
            else:
                if self.grabber == GRABBER_UPPER_LEFT:
                    cr.rectangle(x1 - MIN_CORNER_GRABBER,
                                 y1 - MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_UPPER:
                    cr.rectangle(x1,
                                 y1 - MIN_CORNER_GRABBER,
                                 x2 - x1,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_UPPER_RIGHT:
                    cr.rectangle(x2,
                                 y1 - MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_RIGHT:
                    cr.rectangle(x2,
                                 y1,
                                 MIN_CORNER_GRABBER,
                                 y2 - y1)
                elif self.grabber == GRABBER_LOWER_RIGHT:
                    cr.rectangle(x2,
                                 y2,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_LOWER:
                    cr.rectangle(x1,
                                 y2,
                                 x2 - x1,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_LOWER_LEFT:
                    cr.rectangle(x1 - MIN_CORNER_GRABBER,
                                 y2,
                                 MIN_CORNER_GRABBER,
                                 MIN_CORNER_GRABBER)
                elif self.grabber == GRABBER_LEFT:
                    cr.rectangle(x1 - MIN_CORNER_GRABBER,
                                 y1, 
                                 MIN_CORNER_GRABBER, 
                                 y2 - y1)
                else:
                    assert False # this case should never be reached
            cr.stroke()


    def refresh(self):
        self.image.queue_draw()
        self.refresh_list()
        self.refresh_selection()

    def rescale(self):
        self.scaled_size = (int(self.original_image_size[0] * self.scale), int(self.original_image_size[1] * self.scale))
        self.scaled_image = self.pixbuf.scale_simple(self.scaled_size[0], self.scaled_size[1], gtk.gdk.INTERP_BILINEAR)
        self.image.set_from_pixbuf(self.scaled_image)
        self.image.set_size_request(*self.scaled_size)
        self.event_box.set_size_request(*self.scaled_size)

    def can_zoom_in(self):
        scaled_size = (int(self.original_image_size[0] * self.scale * RESIZE_RATIO), int(self.original_image_size[1] * self.scale * RESIZE_RATIO))
        return scaled_size[0] < MAX_SIZE and scaled_size[1] < MAX_SIZE

    def can_zoom_out(self):
        scaled_size = (int(self.original_image_size[0] * self.scale * RESIZE_RATIO), int(self.original_image_size[1] * self.scale * RESIZE_RATIO))
        return scaled_size[0] >= MIN_SIZE and scaled_size[1] >= MIN_SIZE

    def zoom_in(self):
        if self.can_zoom_in():
            self.scale *= RESIZE_RATIO
            self.rescale()
            self.enable_buttons()

    def zoom_out(self):
        if self.can_zoom_out():
            self.scale /= RESIZE_RATIO
            self.rescale()
            self.enable_buttons()

    # ======================================================
    # managing regions
    # ======================================================

    def check_and_translate_to_proportional(self, mediaref, rect):
        if mediaref:
            return mediaref.get_rectangle()
        else:
            return self.real_to_proportional_rect(rect)

    def find_region(self, x, y):
        result = None
        for region in self.regions:
            if region.contains(x, y):
                if result is None or result.area() > region.area():
                    result = region
        return result

    def intersects_any(self, region):
        for r in self.regions:
            if r.intersects(region):
                return True
        return False

    def enclosing_region(self, region):
        for r in self.regions:
            if r.contains_rect(region):
                return r
        return None

    # ======================================================
    # tooltips
    # ======================================================

    def show_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        if self.in_region:
            person = self.in_region.person
            if person:
                name = name_displayer.display(person)
            else:
                name = ""
            tooltip.set_text(name)
            return True
        else:
            return False

    # ======================================================
    # helpers for updating database objects
    # ======================================================

    def add_reference(self, person, rect):
        """
        Add a reference to the media object to the specified person.
        """
        mediaref = MediaRef()
        mediaref.ref = self.get_current_handle()
        mediaref.set_rectangle(rect)
        person.add_media_reference(mediaref)
        self.commit_person(person)
        return mediaref

    def remove_reference(self, person, mediaref):
        """
        Removes the reference to the media object from the person.
        """
        person.get_media_list().remove(mediaref)
        self.commit_person(person)

    def commit_person(self, person):
        """
        Save the modifications made to a Person object to the database.
        """
        with DbTxn('', self.dbstate.db) as trans:
            self.dbstate.db.commit_person(person, trans)
            msg = _("Edit Person (%s)") % \
                  name_displayer.display(person)
            trans.set_description(msg)

    # ======================================================
    # managing toolbar buttons
    # ======================================================
    def enable_buttons(self):
        self.button_index.set_sensitive(self.current is not None)
        self.button_add.set_sensitive(self.current is not None)
        self.button_del.set_sensitive(self.current is not None and self.current.person is not None)
        self.button_clear.set_sensitive(self.current is not None)
        self.button_edit.set_sensitive(self.current is not None and self.current.person is not None)
        self.button_zoom_in.set_sensitive(self.is_image_loaded() and self.can_zoom_in())
        self.button_zoom_out.set_sensitive(self.is_image_loaded() and self.can_zoom_out())
        self.button_detect.set_sensitive(self.is_image_loaded() and computer_vision_available)

    # ======================================================
    # toolbar button event handles
    # ======================================================
    def add_person_clicked(self, event):
        if self.current:
            person = Person()
            EditPerson(self.dbstate, self.uistate, self.track, person, self.new_person_added)

    def sel_person_clicked(self, event):
        if self.current:
            SelectPerson = SelectorFactory('Person')
            sel = SelectPerson(self.dbstate, self.uistate, self.track, _("Select Person"))
            person = sel.run()
            if person:
                self.set_current_person(person)
                self.current = None
                self.selection = None
                self.refresh()
                self.enable_buttons()

    def del_region_clicked(self, event):
        if self.current:
            self.regions.remove(self.current)
            if self.current.person:
                self.remove_reference(self.current.person, self.current.mediaref)
            self.current = None
            self.selection = None
            self.refresh()
            self.enable_buttons()

    def clear_ref_clicked(self, event):
        if self.clear_current_ref():
            self.refresh()

    def edit_person_clicked(self, event):
        person = self.current.person
        if person:
            EditPerson(self.dbstate, self.uistate, self.track, person)
            self.refresh()

    def zoom_in_clicked(self, event):
        self.zoom_in()

    def zoom_out_clicked(self, event):
        self.zoom_out()

    def detect_faces_clicked(self, event):
        min_face_size = MIN_FACE_SIZE
        media = self.get_current_object()
        image_path = Utils.media_path_full(self.dbstate.db, media.get_path())
        cv_image = cv.LoadImage(image_path, cv.CV_LOAD_IMAGE_GRAYSCALE)
        o_width, o_height = cv_image.width, cv_image.height
        cv.EqualizeHist(cv_image, cv_image)
        cascade = cv.Load(HAARCASCADE_PATH)
        faces = cv.HaarDetectObjects(cv_image, cascade, 
                                     cv.CreateMemStorage(0),
                                     1.2, 2, cv.CV_HAAR_DO_CANNY_PRUNING, 
                                     min_face_size)
        for ((x, y, width, height), neighbors) in faces:
            region = Region(x - DETECTED_REGION_PADDING, y - DETECTED_REGION_PADDING,
                            x + width + DETECTED_REGION_PADDING, y + height + DETECTED_REGION_PADDING)
            if self.enclosing_region(region) is None:
                self.regions.append(region)
        self.refresh()

    # ======================================================
    # helpers for toolbar event handlers
    # ======================================================

    def new_person_added(self, person):
        self.set_current_person(person)
        self.current = None
        self.selection = None
        self.refresh()
        self.enable_buttons()

    def set_current_person(self, person):
        if self.current and person:
            self.clear_current_ref()
            rect = self.check_and_translate_to_proportional(self.current.mediaref, self.current.coords())
            mediaref = self.add_reference(person, rect)
            self.current.person = person
            self.current.mediaref = mediaref

    def clear_current_ref(self):
        if self.current:
            if self.current.person:
                self.remove_reference(self.current.person, self.current.mediaref)
                self.current.person = None
                self.current.mediaref = None
                return True
        return False

    # ======================================================
    # mouse event handlers
    # ======================================================

    def button_press_event(self, obj, event):
        if not self.is_image_loaded():
            return
        if event.button==1:
            self.start_point_screen = (event.x, event.y)
            if self.current is not None and self.grabber is None:
                self.current = None
                self.selection = None
                self.start_point_screen = None
                self.refresh()

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
                    elif self.grabber != INSIDE:
                        # clicked on one of the grabbers
                        dx, dy = (event.x - self.start_point_screen[0], 
                                  event.y - self.start_point_screen[1])
                        self.modify_selection(dx, dy)
                        person = self.current.person
                        mediaref = self.current.mediaref
                        if person and mediaref:
                            mediaref.set_rectangle(self.real_to_proportional_rect(self.selection))
                            self.commit_person(person)
                        self.current.set_coords(*self.selection)
                else:
                    # nothing is currently selected
                    if (abs(self.start_point_screen[0] - event.x) >= MIN_SELECTION_SIZE and
                        abs(self.start_point_screen[1] - event.y) >= MIN_SELECTION_SIZE):
                        # region selection
                        region = Region(*self.selection)
                        self.regions.append(region)
                        self.current = region
                    else:
                        # nothing selected, just a click
                        click_point = self.screen_to_image(self.start_point_screen)
                        self.current = self.find_region(*click_point)
                        self.selection = self.current.coords() if self.current is not None else None

                self.start_point_screen = None
                self.refresh()
                self.enable_buttons()

    def motion_notify_event(self, widget, event):
        if not self.is_image_loaded():
            return
        end_point_orig = self.screen_to_image((event.x, event.y))
        end_point = self.truncate_to_image_size(end_point_orig)
        if self.start_point_screen:
            if self.grabber is not None and self.grabber != INSIDE:
                dx, dy = (event.x - self.start_point_screen[0], 
                          event.y - self.start_point_screen[1])
                self.modify_selection(dx, dy)
            else:
                start_point = self.screen_to_truncated(self.start_point_screen)
                self.selection = order_coordinates(start_point, end_point)
        else:
            self.in_region = self.find_region(*end_point_orig)
            if self.current is not None:
                self.grabber = can_grab(self.rect_image_to_screen(self.current.coords()),
                                        event.x, event.y)
                if self.grabber is not None:
                    self.event_box.window.set_cursor(CURSORS[self.grabber])
                else:
                    self.event_box.window.set_cursor(None)
            else:
                self.grabber = None
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
        (x1, y1, x2, y2) = self.rect_image_to_screen(self.current.coords())
        if self.grabber == GRABBER_UPPER_LEFT:
            x1 += dx
            y1 += dy
        elif self.grabber == GRABBER_UPPER:
            y1 += dy
        elif self.grabber == GRABBER_UPPER_RIGHT:
            x2 += dx
            y1 += dy
        elif self.grabber == GRABBER_RIGHT:
            x2 += dx
        elif self.grabber == GRABBER_LOWER_RIGHT:
            x2 += dx
            y2 += dy
        elif self.grabber == GRABBER_LOWER:
            y2 += dy
        elif self.grabber == GRABBER_LOWER_LEFT:
            x1 += dx
            y2 += dy
        elif self.grabber == GRABBER_LEFT:
            x1 += dx
        (x1, y1) = self.screen_to_truncated((x1, y1))
        (x2, y2) = self.screen_to_truncated((x2, y2))
        self.selection = (x1, y1, x2, y2)

    # ======================================================
    # list event handles
    # ======================================================

    def cursor_changed(self, treeview):
        self.current = self.get_selected_region()
        if self.current is not None:
            self.selection = self.current.coords()
        self.image.queue_draw()
        self.enable_buttons()

    def row_activated(self, treeview, path, view_column):
        self.edit_person_clicked(None)

    # ======================================================
    # helpers for list event handlers
    # ======================================================

    def get_selected_region(self):
        (model, pathlist) = self.treeview.get_selection().get_selected_rows()
        for path in pathlist:
            tree_iter = model.get_iter(path)
            i = model.get_value(tree_iter, 0)
            return self.regions[i - 1]   
        return None

    # ======================================================
    # refreshing the list
    # ======================================================

    def refresh_list(self):
        self.treestore.clear()
        for (i, region) in enumerate(self.regions, start=1):
            name = name_displayer.display(region.person) if region.person else ""
            self.treestore.append(None, (i, name))

    def refresh_selection(self):
        if self.current:
            self.treeview.get_selection().select_path((self.regions.index(self.current),))
        else:
            self.treeview.get_selection().unselect_all()
