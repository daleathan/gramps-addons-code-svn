#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013 Nick Hall
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

"""
AllCensus Gramplet.
"""
#------------------------------------------------------------------------
#
# GTK modules
#
#------------------------------------------------------------------------
import gtk

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gen.plug import Gramplet
from gui.dbguielement import DbGUIElement
import DateHandler
import Errors
import gen.lib
from Census import get_census_citation
from CensusGramplet import CensusEditor

#------------------------------------------------------------------------
#
# Internationalisation
#
#------------------------------------------------------------------------
from TransUtils import get_addon_translator
_ = get_addon_translator(__file__).ugettext

#------------------------------------------------------------------------
#
# AllCensus class
#
#------------------------------------------------------------------------
class AllCensus(Gramplet, DbGUIElement):
    """
    Gramplet to display census events for the active person.
    It allows a census to be created or edited with a census editor.
    """
    def __init__(self, gui, nav_group=0):
        Gramplet.__init__(self, gui, nav_group)
        DbGUIElement.__init__(self, self.dbstate.db)

    def init(self):
        """
        Initialise the gramplet.
        """
        root = self.__create_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(root)
        root.show_all()

    def _connect_db_signals(self):
        """
        called on init of DbGUIElement, connect to db as required.
        """
        self.callman.register_callbacks({'event-update': self.changed})
        self.callman.connect_all(keys=['event'])
    
    def changed(self, handle):
        """
        Called when a registered event is updated.
        """
        self.update()

    def __create_gui(self):
        """
        Create and display the GUI components of the gramplet.
        """
        vbox = gtk.VBox()

        self.model = gtk.ListStore(object, str, str, str)
        view = gtk.TreeView(self.model)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Source"), renderer, text=1)
        view.append_column(column)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Date"), renderer, text=2)
        view.append_column(column)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Place"), renderer, text=3)
        view.append_column(column)
        view.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        view.connect("button_press_event", self.__list_clicked)
        
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.BUTTONBOX_START)
        
        new = gtk.Button(stock=gtk.STOCK_NEW)
        new.connect("clicked", self.__new_census)
        button_box.add(new)
                
        edit = gtk.Button(stock=gtk.STOCK_EDIT)
        edit.connect("clicked", self.__edit_census, view.get_selection())
        button_box.add(edit)
      
        vbox.pack_start(view, expand=True, fill=True)
        vbox.pack_end(button_box, expand=False, fill=True, padding=4)
        
        return vbox

    def __list_clicked(self, view, event):
        """
        Called when the user clicks on the list of censuses.
        """
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.__edit_census(view, view.get_selection())

    def __new_census(self, widget):
        """
        Create a new census and invoke the editor.
        """
        event = gen.lib.Event()
        event.set_type(gen.lib.EventType.CENSUS)
        try:
            CensusEditor(self.gui.dbstate, self.gui.uistate, [], event)
        except Errors.WindowActiveError:
            pass

    def __edit_census(self, widget, selection):
        """
        Edit the selected census.
        """
        model, iter_ = selection.get_selected()
        if iter_:
            event = model.get_value(iter_, 0)
            try:
                CensusEditor(self.gui.dbstate, self.gui.uistate, [], event)
            except Errors.WindowActiveError:
                pass

    def main(self):
        """
        Called to update the display.
        """
        self.model.clear()
        self.callman.unregister_all()

        db = self.dbstate.db
        for handle in db.get_event_handles():
            event = db.get_event_from_handle(handle)

            if event.get_type() == gen.lib.EventType.CENSUS:
                self.callman.register_handles({'event': [handle]})

                p_handle = event.get_place_handle()
                if p_handle:
                    place = db.get_place_from_handle(p_handle)
                    place_text = place.get_display_info()[0]
                else:
                    place_text = ''
                    
                citation = get_census_citation(db, event)
                if citation:
                    source_handle = citation.get_reference_handle()
                    source = db.get_source_from_handle(source_handle)
                    source_text = source.get_title()
                    self.model.append((event,
                                      source_text,
                                      DateHandler.get_date(event),
                                      place_text))

    def db_changed(self):
        """
        Called when the database is changed.
        """
        self.update()
