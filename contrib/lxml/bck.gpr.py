#------------------------------------------------------------------------
#
# Register the Gramplet
#
#------------------------------------------------------------------------

register(GRAMPLET, 
         id="bck Gramplet", 
         name=_("bck Gramplet"), 
         description = _("Gramplet for listing some data via backup files"),
         status = STABLE,
         version = '0.1.1',
         gramps_target_version = "3.4",
         include_in_listing = False,
         height = 400,
         gramplet = "bckGramplet",
         fname ="bck.py",
         gramplet_title =_("bck"),
         )
register(GRAMPLET, 
         id="diff",
         name=_("diff"), 
         description = _("Backported modules from Doug's implementation"),
         status = STABLE,
         version = '0.0.2',
         gramps_target_version = "3.4",
         include_in_listing = False,
         height = 400,
         gramplet = "diff",
         fname ="diff.py",
         gramplet_title =_("diff"),
         )
register(GRAMPLET, 
         id="dictionary", 
         name=_("dictionary"), 
         description = _("Backported modules from Doug's implementation"),
         status = STABLE,
         version = '0.0.2',
         gramps_target_version = "3.4",
         include_in_listing = False,
         height = 400,
         gramplet = "dictionary",
         fname ="dictionary.py",
         gramplet_title =_("dictionary"),
         )
