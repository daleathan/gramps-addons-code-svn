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
         status = STABLE,
         version = '0.0.16',
         gramps_target_version = "4.2",
         fname="DEWebPack.py",
         load_on_reg = True,
         depends_on = ["libwebconnect"]
         )

