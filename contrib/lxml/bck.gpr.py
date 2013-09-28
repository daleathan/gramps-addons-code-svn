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
         version = '0.3.0',
         gramps_target_version = "3.4",
         include_in_listing = False,
         height = 400,
         gramplet = "bckGramplet",
         fname ="bck.py",
         gramplet_title =_("bck"),
         )
register(GENERAL, 
         id="diff",
         name=_("diff"), 
         description = _("Backported modules from Doug's implementation"),
         status = STABLE,
         version = '0.0.2',
         gramps_target_version = "3.4",
         include_in_listing = False,
         fname ="diff.py",
         load_on_reg = True,
         )
register(GENERAL, 
         id="dictionary", 
         name=_("dictionary"), 
         description = _("Backported modules from Doug's implementation"),
         status = STABLE,
         version = '0.0.3',
         gramps_target_version = "3.4",
         include_in_listing = False,
         fname ="dictionary.py",
         load_on_reg = True,
         )
