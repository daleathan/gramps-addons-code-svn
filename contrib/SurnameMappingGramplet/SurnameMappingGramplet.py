#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013  Artem Glebov <artem.glebov@gmail.com>
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

# $Id:  $

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import sgettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from gen.plug import Gramplet

#-------------------------------------------------------------------------
#
# SurnameMappingGramplet
#
#-------------------------------------------------------------------------

class SurnameMappingGramplet(Gramplet):

    def init(self):
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

        #button_panel = gtk.Toolbar()

        #self.button_add = button_panel.insert_stock(gtk.STOCK_ADD, "Add Mapping", None, self.add_mapping_clicked, None, -1)
        #self.button_del = button_panel.insert_stock(gtk.STOCK_REMOVE, "Remove Mapping", None, self.remove_mapping_clicked, None, -1)
        #self.button_edit = button_panel.insert_stock(gtk.STOCK_EDIT, "Edit Mapping", None, self.edit_mapping_clicked, None, -1)

        #vbox.pack_start(button_panel, expand=False, fill=True, padding=5)

        self.treestore = gtk.TreeStore(str, str)

        self.treeview = gtk.TreeView(self.treestore)
        self.column1 = gtk.TreeViewColumn('Surname')
        self.column2 = gtk.TreeViewColumn('Group Name')
        self.treeview.append_column(self.column1)
        self.treeview.append_column(self.column2)

        self.cell1 = gtk.CellRendererText()
        self.cell2 = gtk.CellRendererText()
        self.column1.pack_start(self.cell1, True)
        self.column1.add_attribute(self.cell1, 'text', 0)
        self.column2.pack_start(self.cell2, True)
        self.column2.add_attribute(self.cell2, 'text', 1)

        self.treeview.set_search_column(0)
        self.column1.set_sort_column_id(0)
        self.column2.set_sort_column_id(1)

        vbox.pack_start(self.treeview, expand=True, fill=True)

        return vbox

    def db_changed(self):
        pass

    def main(self):
        self.treestore.clear()
        keys = self.dbstate.db.get_name_group_keys()
        for key in keys:
            group_name = self.dbstate.db.get_name_group_mapping(key)
            #print("{0} -> {1}".format(key, group_name))
            self.treestore.append(None, (key, group_name))

    def add_mapping_clicked(self, event):
        pass

    def remove_mapping_clicked(self, event):
        pass

    def edit_mapping_clicked(self, event):
        pass
