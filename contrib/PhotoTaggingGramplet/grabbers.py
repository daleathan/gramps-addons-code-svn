#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013, 2014 Artem Glebov <artem.glebov@gmail.com>
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
import math

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# grabbers classes
#
#-------------------------------------------------------------------------

class Grabber(object):

    def switch(self, x1, y1, x2, y2):
        if x1 > x2:
            if y1 > y2:
                return self._switches[1]()
            else:
                return self._switches[0]()
        else:
            if y1 > y2:
                return self._switches[2]()
            else:
                return self

    def grabbers_inside(self, rect):
        x1, y1, x2, y2 = rect
        return (x2 - x1 >= MIN_SIDE_FOR_INSIDE_GRABBERS and 
                y2 - y1 >= MIN_SIDE_FOR_INSIDE_GRABBERS)

class RectangularGrabber(Grabber):

    def draw(self, cr, rect):
        if self.grabbers_inside(rect):
            x1, y1, x2, y2 = self.inner(*rect)
        else:
            x1, y1, x2, y2 = self.outer(*rect)
        cr.set_source_rgb(1.0, 0, 0)
        cr.rectangle(x1, y1, x2 - x1, y2 - y1)
        cr.stroke()

    def can_grab(self, rect, x, y):
        if self.grabbers_inside(rect):
            grabber_area = self.inner(*rect)
        else:
            grabber_area = self.outer(*rect)
        return inside_rect(grabber_area, x, y)

class UpperLeftGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [UpperRightGrabber, LowerRightGrabber, LowerLeftGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x1, y1, x1 + MIN_CORNER_GRABBER, y1 + MIN_CORNER_GRABBER)

    def outer(self, x1, y1, x2, y2):
        return (x1 - MIN_CORNER_GRABBER, y1 - MIN_CORNER_GRABBER, x1, y1)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1 + dx, y1 + dy, x2, y2)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.TOP_LEFT_CORNER)

class UpperGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [UpperGrabber, LowerGrabber, LowerGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING, 
                y1, 
                x2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING,
                y1 + MIN_CORNER_GRABBER)

    def outer(self, x1, y1, x2, y2):
        return (x1, y1 - MIN_CORNER_GRABBER, x2, y1)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1, y1 + dy, x2, y2)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.TOP_SIDE)

class UpperRightGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [UpperLeftGrabber, LowerLeftGrabber, LowerRightGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x2 - MIN_CORNER_GRABBER, y1, x2, y1 + MIN_CORNER_GRABBER)

    def outer(self, x1, y1, x2, y2):
        return (x2, y1 - MIN_CORNER_GRABBER, x2 + MIN_CORNER_GRABBER, y1)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1, y1 + dy, x2 + dx, y2)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.TOP_RIGHT_CORNER)

class RightGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [LeftGrabber, LeftGrabber, RightGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x2 - MIN_CORNER_GRABBER,
                y1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING,
                x2,
                y2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING)

    def outer(self, x1, y1, x2, y2):
        return (x2, y1, x2 + MIN_CORNER_GRABBER, y2)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1, y1, x2 + dx, y2)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)

class LowerRightGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [LowerLeftGrabber, UpperLeftGrabber, UpperRightGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x2 - MIN_CORNER_GRABBER, y2 - MIN_CORNER_GRABBER, x2, y2)

    def outer(self, x1, y1, x2, y2):
        return (x2, y2, x2 + MIN_CORNER_GRABBER, y2 + MIN_CORNER_GRABBER)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1, y1, x2 + dx, y2 + dy)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.BOTTOM_RIGHT_CORNER)

class LowerGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [LowerGrabber, UpperGrabber, UpperGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING, 
                y2 - MIN_CORNER_GRABBER, 
                x2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING,
                y2)

    def outer(self, x1, y1, x2, y2):
        return (x1, y2, x2, y2 + MIN_CORNER_GRABBER)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1, y1, x2, y2 + dy)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.BOTTOM_SIDE)

class LowerLeftGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [LowerRightGrabber, UpperRightGrabber, UpperLeftGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x1, y2 - MIN_CORNER_GRABBER, x1 + MIN_CORNER_GRABBER, y2)

    def outer(self, x1, y1, x2, y2):
        return (x1 - MIN_CORNER_GRABBER, y2, x1, y2 + MIN_CORNER_GRABBER)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1 + dx, y1, x2, y2 + dy)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.BOTTOM_LEFT_CORNER)

class LeftGrabber(RectangularGrabber):

    def __init__(self):
        self._switches = [RightGrabber, RightGrabber, LeftGrabber]

    def inner(self, x1, y1, x2, y2):
        return (x1,
                y1 + MIN_CORNER_GRABBER + MIN_GRABBER_PADDING,
                x1 + MIN_CORNER_GRABBER,
                y2 - MIN_CORNER_GRABBER - MIN_GRABBER_PADDING)

    def outer(self, x1, y1, x2, y2):
        return (x1 - MIN_CORNER_GRABBER, y1, x1, y2)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1 + dx, y1, x2, y2)

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE)

class CentralGrabber(Grabber):

    def draw(self, cr, rect):
        if not self.grabbers_inside(rect):
            return
        x1, y1, x2, y2 = rect
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        cr.set_source_rgb(1.0, 0, 0)
        cr.move_to(cx, cy - CENTRAL_GRABBER_CROSS_HALF_SIZE)
        cr.line_to(cx, cy + CENTRAL_GRABBER_CROSS_HALF_SIZE)
        cr.move_to(cx - CENTRAL_GRABBER_CROSS_HALF_SIZE, cy)
        cr.line_to(cx + CENTRAL_GRABBER_CROSS_HALF_SIZE, cy)
        cr.stroke()

    def can_grab(self, rect, x, y):
        if not self.grabbers_inside(rect):
            return False
        x1, y1, x2, y2 = rect
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        return distance(cx, cy, x, y) <= CENTRAL_GRABBER_RADIUS

    def cursor(self):
        return gtk.gdk.Cursor(gtk.gdk.FLEUR)

    def moved(self, x1, y1, x2, y2, dx, dy):
        return (x1 + dx, y1 + dy, x2 + dx, y2 + dy)

    def switch(self, x1, y1, x2, y2):
        return self

#-------------------------------------------------------------------------
#
# grabbers constants and routines
#
#-------------------------------------------------------------------------

MIN_CORNER_GRABBER = 20
MIN_SIDE_GRABBER = 20
MIN_GRABBER_PADDING = 10
CENTRAL_GRABBER_RADIUS = 20
CENTRAL_GRABBER_CROSS_HALF_SIZE = 10
MIN_SIDE_FOR_INSIDE_GRABBERS = (2 * (MIN_CORNER_GRABBER + MIN_GRABBER_PADDING) + 
                                MIN_SIDE_GRABBER)

GRABBERS = [UpperLeftGrabber(),
            UpperGrabber(),
            UpperRightGrabber(),
            RightGrabber(),
            LowerRightGrabber(),
            LowerGrabber(),
            LowerLeftGrabber(),
            LeftGrabber(),
            CentralGrabber()]

# helper functions

def grabber_position(rect):
    x1, y1, x2, y2 = rect
    if (x2 - x1 >= MIN_SIDE_FOR_INSIDE_GRABBERS and 
        y2 - y1 >= MIN_SIDE_FOR_INSIDE_GRABBERS):
        return GRABBER_INSIDE
    else:
        return GRABBER_OUTSIDE

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

def inside_rect(rect, x, y):
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2

def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def can_grab(rect, x, y):
    """
    Checks if (x,y) lies within one of the grabbers of rect.
    """
    for grabber in GRABBERS:
        if grabber.can_grab(rect, x, y):
            return grabber
    return None
