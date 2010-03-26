register(REPORT,
    id = 'FamilyTree',
    name = _('Family Tree'),
    description = _('Produces a graphical family tree.'),
    version = '3.1.3',
    gramps_target_version = '3.2',
    status = STABLE,
    fname = 'FamilyTree.py',
    reportclass = 'FamilyTree',
    optionclass = 'FamilyTreeOptions',
    authors = ['Reinhard Mueller'],
    authors_email = ['reinhard.mueller@bytewise.at'],
    category = CATEGORY_DRAW,
    report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
    )
