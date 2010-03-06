sidebar_list = ["RelationshipView", 
                "EventView", 
                "FamilyView",
                "FanChartView",
                "GeoView",
                "HtmlView",
                "MediaView",
                "NoteView",
                "PedigreeView",
                "PedigreeViewExt",
                "PersonListView",
                "PersonTreeView",
                "PlaceListView",
                "PlaceTreeView",
                "RepositoryView",
                "SourceView"]

for name in sidebar_list:
    register(VIEW, 
             id    = '%sSidebar' % name,
             name  = _("%s Sidebar") % _(name),
             category = ("Splitviews", _("Splitviews")),
             description =  _("View with a Gramplet Sidebar"),
             version = '1.1',
             gramps_target_version = '3.2',
             status = STABLE,
             fname = 'sidebarviews.py',
             authors = [u"Doug Blank"],
             authors_email = ["doug.blank@gmail.com"],
             viewclass = '%sSidebar' % name,
      )
