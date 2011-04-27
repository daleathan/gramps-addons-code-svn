register(IMPORT,
         id    = 'im_sqlite',
         name  = _('SQLite Import'),
         description =  _('SQLite is a common local database format'),
         version = '1.0.8',
         gramps_target_version = "3.3",
         status = STABLE,
         fname = 'ImportSql.py',
         import_function = 'importData',
         extension = "sql"
)

register(EXPORT,
         id    = 'ex_sqlite',
         name  = _('SQLite Export'),
         description =  _('SQLite is a common local database format'),
         version = '1.0.7',
         gramps_target_version = "3.3",
         status = STABLE,
         fname = 'ExportSql.py',
         export_function = 'exportData',
         extension = "sql",
         export_options = 'WriterOptionBox'
)
