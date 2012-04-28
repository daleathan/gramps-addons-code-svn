#------------------------------------------------------------------------
#
# Register the report
#
#------------------------------------------------------------------------

register(QUICKREPORT, 
         id    = 'timelinequickview',
         name  = _("Timeline"),
         description= _("Display a person's events on a timeline"),
         version = '1.0.9',
         gramps_target_version = '3.5',
         status = STABLE,
         fname = 'TimelineQuickview.py',
         authors = ["Douglas Blank"],
         authors_email = ["dblank@cs.brynmawr.edu"],
         category = CATEGORY_QR_PERSON,
         runfunc = 'run',
  )
