#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2014       Nick Hall
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""Tools/Database Processing/Check for broken place links"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

from gramps.gui.plug import tool
from gramps.gen.db import DbTxn

#-------------------------------------------------------------------------
#
# PlaceDebug
#
#-------------------------------------------------------------------------
class PlaceDebug(tool.BatchTool):

    def __init__(self, dbstate, user, options_class, name, callback=None):
        self.user = user
        tool.BatchTool.__init__(self, dbstate, user, options_class, name)

        if not self.fail:
            self.run()

    def run(self):
        """
        Perform the actual check for broken links.
        """
        broken_links = []
        for event in self.db.iter_events():
            handle = event.get_place_handle()
            if handle:
                place = self.db.get_place_from_handle(handle)
                if place is None:
                    # Broken link
                    broken_links.append((event.get_gramps_id(), handle))
        
        for place in self.db.iter_places():
            for placeref in place.get_placeref_list():
                handle = placeref.ref
                if handle:
                    place = self.db.get_place_from_handle(handle)
                    if place is None:
                        # Broken link
                        broken_links.append((place.get_gramps_id(), handle))
                else:
                    # Every placeref should have a valid handle
                    broken_links.append((place.get_gramps_id(), handle))
        
        links = ''
        for link in broken_links:
            links += link[0] + ' -> ' + link[1] + '\n'
        
        if links:
            self.user.info(_('Broken links'), links)
        else:
            self.user.info(_('Broken links'), _('No broken links found'))


#------------------------------------------------------------------------
#
# PlaceDebugOptions
#
#------------------------------------------------------------------------
class PlaceDebugOptions(tool.ToolOptions):
    """
    Define options and provides handling interface.
    """

    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)
