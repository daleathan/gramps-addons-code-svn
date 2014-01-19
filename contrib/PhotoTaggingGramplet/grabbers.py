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

class UpperLeftGrabber(Grabber):

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

class UpperGrabber(Grabber):

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

class UpperRightGrabber(Grabber):

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

class RightGrabber(Grabber):

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

class LowerRightGrabber(Grabber):

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

class LowerGrabber(Grabber):

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

class LowerLeftGrabber(Grabber):

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

class LeftGrabber(Grabber):

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

class GrabberWrapper(Grabber):

    def __init__(self, grabber, inner):
        self._grabber = grabber
        self._inner = inner
        if inner:
            self._boundaries = self._grabber.inner
        else:
            self._boundaries = self._grabber.outer

    def moved(self, x1, y1, x2, y2, dx, dy):
        return self._grabber.moved(x1, y1, x2, y2, dx, dy)

    def cursor(self):
        return self._grabber.cursor()

    def boundaries(self, x1, y1, x2, y2):
        return self._boundaries(x1, y1, x2, y2)

    def switch(self, x1, y1, x2, y2):
        return GrabberWrapper(self._grabber.switch(x1, y1, x2, y2), 
                              self._inner)

#-------------------------------------------------------------------------
#
# grabbers constants and routines
#
#-------------------------------------------------------------------------

MIN_CORNER_GRABBER = 20
MIN_SIDE_GRABBER = 20
MIN_GRABBER_PADDING = 10
MIN_SIDE_FOR_INSIDE_GRABBERS = (2 * (MIN_CORNER_GRABBER + MIN_GRABBER_PADDING) + 
                                MIN_SIDE_GRABBER)

# switching

upper_left_grabber = UpperLeftGrabber()
upper_grabber = UpperGrabber()
upper_right_grabber = UpperRightGrabber()
right_grabber = RightGrabber()
lower_right_grabber = LowerRightGrabber()
lower_grabber = LowerGrabber()
lower_left_grabber = LowerLeftGrabber()
left_grabber = LeftGrabber()

GRABBERS = [upper_left_grabber,
            upper_grabber,
            upper_right_grabber,
            right_grabber,
            lower_right_grabber,
            lower_grabber,
            lower_left_grabber,
            left_grabber]

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
        for grabber in GRABBERS:
            grabber_area = grabber.inner(x1, y1, x2, y2)
            if inside_rect(grabber_area, x, y):
                return GrabberWrapper(grabber, True)
        return None
    else:
        # grabbers are outside
        if x1 <= x <= x2 and y1 <= y <= y2:
            return None
        for  grabber in GRABBERS:
            grabber_area = grabber.outer(x1, y1, x2, y2)
            if inside_rect(grabber_area, x, y):
                return GrabberWrapper(grabber, False)
        return None
