#------------------------------------------------------------------------
#
# Register the Gramplet
#
#------------------------------------------------------------------------

register(GRAMPLET,
id="lxml Gramplet",
name=_("lxml Gramplet"),
description = _("Gramplet for testing lxml and XSLT"),
status = STABLE,
version = '0.3.6',
gramps_target_version = "4.0",
include_in_listing = False,
height = 300,
gramplet = "lxmlGramplet",
fname ="lxmlGramplet.py",
gramplet_title =_("lxml"),
)
