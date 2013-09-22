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
         version = '0.0.8',
         gramps_target_version = "3.4",
         include_in_listing = False,
         height = 400,
         gramplet = "bckGramplet",
         fname ="bck.py",
         gramplet_title =_("bck"),
         )
