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

# abilty to escape certain characters from html output...
from xml.sax.saxutils import escape as _html_escape

from itertools import chain

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
    raise Exception(msg)

    WarningDialog(msg)
    raise Exception(msg)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
# available image types for exiv2
_valid_types = ["jpeg", "jpg", "exv", "tiff", "dng", "nef", "pef", "pgf", "png", "psd", "jp2"]

# set up Exif keys for Image.exif_keys
_DATAMAP = {
    "Exif.Image.ImageDescription"  : "Description",
    "Exif.Image.DateTime"          : "DateTime",
    "Exif.Image.Artist"            : "Artist",
    "Exif.Image.Copyright"         : "Copyright",
    "Exif.GPSInfo.GPSLatitudeRef"  : "LatitudeRef",
    "Exif.GPSInfo.GPSLatitude"     : "Latitude",
    "Exif.GPSInfo.GPSLongitudeRef" : "LongitudeRef",
    "Exif.GPSInfo.GPSLongitude"    : "Longitude",
    "Exif.GPSInfo.GPSAltitudeRef"  : "AltitudeRef",
    "Exif.GPSInfo.GPSAltitude"     : "Altitude"}
_DATAMAP = dict( chain(_DATAMAP.iteritems(), ((val, key) for key, val in _DATAMAP.iteritems() )))

def _help_page(obj):
    """
    will bring up a Wiki help page.
    """

    import GrampsDisplay

    GrampsDisplay.help(webpage='Image Metadata Gramplet')

def _return_month(month):
    """
    returns either an integer of the month number or the abbreviated month name

    @param: rmonth -- can be one of:
        10, "10", "Oct", or "October"
    """
    _allmonths = list([_dd.short_months[i], _dd.long_months[i], i] for i in range(1, 13))

    try:
        month = int(month)

    except ValueError:
        for sm, lm, index in _allmonths:
            found = any(month == value for value in [sm, lm])
            if found:
                month = int(index)
                break
            else:
                if str(month) == index:
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
        rows.pack_start(medialabel, expand =False)

        self.model = gtk.ListStore(object, str, str)
        view = gtk.TreeView(self.model)

        # Key Column
        view.append_column( self.__create_column(_("Key"), 1) )

        # Value Column
        view.append_column( self.__create_column(_("Value"), 2) )
        rows.pack_start(view, padding =10)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)

        button = gtk.Button(_("Copy to Edit Area"))
        button.connect("clicked", self.copy_to)
        button.set_sensitive(False)
        self.exif_widgets["CopyTo"] = button
        button_box.add( self.exif_widgets["CopyTo"] )

        # Clear button...
        button = gtk.Button(stock=gtk.STOCK_CLEAR)
        button.set_tooltip_text(_("Clears the metadata from these fields."))
        button.connect("clicked", self.clear_metadata)
        button.set_sensitive(False) 
        self.exif_widgets["Clear"] = button
        button_box.add( self.exif_widgets["Clear"] )

        rows.pack_start(button_box, expand =False, fill =False)

        for items in [

            # Image Description
            ("Description",     _("Description"),    None, False, [],  True,  0),

            # calendar date clickable entry
            ("Date",            "",                  None, True,
            [("Select",         _("Select Date"),  "button", self.select_date)],
                                                                     True,  0),

            # Manual Date/ Time Entry, 1826-April-12 14:06:00
            ("DateTime",         _("Date/ Time"),    None, False,  [], True,  0),

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

        # provide tooltips for this gramplet
        self.setup_tooltips(self.orig_image)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        rows.pack_start(button_box, expand =False, fill =False)

        # Help button...
        button = gtk.Button(stock=gtk.STOCK_HELP)
        button.set_tooltip_text(_("Will bring up a Wiki manual page to help you with this gramplet."))
        button.connect("clicked", _help_page)
        self.exif_widgets["Help"] = button
        button_box.add( self.exif_widgets["Help"] )

        # Save button...
        button = gtk.Button(stock=gtk.STOCK_SAVE)
        button.set_tooltip_text(_("Saves the information entered here to the image metadata.  "
            "WARNING: Metadata values will be removed if you save blank data..."))
        button.connect("clicked", self.save_metadata)
        button.set_sensitive(False)
        self.exif_widgets["Save"] = button
        button_box.add( self.exif_widgets["Save"] )

        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(rows)
        rows.show_all()

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

    def main(self): # return false finishes
        """
        get the active media, mime type, and reads the image metadata
        """
        db = self.dbstate.db

        active_handle = self.get_active("Media")
        if not active_handle:
            return

        self.orig_image = db.get_object_from_handle(active_handle)
        if not self.orig_image:
            return

        # get media full path
        self.image_path = Utils.media_path_full(db, self.orig_image.get_path() )

        # check media read/ write privileges...
        _readable = os.access(self.image_path, os.R_OK)
        _writable = os.access(self.image_path, os.W_OK)
        if not _readable:
            return

        # if media object is not writable, disable Save Button?
        if not _writable:
            self.exif_widgets["Save"].set_sensitive(False)

        # display file description/ title...
        self.exif_widgets["Media:Label"].set_text(self.orig_image.get_description())

        # get media mime type
        mime_type = self.orig_image.get_mime_type()
        self.__mtype = gen.mime.get_description(mime_type)
        if (mime_type and mime_type.startswith("image") ):

                # set up tooltips text for all buttons
                self.setup_tooltips(self.orig_image)

                # read the media metadata and display it
                self.display_exif_tags(self.image_path)

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

        # Author
        self.exif_widgets["Artist"].set_tooltip_text(_("Enter the Artist/ Author of this image.  "
            "The person's name or the company who is responsible for the creation of this image."))

        # Copyright
        self.exif_widgets["Copyright"].set_tooltip_text(_("Enter the copyright"
            " information for the image.  xample: (C) 2010 Smith and Wesson"))

        # Select Data button
        self.exif_widgets["Date:Select"].set_tooltip_text(_("Allows you to select a date from a "
            "pop-up window calendar.  You will still need to enter the time..."))

        # Manual Date Entry 
        self.exif_widgets[ "DateTime"].set_tooltip_text(_("Manual Date Entry, \n"
            "Example: 1826-Apr-12 or 1826-April-12"))

        # Convert Decimal button
        self.exif_widgets["GPSFormat:Decimal"].set_tooltip_text(_("Converts Degree, Minutes, Seconds "
            "GPS Coordinates to a Decimal representation."))

        # Degrees, Minutes, Seconds button
        self.exif_widgets["GPSFormat:DMS"].set_tooltip_text(_("Converts Decimal "
            "GPS Coordinates to a Degrees, Minutes, Seconds representation."))

        # Leaning Tower of Pisa, Pisa, Italy
        # GPS Latitude Coordinates
        self.exif_widgets["Latitude"].set_tooltip_text(_("Enter the GPS Latitude Coordinates for "
            "your image,\n"
            "Example: 43.722965, 43 43 22 N, 38° 38′ 03″ N, 38 38 3"))

        # GPS Longitude Coordinate
        self.exif_widgets["Longitude"].set_tooltip_text(_("Enter the GPS Longitude Coordinates for "
            "your image,\n"
            "Example: 10.396378, 10 23 46 E, 105° 6′ 6″ W, -105 6 6"))

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
            for key in ["Artist", "Copyright", "DateTime",  "Latitude", "Longitude",
                    "Description"]:
                self.exif_widgets[key].set_text("")

            self.model.clear()

        # clear only the date and time fields
        else:
             self.exif_widgets["DateTime"].set_text("")

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
            MediaDataTags = [KeyTag for KeyTag in self.plugin_image.exifKeys() ]
            MediaDataTags.append( [KeyTag for KeyTag in self.plugin_image.xmpKeys()] )
            MediaDataTags.append( [KeyTag for KeyTag in self.plugin_image.iptcKeys()] )

            # get Thumbnail Data
            ttype, tdata = self.plugin_image.getThumbnailData()  

        else: # pyexiv2-0.2.0 and above
            self.plugin_image = pyexiv2.ImageMetadata(full_path)
            self.plugin_image.read()

            # get all KeyTags for this Media object for diplay only...
            MediaDataTags = [KeyTag for KeyTag in self.plugin_image.exif_keys ]
            MediaDataTags.append( [KeyTag for KeyTag in self.plugin_image.xmp_keys ] )
            MediaDataTags.append( [KeyTag for KeyTag in self.plugin_image.iptc_keys ] )

            # get Thumbnail data if any?
            previews = self.plugin_image.previews
            if previews:
                preview = previews[0]
                thumbData = preview.data

        # check to see if we got metadata from media object?
        for KeyTag in MediaDataTags:

            tagValue = self._get_value(KeyTag)
            if tagValue:

                if LesserVersion: # prior to pyexiv2-0.2.0
                    label = self.plugin_image.tagDetails(KeyTag)[0]
                    human_value = self.plugin_image.interpretedExifValue(KeyTag)

                else:  # pyexiv2-0.2.0 and above
                    tag = self.plugin_image[KeyTag]
                    label = tag.label
                    human_value = tag.human_value

                # add tagValue to display...
                self.model.append( (self.plugin_image, label, human_value) )

            # set CopyTo and Clear buttons to active state...
            self.exif_widgets["CopyTo"].set_sensitive(True)
            self.exif_widgets["Clear"].set_sensitive(True)

    def copy_to(self, obj):
        """
        reads the image metadata after the pyexiv2.Image has been created
        """

        # reads the media metadata into this addon
        # LesserVersion would only be True when pyexiv2-to 0.1.3 is installed
        if LesserVersion: # prior to v0.2.0
            imageKeyTags = [KeyTag for KeyTag in self.plugin_image.exifKeys()
                    if KeyTag in _DATAMAP ]

        else: # v0.2.0 and above
            imageKeyTags = [KeyTag for KeyTag in self.plugin_image.exif_keys
                    if KeyTag in _DATAMAP ]

        for KeyTag in imageKeyTags:

            # name for matching to exif_widgets 
            matchValue = _DATAMAP[KeyTag]  

            # image Description
            if matchValue == "Description":
                self.exif_widgets[matchValue].set_text(
                    self._get_value(KeyTag) )

            # media image DateTime
            elif matchValue == "DateTime":

                # date1 and date2 comes from the image metadata
                # date3 may come from the Gramps database 
                date1 = self._get_value("Exif.Photo.DateTimeOriginal")
                date2 = self._get_value(KeyTag)
                date3 = self.orig_image.get_date_object()

                use_date = date1 or date2 or date3
                if use_date:
                    rdate = self.process_date(use_date)
                    if rdate is not False:
                        self.exif_widgets[matchValue].set_text(rdate)

            # Media image Author/ Artist
            elif matchValue == "Artist":
                self.exif_widgets[matchValue].set_text(
                    self._get_value(KeyTag) )

            # media image Copyright
            elif matchValue == "Copyright":
                self.exif_widgets[matchValue].set_text(
                    self._get_value(KeyTag) )

            # Latitude and Latitude Reference
            elif matchValue == "Latitude":

                latitude  =  self._get_value(KeyTag)
                longitude = self._get_value(_DATAMAP["Longitude"] )
                altitude = self._get_value(_DATAMAP["Altitude"] )

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
            elif matchValue == "Altitude":
                deg, min, sec = rational_to_dms( self._get_value(KeyTag) )

                altitudeRef = self._get_value(_DATAMAP["AltitudeRef"] )
                if altitudeRef:
                    self.exif_widgets[matchValue].set_text(
                        """%s° %s′ %s″ %s""" % (deg, min, sec, altitudeRef) )

        # activate the Save button after metadata has been "Copied to Edit Area"...
        self.exif_widgets["Save"].set_sensitive(True)

    def _set_value(self, KeyTag, KeyValue):
        """
        sets the value for the Exif keys

        @param: KeyTag   -- exif key
        @param: KeyValue -- value to be saved
        """

        # for pyexiv2-0.1.3 users
        if LesserVersion:
            self.plugin_image[KeyTag] = KeyValue 
        else:
            # Exif KeyValue family?
            if "Exif" in KeyTag:
                try:
                    self.plugin_image[KeyTag].value = KeyValue

                except KeyError:
                    self.plugin_image[KeyTag] = pyexiv2.ExifTag(KeyTag, KeyValue)

                except (ValueError, AttributeError):
                    pass

            # Iptc KeyValue family?
            else:
                try:
                    self.plugin_image[KeyTag].values = KeyValue

                except KeyError:
                    self.plugin_image[KeyTag] = pyexiv2.IptcTag(KeyTag, KeyValue)

                except (ValueError, AttributeError):
                    pass

#------------------------------------------------
#     Writes/ saves metadata to image
#------------------------------------------------
    def save_metadata(self, obj):
        """
        gets the information from the plugin data fields
        and sets the keytag = keyvalue image metadata
        """

        # Author data field
        artist = self.exif_widgets["Artist"].get_text()
        self._set_value(_DATAMAP["ImageArtist"], artist)

        # Copyright data field
        copyright = self.exif_widgets["Copyright"].get_text()
        self._set_value(_DATAMAP["ImageCopyright"], copyright)

        # get date from data field for saving
        wdate = self._write_date( self.exif_widgets["Date"].get_text() )
        if wdate is False:
            self._set_value(_DATAMAP["ImageDateTime"], "")
        else:
            self._set_value(_DATAMAP["ImageDateTime"], wdate)

        # get Latitude/ Longitude from this addon...
        latitude  =  self.exif_widgets["Latitude"].get_text()
        longitude = self.exif_widgets["Longitude"].get_text()

        # check to see if Latitude/ Longitude exists?
        if (latitude and longitude):

            # complete some error checking to prevent crashes...
            # if "?" character exist, remove it?
            if ("?" in latitude or "?" in longitude):
                latitude = latitude.replace("?", "")
                longitude = longitude.replace("?", "")

            # if "," character exists, remove it?
            if ("," in latitude or "," in longitude): 
                latitude = latitude.replace(",", "")
                longitude = longitude.replace(",", "") 

            # if it is in decimal format, convert it to DMS?
            # if not, then do nothing?
            self.convert2dms(self.plugin_image)

            # get Latitude/ Longitude from the data fields
            latitude  =  self.exif_widgets["Latitude"].get_text()
            longitude = self.exif_widgets["Longitude"].get_text()

            # will add (degrees, minutes, seconds) symbols if needed?
            # if not, do nothing...
            latitude, longitude = self.addsymbols2gps(latitude, longitude)

            # set up display
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
            latitude, longitude = _removesymbols4saving(latitude, longitude) 

            # convert (degrees, minutes, seconds) to Rational for saving
            self._set_value(_DATAMAP["ImageLatitude"], coords_to_rational(latitude))
            self._set_value(_DATAMAP["ImageLatitudeRef"], LatitudeRef)

            # convert (degrees, minutes, seconds) to Rational for saving
            self._set_value(_DATAMAP["ImageLongitude"], coords_to_rational(longitude))
            self._set_value(_DATAMAP["ImageLongitudeRef"], LongitudeRef)

        # description data field
        meta_descr = self.exif_widgets["Description"].get_text()
        self._set_value(_DATAMAP["ImageDescription"], meta_descr)

        # writes the metdata KeyTags to the image...  
        # LesserVersion would only be True when pyexiv2-to 0.1.3 is installed
        if not LesserVersion:
            self.plugin_image.write()
        else:
            self.plugin_image.writeMetadata()

        # notify the user of successful write...
        OkDialog(_("Image metadata has been saved."))

#------------------------------------------------
# Process Date/ Time fields for saving to image
#------------------------------------------------
    def _write_date(self, wdate =False, wtime =False):
        """
        process the date/ time for writing to image

        @param: wdate -- date from the interface
        @param: wtime -- time from the interface
        """

        # Time, but no Date
        if (wtime and not wdate):
            values = "Time"

        # date, but no time
        elif (wdate and not wtime):
            values = "Date"

        # no date, no time
        elif (not wdate and not wtime):
            values = "None"

        # date and time...
        elif (wdate and wtime):
            vales = "DateTime"

        if (values == "None" or values == "Time"):
            self.clear_metadata(self.plugin_image, "Date") 
            return False

        elif values == "DateTime":

            # if date is in proper format: 1826-Apr-12 or 1826-April-12
            wdate = _split_values(wdate)
            if len(wdate) == 3:
                wyear, wmonth, wday = wdate[0], wdate[1], wdate[2]
            else:
                wyear, wmonth, wday = False, False, False
 
            wtime = _split_values(wtime)
            if len(wtime) == 3:
                hour, minutes, seconds = wtime[0], wtime[1], wtime[2]
            else:
                hour, minutes, seconds = False, False, False

            # if any value for date or time is False, then do not save date
            bad_datetime = any(value == False for value in [wyear, wmonth, wday, hour, minutes, seconds] )
            if not bad_datetime:

                # convert each value for date/ time
                try:
                    wyear, wday = int(wyear), int(wday)

                except ValueError:
                    pass

                try:
                    hour, minutes, seconds = int(hour), int(minutes), int(seconds)

                except ValueError:
                    pass

                # do some error trapping...
                if wday == 0:
                    wday = 1
                if hour >= 24:
                    hour = 0
                if minutes > 59:
                    minutes = 59
                if seconds > 59:
                    seconds = 59

                # convert month, and do error trapping
                try:
                    wmonth = int(wmonth)
                except ValueError:
                    wmonth = _return_month(wmonth)
                    if wmonth > 12:
                        wmonth = 12

                # get the number of days in wyear of all months
                numdays = [0] + [calendar.monthrange(year, month)[1] for year 
                    in [wyear] for month in range(1, 13) ]

                if wday > numdays[wmonth]:
                    wday = numdays[wmonth]

                # ExifImage Year must be greater than 1900
                # if not, we save it as a string
                if wyear < 1900:
                    wdate = "%04d-%s-%02d %02d:%02d:%02d" % (
                        wyear, _dd.long_months[wmonth], wday, hour, minutes, seconds)

                # year -> or equal to 1900
                else:
                    try:
                        wdate = datetime(wyear, wmonth, wday, hour, minutes, seconds)

                    except ValueError:
                        return Flse

                self.exif_widgets["DateTime"].set_text("%04d-%s-%02d" % (
                    wyear, _dd.long_months[wmonth], wday))

        elif values == "Date":

            wdate = _split_values(wdate)
            if len(wdate) == 3:
                wyear, wmonth, wday = wdate[0], wdate[1], wdate[2]
            else:
                wyear, wmonth, wday = False, False, False

            date_date = any( value == False for value in [wyear, wmonth, wday] )
            if not bad_date:

                try:
                    wyear, wday = int(wyear), int(wday)

                except ValueError:
                    wyear, wday = False, False

                try:
                    wmonth = int(wmonth)

                except ValueError:
                    wmonth = _return_month(wmonth)

                 # do some error trapping...
                if wday == 0: wday = 1

                if wmonth > 12: wmonth = 12

                if wyear < 1900:
                    wdate = "%04d-%02d-%02d" % (wyear, wmonth, wday) 

                else:
                    try:
                        wdate = date(wyear, wmonth, wday)

                    except ValueError:
                        return False

                self.exif_widgets["DateTime"].set_text("%04d-%02d-%02d" % (wyear, wmonth, wday) )

        return wdate


#------------------------------------------------
#     Date/ Time functions
#------------------------------------------------
    def process_date(self, tmpDate):
        """
        Process the date for read and write processes
        year, month, day, hour, minutes, seconds

        @param: tmpDate = variable to be processed
        """

        year, month, day = False, False, False

        now = time.localtime()
        datetype = tmpDate.__class__

        # get local time for when if it is not available?
        hour, minutes, seconds = now[3:6]

        found = any( datetype == _type for _type in [datetime, date, gen.lib.date.Date, list])
        if found:

            # ImageDateTime is in datetime.datetime format
            if datetype == datetime:
                year, month, day = tmpDate.year, tmpDate.month, tmpDate.day
                hour, minutes, seconds = tmpDate.hour, tmpDate.minute, tmpDate.second

            # ImageDateTime is in datetime.date format
            elif datetype == date:
                year, month, day = tmpDate.year, tmpDate.month, tmpDate.day

            # ImageDateTime is in gen.lib.date.Date format
            elif datetype == gen.lib.date.Date:
                year, month, day = tmpDate.get_year(), tmpDate.get_month(), tmpDate.get_day()

            # ImageDateTime is in list format
            else:
                year, month, day = tmpDate[0].year, tmpDate[0].month, tmpDate[0].day

        # ImageDateTime is in string format
        elif datetype == str:

            # separate date and time from the string
            if " " in tmpDate:
                rdate, rtime = tmpDate.split(" ")
            elif "/" in tmpDate:
                rdate, rtime = tmpDate.split("/")
            else:
                rdate, rtime = False, False

            if rdate is not False:
                # split date elements
                year, month, day = _split_values(rdate)

            # split time elements
            if rtime is not False:
                hour, minutes, seconds = _split_values(rtime)
 
        bad_datetime = any( value == False for value in [year, month, day] )
        if not bad_datetime:

            # convert values to integers
            try:
                year, day = int(year), int(day)
            except ValueError:
                year, day = False, False
 
            try:
                month = int(month)
            except ValueError:
                month = _return_month(month)

            # convert time into integers...
            try:
                hour, minutes, seconds = int(hour), int(minutes), int(seconds) 
            except ValueError:
                hour, minutes, seconds = False, False, False

        rdate = False
        if (year, month, day):
            rdate = "%04d-%s-%02d" % (year, _dd.long_months[month], day)

        if ( rdate and (hour, minutes, seconds) ):
            rdate += " %02d:%02d:%02d" % (hour, minutes, seconds)

        return rdate

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
        self.exif_widgets["DateTime"].set_text(
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
    def addsymbols2gps(self, latitude =False, longitude =False):
        """
        converts a degrees, minutes, seconds representation of Latitude/ Longitude
        without their symbols to having them...

        @param: latitude -- Latitude GPS Coordinates
        @param: longitude -- Longitude GPS Coordinates
        """
        LatitudeRef, LongitudeRef = "N", "E"

        # check to see if Latitude/ Longitude exits?
        if (latitude and longitude):

            if (latitude.count(".") == 1 and longitude.count(".") == 1):
                self.convert2dms(self.plugin_image)

                # get Latitude/ Longitude from data fields
                # after the conversion
                latitude  =  self.exif_widgets["Latitude"].get_text()
                longitude = self.exif_widgets["Longitude"].get_text()

            # add DMS symbols if necessary?
            # the conversion to decimal format, require the DMS symbols
            elif ( (latitude.count("°") == 0 and longitude.count("°") == 0) and
                (latitude.count("′") == 0 and longitude.count("′") == 0) and
                (latitude.count('″') == 0 and longitude.count('″') == 0) ):

                # is there a direction element here?
                if (latitude.count("N") == 1 or latitude.count("S") == 1):
                    latdeg, latmin, latsec, LatitudeRef = latitude.split(" ", 3)
                else:
                    atitudeRef = "N"
                    latdeg, latmin, latsec = latitude.split(" ", 2)
                    if latdeg[0] == "-":
                        latdeg = latdeg.replace("-", "")
                        LatitudeRef = "S"

                # is there a direction element here?
                if (longitude.count("E") == 1 or longitude.count("W") == 1):
                    longdeg, longmin, longsec, LongitudeRef = longitude.split(" ", 3)
                else:
                    ongitudeRef = "E"
                    longdeg, longmin, longsec = longitude.split(" ", 2)
                    if longdeg[0] == "-":
                        longdeg = longdeg.replace("-", "")
                        LongitudeRef = "W"

                latitude  = """%s° %s′ %s″ %s""" % (latdeg, latmin, latsec, LatitudeRef)
                longitude = """%s° %s′ %s″ %s""" % (longdeg, longmin, longsec, LongitudeRef)
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
                if ( (latitude.count("°") == 0 and longitude.count("°") == 0) and
                    (latitude.count("′") == 0 and longitude.count("′") == 0) and
                    (latitude.count('″') == 0 and longitude.count('″') == 0) ):

                    latitude, longitude = self.addsymbols2gps(latitude, longitude)

                # convert degrees, minutes, seconds w/ symbols to an 8 point decimal
                latitude, longitude = conv_lat_lon( unicode(latitude),
                                                    unicode(longitude), "D.D8")

                self.exif_widgets["Latitude"].set_text(latitude)
                self.exif_widgets["Longitude"].set_text(longitude)

    def convert2dms(self, obj):
        """
        will convert a decimal GPS Coordinates into degrees, minutes, seconds
        for display only
        """

        # get Latitude/ Longitude from the data fields
        latitude = self.exif_widgets["Latitude"].get_text()
        longitude = self.exif_widgets["Longitude"].get_text()

        # if Latitude/ Longitude exists?
        if (latitude and longitude):

            # if coordinates are in decimal format?
            if (latitude.count(".") == 1 and longitude.count(".") == 1):

                # convert latitude and longitude to a DMS with separator of ":"
                latitude, longitude = conv_lat_lon(latitude, longitude, "DEG-:")
 
                # remove negative symbol if there is one?
                LatitudeRef = "N"
                if latitude[0] == "-":
                    latitude = latitude.replace("-", "")
                    LatitudeRef = "S"
                latdeg, latmin, latsec = latitude.split(":", 2)

               # remove negative symbol if there is one?
                LongitudeRef = "E"
                if longitude[0] == "-":
                    longitude = longitude.replace("-", "")
                    LongitudeRef = "W"
                longdeg, longmin, longsec = longitude.split(":", 2)

                self.exif_widgets["Latitude"].set_text(
                    """%s° %s′ %s″ %s""" % (latdeg, latmin, latsec, LatitudeRef) )

                self.exif_widgets["Longitude"].set_text(
                    """%s° %s′ %s″ %s""" % (longdeg, longmin, longsec, LongitudeRef) )

def string_to_rational(coordinate):
    """
    convert string to rational variable for GPS
    """

    if '.' in coordinate:
        value1, value2 = coordinate.split('.')
        return pyexiv2.Rational(int(float(value1 + value2)), 10**len(value2))
    else:
        return pyexiv2.Rational(int(coordinate), 1)

def _removesymbols4saving(latitude =False, longitude =False):
    """
    will recieve a DMS with symbols and return it without them

    @param: latitude -- Latitude GPS Coordinates
    @param: longitude -- GPS Longitude Coordinates
    """

    # check to see if latitude/ longitude exist?
    if (latitude and longitude):

        # remove degrees symbol if it exist?
        latitude = latitude.replace("°", "")
        longitude = longitude.replace("°", "")

        # remove minutes symbol if it exist?
        latitude = latitude.replace("′", "")
        longitude = longitude.replace("′", "")

        # remove seconds symbol if it exist?
        latitude = latitude.replace('″', "")
        longitude = longitude.replace('″', "")

    return latitude, longitude

def coords_to_rational(Coordinates):
    """
    returns the GPS coordinates to Latitude/ Longitude
    """

    return [string_to_rational(coordinate) for coordinate in Coordinates.split( " ")]

def convert_value(value):
    """
    will take a value from the coordinates and return its value
    """
    from decimal import *
    getcontext().prec = 4
    from fractions import Fraction

    if (isinstance(value, Fraction) or isinstance(value, pyexiv2.Rational)):

        return str( ( Decimal(value.numerator) / Decimal(value.denominator) ) )

def rational_to_dms(coords):
    """
    takes a rational set of coordinates and returns (degrees, minutes, seconds)

    [Fraction(40, 1), Fraction(0, 1), Fraction(1079, 20)]
    """

    deg, min, sec = False, False, False
    # coordinates look like:
    #     [Rational(38, 1), Rational(38, 1), Rational(150, 50)]
    # or [Fraction(38, 1), Fraction(38, 1), Fraction(318, 100)]   
    if isinstance(coords, list):
    
        if len(coords) == 3:
            deg, min, sec = coords[0], coords[1], coords[2]
            return [convert_value(coordinate) for coordinate in [deg, min, sec] ]

    return deg, min, sec
