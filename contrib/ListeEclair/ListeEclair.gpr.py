register(REPORT,
id    = 'ListeEclair',
name  = _("Liste Eclair"),
description =  _("Produit une liste eclair"),
version = '1.0.2',
gramps_target_version = '3.4',
status = STABLE, # strange indentation, bug with pdf file format
fname = 'ListeEclair.py',
authors = ["Eric Doutreleau"],
authors_email = ["eric@doutreleau.fr"],
category = CATEGORY_TEXT,
require_active = False,
reportclass = 'ListeEclairReport',
optionclass = 'ListeEclairOptions',
report_modes = [REPORT_MODE_GUI, REPORT_MODE_CLI]
)
