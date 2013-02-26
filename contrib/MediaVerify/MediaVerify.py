#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013      Nick Hall
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

"""Tools/Utilities/Media Verify"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import os
import hashlib

#-------------------------------------------------------------------------
#
# Gtk modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gui.plug import tool
from gui.utils import ProgressMeter
from gen.db import DbTxn
from gen.lib import Attribute, AttributeType
import ManagedWindow
import Utils

#-------------------------------------------------------------------------
#
# Media Verify
#
#-------------------------------------------------------------------------
class MediaVerify(tool.Tool, ManagedWindow.ManagedWindow):
    def __init__(self, dbstate, uistate, options_class, name, callback=None):

        tool.Tool.__init__(self, dbstate, options_class, name)

        self.window_name = _('Media Verify Tool')
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)

        self.db = dbstate.db
        self.moved_files = []

        window = gtk.Window()
        vbox = gtk.VBox()
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.view = gtk.TreeView()
        column = gtk.TreeViewColumn(_('Files'))
        self.view.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        self.model = gtk.TreeStore(str)
        self.view.set_model(self.model)
        scrolled_window.add(self.view)
        vbox.pack_start(scrolled_window, True, True, 5)
        bbox = gtk.HButtonBox()
        vbox.pack_start(bbox, False, False, 5)
        close = gtk.Button(_('Close'))
        close.set_tooltip_text(_('Close the Media Verify Tool'))
        close.connect('clicked', self.close)
        generate = gtk.Button(_('Generate'))
        generate.set_tooltip_text(_('Generate md5 hashes for media objects'))
        generate.connect('clicked', self.generate_md5)
        verify = gtk.Button(_('Verify'))
        verify.set_tooltip_text(_('Check media paths and report missing, '
                                  'duplicate and extra files'))
        verify.connect('clicked', self.verify_media)
        fix = gtk.Button(_('Fix'))
        fix.set_tooltip_text(_('Fix media paths of moved and renamed files'))
        fix.connect('clicked', self.fix_media)
        bbox.add(close)
        bbox.add(generate)
        bbox.add(verify)
        bbox.add(fix)
        vbox.show_all()

        window.add(vbox)
        window.set_size_request(500, 300)
        self.set_window(window, None, self.window_name)
        self.show()

    def build_menu_names(self, obj):
        return (_('Verify Gramps media using md5 hashes'), 
                self.window_name)

    def generate_md5(self, button):
        """
        Generate md5 hashes for media files and attach them as attributes to
        media objects.
        """
        progress = ProgressMeter(_('Media Verify'), can_cancel=True)

        length = self.db.get_number_of_media_objects()
        progress.set_pass(_('Generating media hashes'), length)

        with DbTxn(_("Set media hashes"), self.db, batch=True) as trans:

            for handle in self.db.get_media_object_handles():
                media = self.db.get_object_from_handle(handle)

                full_path = Utils.media_path_full(self.db, media.get_path())
                try:
                    media_file = open(full_path, 'r')
                except IOError:
                    progress.step()
                    continue
                md5sum = hashlib.md5(media_file.read()).hexdigest()
                media_file.close()

                for attr in media.get_attribute_list():
                    if str(attr.get_type()) == 'md5':
                        media.remove_attribute(attr)
                        break

                attr = Attribute()
                attr.set_type(AttributeType('md5'))
                attr.set_value(md5sum)

                media.add_attribute(attr)
                
                self.db.commit_media_object(media, trans)

                progress.step()
                if progress.get_cancelled():
                    break

        progress.close()

    def verify_media(self, button):
        """
        Verify media objects have the correct path to files in the media
        directory.  List missing files, duplicate files, and files that do not
        yet have a media file in Gramps.
        """
        self.model.clear()
        self.moved_files = []

        moved = self.model.append(None, (_('Moved Files'),))
        missing = self.model.append(None, (_('Missing Files'),))
        duplicate = self.model.append(None, (_('Duplicate Files'),))
        extra = self.model.append(None, (_('Extra Files'),))

        media_path = self.db.get_mediapath()
        if media_path is None:
            return

        progress = ProgressMeter(_('Media Verify'), can_cancel=True)
            
        length = self.db.get_number_of_media_objects()
        progress.set_pass(_('Finding files'), length)

        all_files = {}
        for root, dirs, files in os.walk(media_path):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                media_file = open(full_path, 'r')
                md5sum = hashlib.md5(media_file.read()).hexdigest()
                media_file.close()

                rel_path = Utils.relative_path(full_path, media_path)
                if md5sum in all_files:
                    all_files[md5sum].append(rel_path)
                else:
                    all_files[md5sum] = [rel_path]

                progress.step()
                if progress.get_cancelled():
                    break

        progress.set_pass(_('Checking paths'), length)

        in_gramps = []
        for handle in self.db.get_media_object_handles():
            media = self.db.get_object_from_handle(handle)

            md5sum = None
            for attr in media.get_attribute_list():
                if str(attr.get_type()) == 'md5':
                    md5sum = attr.get_value()
                    in_gramps.append(md5sum)
                    break

            # Fix the path if possible
            gramps_path = media.get_path()
            if md5sum in all_files:
                file_path = all_files[md5sum]
                if gramps_path not in file_path:
                    if len(file_path) == 1:
                        self.moved_files.append((handle, file_path[0]))
                        text = '%s -> %s' % (gramps_path, file_path[0])
                        self.model.append(moved, (text,))
                    else:
                        gramps_name = os.path.basename(gramps_path)
                        for path in file_path:
                            if os.path.basename(path) == gramps_name:
                                self.moved_files.append((handle, path))
                                text = '%s -> %s' % (gramps_path, path)
                                self.model.append(moved, (text,))
            else:
                self.model.append(missing, (gramps_path,))

            progress.step()
            if progress.get_cancelled():
                break

        # Duplicate files or files not in Gramps
        for md5sum in all_files:
            if len(all_files[md5sum]) > 1:
                text = ', '.join(all_files[md5sum])
                self.model.append(duplicate, (text,))
            if md5sum not in in_gramps:
                text = ', '.join(all_files[md5sum])
                self.model.append(extra, (text,))

        progress.close()
        self.view.expand_all()

    def fix_media(self, button):
        """
        Fix paths to moved media files.
        """
        progress = ProgressMeter(_('Media Verify'), can_cancel=True)
        progress.set_pass(_('Fixing file paths'), len(self.moved_files))

        with DbTxn(_("Fix media paths"), self.db, batch=True) as trans:
            
            for handle, new_path in self.moved_files:
                media = self.db.get_object_from_handle(handle)
                media.set_path(new_path)
                self.db.commit_media_object(media, trans)

                progress.step()
                if progress.get_cancelled():
                    break

        progress.close()

#------------------------------------------------------------------------
#
# Media Verify Options
#
#------------------------------------------------------------------------
class MediaVerifyOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """
    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)
