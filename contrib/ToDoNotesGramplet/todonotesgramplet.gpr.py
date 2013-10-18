#------------------------------------------------------------------------
#
# Register Gramplet
#
#------------------------------------------------------------------------
register(GRAMPLET, 
         id="TODO2", 
         name=_("TODO2"), 
         description = _("Gramplet for generic notes"),
         #data =[''],
         status = STABLE,
         fname="todonotesgramplet.py",
         height=300,
         expand=True,
         gramplet = 'TODONotesGramplet',
         gramplet_title=_("TODO List"),
         version = '0.0.3',
         gramps_target_version="3.4",
         )
