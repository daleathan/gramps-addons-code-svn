#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009-2011 Rob G. Healey <robhealey1@gmail.com>
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

# $Id$

# *****************************************************************************
# Python Modules
# *****************************************************************************
import os, sys
from datetime import datetime, date
import time, calendar

import subprocess

# abilty to escape certain characters from html output...
from xml.sax.saxutils import escape as _html_escape

from itertools import chain

from decimal import *
getcontext().prec = 4
from fractions import Fraction

#------------------------------------------------
# Internaturilation
#------------------------------------------------
from TransUtils import get_addon_translator
_ = get_addon_translator().ugettext

# -----------------------------------------------------------------------------
# GTK modules
# -----------------------------------------------------------------------------
import gtk

# -----------------------------------------------------------------------------
# GRAMPS modules
# -----------------------------------------------------------------------------
from QuestionDialog import OkDialog, WarningDialog
from ListModel import ListModel, NOSORT

from gen.plug import Gramplet
from DateHandler import displayer as _dd

import gen.lib
import Utils
from PlaceUtils import conv_lat_lon

# pyexiv2 download page (C) Olivier Tilloy
_DOWNLOAD_LINK = "http://tilloy.net/dev/pyexiv2/download.html"

# make sure the pyexiv2 library is installed and at least a minimum version
software_version = False
Min_VERSION = (0, 1, 3)
Min_VERSION_str = "pyexiv2-%d.%d.%d" % Min_VERSION
Pref_VERSION_str = "pyexiv2-%d.%d.%d" % (0, 3, 0)

# to be able for people that have pyexiv2-0.1.3 to be able to use this addon also...
LesserVersion = False

try:
    import pyexiv2
    software_version = pyexiv2.version_info

except ImportError, msg:
    WarningDialog(_("You need to install, %s or greater, for this addon to work...\n"
                    "I would recommend installing, %s, and it may be downloaded from here: \n%s") % (
                        Min_VERSION_str, Pref_VERSION_str, _DOWNLOAD_LINK), str(msg))
    raise Exception(_("Failed to load 'Image Metadata Gramplet/ Addon'..."))
               
# This only happends if the user only has pyexiv2-0.1.3 installed on their computer...
# it requires the use of a few different things, which you will see when this variable is in aa conditional,
# to still use this addon...
except AttributeError:
    LesserVersion = True

# the library is either not installed or does not meet 
# minimum required version for this addon....
if (software_version and (software_version < Min_VERSION)):
    msg = _("The minimum required version for pyexiv2 must be %s \n"
        "or greater.  Or you do not have the python library installed yet.  "
        "You may download it from here: %s\n\n  I recommend getting, %s") % (
         Min_VERSION_str, _DOWNLOAD_LINK, Pref_VERSION_str)
    WarningDialog(msg)
    raise Exception(msg)

if os.sys.platform == "win32":
    _MAGICK_FOUND = Utils.search_for("ImageMagick.exe")
else:
    _MAGICK_FOUND = Utils.search_for("ImageMagick")

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
# available image types for exiv2
_valid_types = ["jpeg", "jpg", "exv", "tiff", "dng", "nef", "pef", "pgf", "png", "psd", "jp2"]

# set up Exif keys for Image.exif_keys
_DATAMAP  = {
    "Exif.Image.ImageDescription"  : "Description",
    "Exif.Image.DateTime"          : "ModDateTime",
    "Exif.Photo.DateTimeOriginal"  : "OrigDateTime",
    "Exif.Image.Artist"            : "Artist",
    "Exif.Image.Copyright"         : "Copyright",
    "Exif.GPSInfo.GPSLatitudeRef"  : "LatitudeRef",
    "Exif.GPSInfo.GPSLatitude"     : "Latitude",
    "Exif.GPSInfo.GPSLongitudeRef" : "LongitudeRef",
    "Exif.GPSInfo.GPSLongitude"    : "Longitude",
    "Exif.GPSInfo.GPSAltitudeRef"  : "AltitudeRef",
    "Exif.GPSInfo.GPSAltitude"     : "Altitude",
    "Exif.Image.XResolution"       : "ImageWidth",
    "Exif.Image.YResolution"       : "ImageHeight",
    "Exif.Image.ResolutionUnit"    : "ResolutionUnit"}
_DATAMAP = dict( (key, val) for key, val in _DATAMAP.items() )
_DATAMAP.update( (val, key) for key, val in _DATAMAP.items() )

# define tooltips for all entries and buttons...
_TOOLTIPS = {

    # CopyTo button...
    "CopyTo"            : _("Copies information from the Display area to the Edit area."),

    # Clear Edit Area button... 
    "Clear"             : _("Clears the Exif metadata from the Edit area."),

    # Artist 
    "Artist"            : _("Enter the Artist/ Author of this image.  The person's name or "
        "the company who is responsible for the creation of this image."),

    # Copyright
    "Copyright"         : _("Enter the copyright information for this image. \n"
        "Example: (C) 2010 Smith and Wesson"),

    # Calendar date select...
    "Date:Select"       : _("Allows you to select a date from a pop-up window calendar. \n"
        "Warning:  You will still need to edit the time..."),

    # Manual Date/ Time... 
    "ModDateTime"       : _("Manual Date/ Time Entry, \n"
        "Example: 1826-Apr-12 14:30:00, 1826-April-12, 1998-01-31 13:30:00"),

    # Convert to decimal button...
    "GPSFormat:Decimal" : _("Converts Degree, Minutes, Seconds GPS Coordinates to a "
        "Decimal representation."),

    # convert to degrees, minutes, seconds button...
    "GPSFormat:DMS"     : _("Converts Decimal GPS Coordinates "
        "to a Degrees, Minutes, Seconds representation."),

    # GPS Latitude...
    "Latitude"          : _("Enter the GPS Latitude Coordinates for your image,\n"
        "Example: 43.722965, 43 43 22 N, 38° 38′ 03″ N, 38 38 3"),

    # GPS Longitude...
    "Longitude"         : _("Enter the GPS Longitude Coordinates for your image,\n"
        "Example: 10.396378, 10 23 46 E, 105° 6′ 6″ W, -105 6 6"),

    # Wiki Help button...
    "Help"              : _("Displays the Gramps Wiki Help page for 'Image Metadata Gramplet' "
        "in your web browser."),

    # Save Exif Metadata button...
    "Save"              : _("Saves/ writes the Exif metadata to this image.\n"
        "WARNING: Exif metadata will be erased if you save a blank entry field...") }.items()

def _help_page(obj):
    """
    will bring up a Wiki help page.
    """

    import GrampsDisplay

    GrampsDisplay.help(webpage = 'Image Metadata Gramplet')

_allmonths = list([_dd.short_months[i], _dd.long_months[i], i] for i in range(1, 13))

def _return_month(month):
    """
    returns either an integer of the month number or the abbreviated month name

    @param: rmonth -- can be one of:
        10, "10", "Oct", or "October"
    """

    try:
        month = int(month)

    except ValueError:
        for sm, lm, index in _allmonths:
            if month == sm or month == lm:
                month = int(index)
                break
            elif str(month) == index:
                    month = lm
                    break
    return month

def _split_values(text):
    """
    splits a variable into its pieces
    """

    # a hypen
    if "-" in text:
        separator = "-"

    # a period
    elif "." in text:
        separator = "."

    # a colon
    elif ":" in text:
        separator = ":"

    # a space
    else:
        separator = " "
    return [value for value in text.split(separator)]

# ------------------------------------------------------------------------
# Gramplet class
# ------------------------------------------------------------------------
class imageMetadataGramplet(Gramplet):

    def init(self):

        self.exif_column_width = 15
        self.exif_widgets = {}

        # set all dirty variables to False to begin this addon...
        self._dirty = False

        self.orig_image   = False
        self.image_path   = False
        self.plugin_image = False

        rows = gtk.VBox()

        medialabel = gtk.HBox(False)
        self.exif_widgets["Media:Label"] = gtk.Label(_("Click a media object to begin...") )
        self.exif_widgets["Media:Label"].set_alignment(0.0, 0.0)
        medialabel.pack_start(self.exif_widgets["Media:Label"], expand =False)

        messagearea = gtk.HBox(False)
        self.exif_widgets["Message:Area"] = gtk.Label()
        self.exif_widgets["Message:Area"].set_alignment(0.0, 0.0)
        messagearea.pack_start(self.exif_widgets["Message:Area"], expand =False)

        self.model = gtk.ListStore(object, str, str)
        view = gtk.TreeView(self.model)

        # Key Column
        view.append_column( self.__create_column(_("Key"), 1) )

        # Value Column
        view.append_column( self.__create_column(_("Value"), 2) )

        copyclear = gtk.HButtonBox()
        copyclear.set_layout(gtk.BUTTONBOX_START)

        # Copy To button...
        copyclear.add( self.__create_button(
            "CopyTo", _("Copy to Edit Area"), self.copy_to, False, False) )

        # Clear button...
        copyclear.add( self.__create_button(
            "Clear", False, self.clear_metadata, gtk.STOCK_CLEAR) )

        rows.pack_start(medialabel, expand =False)
        rows.pack_start(messagearea, expand =False)
        rows.pack_start(view, padding =10)
        rows.pack_start(copyclear, expand =False, fill =False)

        for items in [

            # Image Description
            ("Description",     _("Description"),    None, False, [],  True,  0),

            # calendar date clickable entry
            ("Date",            "",                  None, True,
            [("Select",         _("Select Date"),  "button", self.select_date)],
                                                                     True,  0),

            # Manual Date/ Time Entry, 1826-April-12 14:06:00
            ("ModDateTime",         _("Date | Time"),    None, False,  [], True,  0),

            # Author field
            ("Artist",          _("Artist/ Author"), None, False, [],  True,  0),

            # copyright field
            ("Copyright",       _("Copyright"),      None, False, [],  True,  0),

            # Convert GPS Coordinates
            ("GPSFormat",       _("Convert GPS"),    None, True,
            [("Decimal",        _("Decimal"),        "button", self.convert2decimal),
             ("DMS",            _("Deg. Min. Sec."), "button", self.convert2dms)], 
                                                                       False, 0),    
  
            # Latitude and Longitude for this image 
            ("Latitude",        _("Latitude"),       None, False, [],  True,  0),
            ("Longitude",       _("Longitude"),      None, False, [],  True,  0),

            # GPS Altitude
            ("Altitude",        _("Altitude"),       None, False, [],  True,  0) ]:

            pos, text, choices, readonly, callback, dirty, default = items
            row = self.make_row(pos, text, choices, readonly, callback, dirty, default)
            rows.pack_start(row, False)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)

        # Help button...
        button_box.add( self.__create_button(
            "Help", False, _help_page, gtk.STOCK_HELP) )

        # Save button...
        button_box.add( self.__create_button(
            "Save", False, self.save_metadata, gtk.STOCK_SAVE, False) )

        # Is ImageMagick installed on this computer?
        if _MAGICK_FOUND:

            # Erase Exif Metadata button...
            button_box.add( self.__create_button(
                "Exifmetadata", _("Erase Exif metadata"), self._wipe_metadata, False) )

            # Erase Exif metadata button...
            self.exif_widgets["Exifmetadata"].set_tooltip_text(_("WARNING!  You are about "
                "to permanently erase/ wipe all Exif metadata for this image...\n"
                "Are you sure that you want to remove all Exif metadata? [Yes/ No]"))
        rows.pack_start(button_box, expand =False, fill =False)

        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(rows)
        rows.show_all()

        # provide tooltips for all fields and buttons...
        self.setup_tooltips(self.orig_image)

    def __create_column(self, name, colnum, fixed =True):
        """
        will create the column for the column row...
        """

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(name, renderer, text =colnum)

        if fixed:
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_expand(True)

        else:
            column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            column.set_expand(False)

        column.set_alignment(0.0)
        column.set_sort_column_id(colnum)

        return column

    def __create_button(self, pos, text, callback, icon =False, sensitive = True):
        """
        creates and returns a button for display
        """

        if (icon and not text):
            button = gtk.Button(stock=icon)
        else:
            button = gtk.Button(text)

        button.connect("clicked", callback)

        if not sensitive:
            button.set_sensitive(False)
        self.exif_widgets[pos] = button

        return button

    def main(self): # return false finishes
        """
        get the active media, mime type, and reads the image metadata
        """
        db = self.dbstate.db

        # clear Edit Area
        self.clear_metadata(self.orig_image)
        self.model.clear()

        active_handle = self.get_active("Media")
        if not active_handle:
            return

        self.orig_image = db.get_object_from_handle(active_handle)
        if not self.orig_image:
            self.exif_widgets["Message:Area"].set_text(_("Image is missing or deleted.  "
                "Choose another media object..."))
            return

        # get media full path
        self.image_path = Utils.media_path_full(db, self.orig_image.get_path() )

        # check media read/ write privileges...
        _readable = os.access(self.image_path, os.R_OK)
        _writable = os.access(self.image_path, os.W_OK)
        if not _readable:
            self.exif_widgets["Message:Area"].set_text(_("This image is not readable.  "
                "Choose another media object..."))
            return

        # if media object is not writable, disable Save Button?
        if not _writable:
            self.exif_widgets["Message:Area"].set_text(_("This image is not writable..."))
            self.exif_widgets["Save"].set_sensitive(False)

        # display file description/ title...
        self.exif_widgets["Media:Label"].set_text(
            _html_escape(self.orig_image.get_description() ) )

        # get mime type information...
        mime_type = self.orig_image.get_mime_type()
        self.__mtype = gen.mime.get_description(mime_type)

        # determine if it is a mime image object?
        if mime_type:
            self.exif_widgets["Message:Area"].set_text(self.__mtype)

            if mime_type.startswith("image"):

                # read the media metadata and display it
                self.display_exif_tags(self.image_path)
            else:
                return   

        # disable all buttons of "CopyTo", "Clear", and "Save"...
        else:
            self.exif_widgets["Message:Area"].set_text("%s, %s" % (self.__mtype,
                _("Please choose another media object...") ) )
            return

    def make_row(self, pos, text, choices=None, readonly=False, callback_list=[],
                 mark_dirty=False, default=0):

        # Image Metadata Gramplet
        row = gtk.HBox()
        label = gtk.Label()
        if readonly:
            label.set_text("<b>%s</b>" % text)
            label.set_width_chars(self.exif_column_width)
            label.set_use_markup(True)
            self.exif_widgets[pos] = gtk.Label()
            self.exif_widgets[pos].set_alignment(0.0, 0.5)
            self.exif_widgets[pos].set_use_markup(True)
            label.set_alignment(0.0, 0.5)
            row.pack_start(label, False)
            row.pack_start(self.exif_widgets[pos], False)
        else:
            label.set_text("%s: " % text)
            label.set_width_chars(self.exif_column_width)
            label.set_alignment(1.0, 0.5) 
            if choices == None:
                self.exif_widgets[pos] = gtk.Entry()
                if mark_dirty:
                    self.exif_widgets[pos].connect("changed", self._mark_dirty)
                row.pack_start(label, False)
                row.pack_start(self.exif_widgets[pos], True)
            else:
                eventBox = gtk.EventBox()
                self.exif_widgets[pos] = gtk.combo_box_new_text()
                eventBox.add(self.exif_widgets[pos])
                for add_type in choices:
                    self.exif_widgets[pos].append_text(add_type)
                self.exif_widgets[pos].set_active(default) 
                if mark_dirty:
                    self.exif_widgets[pos].connect("changed", self._mark_dirty)
                row.pack_start(label, False)
                row.pack_start(eventBox, True)
        for name, text, cbtype, callback in callback_list:
            if cbtype == "button":
                label = gtk.Label()
                label.set_text(text)
                self.exif_widgets[pos + ":" + name + ":Label"] = label
                row.pack_start(label, False)
                icon = gtk.STOCK_EDIT
                size = gtk.ICON_SIZE_MENU
                button = gtk.Button()
                image = gtk.Image()
                image.set_from_stock(icon, size)
                button.add(image)
                button.set_relief(gtk.RELIEF_NONE)
                button.connect("clicked", callback)
                self.exif_widgets[pos + ":" + name] = button
                row.pack_start(button, False)
            elif cbtype == "checkbox":
                button = gtk.CheckButton(text)
                button.set_active(True)
                button.connect("clicked", callback)
                self.exif_widgets[pos + ":" + name] = button
                row.pack_start(button, False)
        row.show_all()
        return row

    def setup_tooltips(self, obj):
        """
        setup tooltips for each field
        """

        for widget, tooltip in _TOOLTIPS:
            self.exif_widgets[widget].set_tooltip_text(tooltip)
 
# -----------------------------------------------
# Error Checking functions
# -----------------------------------------------
    def _mark_dirty(self, obj):
        pass

    def clear_metadata(self, obj, cleartype = "All"):
        """
        clears all data fields to nothing

        @param: cleartype -- 
            "Date" = clears only Date entry fields
            "All" = clears all data fields
        """

        # clear all data fields
        if cleartype == "All":
            for key in ["Artist", "Copyright", "ModDateTime",  "Latitude", "Longitude",
                    "Description", "Altitude"]:
                self.exif_widgets[key].set_text("")

        # clear only the date and time fields
        else:
             self.exif_widgets["ModDateTime"].set_text("")

    def _get_value(self, KeyTag):
        """
        gets the value from the Exif Key, and returns it...

        @param: KeyTag -- image metadata key
        """

        KeyValue = ""

        # LesserVersion would only be True when pyexiv2-to 0.1.3 is installed
        if LesserVersion:
            KeyValue = self.plugin_image[KeyTag]

        else:
            try:
                KeyValue = self.plugin_image[KeyTag].value

            except (KeyError, ValueError, AttributeError):
                pass

        return KeyValue

    def display_exif_tags(self, full_path):
        """
        reads the image metadata after the pyexiv2.Image has been created

        @param: full_path -- complete path to media object on local computer
        """
        self.model.clear()

        if LesserVersion:  # prior to pyexiv2-0.2.0
            self.plugin_image = pyexiv2.Image(full_path)
            self.plugin_image.readMetadata()

            # get all KeyTags for this Media object for diplay only...
            MediaDataTags = [KeyTag for KeyTag in chain(
                                self.plugin_image.exifKeys(),
                                self.plugin_image.xmpKeys(),
                                self.plugin_image.iptcKeys())
                            ]

            # get Thumbnail Data
            # ttype, tdata = self.plugin_image.getThumbnailData()  

        else: # pyexiv2-0.2.0 and above
            self.plugin_image = pyexiv2.ImageMetadata(full_path)
            self.plugin_image.read()

            # get all KeyTags for this Media object for diplay only...
            MediaDataTags = [KeyTag for KeyTag in chain(
                                self.plugin_image.exif_keys,
                                self.plugin_image.xmp_keys,
                                self.plugin_image.iptc_keys)
                            ]

            # get Thumbnail data if any?
            # previews = self.plugin_image.previews
            # if previews:
            #    preview = previews[0]
            #    thumbData = preview.data

        # check to see if we got metadata from media object?
        if MediaDataTags:
            for KeyTag in MediaDataTags:

                tagValue = self._get_value(KeyTag)
                if tagValue:

                    if LesserVersion: # prior to pyexiv2-0.2.0
                        label = self.plugin_image.tagDetails(KeyTag)[0]
                        human_value = self.plugin_image.interpretedExifValue(KeyTag)

                    else:  # pyexiv2-0.2.0 and above
                        try:
                            tag = self.plugin_image[KeyTag]
                            label = tag.label
                            human_value = tag.human_value
                        except AttributeError:
                            label = human_value = ""

                    if KeyTag in ("Exif.Image.DateTime",
                        "Exif.Photo.DateTimeOriginal",
                        "Exif.Photo.DateTimeDigitized"):
                        human_value = _process_date( self._get_value(KeyTag) )

                    # add tagValue to display...
                    self.model.append( (self.plugin_image, label, human_value) )

                # set CopyTo and Clear buttons to active state...
                self.exif_widgets["CopyTo"].set_sensitive(True)
                self.exif_widgets["Clear"].set_sensitive(True)
        else:
            self.exif_widgets["Message:Area"].set_text(_("There is no Exif metadata "
                "for this image..."))
            self.exif_widgets["Save"].set_sensitive(True)

    def copy_to(self, obj):
        """
        reads the image metadata after the pyexiv2.Image has been created
        """

        if LesserVersion: # prior to pyexiv2-0.2.0
            imageKeyTags = [KeyTag for KeyTag in self.plugin_image.exifKeys() if KeyTag in _DATAMAP]

        else: # pyexiv2-0.2.0 and above
            imageKeyTags = [KeyTag for KeyTag in self.plugin_image.exif_keys if KeyTag in _DATAMAP]

        for KeyTag in imageKeyTags:

            # name for matching to exif_widgets 
            widgetsName = _DATAMAP[KeyTag]

            tagValue = self._get_value(KeyTag)
            if tagValue:

                if widgetsName in ["Description", "Artist", "Copyright"]:
                    self.exif_widgets[widgetsName].set_text(tagValue)

                elif widgetsName == "ModDateTime":
                    # date1 comes from the Original Date of the image
                    # date2 comes from the Modification Date of the image
                    # date3 comes from the date that the image was digitized
                    # date4 comes from the date inside of Gramps
                    date1 = self._get_value(_DATAMAP["OrigDateTime"] )
                    date2 = self._get_value(_DATAMAP["ModDateTime"] )
                    date3 = self._get_value("Exif.Photo.DateTimeDigitized")
                    date4 = self.orig_image.get_date_object()

                    use_date = date1 or date2 or date3 or date4
                    if use_date:
                        self.exif_widgets[widgetsName].set_text( _process_date(use_date) )

                # Latitude and Latitude Reference
                elif widgetsName == "Latitude":

                    latitude  =  self._get_value(KeyTag)
                    longitude = self._get_value(_DATAMAP["Longitude"] )

                    # if latitude and longitude exist, display them?
                    if (latitude and longitude):

                        # split latitude metadata into (degrees, minutes, and seconds) from Rational
                        latdeg, latmin, latsec = rational_to_dms(latitude)

                        # split longitude metadata into degrees, minutes, and seconds
                        longdeg, longmin, longsec = rational_to_dms(longitude)

                        # check to see if we have valid GPS Coordinates?
                        latfail = any(coords == False for coords in [latdeg, latmin, latsec])
                        longfail = any(coords == False for coords in [longdeg, longmin, longsec])
                        if (not latfail and not longfail):

                            # Latitude Direction Reference
                            LatitudeRef = self._get_value(_DATAMAP["LatitudeRef"] )

                            # Longitude Direction Reference
                            LongitudeRef = self._get_value(_DATAMAP["LongitudeRef"] )

                            # set display for Latitude GPS Coordinates
                            self.exif_widgets["Latitude"].set_text(
                                """%s° %s′ %s″ %s""" % (latdeg, latmin, latsec, LatitudeRef) )

                            # set display for Longitude GPS Coordinates
                            self.exif_widgets["Longitude"].set_text(
                                """%s° %s′ %s″ %s""" % (longdeg, longmin, longsec, LongitudeRef) )

                # GPS Altitude and Altitude Reference...
                elif widgetsName == "Altitude":
                    deg, min, sec = rational_to_dms(tagValue)

                    altitudeRef = self._get_value(_DATAMAP["AltitudeRef"] )
                    if altitudeRef:
                        value = """%s° %s′ %s″ %s""" % (deg, min, sec, altitudeRef)
                    else:
                        value = """%s° %s′ %s″""" % (deg, min, sec)
                    self.exif_widgets[widgetsName].set_text(value)

        # activate the Save button after metadata has been "Copied to Edit Area"...
        self.exif_widgets["Save"].set_sensitive(True)

    def _set_value(self, KeyTag, KeyValue):
        """
        sets the value for the metadata keytags
        """

        if LesserVersion:  # prior to pyexiv2-0.2.0
            self.plugin_image[KeyTag] = KeyValue

        else:  # pyexiv2-0.2.0 and above
            try:  # tag is being modified...
                self.plugin_image[KeyTag].value = KeyValue

            except KeyError:  # tag has not been set...
                self.plugin_image[KeyTag] = pyexiv2.ExifTag(KeyTag, KeyValue)

            except (ValueError, AttributeError):  # there is an issue with either KeyTag or KeyValue
                pass

#------------------------------------------------
#     Writes/ saves metadata to image
#------------------------------------------------
    def save_metadata(self, obj):
        """
        gets the information from the plugin data fields
        and sets the keytag = keyvalue image metadata
        """

        SavedEntries = []
        for widgetsName in ["Description", "Artist", "Copyright"]:

            widgetsValue = self.exif_widgets[widgetsName].get_text()
            if widgetsValue is not "":
                SavedEntries.append( [widgetsName] )
            self._set_value(_DATAMAP[widgetsName], widgetsValue)

        # write date/ time to Exif metadata
        tmpDate = self.exif_widgets["ModDateTime"].get_text()
        tmpDate = _write_date(tmpDate) if tmpDate else ""
         
        if tmpDate is not False:
            if tmpDate is not "":
                SavedEntries.append( ["ModDateTime"] )
            self._set_value(_DATAMAP["ModDateTime"], tmpDate)

        # check to see if there is an Original DateTime or not?
        OrigDateTime = self._get_value(_DATAMAP["OrigDateTime"] )

        if ((OrigDateTime == False or OrigDateTime == "") and tmpDate is not False):
            if (tmpDate is not "" and OrigDateTime is not ""):
                SavedEntries.append( ["OrigDateTime"] )
            self._set_value(_DATAMAP["OrigDateTime"], tmpDate)

        # get Latitude/ Longitude from this addon...
        latitude  =  self.exif_widgets["Latitude"].get_text()
        longitude = self.exif_widgets["Longitude"].get_text()

        # if there are no values for latitude/ longitude, erase them?
        if (not latitude and not longitude):
            latitude, longitude = "", ""
            LatitudeRef, LongitudeRef = "", ""

        elif (latitude and longitude):

            # if "?" character exist, remove it?
            if "?" in latitude:
                latitude = latitude.replace("?", "")
            if "?" in longitude:
                longitude = longitude.replace("?", "")

            # if "," character exists, remove it?
            if "," in latitude: 
                latitude = latitude.replace(",", "")
            if "," in longitude:
                longitude = longitude.replace(",", "") 

            # if it is in decimal format, convert it to DMS?
            # or if Directional Reference is missing, add it?
            latitude, longitude = self.convert2dms(latitude, longitude)

            # will add (degrees, minutes, seconds) symbols if needed?
            latitude, longitude = self.addsymbols2gps(latitude, longitude)

            # set display for modified/ corrected Latitude/ Longitude...
            self.exif_widgets["Latitude"].set_text(latitude)
            self.exif_widgets["Longitude"].set_text(longitude)

            LatitudeRef = " N"
            if "S" in latitude:
                LatitudeRef = " S"
            latitude = latitude.replace(LatitudeRef, "")
            LatitudeRef = LatitudeRef.replace(" ", "")

            LongitudeRef = " E"
            if "W" in longitude:
                LongitudeRef = " W"
            longitude = longitude.replace(LongitudeRef, "")
            LongitudeRef = LongitudeRef.replace(" ", "")

            # remove symbols for saving Latitude/ Longitude GPS Coordinates
            latitude  =  removesymbols4saving(latitude)
            longitude = removesymbols4saving(longitude)

            # convert (degrees, minutes, seconds) to Rational for saving
            latitude  =  coords_to_rational(latitude)
            longitude = coords_to_rational(longitude)

        # save Latitude and Latitude Reference to image...
        self._set_value(_DATAMAP["Latitude"], latitude)
        self._set_value(_DATAMAP["LatitudeRef"], LatitudeRef)
        if (latitude is not "" and LatitudeRef is not ""):
            SavedEntries.append( ["Latitude"] )

        # save Longitude and Longitude Reference to image...
        self._set_value(_DATAMAP["Longitude"], longitude)
        self._set_value(_DATAMAP["LongitudeRef"], LongitudeRef)
        if (longitude is not "" and LongitudeRef is not ""):
            SavedEntries.append( ["Longitude"] ) 

        if LesserVersion:  # prior to pyexiv2-0.2.0
            MediaDataTags = [KeyTag for KeyTag in chain(
                                self.plugin_image.exifKeys(),
                                self.plugin_image.xmpKeys(),
                                self.plugin_image.iptcKeys() )
                            ]
        else:  # pyexiv2-0.2.0 and above
            # get all KeyTags for this Media object for diplay only...
            MediaDataTags = [KeyTag for KeyTag in chain(
                                self.plugin_image.exif_keys,
                                self.plugin_image.xmp_keys,
                                self.plugin_image.iptc_keys )
                            ]

        if SavedEntries:
            # Notify the user of successful write...
            OkDialog(_("Image Exif metadata has been saved..."))
#        else:
#            for KeyTag in MediaDataTags:
#                self._set_value(KeyTag, "")

#           # All Exif Metadata has been cleared...
#           OkDialog(_("All Exif metadata has been cleared from this image..."))

        # writes all Exif Metadata to image...
        if LesserVersion:  # prior to pyexiv2-0.2.0
            self.plugin_image.writeMetadata()
        else:  # pyexiv2-0.2.0 and above
            self.plugin_image.write()

    def _wipe_metadata(self, obj):
        """
        Attempt to remove/ erase all Exif metadata from this image.
        """

        wipe = subprocess.check_call( ["convert", self.image_path, "-strip", self.image_path] )
        wipe_results = str(wipe)

        if wipe_results:
            self.exif_widgets["Message:Area"].set_text(_("You have sucessfully ERASED "
                "all Exif metadata from this media object!"))
        else:
            self.exif_widgets["Message:Area"].set_text(_("An error has occurred with "
                "the strip/ erase Exif metadata process!"))

# -----------------------------------------------
#              Date Calendar functions
# -----------------------------------------------
    def select_date(self, obj):
        """
        will allow you to choose a date from the calendar widget
        """
 
        tip = _("Double click a date to return the date.")

        self.app = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.app.tooltip = tip
        self.app.set_title(_("Select Date"))
        self.app.set_default_size(450, 200)
        self.app.set_border_width(10)
        self.exif_widgets["Calendar"] = gtk.Calendar()
        self.exif_widgets["Calendar"].connect('day-selected-double-click', self.double_click)
        self.app.add(self.exif_widgets["Calendar"])
        self.exif_widgets["Calendar"].show()
        self.app.show()

    def double_click(self, obj):
        """
        receives double-clicked and returns the selected date
        widget
        """
        now = time.localtime()

        year, month, day = self.exif_widgets["Calendar"].get_date()
        self.exif_widgets["ModDateTime"].set_text(
                "%04d-%s-%02d %02d:%02d:%02d" % (
            year, _dd.long_months[month + 1], day, now[3], now[4], now[5]) )

        # close this window
        self.app.destroy()

#------------------------------------------------
#     Database functions
#------------------------------------------------
    def post_init(self):
        self.connect_signal("Media", self.update)
        
    def db_changed(self):
        self.dbstate.db.connect('media-update', self.update)
        self.update()

# -------------------------------------------------------------------
#          GPS Coordinates functions
# -------------------------------------------------------------------
    def addsymbols2gps(self, latitude, longitude):
        """
        converts a degrees, minutes, seconds representation of Latitude/ Longitude
        without their symbols to having them...

        The Degrees, Minutes, Seconds symbols are required for
        conversion to decimal and nice for display purposes...
        """
        # check to see if Latitude/ Longitude exits?
        if (latitude and longitude):

            # break into its pieces before checking for symbols...
            latdeg, latmin, latsec, LatRef = latitude.split(" ")
            longdeg, longmin, longsec, LongRef = longitude.split(" ")

            # add degrees symbol if necessary?
            if (latdeg and latdeg[-1] is not "°"):
                latdeg += "°"
            if (longdeg and longdeg[-1] is not "°"):
                longdeg += "°"

            # add minutes' symbol if necessary?
            if (latmin and latmin[-1] is not "′"):
                latmin += "′"
            if (longmin and longmin[-1] is not "′"):
                longmin += "′"

            # add seconds' symbol if necessary?
            if (latsec and latsec[-1] is not '″'):
                latsec += '″'
            if (longsec and longsec[-1] is not '″'):
                longsec += '″'

            # re-assemble Latitude
            latitude  = ("""%(degrees)s %(minutes)s %(seconds)s %(dirRef)s""") % {
                'degrees' : latdeg, 'minutes' : latmin, 'seconds' : latsec, 'dirRef' : LatRef}

            # re-assemble Longitude
            longitude  = ("""%(degrees)s %(minutes)s %(seconds)s %(dirRef)s""") % {
                'degrees' : longdeg, 'minutes' : longmin, 'seconds' : longsec, 'dirRef' : LongRef}

        return latitude, longitude

    def convert2decimal(self, obj):
        """
        will convert a decimal GPS Coordinates into decimal format
        """

        # get Latitude/ Longitude from the data fields
        latitude  =  self.exif_widgets["Latitude"].get_text()
        longitude = self.exif_widgets["Longitude"].get_text()

        # if latitude and longitude exist?
        if (latitude and longitude):

            # is Latitude/ Longitude are in DMS format?
            if (latitude.count(" ") >= 2 and longitude.count(" ") >= 2): 

                # add DMS symbols if necessary?
                # the conversion to decimal format, require the DMS symbols
                if not any(latitude.count(sym) or longitude.count(sym)
                            for sym in ("°", "′", '″')
                          ):

                    latitude, longitude = self.addsymbols2gps(latitude, longitude)

                # convert degrees, minutes, seconds w/ symbols to an 8 point decimal
                latitude, longitude = conv_lat_lon( unicode(latitude),
                                                    unicode(longitude), "D.D8")

                self.exif_widgets["Latitude"].set_text(latitude)
                self.exif_widgets["Longitude"].set_text(longitude)

    def convert2dms(self, latitude =False, longitude =False):
        """
        will convert a decimal GPS Coordinates into degrees, minutes, seconds

        will add direction Reference if it is missing...
        """

        # if lat/ long are False, get from data fields...
        if (not latitude and not longitude):
            latitude = self.exif_widgets["Latitude"].get_text()
            longitude = self.exif_widgets["Longitude"].get_text()

        # if Latitude/ Longitude exists?
        if (latitude and longitude):

            # if coordinates are in decimal format?
            if (latitude[0] == "." and longitude[0] == "."):

                # convert latitude and longitude to a DMS with separator of ":"
                latitude, longitude = conv_lat_lon(latitude, longitude, "DEG-:")
 
                latdeg, latmin, latsec = latitude.split(":", 2)
                latitude = """%s° %s′ %s″""" % (latdeg, latmin, latsec)

                longdeg, longmin, longsec = longitude.split(":", 2)
                longitude = """%s° %s′ %s″""" % (longdeg, longmin, longsec)

            LatRef = False
            if (latitude[0] == "-" and latitude[-1] is not "S"):
                latitude = latitude[1:]
                LatRef = "S"
            elif (latitude[0] is not "-" and latitude[-1] is not "N"):
                LatRef = "N"

            # Add Latitude Reference if missing?
            if LatRef:
                latitude += " " + LatRef
                 
            LongRef = False
            if (longitude[0] == "-" and longitude[-1] is not "W"):
                longitude = longitude[1:]
                LongRef = "W"
            elif (longitude[0] is not "-" and longitude[-1] is not "E"):
                LongRef = "E"

            # Add Longitude Reference if missing?
            if LongRef:
                longitude += " " + LongRef

            # display modified latitude
            self.exif_widgets["Latitude"].set_text(latitude)

            # display modified longitude 
            self.exif_widgets["Longitude"].set_text(longitude)

            return latitude, longitude

def string_to_rational(coordinate):
    """
    convert string to rational variable for GPS
    """

    if '.' in coordinate:
        value1, value2 = coordinate.split('.')
        return pyexiv2.Rational(int(float(value1 + value2)), 10**len(value2))
    else:
        return pyexiv2.Rational(int(coordinate), 1)

def removesymbols4saving(dmsStr):
    """
    will recieve a DMS with symbols and return it without them
    """

    # make sure that the variable has DMS...
    if dmsStr:       

        # remove degrees' symbol if it exist?
        if dmsStr.count("°") == 1:
            dmsStr = dmsStr.replace("°", "")

        # remove minutes' symbol if it exist?
        if dmsStr.count("′") == 1:
            dmsStr = dmsStr.replace("′", "")

        # remove seconds' symbol if it exist?
        if dmsStr.count('″') == 1:
            dmsStr = dmsStr.replace('″', "")

    return dmsStr

def coords_to_rational(Coordinates):
    """
    returns the GPS coordinates to Latitude/ Longitude
    """

    return [string_to_rational(coordinate) for coordinate in Coordinates.split( " ")]

def convert_value(value):
    """
    will take a value from the coordinates and return its value
    """

    if isinstance(value, (Fraction, pyexiv2.Rational)):

        return str( ( Decimal(value.numerator) / Decimal(value.denominator) ) )

def rational_to_dms(coords):
    """
    takes a rational set of coordinates and returns (degrees, minutes, seconds)

    [Fraction(40, 1), Fraction(0, 1), Fraction(1079, 20)]
    """

    deg, min, sec =     False, False, False
    # coordinates look like:
    #     [Rational(38, 1), Rational(38, 1), Rational(150, 50)]
    # or [Fraction(38, 1), Fraction(38, 1), Fraction(318, 100)]   
    if isinstance(coords, list):
    
        if len(coords) == 3:
            return [convert_value(coordinate) for coordinate in coords]

    return deg, min, sec

def _format_datetime(exif_dt):
    """
    Convert a python datetime object into a string for display, using the
    standard Gramps date format.
    """
    if type(exif_dt) is not datetime:
        return ''

    date_part = gen.lib.Date()
    date_part.set_yr_mon_day(exif_dt.year, exif_dt.month, exif_dt.day)
    date_str = _dd.display(date_part)
    time_str = exif_dt.strftime('%H:%M:%S')

    return _('%(date)s %(time)s') % {'date': date_str, 'time': time_str}

def _get_date_format(datestr):
    """
    attempt to retrieve date format from date string
    """

    # attempt to determine the dateformat of the variable passed to it...
    for dateformat in ["%Y-%m-%d %H:%M:%S", "%Y %m %d %H:%M:%S",
                       "%Y-%b-%d %H:%M:%S", "%Y %b %d %H:%M:%S",
                       "%Y-%B-%d %H:%M:%S", "%Y %B %d %H:%M:%S",
                       "%d-%m-%Y %H:%M:%S", "%d %m %Y %H:%M:%S",
                       "%d-%b-%Y %H:%M:%S", "%d %b %Y %H:%M:%S",
                       "%d-%B-%Y %H:%M:%S", "%d %B %Y %H:%M:%S",
                       "%m-%d-%Y %H:%M:%S", "%m %d %Y %H:%M:%S",
                       "%b-%d-%Y %H:%M:%S", "%b %d %Y %H:%M:%S",
                       "%B-%d-%Y %H:%M:%S", "%B %d %Y %H:%M:%S"]:

        # find date string format
        try:
            tmpDate = time.strptime(datestr, dateformat)
            break

        # datestring format  not found...
        except ValueError:
            tmpDate = False

    return tmpDate

def _write_date(wdatetime):
    """
    handle the ModDateTime field for saing
    """

    datestr = _get_date_format(wdatetime)
    if datestr is not False:
        wyear, wmonth, day, hour, minutes, seconds = datestr[0:6]

    else:
        wyear, wmonth, day, hour, minutes, seconds = [False]*6

        # do some error trapping...
        if wmonth > 12: wmonth = 12
        if day == 0: day = 1
        if hour >= 24: hour = 0
        if minutes > 59: minutes = 59
        if seconds > 59: seconds = 59

        # get the number of days in year for all months
        numdays = [0] + [calendar.monthrange(year, month)[1] for year
                        in [wyear] for month in range(1, 13) ]

        if day > numdays[wmonth]:
            day = numdays[wmonth]

    if wyear < 1900:
        try:
            tmpDate = "%04d-%s-%02d %02d:%02d:%02d" % (wyear, _dd.long_months[wmonth], day,
                                                hour, minutes, seconds)
        except ValueError:
            tmpDate = ""
    else:
        try:
            tmpDate = datetime(wyear, wmonth, day, hour, minutes, seconds)

        except ValueError:
            tmpDate = False

    return tmpDate
    
def _process_date(tmpDate):
    """
    will attempt to parse the date/ time Exif metadata entry into its pieces...
        (year, month, day, hour, minutes, seconds)
    """

    if not tmpDate:
        return ""

    datetype = type(tmpDate)

    # if variable is already in datetime.datetime() format, return it?
    if datetype == datetime:
        return _format_datetime(tmpDate)

    elif datetype in [date, gen.lib.date.Date, list]:
        hour, minutes, seconds = time.localtime()[3:6]

        # ImageDateTime is in datetime.date format
        if datetype == date:
            pyear, pmonth, day = tmpDate.year, tmpDate.month, tmpDate.day

        # ImageDateTime is in gen.lib.date.Date format
        elif datetype == gen.lib.date.Date:
            pyear, pmonth, day = tmpDate.get_year(), tmpDate.get_month(), tmpDate.get_day()

        # ImageDateTime is in list format
        else:
            pyear, pmonth, day = tmpDate[0].year, tmpDate[0].month, tmpDate[0].day

    # datetime is in string format...
    elif datetype == str:

        datestr = _get_date_format(tmpDate)
        if datestr is not False:
            pyear, pmonth, day, hour, minutes, seconds = datestr[0:6]

        else:
            pyear, pmonth, day, hour, minutes, seconds = [False]*6

        # do some error trapping...
        if pmonth > 12: pmonth = 12
        if day == 0: day = 1
        if hour >= 24: hour = 0
        if minutes > 59: minutes = 59
        if seconds > 59: seconds = 59

        # get the number of days in year for all months
        numdays = [0] + [calendar.monthrange(year, month)[1] for year
                        in [pyear] for month in range(1, 13) ]

        if day > numdays[pmonth]:
            day = numdays[pmonth]

    if pyear < 1900:
        try:
            tmpDate = "%04d-%s-%02d %02d:%02d:%02d" % (pyear, _dd.long_months[pmonth], day,
                                                hour, minutes, seconds)
        except ValueError:
            tmpDate = ""
    else:
        try:
            tmpDate = datetime(pyear, pmonth, day, hour, minutes, seconds)

        except ValueError:
            tmpDate = False

    if tmpDate is not False:
        if type(tmpDate) == datetime:
            return _format_datetime(tmpDate)
        else:
            try:
                return "%04d-%s-%02d %02d:%02d:%02d" % (pyear, _dd.long_months[pmonth], day,
                                                hour, minutes, seconds)
            except ValueError:
                return ""
    else:
        return ""
