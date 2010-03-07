#
# Gramps - a GTK+/GNOME based genealogy program
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# Useful in very special case : user wants to know where data are stored !
# Instead use Filter sidebar and Family Trees -> Export screen functions

"""Individuals with locations"""

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from TransUtils import get_addon_translator
from ReportBase import Report, ReportUtils, MenuReportOptions, CATEGORY_TEXT
from gen.display.name import displayer as name_displayer
from gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle, 
                             FONT_SANS_SERIF, FONT_SERIF, 
                             INDEX_TYPE_TOC, PARA_ALIGN_CENTER)
from Filters import GenericFilterFactory, Rules

_ = get_addon_translator(__file__).ugettext

#------------------------------------------------------------------------
#
# LocationsReport
#
#------------------------------------------------------------------------
class LocationsReport(Report):
    """
    Individuals with locations
    """
    def __init__(self, database, options_class):
        """
        Create the object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options_class   - instance of the Options class for this report
        """
        Report.__init__(self, database, options_class)
        self.__db = database

    def write_report(self):
        """
        The routine the actually creates the report. At this point, the document
        is opened and ready for writing.
        """
        # Write the title line. Set in INDEX marker so that this section will be
        # identified as a major category if this is included in a Book report.

        self.doc.start_paragraph("Loc-Title")
        title = _("Locations")
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        self.write_pcensus()
        self.write_presidence()
        self.write_fcensus()
        self.write_fresidence()
        self.write_address()

    def write_pcensus(self):
        """
        The routine creates the census event paragraph for individuals.
        Using existing filter rule.
        """
        filter_class = GenericFilterFactory('Person')
        filter = filter_class()
        # see number of arguments on Filters/Rules/Person/_HasEvent.py
        filter.add_rule(Rules.Person.HasEvent(['Census', '', '', '']))
        plist = self.database.get_person_handles(sort_handles=False)
        ind_list = filter.apply(self.database, plist)
        # same idea for an other rule on new ind_list
        # filter.add_rule()
        # list = filter.apply(self.database, ind_list)
        self.doc.start_paragraph('Loc-New')
        self.doc.write_text(_("\nCensus event (Individual)\n"))
        self.doc.end_paragraph()
        for person_handle in ind_list:
            person = self.database.get_person_from_handle(person_handle)
            self.doc.start_paragraph('Loc-Normal')
            name = name_displayer.display(person)
            id = person.get_gramps_id()
            self.doc.write_text(id + ":\t" + name)
            self.doc.end_paragraph()

    def write_presidence(self):
        """
        The routine creates the residence event paragraph for individuals.
        Using existing filter rule.
        """
        filter_class = GenericFilterFactory('Person')
        filter = filter_class()
        filter.add_rule(Rules.Person.HasEvent(['Residence', '', '', '']))
        plist = self.database.get_person_handles(sort_handles=False)
        ind_list = filter.apply(self.database, plist)
        self.doc.start_paragraph('Loc-New')
        self.doc.write_text(_("\nResidence event (Individual)\n"))
        self.doc.end_paragraph()
        for person_handle in ind_list:
            person = self.database.get_person_from_handle(person_handle)
            self.doc.start_paragraph('Loc-Normal')
            name = name_displayer.display(person)
            id = person.get_gramps_id()
            self.doc.write_text(id + ":\t" + name)
            self.doc.end_paragraph()

    def write_fcensus(self):
        """
        The routine creates the census event paragraph for families.
        Using existing filter rule.
        """
        filter_class = GenericFilterFactory('Person')
        filter = filter_class()
        filter.add_rule(Rules.Person.HasFamilyEvent(['Census', '', '', '']))
        plist = self.database.get_person_handles(sort_handles=False)
        ind_list = filter.apply(self.database, plist)
        self.doc.start_paragraph('Loc-New')
        self.doc.write_text(_("\nCensus event (Family)\n"))
        self.doc.end_paragraph()
        for person_handle in ind_list:
            person = self.database.get_person_from_handle(person_handle)
            self.doc.start_paragraph('Loc-Normal')
            name = name_displayer.display(person)
            id = person.get_gramps_id()
            self.doc.write_text(id + ":\t" + name)
            self.doc.end_paragraph()

    def write_fresidence(self):
        """
        The routine creates the residence event paragraph for families.
        Using existing filter rule.
        """
        filter_class = GenericFilterFactory('Person')
        filter = filter_class()
        filter.add_rule(Rules.Person.HasFamilyEvent(['Residence', '', '', '']))
        plist = self.database.get_person_handles(sort_handles=False)
        ind_list = filter.apply(self.database, plist)
        self.doc.start_paragraph('Loc-New')
        self.doc.write_text(_("\nResidence event (Family)\n"))
        self.doc.end_paragraph()
        for person_handle in ind_list:
            person = self.database.get_person_from_handle(person_handle)
            self.doc.start_paragraph('Loc-Normal')
            name = name_displayer.display(person)
            id = person.get_gramps_id()
            self.doc.write_text(id + ":\t" + name)
            self.doc.end_paragraph()

    def write_address(self):
        """
        The routine creates the address paragraph for individuals.
        Using existing filter rule.
        """
        filter_class = GenericFilterFactory('Person')
        filter = filter_class()
        filter.add_rule(Rules.Person.HasAddress(['0', 'greater than']))
        plist = self.database.get_person_handles(sort_handles=False)
        ind_list = filter.apply(self.database, plist)
        self.doc.start_paragraph('Loc-New')
        self.doc.write_text(_("\nAddress filter (Person)\n"))
        self.doc.end_paragraph()
        for person_handle in ind_list:
            person = self.database.get_person_from_handle(person_handle)
            self.doc.start_paragraph('Loc-Normal')
            name = name_displayer.display(person)
            id = person.get_gramps_id()
            self.doc.write_text(id + ":\t" + name)
            self.doc.end_paragraph()

#------------------------------------------------------------------------
#
# LocationsOptions
#
#------------------------------------------------------------------------
class LocationsOptions(MenuReportOptions):
    """
    Defines options.
    """
    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu.
        """
        pass

    def make_default_style(self, default_style):
        """Make the default output style"""
        font = FontStyle()
        font.set_size(20)
        font.set_type_face(FONT_SANS_SERIF)
        font.set_bold(1)
        para = ParagraphStyle()
        para.set_header_level(1)
        para.set_bottom_border(1)
        para.set_bottom_margin(ReportUtils.pt2cm(8))
        para.set_font(font)
        para.set_alignment(PARA_ALIGN_CENTER)
        para.set_description(_("The style used for the title of the page."))
        default_style.add_paragraph_style("Loc-Title", para)

        font = FontStyle()
        font.set_size(14)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_top_margin(ReportUtils.pt2cm(6))
        para.set_description(_('The basic style used for the paragraph title.'))
        default_style.add_paragraph_style("Loc-New", para)

        font = FontStyle()
        font.set_size(10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("Loc-Normal", para)

