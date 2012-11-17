register(VIEW, 
         id    = 'graphview',
         name  = _("Graph View"),
         category = ("Ancestry", _("Ancestry")),
         description =  _("Dynamic graph of relations"),
         version = '1.0.30',
         gramps_target_version = '4.0',
         status = STABLE,
         fname = 'graphview.py',
         authors = [u"Gary Burton"],
         authors_email = ["gary.burton@zen.co.uk"],
         viewclass = 'GraphView',
  )
