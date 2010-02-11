# encoding: utf-8
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009 Rob G. Healey <robhealey1@gmail.com>
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

#*************************************************************************************************
# Python Modules
#*************************************************************************************************
import os
import datetime, time, calendar

from gettext import gettext as gt
from gen.lib import Date

# import the pyexiv2 python library classes that we will be needing
try:
    import pyexiv2
except ImportError:
    pyexiv2msg = gt("The, pyexiv2, python binding library, to exiv2 is not installed on "
                    "this computer.\n  It can be downloaded either from your local repository "
                    "or from here\n")
    pyexiv2msg += "http://tilloy.net/dev/pyexiv2/"
    raise Exception(pyexiv2msg)

#-----------------------------------------------------------------------
# GTK modules
#-----------------------------------------------------------------------
import gtk

#------------------------------------------------------------------------
# GRAMPS modules
#------------------------------------------------------------------------
from PlaceUtils import conv_lat_lon

from gen.plug import Gramplet
import Utils
import GrampsLocale

from DateHandler import parser as _dp
from DateHandler import displayer as _dd

from TransUtils import get_addon_translator

_ = get_addon_translator(__file__).gettext

from QuestionDialog import ErrorDialog, OkDialog
#-----------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------
# first camera was created April 12, 1826
# http://wiki.answers.com/Q/What_date_was_the_camera_invented 
FIRST_DATE = datetime.datetime(1826, 4, 12, 16, 30, 00)

FIRST_DESCRIPTION = _("Enter text describing this image and who might be in the image.  "
                      "It might be best to enter a location for this image, especially "
                      "if there is no GPS Latitude/ Longitude information available.")
FIRST_GPS = "° " + "' " + '"'

_DATAMAP = [
    "Exif.Image.ImageDescription",
    "Exif.Image.DateTime",
    "Exif.Image.Artist",
    "Exif.Image.Copyright",
    "Exif.GPSInfo.GPSLatitudeRef",
    "Exif.GPSInfo.GPSLatitude",
    "Exif.GPSInfo.GPSLongitudeRef",
    "Exif.GPSInfo.GPSLongitude" ]

# set up exif keys for the image
ImageDescription =  "Exif.Image.ImageDescription"
ImageDateTime =     "Exif.Image.DateTime"
ImagePhotographer = "Exif.Image.Artist"
ImageCopyright =    "Exif.Image.Copyright"
ImageLatitudeRef =  "Exif.GPSInfo.GPSLatitudeRef"
ImageLatitude =     "Exif.GPSInfo.GPSLatitude"
ImageLongitudeRef = "Exif.GPSInfo.GPSLongitudeRef"
ImageLongitude =    "Exif.GPSInfo.GPSLongitude"

# Get Abbreviated Month names for the year
_ABBREV_MONTHS = []
_ABBREV_MONTHS.insert(0, "")
_ABBREV_MONTHS.extend(_dd.short_months[month]
    for month in range(1, 13)
    )

#------------------------------------------------------------------------
# Gramplet class
#------------------------------------------------------------------------
class imageMetadataGramplet(Gramplet):

    def init(self):
        """ sets up the variables, widgets, and data fields """
        
        self.exif_column_width = 15
        self.dirty = False
        self.exif_widgets = {}
        self.image_exif_Keys = []

        rows = gtk.VBox()
        for items in [
            ("Active image",  _("Active image"),      None, True,  [], False, 0),
            ("Photographer",  _("Photographer"),      None, False, [], True,  0),
            ("Select Date",   _("Select Date"),       None, True,  [("Select Date", "", self.select_date)], True, 0),
            ("Date",          _("Date"),              None, False, [], True,  0),
            ("Copyright",     _("Copyright"),         None, False, [], True,  0) ]:

            pos, text, choices, readonly, callback, dirty, default = items
            row = self.make_row(pos, text, choices, readonly, callback, dirty, default)
            rows.pack_start(row, False)

        # Latitude Degrees, Minutes, Seconds
        row = gtk.HBox()
        label = gtk.Label()
        label.set_text("<b>%s</b>" % _("Latitude"))
        label.set_use_markup(True)
        label.set_width_chars(10)
        row.pack_start(label, True)
        self.exif_widgets["Latitude"] = gtk.Entry()
        self.exif_widgets["Latitude"].set_width_chars(10)
        row.pack_start(self.exif_widgets["Latitude"], True)

        # Longitude Degrees, Minutes, Seconds
        label = gtk.Label()
        label.set_text("<b>%s</b>" % _("Longitude"))
        label.set_use_markup(True)
        label.set_width_chars(10)
        row.pack_start(label, True)
        self.exif_widgets["Longitude"] = gtk.Entry()
        self.exif_widgets["Longitude"].set_width_chars(10)
        row.pack_start(self.exif_widgets["Longitude"], True)
        rows.pack_start(row, True, True, 0)

        # Latitude Reference
        row = gtk.HBox()
        label = gtk.Label()
        label.set_text(_("Lat. Ref."))
        label.set_width_chars(12)
        row.pack_start(label, True)
        self.exif_widgets["LatitudeRef"] = gtk.Entry()
        self.exif_widgets["LatitudeRef"].set_width_chars(2)
        row.pack_start(self.exif_widgets["LatitudeRef"], True)

        # Longitude Reference
        label = gtk.Label()
        label.set_text(_("Long. Ref."))
        label.set_width_chars(12)
        row.pack_start(label, True)
        self.exif_widgets["LongitudeRef"] = gtk.Entry()
        self.exif_widgets["LongitudeRef"].set_width_chars(2)
        row.pack_start(self.exif_widgets["LongitudeRef"], True)
        rows.pack_start(row, True)

        # show separator before description textbox
        separator = gtk.HSeparator()
        rows.pack_start(separator, False)

        # description textbox label
        label = gtk.Label()
        label.set_text("<b><u>%s</u></b>" % _("Description"))
        label.set_use_markup(True)
        rows.pack_start(label, False)

        # description textbox
        description_box = gtk.TextView()
        description_box.set_wrap_mode(gtk.WRAP_WORD)
        description_box.set_editable(True)
        self.exif_widgets["Description"] = description_box.get_buffer()
        self.exif_widgets["Description"].set_text(FIRST_DESCRIPTION)
        rows.pack_start(description_box, True, True, 0)

        # set up tooltip information for the fields
        self.exif_widgets["Photographer"].set_tooltip_text(_("Enter the name of the person who took this image."))

        self.exif_widgets["Date"].set_tooltip_text(_("Press the Select Date Button to bring up a calendar "
                                                     "where you can choose a date.  Please add the time in "
                                                     "HH:MM:SS format too."))

        self.exif_widgets["Copyright"].set_tooltip_text(_("Enter the copyright information for the image.  "
                                                          "Example: (C) 2010 Smith and Wesson"))

        # Save, Clear, Re-Display
        row = gtk.HBox()
        button = gtk.Button(_("Save"))
        button.connect("clicked", self.write_image_metadata)
        row.pack_start(button, True)
        button = gtk.Button(_("Clear"))
        button.connect("clicked", self.clear_data_entry)
        row.pack_start(button, True)
        rows.pack_start(row, False)

        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(rows)
        rows.show_all()

        self.connect_signal("Media", self.media_changed)

    def media_changed(self, handle):
        """
        handles when an image has been changed

        @param: handle -- handle for the image in the database
        """

        # get media and pyexiv2 image
        self.media = self.dbstate.db.get_object_from_handle(handle)
        self.orig_image, self.image = self._get_image(self.media)

        # get metadata from image
        self.read_image_metadata(None)

        # update all widgets
        self.update_widgets()

    def main(self):
        """ gets media handle, media, pyexiv2.Image, and first values """

        pass

    def update_widgets(self):
        """
        update the image exif Metadata
        """
        if self.media is None:
            return

        # display image title/ description
        image_descr = self.media.get_description()
        if not image_descr:
            image_descr = self.media.get_path()
        self.exif_widgets["Active image"].show()
        self.exif_widgets["Active image"].set_text(image_descr)

        # read image metadata
        self.read_image_metadata(None)

    def make_row(self, pos, text, choices=None, readonly=False, callback_list=[], 
                 mark_dirty=False, default=0):
        """ creates the gtk row """

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
                row.pack_start(label, False)
                row.pack_start(self.exif_widgets[pos], True)
            else:
                eventBox = gtk.EventBox()
                self.exif_widgets[pos] = gtk.combo_box_new_text()
                eventBox.add(self.exif_widgets[pos])
                for add_type in choices:
                    self.exif_widgets[pos].append_text(add_type)
                self.exif_widgets[pos].set_active(default) 
                row.pack_start(label, False)
                row.pack_start(eventBox, True, True)
        for name, text, callback in callback_list:
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
        row.show_all()
        return row

    def mark_dirty(self, obj):
        self.dirty = True

    def edit_callback(self, person):
        self.dirty = False
        self.update()

    def str_to_date(self, str2date):
        """
        converts a date string to datetime.datetime

        @param: str2date -- a date string: will always bee in ISO format
        """
        if not str2date:
            return datetime.datetime.now()

        # return the date string to datetime.datetime format
        return datetime.datetime(*time.strptime(str2date, "%Y %b %d %H:%M:%S")[0:6])

    def date_to_str(self, date2str):
        """
        converts a datetime.datetime to string

        @param: date2str -- a datetime.datetime to string
        """
        if not date2str:
            return ""  

        dateType = date2str.__class__
        time = time.localtime()
        if dateType == datetime.datetime:
            date2str = "%04d %s %02d %02d:%02d:%02d" % (date2str.year, _ABBREV_MONTHS[date2str.month], date2str.day, 
                date2str.hour, date2str.minute, date2str.second)
        elif dateType == datetime.date:
            date2str = "%04d %s %02d %02d:%02d:%02d" % (date2str.year, _ABBREV_MONTHS[date2str.month], date2str.day,
            time[3], time[4], time[5])
        else:
            date2str = "%04d %s %02d %02d:%02d:%02d" % (date2str.year, _ABBREV_MONTHS[date2str.month], date2str.day,
                time[3], time[4], time[5])

        # return date as a string to its callers
        return date2str
 
    def set_value(self, key, KeyValue):
        """
        sets the value for the Exif keys

        @param: key      -- exif key
        @param: KeyValue -- value to be set
        """

        self.image[key] = KeyValue

    def write_image_metadata(self, obj):
        """
        saves the data fields to the image
        """

        # image is writable
        can_write = os.access(self.orig_image, os.W_OK)
        if can_write:

            # Image Description
            start = self.exif_widgets["Description"].get_start_iter()
            end = self.exif_widgets["Description"].get_end_iter()
            meta_descr = self.exif_widgets["Description"].get_text(start, end)
            if meta_descr:
                self.set_value(ImageDescription, meta_descr)

            # image Date/ Time
            self.set_value(ImageDateTime, self.exif_widgets["Date"].get_text() )

            # Image Photographer
            self.set_value(ImagePhotographer, self.exif_widgets["Photographer"].get_text() )

            # Image Copyright
            self.set_value(ImageCopyright, self.exif_widgets["Copyright"].get_text() )

            # GPS Latitude Reference
            latref = self.exif_widgets["LatitudeRef"].get_text()
            if latref:
                self.set_value(ImageLatitudeRef, latref)

            # GPS Latitude
            latitude = self.exif_widgets["Latitude"].get_text()
            if latitude:
                self.set_value(ImageLatitude, coords_to_rational(latitude) )

            # GPS Longitude Reference
            longref = self.exif_widgets["LongitudeRef"].get_text()
            if longref:
                self.set_value(ImageLongitudeRef, longref)

            # GPS Longitude
            longitude = self.exif_widgets["Longitude"].get_text()
            if longitude:
                self.set_value(ImageLongitude, coords_to_rational(longitude) )

            # write the metadata to the image
            self.image.writeMetadata()
            OkDialog(_("Image metadata has been saved."))  

        else:
            basename = os.path.basename(self.media)
            ErrorDialog(_("The image file %s does NOT have write access/ permissions. "
                          "If you have access and rights to change the permissions, "
                          "then please do it now." % basename))
            return None

    def clear_data_entry(self, obj):
        """ clears all data fields to nothing """

        # Description textBox()
        self.exif_widgets["Description"].set_text("")

        # Date/ Time
        self.exif_widgets["Date"].set_text("")

        # Photographer
        self.exif_widgets["Photographer"].set_text("")

        # Copyright
        self.exif_widgets["Copyright"].set_text("")

        # Latitude Reference
        self.exif_widgets["LatitudeRef"].set_text("")

        # Latitude 
        self.exif_widgets["Latitude"].set_text("")

        # Longitude Reference
        self.exif_widgets["LongitudeRef"].set_text("")

        # Longitude
        self.exif_widgets["Longitude"].set_text("")

    def _get_media(self, media_id):
        """ returns an image object from the database """

        if not media_id:
            return None 

        # ge media object from the database
        media = self.dbstate.db.get_object_from_gramps_id(media_id)

        # return the media object to its callers
        return media
    
    def _get_image(self, media_obj):
        """
        creates the pyexiv2 image based on media object
        """

        if not media_obj:
            return None, None

        # get full image path
        originalimage = Utils.media_path_full(self.dbstate.db, media_obj.get_path() )

        # get the pyexiv2 image file
        grampletimage = pyexiv2.Image(originalimage)

        # return originalimage and grampletimage to its callers
        return originalimage, grampletimage  

    def get_value(self, key):
        """
        gets the value from the Exif Key, and returns it...

        @param: key -- exif key
        """

        # return the key value to its caller
        return self.image[key]

    def read_image_metadata(self, obj):
        """
        reads the image metadata after the pyexiv2.Image has been created
        """

        # check to see if the image is on the computer or not?
        basename = os.path.basename(self.orig_image)
        if os.path.isfile(self.orig_image):

            # check to see if the image is readable
            can_read = os.access(self.orig_image, os.R_OK)
            if can_read:

                # read the image metadata
                self.image.readMetadata()

                # get the exif tags for this image
                exifKeyTags = self.image.exifKeys()
                ##################################################################
                # remove all exif keys if they are not in _DATAMAP
                exifKeyTags = [(keytag) for keytag in exifKeyTags
                                        if keytag in _DATAMAP]
                for keytag in exifKeyTags:

                    # Image description
                    if keytag == ImageDescription:
                        self.exif_widgets["Description"].set_text( self.get_value(keytag) )

                    # Image DateTime
                    elif keytag == ImageDateTime:
                        self.exif_widgets["Date"].set_text( self.get_value(keytag) )

                    # image Photographer
                    elif keytag == ImagePhotographer:
                        self.exif_widgets["Photographer"].set_text( self.get_value(keytag) )

                    # Image Copyright
                    elif keytag == ImageCopyright:
                        self.exif_widgets["Copyright"].set_text( self.get_value(keytag) )

                    # GPS Latitude Reference
                    elif keytag == ImageLatitudeRef:
                        self.exif_widgets["LatitudeRef"].set_text( self.get_value(keytag) ) 

                    # GPS Latitude
                    elif keytag == ImageLatitude:
                        latitude = self.get_value(keytag)
                        if latitude:
                            degrees, minutes, seconds = str(latitude[0]), str(latitude[1]), str(latitude[2])
                            degrees, rest = degrees.split("/", 1)
                            minutes, rest = minutes.split("/", 1)
                            seconds, rest = seconds.split("/", 1)
                            self.exif_widgets["Latitude"].set_text("%s %s %s" % (degrees, minutes, seconds))  

                    # GPS Longitude Reference
                    elif keytag == ImageLongitudeRef:
                        self.exif_widgets["LongitudeRef"].set_text( self.get_value(keytag) )

                    # GPS Longitude
                    elif keytag == ImageLongitude:
                        longitude = self.get_value(keytag)
                        if longitude:
                            degrees, minutes, seconds = str(longitude[0]), str(longitude[1]), str(longitude[2])
                            degrees, rest = degrees.split("/", 1)
                            minutes, rest = minutes.split("/", 1)
                            seconds, rest = seconds.split("/", 1)
                            self.exif_widgets["Longitude"].set_text("%s %s %s" % (degrees, minutes, seconds))  

            # image is not readable
            else:
                ErrorDialog(_("The image file %s does NOT have read access/ permissions. "
                              "If you have access and rights to change the permissions, "
                              "then please do it now." % basename))

        # image does not exists at all
        else:
            OkDialog(_("The image file is missing.  Please select another image or "
                       "edit the media object to fix this problem."))

    def select_date(self, obj):
        """
        will allow me to choose a date from the calendar widget
        """
 
        self.app = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.app.set_title(_("Select Date"))
        self.app.set_default_size(450, 200)
        self.app.set_border_width(5)
        self.exif_widgets["Calendar"] = gtk.Calendar()
        self.exif_widgets["Calendar"].connect('day-selected-double-click', self.double_click)
        self.app.add(self.exif_widgets["Calendar"])
        self.exif_widgets["Calendar"].show()
        self.app.show()

    def post_init(self):
        self.disconnect("active-changed")

    def double_click(self, obj):
        """ receives double-clicked and returns the selected date to "Date" widget """

        year, month, day = self.exif_widgets["Calendar"].get_date()
        image_date = "%04d %s %02d" % (year, _ABBREV_MONTHS[(month + 1)], day)
        self.exif_widgets["Date"].set_text(image_date)
        self.app.destroy()

    def _validate_coordinate(self, widget, text, typedeg):
        if (typedeg == 'lat') and not conv_lat_lon(text, "0", "ISO-D"):
            return ValidationError(_(u"Invalid latitude (syntax: 18\u00b09'") +
                                   _('48.21"S, -18.2412 or -18:9:48.21)'))
        elif (typedeg == 'lon') and not conv_lat_lon("0", text, "ISO-D"):
            return ValidationError(_(u"Invalid longitude (syntax: 18\u00b09'") +
                                   _('48.21"E, -18.2412 or -18:9:48.21)'))

def string_to_rational(Coordinate):
    """ convert string to rational variable for GPS """

    if '.' in Coordinate:
        value1, value2 = Coordinate.split('.')
        return pyexiv2.Rational(int(float(value1 + value2)), 10**len(value2))
    else:
        return pyexiv2.Rational(int(Coordinate), 1)

def coords_to_rational(Coordinates):
    """ returns the GPS Coordinates to Latitude/ Longitude """

    return [string_to_rational(coordinate) for coordinate in Coordinates.split(' ')]
