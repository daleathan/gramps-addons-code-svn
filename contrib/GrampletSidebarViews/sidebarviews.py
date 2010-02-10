import gtk

from relview import RelationshipView
from eventview import EventView
from familyview import FamilyView
from fanchartview import FanChartView
from geoview import GeoView
from htmlrenderer import HtmlView
from mediaview import MediaView
from noteview import NoteView
from pedigreeview import PedigreeView
from pedigreeviewext import PedigreeViewExt
from personlistview import PersonListView
from persontreeview import PersonTreeView
from placelistview import PlaceListView
from placetreeview import PlaceTreeView
from repoview import RepositoryView
from sourceview import SourceView

from gui.widgets.grampletpane import GrampletPane

def extend(class_):
    class SidebarView(class_):
        def on_delete(self):
            super(SidebarView, self).on_delete()
            self.gramplet_pane.on_delete()

        def build_widget(self):
            container = super(SidebarView, self).build_widget()
            widget = gtk.HPaned()
            self.gramplet_pane = \
                GrampletPane("%s_%s" % (self.navigation_type(), self.__class__.__name__), 
                             self, self.dbstate, self.uistate, 
                             column_count=1,
                             default_gramplets=["Attributes Gramplet"])
            widget.pack1(container, resize=True, shrink=True)
            widget.pack2(self.gramplet_pane, resize=True, shrink=True)
            widget.set_position(self.gramplet_pane.pane_position)
            widget.connect("notify", self.move_handle)
            return widget

        def move_handle(self, widget, notify_type):
            if notify_type.name == "position-set":
                self.gramplet_pane.pane_position = widget.get_position()

        def ui_definition(self):
            uid = super(SidebarView, self).ui_definition()
            this_uid = """            
                <menuitem action="AddGramplet"/>
                <menuitem action="RestoreGramplet"/>
                <separator/>
                """
            if "</popup>" in uid:
                uid = uid.replace("</popup>", this_uid + "</popup>")
            elif "</ui>" in uid:
                uid = uid.replace("</ui>", """<popup name="Popup">%s</popup></ui>""" % this_uid)
            else:
                uid = """<ui><popup name="Popup">%s</popup></ui>""" % this_uid
            return uid

        def define_actions(self):
            super(SidebarView, self).define_actions()
            self._add_action("AddGramplet", None, _("Add a gramplet"))
            self._add_action("RestoreGramplet", None, _("Restore a gramplet"))

        def set_inactive(self):
            super(SidebarView, self).set_inactive()
            self.gramplet_pane.set_inactive()

        def set_active(self):
            super(SidebarView, self).set_active()
            self.gramplet_pane.set_active()

        #def can_configure(self):
        #    """
        #    See :class:`~gui.views.pageview.PageView 
        #    :return: bool
        #    """
        #    self._config = self.gramplet_pane._config
        #    return super(SidebarView, self).can_configure() or self.gramplet_pane.can_configure()

        #def _get_configure_page_funcs(self):
        #    """
        #    Return a list of functions that create gtk elements to use in the 
        #    notebook pages of the Configure dialog
        #    
        #    :return: list of functions
        #    """
        #    return super(SidebarView, self)._get_configure_page_funcs() + self.gramplet_pane._get_configure_page_funcs()

    return SidebarView

class RelationshipViewSidebar(extend(RelationshipView)):
    """
    """

class EventViewSidebar(extend(EventView)):
    """
    EventView with Gramplet Sidebar.
    """

class FamilyViewSidebar(extend(FamilyView)):
    """
    FamilyView with Gramplet Sidebar.
    """

class FanChartViewSidebar(extend(FanChartView)):
    """
    FanChartView with Gramplet Sidebar.
    """

class GeoViewSidebar(extend(GeoView)):
    """
    GeoView with Gramplet Sidebar.
    """

class HtmlViewSidebar(extend(HtmlView)):
    """
    HtmlView with Gramplet Sidebar.
    """

class MediaViewSidebar(extend(MediaView)):
    """
    MediaView with Gramplet Sidebar.
    """

class NoteViewSidebar(extend(NoteView)):
    """
    NoteView with Gramplet Sidebar.
    """

class PedigreeViewSidebar(extend(PedigreeView)):
    """
    PedigreeView with Gramplet Sidebar.
    """

class PedigreeViewExtSidebar(extend(PedigreeViewExt)):
    """
    PedigreeViewext with Gramplet Sidebar.
    """

class PersonListViewSidebar(extend(PersonListView)):
    """
    PersonlistView with Gramplet Sidebar.
    """

class PersonTreeViewSidebar(extend(PersonTreeView)):
    """
    PersontreeView with Gramplet Sidebar.
    """

class PlaceListViewSidebar(extend(PlaceListView)):
    """
    PlacelistView with Gramplet Sidebar.
    """

class PlaceTreeViewSidebar(extend(PlaceTreeView)):
    """
    PlacetreeView with Gramplet Sidebar.
    """

class RepositoryViewSidebar(extend(RepositoryView)):
    """
    RepoView with Gramplet Sidebar.
    """

class SourceViewSidebar(extend(SourceView)):
    """
    SourceView with Gramplet Sidebar.
    """

