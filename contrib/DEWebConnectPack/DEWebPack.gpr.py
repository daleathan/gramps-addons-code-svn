#------------------------------------------------------------------------
#
# Register the Addon
#
#------------------------------------------------------------------------

register(GENERAL,
         category="WebConnect",
         id="DE Web Connect Pack",
         name=_("DE Web Connect Pack"),
         description = _("Collection of Web sites for the DE (requires libwebconnect)"),
         status = UNSTABLE, # unicode issue with python 3
         version = '0.0.9',
         gramps_target_version = "4.0",
         fname="DEWebPack.py",
         load_on_reg = True,
         depends_on = ["libwebconnect"]
         )

