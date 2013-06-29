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
import gen.mime
import ThumbNails
import Utils
from gen.db import DbTxn
from gen.display.name import displayer as name_displayer
from gen.plug import Gramplet
from glade import Glade
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
# PhotoTaggingGramplet
#
#-------------------------------------------------------------------------

RESIZE_RATIO = 1.5
SHADING_OPACITY = 0.7

path, filename = os.path.split(__file__)
HAARCASCADE_PATH = os.path.join(path, 'haarcascade_frontalface_alt.xml')

def resize_keep_aspect(orig_x, orig_y, target_x, target_y):
    orig_aspect = float(orig_x) / orig_y
    target_aspect = float(target_x) / target_y
    if orig_aspect > target_aspect:
        return (target_x, target_x * orig_y // orig_x)
    else:
        return (target_y * orig_x // orig_y, target_y)

def scale_to_fit(orig_x, orig_y, target_x, target_y):
    orig_aspect = float(orig_x) / orig_y
    target_aspect = float(target_x) / target_y
    if orig_aspect > target_aspect:
        return float(target_x) / orig_x
    else:
        return float(target_y) / orig_y

class PhotoTaggingGramplet(Gramplet):

    def init(self):
        self.pixbuf = None
        self.current = None
        self.scaled_pixbuf = None
        self.scale = 1.0

        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
        self.top.show_all()

    def build_gui(self):
        """
        Build the GUI interface.
        """
        vbox = gtk.VBox()
        self.top = vbox

        button_panel = gtk.Toolbar()

        self.button_index = button_panel.insert_stock(gtk.STOCK_INDEX, "Select Person", None, self.sel_person_clicked, None, -1)
        self.button_add = button_panel.insert_stock(gtk.STOCK_ADD, "Add Person", None, self.add_person_clicked, None, -1)
        self.button_del = button_panel.insert_stock(gtk.STOCK_REMOVE, "Remove Region", None, self.del_person_clicked, None, -1)
        self.button_clear = button_panel.insert_stock(gtk.STOCK_CLEAR, "Clear Reference", None, self.clear_ref_clicked, None, -1)
        self.button_edit = button_panel.insert_stock(gtk.STOCK_EDIT, "Edit Person", None, self.edit_person_clicked, None, -1)

        self.button_detect = button_panel.insert_stock(gtk.STOCK_EXECUTE, "Detect faces", None, self.detect_faces_clicked, None, -1)

        self.enable_buttons()

        vbox.pack_start(button_panel, expand=False, fill=True, padding=5)

        self.image = gtk.Image()
        self.image.set_has_tooltip(True)
        self.image.connect_after("expose-event", self.expose_handler)
        self.image.connect("query-tooltip", self.show_tooltip)

        self.ebox_ref = gtk.EventBox()
        self.ebox_ref.connect('button-press-event', self.button_press_event)
        self.ebox_ref.connect('button-release-event', self.button_release_event)
        self.ebox_ref.connect('motion-notify-event', self.motion_notify_event)
        self.ebox_ref.connect('scroll-event', self.motion_scroll_event)
        self.ebox_ref.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.ebox_ref.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.ebox_ref.add_events(gtk.gdk.POINTER_MOTION_MASK)

        self.ebox_ref.add(self.image)

        self.viewport = gtk.Viewport()
        self.viewport.add(self.ebox_ref)

        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.add(self.viewport)

        vbox.pack_start(self.scrolled_window, expand=True, fill=True)

        return vbox

    def db_changed(self):
        self.dbstate.db.connect('media-update', self.update)
        self.connect_signal('Media', self.update)

    def main(self):
        media = self.get_current_object()
        self.top.hide()
        if media:
            self.load_image(media)
        self.top.show()

    def load_image(self, media):
        self.start_point = None
        self.selection = None
        self.current = None
        self.in_fragment = None
        self.fragments = {}
        self.translation = {}

        image_path = Utils.media_path_full(self.dbstate.db, media.get_path())
        try:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(image_path)
            self.original_image_size = (self.pixbuf.get_width(), self.pixbuf.get_height())

            viewport_size = self.viewport.get_allocation()
            self.scale = scale_to_fit(self.pixbuf.get_width(), self.pixbuf.get_height(), 
                                  viewport_size.width, viewport_size.height)
            self.rescale()
            self.retrieve_backrefs()
            self.enable_buttons()
        except (gobject.GError, OSError):
            self.pixbuf = None
            self.image.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)

    def is_image_loaded(self):
        return self.pixbuf is not None

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

    def proportional_to_real(self, rect):
        """
        Translate proportional (ranging from 0 to 100) coordinates to image coordinates (in pixels).
        """
        w, h = self.original_image_size
        return (rect[0] * w / 100, rect[1] * h / 100, rect[2] * w / 100, rect[3] * h / 100)

    def real_to_proportional(self, rect):
        """
        Translate image coordinates (in pixels) to proportional (ranging from 0 to 100).
        """
        w, h = self.original_image_size
        return (rect[0] * 100 / w, rect[1] * 100 / h, rect[2] * 100 / w, rect[3] * 100 / h)

    def check_and_translate_to_proportional(self, rect):
        mediaref = self.translation.get(rect)
        if mediaref:
            return mediaref.get_rectangle()
        else:
            return self.real_to_proportional(rect)

    def image_to_screen(self, coords):
        """
        Translate image coordinates to viewport coordinates using the current scale and viewport size.
        """
        viewport_rect = self.viewport.get_allocation()
        image_rect = self.scaled_size
        if image_rect[0] < viewport_rect.width:
            offset_x = (image_rect[0] - viewport_rect.width) / 2
        else:
            offset_x = 0
        if image_rect[1] < viewport_rect.height:
            offset_y = (image_rect[1] - viewport_rect.height) / 2
        else:
            offset_y = 0
        return (int(coords[0] * self.scale) - offset_x, int(coords[1] * self.scale) - offset_y)

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
            offset_x = 0
        if image_rect[1] < viewport_rect.height:
            offset_y = (image_rect[1] - viewport_rect.height) / 2
        else:
            offset_y = 0
        return (int((coords[0] + offset_x) / self.scale), int((coords[1] + offset_y) / self.scale))

    def truncate_to_image_size(self, coords):
        x, y = coords
        image_size = self.get_original_image_size()
        x = max(x, 0)
        x = min(x, image_size[0])
        y = max(y, 0)
        y = min(y, image_size[1])
        return (x, y) 

    def retrieve_backrefs(self):
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
                            fragment = self.proportional_to_real(rect)
                            self.fragments[fragment] = person
                            self.translation[fragment] = mediaref

    def rescale(self):
        self.scaled_size = (int(self.original_image_size[0] * self.scale), int(self.original_image_size[1] * self.scale))
        self.scaled_image = self.pixbuf.scale_simple(self.scaled_size[0], self.scaled_size[1], gtk.gdk.INTERP_BILINEAR)
        self.image.set_from_pixbuf(self.scaled_image)
        self.image.set_size_request(*self.scaled_size)
        self.ebox_ref.set_size_request(*self.scaled_size)

    def expose_handler(self, widget, event):
        if self.pixbuf:
            self.draw_selection()

    def show_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        if self.in_fragment:
            tooltip.set_text(name_displayer.display(self.in_fragment[1]))
            return True
        else:
            return False

    def draw_selection(self):
        if not self.scaled_size:
            return

        w, h = self.scaled_size
        offset_x, offset_y = self.image_to_screen((0, 0))

        cr = self.image.window.cairo_create()

        if self.selection:
            x1, y1, x2, y2 = self.selection
            x1, y1 = self.image_to_screen((x1, y1))
            x2, y2 = self.image_to_screen((x2, y2))

            # transparent shading
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

            # selection frame
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.rectangle(x1, y1, x2 - x1, y2 - y1)
            cr.stroke()
            cr.set_source_rgb(0.0, 0.0, 1.0)
            cr.rectangle(x1 - 2, y1 - 2, x2 - x1 + 4, y2 - y1 + 4)
            cr.stroke()
        elif self.fragments:
            # selection frame
            cr.set_font_size(14)
            for (rect, person) in self.fragments.items():
                x1, y1, x2, y2 = rect
                x1, y1 = self.image_to_screen((x1, y1))
                x2, y2 = self.image_to_screen((x2, y2))
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.rectangle(x1, y1, x2 - x1, y2 - y1)
                cr.stroke()
                cr.set_source_rgb(0.0, 0.0, 1.0)
                cr.rectangle(x1 - 2, y1 - 2, x2 - x1 + 4, y2 - y1 + 4)
                cr.stroke()

    def find_fragment(self, x, y):
        for (rect, person) in self.fragments.items():
            x1, y1, x2, y2 = rect
            if x1 <= x <= x2 and y1 <= y <= y2:
                return rect
        return None

    def button_press_event(self, obj, event):
        if not self.is_image_loaded():
            return
        RADIUS = 5
        if event.button==1:
            if self.selection:
                x1, y1, x2, y2 = self.selection
                sx1, sy1 = self.image_to_screen((x1, y1))
                sx2, sy2 = self.image_to_screen((x2, y2))
                if abs(event.x - sx1) <= RADIUS and abs(event.y - sy1) <= RADIUS:
                    self.start_point = (x2, y2)
                elif abs(event.x - sx1) <= RADIUS and abs(event.y - sy2) <= RADIUS:
                    self.start_point = (x2, y1)
                elif abs(event.x - sx2) <= RADIUS and abs(event.y - sy1) <= RADIUS:
                    self.start_point = (x1, y2)
                elif abs(event.x - sx2) <= RADIUS and abs(event.y - sy2) <= RADIUS:
                    self.start_point = (x1, y1)
                else:
                    self.start_point = self.screen_to_image((event.x, event.y))
                    self.start_point = self.truncate_to_image_size(self.start_point)
            else:
                self.start_point = self.screen_to_image((event.x, event.y))
                self.start_point = self.truncate_to_image_size(self.start_point)
            # prepare drawing of a feedback rectangle
            self.rect_pixbuf = self.image.get_pixbuf()
            w,h = self.rect_pixbuf.get_width(), self.rect_pixbuf.get_height()
            self.rect_pixbuf_render = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
            self.cm = gtk.gdk.colormap_get_system()
            color = self.cm.alloc_color(gtk.gdk.Color("blue"))
            self.rect_pixmap = gtk.gdk.Pixmap(None, w, h, self.cm.get_visual().depth)
            self.rect_pixmap.set_colormap(self.cm)
            self.rect_gc = self.rect_pixmap.new_gc()
            self.rect_gc.set_foreground(color)

    def enable_buttons(self):
        self.button_index.set_sensitive(self.current is not None)
        self.button_add.set_sensitive(self.current is not None)
        self.button_del.set_sensitive(self.current is not None)
        self.button_clear.set_sensitive(self.current is not None and self.fragments.get(self.current) is not None)
        self.button_edit.set_sensitive(self.current is not None and self.fragments.get(self.current) is not None)

        self.button_detect.set_sensitive(self.pixbuf is not None and computer_vision_available)

    def button_release_event(self, obj, event):
        if not self.is_image_loaded():
            return
        # context menu is disabled
        #if event.button == 3:
        #    for (rect, person) in self.fragments.items():
        #        x1, y1, x2, y2 = self.proportional_to_real(rect)
        #        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
        #            if person:
        #                name = person.get_primary_name().get_name()
        #                self.removemenu.set_sensitive(True)
        #            else:
        #                name = "[not selected]"
        #                self.removemenu.set_sensitive(False)
        #            self.nameitem.set_label(name)
        #            self.current = rect
        #            self.menu.popup(None, None, None, event.button, event.time, None)
        #            self.menu.show_all()
        if event.button == 1:
            if self.start_point:
                end_point = self.screen_to_image((event.x, event.y))
                end_point = self.truncate_to_image_size(end_point)
                x1 = min(self.start_point[0], end_point[0])
                x2 = max(self.start_point[0], end_point[0])
                y1 = min(self.start_point[1], end_point[1])
                y2 = max(self.start_point[1], end_point[1])

                self.selection = (x1, y1, x2, y2)

                if self.rect_pixbuf is None:
                    return
                self.image.set_from_pixbuf(self.rect_pixbuf)

                if x2 - x1 >= 5 and y2 - y1 >= 5:
                    if self.current:
                        person = self.fragments.get(self.current)
                        if person:
                            mediaref = self.translation.get(self.current)
                            self.translation[self.selection] = mediaref
                            mediaref.set_rectangle(self.real_to_proportional(self.selection))
                            self.commit_person(person)
                        del self.fragments[self.current]
                        self.fragments[self.selection] = person
                    self.current = self.selection
                    self.rect_pixbuf = None
                else:
                    rect = self.find_fragment(end_point[0], end_point[1])
                    if rect:
                        self.selection = rect
                        self.current = rect
                    else:
                        self.selection = None
                        self.current = None

            self.start_point = None
            self.enable_buttons()

    def commit_person(self, person):
        """
        Save the modifications made to a Person object to the database.
        """
        with DbTxn('', self.dbstate.db) as trans:
            self.dbstate.db.commit_person(person, trans)
            msg = _("Edit Person (%s)") % \
                    name_displayer.display(person)
            trans.set_description(msg)

    def add_reference(self, person, rect):
        """
        Add a reference to the current media object to the specified person.
        """
        media_ref = gen.lib.MediaRef()
        media_ref.ref = self.get_current_handle()
        media_ref.set_rectangle(rect)
        person.add_media_reference(media_ref)
        self.commit_person(person)

    def remove_reference(self, person, rect):
        """
        Add a reference to the current media object from the specified person.
        """
        # because MediaBase does not have a method to remove a single reference
        # (remove_media_references removes all references to a particular object,
        # i.e. if a person references several fragments of the same photo, all
        # references to this photo will be removed), we have to manually search
        # the media list for the reference in question and remove it
        new_list = []
        media_list = person.get_media_list()
        for mediaref in media_list:
            referenced_handles = mediaref.get_referenced_handles()
            if len(referenced_handles) == 1:
                handle_type, handle = referenced_handles[0]
                if handle_type == "MediaObject" and handle == self.get_current_handle():
                    if mediaref.get_rectangle() == rect:
                        continue
            new_list.append(mediaref)
        person.set_media_list(new_list)
        self.commit_person(person)

    def sel_person_clicked(self, event):
        if self.current:
            SelectPerson = SelectorFactory('Person')
            sel = SelectPerson(self.dbstate, self.uistate, self.track, _("Select Person"))
            person = sel.run()
            if person:
                rect = self.check_and_translate_to_proportional(self.current)
                old_person = self.fragments.get(self.current)
                self.fragments[self.current] = person
                if old_person:
                    self.remove_reference(old_person, rect)
                self.add_reference(person, rect)

    def del_person_clicked(self, event):
        if self.current:
            person = self.fragments.get(self.current)
            if person:
                rect = self.check_and_translate_to_proportional(self.current)
                self.remove_reference(person, rect)
            del self.fragments[self.current]
            self.current = None
            self.selection = None
            self.image.queue_draw()

    def clear_ref_clicked(self, event):
        if self.current:
            person = self.fragments.get(self.current)
            if person:
                self.fragments[self.current] = None
                rect = self.check_and_translate_to_proportional(self.current)
                self.remove_reference(person, rect)

    def add_person_clicked(self, event):
        if self.current:
            person = gen.lib.Person()
            EditPerson(self.dbstate, self.uistate, self.track, person, self.new_person_added)

    def new_person_added(self, person):
        if self.current and person:
            self.fragments[self.current] = person
            rect = self.check_and_translate_to_proportional(self.current)
            self.add_reference(person, rect)

    def edit_person_clicked(self, event):
        person = self.fragments[self.current]
        if person:
            EditPerson(self.dbstate, self.uistate, self.track, person)

    def detect_faces_clicked(self, event):
        min_face_size = (50,50) # FIXME: get from setting
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
            self.fragments[(x, y, x + width, y + height)] = None

        self.image.queue_draw()

    def motion_notify_event(self, widget, event):
        if not self.is_image_loaded():
            return
        end_point = self.screen_to_image((event.x, event.y))
        end_point = self.truncate_to_image_size(end_point)
        if self.start_point:
            x1 = min(self.start_point[0], end_point[0])
            x2 = max(self.start_point[0], end_point[0])
            y1 = min(self.start_point[1], end_point[1])
            y2 = max(self.start_point[1], end_point[1])

            self.selection = (x1, y1, x2, y2)

            w, h = (self.rect_pixbuf.get_width(), self.rect_pixbuf.get_height())
            image_rect = self.original_image_size

            self.rect_pixmap.draw_pixbuf(self.rect_gc, self.rect_pixbuf, 0, 0, 0, 0)        

            self.rect_pixbuf_render.get_from_drawable(self.rect_pixmap,
                                gtk.gdk.colormap_get_system(),
                                0,0,0,0, w, h)
            self.image.set_from_pixbuf(self.rect_pixbuf_render)

        fragment = self.find_fragment(end_point[0], end_point[1])
        if fragment:
            self.in_fragment = (fragment, self.fragments[fragment])
        else:
            self.in_fragment = None
        self.image.queue_draw()

    def motion_scroll_event(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.scale *= RESIZE_RATIO
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.scale /= RESIZE_RATIO
        self.rescale()
