#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2015       Tim G L Lyons
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

# $Id$

"""Tools/Utilities/Download Media"""

#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
import os
import logging
LOG = logging.getLogger(".downloadmedia")
from urllib import urlopen
from urlparse import urlparse
import re

#-------------------------------------------------------------------------
#
# gnome/gtk
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from gui.utils import ProgressMeter
from gui.plug import tool
from QuestionDialog import OkDialog
import ManagedWindow
import gen.lib
from gen.db import DbTxn
from Utils import media_path_full
from gen.ggettext import sgettext as _
from const import USER_HOME
import gen.mime
import Utils

class DownloadMedia(tool.Tool, ManagedWindow.ManagedWindow):
    """
    Gramplet that downloads media from the internet.
    """
    
    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        self.label = _('Download media')
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.set_window(gtk.Window(), gtk.Label(), '')
        tool.Tool.__init__(self, dbstate, options_class, name)
        
        self.num_downloads = 0
        dialog = self.display()
        response = dialog.run()
        dialog.destroy()
        
        if response == gtk.RESPONSE_ACCEPT:
            self.on_ok_clicked()
            OkDialog(_('Media downloaded'),
                     _("%d media files downloaded") % self.num_downloads)

        self.close()

    def display(self):
        """
        Constructs the GUI, consisting of a message, and fields to enter the
        name and password (commented out for now)
        """


        # GUI setup:
        dialog = gtk.Dialog(_("Download media tool"),
                                self.uistate.window,
                                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                 gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        label = gtk.Label(_("Make sure you are connected to the internet "
                            "before starting this tool."))
        label.set_line_wrap(True)
        vbox = gtk.VBox()
        vbox.pack_start(label, True)

#        hbox1 = gtk.HBox()
#        label_name = gtk.Label(_("Name") + ":")
#        self.name_entry = gtk.Entry()
#        self.name_entry.set_text("%s" % name)
#        hbox1.pack_start(label_name, False)
#        hbox1.pack_start(self.name_entry, True)
#        vbox.pack_start(hbox1, False)
#
#        hbox2 = gtk.HBox()
#        label_password = gtk.Label(_("Password") + ":")
#        self.password_entry = gtk.Entry()
#        self.password_entry.set_text("%s" % password)
#        hbox2.pack_start(label_password, False)
#        hbox2.pack_start(self.password_entry, True)
#        vbox.pack_start(hbox2, False)
        
        dialog.vbox.set_spacing(10)
        dialog.vbox.pack_start(vbox)
        dialog.show_all()
        return dialog
    
    def on_ok_clicked(self):
        """
        Method that is run when you click the OK button.
        """
        downloaded = {}
        
        # Get a directory to put the media files in. If the media path in
        # preferences is not just the user's home, then we will use that. If it
        # is the user's home, we create a new directory below that, so we don't
        # splatter files into home.
        media_path = self.db.get_mediapath()
        if media_path == USER_HOME or media_path == "" or media_path == None:
            media_path = os.path.join(USER_HOME, "mediadir")
        if not os.path.isdir(media_path):
            os.makedirs(media_path)
        
        # Many thanks to 'sirex' from whom I have taken the code he submitted as
        # part of bug 0003553: Import media files from GEDCOM
        file_pattern = re.compile(r'.*\.(png|jpg|jpeg|gif)$')
        
        def fetch_file(url, filename):
            LOG.debug("Downloading url %s to file %s" % (url, filename))
            fr = urlopen(url)
            fw = open(filename, 'wb')
            for block in fr:
                fw.write(block)
            fw.close()
            fr.close()

        self.progress = ProgressMeter(
            _('Downloading files'), '')
        self.progress.set_pass(_('Downloading files'),
                               self.db.get_number_of_media_objects())
        
        self.db.disable_signals()
        with DbTxn('Download files', self.db) as trans:
            for media_handle in self.db.media_map.keys():
                media = self.db.get_object_from_handle(media_handle)
                url = media.get_path()
                res = urlparse(url)
                LOG.debug(res)
                if res.scheme == "http" or res.scheme == "https":
                    if file_pattern.match(url):
                        if url in downloaded:
                            full_path = downloaded[url]
                        else:
                            filename = url.split('/')[-1]
                            full_path = os.path.join(media_path, filename)
                            fetch_file(url, full_path)
                            downloaded[url] = full_path
                            self.num_downloads += 1
                        media.set_path(full_path)
                        media.set_mime_type(gen.mime.get_type(
                                                Utils.find_file(full_path)))
                        self.db.commit_media_object(media, trans)
                
                self.progress.step()
            
        self.db.enable_signals()
        self.db.request_rebuild()
        self.progress.close()
        
#        self.options.handler.options_dict['name'] = name
#        self.options.handler.options_dict['password'] = password
#        # Save options
#        self.options.handler.save_options()

class DownloadMediaOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)

        # Options specific for this report
        self.options_dict = {
            'name'   : 2,
            'password' : 2,
        }
        self.options_help = {
            'name'   : ("=num", 
                           "Name to login to website", 
                           "?string?"),
            'password' : ("=num",
                           "Password to log in to website",
                           "Integer number")
            }
