#-------------------------------------------------------------------------
#
# register_report
#
#-------------------------------------------------------------------------
register(REPORT,
  id    = 'AncestorFill',
  name  = _("AncestorFill"),
  description =  _("Report on the filling of the tree"),
  version = '1.0.1',
  gramps_target_version = '3.4',
  status = STABLE,
  fname = 'AncestorFill.py',
  authors = ["Eric Doutreleau"],
  authors_email = ["eric@doutreleau.fr"],
  category = CATEGORY_TEXT,
  require_active = False,
  reportclass = 'AncestorFillReport',
  optionclass = 'AncestorFillOptions',
  report_modes = [REPORT_MODE_GUI, REPORT_MODE_CLI],
)
