# Copyright (C) 2011 Adam Stein <adam@csh.rit.edu>
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

"""Reports/Text Reports/Filtered Descendant Report"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
from functools import partial

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gen.display.name import displayer as _nd
from Errors import ReportError
from Filters import GenericFilter
from gen.lib import FamilyRelType, Person, NoteType
from gen.plug.menu import (BooleanOption, NumberOption, 
                           EnumeratedListOption, FilterOption,
                           StringOption, TextOption)
from gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle, 
                             FONT_SANS_SERIF, FONT_SERIF, 
                             INDEX_TYPE_TOC, PARA_ALIGN_CENTER)
from gen.plug.report import (Report, Bibliography)
from gen.plug.report import endnotes
from gen.plug.report import utils as ReportUtils
from gen.plug.report import MenuReportOptions
                        
from libnarrate import Narrator
import TransUtils
from libtranslate import Translator, get_language_string
from libsubstkeyword import SubstKeywords

from TransUtils import get_addon_translator
_ = get_addon_translator(__file__).gettext

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
EMPTY_ENTRY = "_____________"
HENRY = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

#------------------------------------------------------------------------
#
# DescendantReport
#
#------------------------------------------------------------------------
class DescendantReport(Report):
    def __init__(self, database, options, user):
        """
        Create the DescendantReport object that produces the report.
                        
        The arguments are:

        database      - the GRAMPS database instance
        options       - instance of the Options class for this report
        user          - instance of the User class (used for interaction with the user)

        This report needs the following parameters (class variables)
        that come in the options class.
        
        gen           - Maximum number of generations to include.
        pagebgg       - Whether to include page breaks between generations.
        pageben       - Whether to include page break before End Notes.
        fulldates     - Whether to use full dates instead of just year.
        listc         - Whether to list children.
        incnotes      - Whether to include notes.
        usecall       - Whether to use the call name as the first name.
        repplace      - Whether to replace missing Places with ___________.
        repdate       - Whether to replace missing Dates with ___________.
        computeage    - Whether to compute age.
        omitda        - Whether to omit duplicate ancestors (e.g. when distant cousins marry).
        verbose       - Whether to use complete sentences.
        numbering     - The descendancy numbering system to be utilized.
        desref        - Whether to add descendant references in child list.
        incphotos     - Whether to include images.
        incnames      - Whether to include other names.
        incevents     - Whether to include events.
        incaddresses  - Whether to include addresses.
        incsrcnotes   - Whether to include source notes in the Endnotes section. Only works if Include sources is selected.
        incmates      - Whether to include information about partners
        incattrs      - Whether to include attributes
        incpaths      - Whether to include the path of descendancy from the start-person to each descendant.
        incssign      - Whether to include a sign ('+') before the descendant number in the child-list to indicate a child has succession.
        caption_fmt   - Caption format.
        filter        - Filter to be applied to the people of the database.
        honor_private - Honor the private flag setting when getting information
        inc_captions  - Whether to include captions under photos.
        incsources    - Whether to include source references.
        links         - Whether to turn URLs into real links
        title         - Report title
        """
        Report.__init__(self, database, options, user)

        self.map = {}
        self._user = user

        menu = options.menu
        get_option_by_name = menu.get_option_by_name
        get_value = lambda name: get_option_by_name(name).get_value()
        self.max_generations = get_value('gen')
        self.pgbrk         = get_value('pagebbg')
        self.pgbrkenotes   = get_value('pageben')
        self.fulldate      = get_value('fulldates')
        self.listchildren  = get_value('listc')
        self.inc_notes     = get_value('incnotes')
        use_call           = get_value('usecall')
        blankplace         = get_value('repplace')
        blankdate          = get_value('repdate')
        self.calcageflag   = get_value('computeage')
        self.dubperson     = get_value('omitda')
        self.verbose       = get_value('verbose')
        self.childref      = get_value('desref')
        self.addimages     = get_value('incphotos')
        self.inc_names     = get_value('incnames')
        self.inc_events    = get_value('incevents')
        self.inc_addr      = get_value('incaddresses')
        self.inc_sources   = get_value('incsources')
        self.inc_srcnotes  = get_value('incsrcnotes')
        self.inc_mates     = get_value('incmates')
        self.inc_attrs     = get_value('incattrs')
        self.inc_paths     = get_value('incpaths')
        self.inc_ssign     = get_value('incssign')
        self.caption_fmt   = get_value("captionfmt")
        self.filter        = get_option_by_name("filter")
        self.honor_private = get_value("honorprivate")
        self.inc_captions  = get_value("inccaptions")
        self.links         = get_value("links")
        self.title         = get_value("title")

        self.gen_handles = {}
        self.prev_gen_handles = {}
        self.gen_keys = [[] for x in xrange(self.max_generations)]
        self.dnumber = {}

        if blankdate:
            empty_date = EMPTY_ENTRY
        else:
            empty_date = ""

        if blankplace:
            empty_place = EMPTY_ENTRY
        else:
            empty_place = ""

        language = get_value('trans')
        translator = Translator(language)
        self._ = translator.gettext

        self.__narrator = Narrator(self.database, self.verbose,
                                   use_call, self.fulldate, 
                                   empty_date, empty_place,
                                   translator=translator,
                                   get_endnote_numbers=self.endnotes)

        self.__get_date = translator.get_date

        self.__get_type = translator.get_type

        self.bibli = Bibliography(Bibliography.MODE_DATE|Bibliography.MODE_PAGE)

    def apply_mod_reg_filter_aux(self, person_handle, index, cur_gen):
        if (not person_handle) or (cur_gen > self.max_generations) or \
           (person_handle in self.map.values()):
            return

        self.map[index] = person_handle

        self.gen_keys[cur_gen-1].append(index)

        person = self.database.get_person_from_handle(person_handle)

        for family_handle in person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)

            for child_ref in family.get_child_ref_list():
                ix = max(self.map)
                self.apply_mod_reg_filter_aux(child_ref.ref, ix + 1,
                                              self.gen_info[child_ref.ref])

    # Filter for Record-style (Modified Register) numbering
    def apply_mod_reg_filter(self, person_handle, cur_gen):
        self.apply_mod_reg_filter_aux(person_handle, len(self.map)+1, cur_gen)

        mod_reg_number = 1

        for generation in xrange(len(self.gen_keys)):
            for key in self.gen_keys[generation]:
                person_handle = self.map[key]
                self.dnumber[person_handle] = mod_reg_number

                mod_reg_number += 1

    def write_report(self):
        """
        This function is called by the report system and writes the report.
        """

        self._create_person_list()

        self.doc.start_paragraph("DDR-Title")

        title = self._(self.title)
        mark = IndexMark(title, INDEX_TYPE_TOC, 1)
        self.doc.write_text(title, mark)
        self.doc.end_paragraph()

        for generation in xrange(len(self.gen_keys)):
            if len(self.gen_keys[generation]):
                if self.pgbrk and generation > 0:
                    self.doc.page_break()
                self.doc.start_paragraph("DDR-Generation")
                text = self._("Generation %d") % (generation+1)
                mark = IndexMark(text, INDEX_TYPE_TOC, 2)
                self.doc.write_text(text, mark)
                self.doc.end_paragraph()
                if self.childref:
                    self.prev_gen_handles = self.gen_handles.copy()
                    self.gen_handles.clear()

                for key in self.gen_keys[generation]:
                    person_handle = self.map[key]
                    self.gen_handles[person_handle] = key
                    self.write_person(key)

        if self.inc_sources:
            if self.pgbrkenotes:
                self.doc.page_break()
            # it ignores language set for Note type (use locale)
            endnotes.write_endnotes(self.bibli, self.database, self.doc,
                                    printnotes=self.inc_srcnotes,
                                    links=self.links)

    def write_path(self, person):
        path = []
        while True:
            #person changes in the loop
            family_handle = person.get_main_parents_family_handle()
            if family_handle:
                family = self.database.get_family_from_handle(family_handle)
                mother_handle = family.get_mother_handle()
                father_handle = family.get_father_handle()
                if mother_handle and mother_handle in self.dnumber:
                    person = self.database.get_person_from_handle(mother_handle)
                    person_name = _nd.display_name(person.get_primary_name())
                    path.append(person_name)
                elif father_handle and father_handle in self.dnumber:
                    person = self.database.get_person_from_handle(father_handle)
                    person_name = _nd.display_name(person.get_primary_name())
                    path.append(person_name)
                else:
                    break
            else:
                break

        index = len(path)

        if index:
            self.doc.write_text("(")

        for name in path:
            if index == 1:
                self.doc.write_text(name + "-" + str(index) + ") ")
            else:
                self.doc.write_text(name + "-" + str(index) + "; ")
            index -= 1

    def write_person(self, key):
        """Output birth, death, parentage, marriage and notes information """

        person_handle = self.map[key]
        person = self.database.get_person_from_handle(person_handle)

        val = self.dnumber[person_handle]
        self.doc.start_paragraph("DDR-First-Entry","%s." % val)

        name = _nd.display_formal(person)
        mark = ReportUtils.get_person_mark(self.database, person)

        self.doc.start_bold()
        self.doc.write_text(name, mark)
        if name[-1:] == '.':
            self.doc.write_text_citation("%s " % self.endnotes(person), links=self.links )
        else:
            self.doc.write_text_citation("%s. " % self.endnotes(person), links=self.links )
        self.doc.end_bold()

        if self.inc_paths:
            self.write_path(person)
        
        if self.dubperson:
            # Check for duplicate record (result of distant cousins marrying)
            for dkey in sorted(self.map):
                if dkey >= key: 
                    break
                if self.map[key] == self.map[dkey]:
                    self.doc.write_text(self._(
                        "%(name)s is the same person as [%(id_str)s].") % {
                            'name' :'',
                            'id_str': str(dkey),
                            }
                        )
                    self.doc.end_paragraph()
                    return

        self.doc.end_paragraph()
       
        self.write_person_info(person)

        if (self.inc_mates or self.listchildren or self.inc_notes or
            self.inc_events or self.inc_attrs):
            for family_handle in person.get_family_handle_list():
                family = self.database.get_family_from_handle(family_handle)
                if self.inc_mates:
                    self.__write_mate(person, family)
                if self.listchildren:
                    self.__write_children(family)
                if self.inc_notes:
                    self.__write_family_notes(family)
                first = True
                if self.inc_events:
                    first = self.__write_family_events(family)
                if self.inc_attrs:
                    self.__write_family_attrs(family, first)

    def write_event(self, event_ref):
        text = ""
        event = self.database.get_event_from_handle(event_ref.ref)

        # Don't write out private events if honoring the flag
        if self.honor_private and event.get_privacy() == True:
            return

        if self.fulldate:
            date = self.__get_date(event.get_date_object())
        else:
            date = event.get_date_object().get_year()

        ph = event.get_place_handle()
        if ph:
            place = self.database.get_place_from_handle(ph).get_title()
        else:
            place = u''

        self.doc.start_paragraph('DDR-MoreDetails')
        event_name = self.__get_type(event.get_type())
        if date and place:
            text +=  self._('%(date)s, %(place)s') % { 
                       'date' : date, 'place' : place }
        elif date:
            text += self._('%(date)s') % {'date' : date}
        elif place:
            text += self._('%(place)s') % { 'place' : place }

        if event.get_description():
            if text:
                text += ". "
            text += event.get_description()
            
        text += self.endnotes(event)
        
        if text:
            text += ". "
            
        text = self._('%(event_name)s: %(event_text)s') % {
                 'event_name' : self._(event_name),
                 'event_text' : text }
        
        self.doc.write_text_citation(text, links=self.links )
        
        if self.inc_attrs:
            text = ""
            attr_list = event.get_attribute_list()
            attr_list.extend(event_ref.get_attribute_list())
            for attr in attr_list:
                # Don't write out private attributes if honoring the flag
                if self.honor_private and attr.get_privacy() == True:
                    continue
                if text:
                    text += "; "
                attrName = self.__get_type(attr.get_type())
                text += self._("%(type)s: %(value)s%(endnotes)s") % {
                    'type'     : self._(attrName),
                    'value'    : attr.get_value(),
                    'endnotes' : self.endnotes(attr) }

            text = " " + text
            self.doc.write_text_citation(text, links=self.links )

        self.doc.end_paragraph()

        if self.inc_notes:
            # if the event or event reference has a note attached to it,
            # get the text and format it correctly
            notelist = event.get_note_list()
            notelist.extend(event_ref.get_note_list())
            for notehandle in notelist:
                note = self.database.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(), 
                        note.get_format(),"DDR-MoreDetails",
                        contains_html= note.get_type() == NoteType.HTML_CODE,
                        links=self.links)

    def __write_parents(self, person):
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.database.get_family_from_handle(family_handle)
            mother_handle = family.get_mother_handle()
            father_handle = family.get_father_handle()
            if mother_handle:
                mother = self.database.get_person_from_handle(mother_handle)
                mother_name = _nd.display_name(mother.get_primary_name())
                mother_mark = ReportUtils.get_person_mark(self.database, mother)
            else:
                mother_name = ""
                mother_mark = ""
            if father_handle:
                father = self.database.get_person_from_handle(father_handle)
                father_name = _nd.display_name(father.get_primary_name())
                father_mark = ReportUtils.get_person_mark(self.database, father)
            else:
                father_name = ""
                father_mark = ""
            text = self.__narrator.get_child_string(father_name, mother_name)
            if text:
                self.doc.write_text(text)
                if father_mark:
                    self.doc.write_text("", father_mark)
                if mother_mark:
                    self.doc.write_text("", mother_mark)

    def write_marriage(self, person):
        """ 
        Output marriage sentence.
        """
        is_first = True
        for family_handle in person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)
            spouse_handle = ReportUtils.find_spouse(person, family)
            spouse = self.database.get_person_from_handle(spouse_handle)
            text = ""
            spouse_mark = ReportUtils.get_person_mark(self.database, spouse)
            
            text = self.__narrator.get_married_string(family, is_first)
            
            if text:
                self.doc.write_text_citation(text, spouse_mark, links=self.links )
                is_first = False
                
    def __write_mate(self, person, family):
        """
        Write information about the person's spouse/mate.
        """
        if person.get_gender() == Person.MALE:
            mate_handle = family.get_mother_handle()
        else:
            mate_handle = family.get_father_handle()
            
        if mate_handle:
            mate = self.database.get_person_from_handle(mate_handle)

            self.doc.start_paragraph("DDR-MoreHeader")
            name = _nd.display_formal(mate)
            mark = ReportUtils.get_person_mark(self.database, mate)
            if family.get_relationship() == FamilyRelType.MARRIED:
                self.doc.write_text(self._("Spouse: %s") % name, mark)
            else:
                self.doc.write_text(self._("Relationship with: %s") % name, mark)
            if name[-1:] != '.':
                self.doc.write_text(".")
            self.doc.write_text_citation(self.endnotes(mate), links=self.links )
            self.doc.end_paragraph()

            self.write_person_info(mate)

    def __get_mate_names(self, family):
        mother_handle = family.get_mother_handle()
        if mother_handle:
            mother = self.database.get_person_from_handle(mother_handle)
            mother_name = _nd.display(mother)
        else:
            mother_name = self._("unknown")

        father_handle = family.get_father_handle()
        if father_handle:
            father = self.database.get_person_from_handle(father_handle)
            father_name = _nd.display(father)
        else:
            father_name = self._("unknown")

        return mother_name, father_name

    def __write_children(self, family):
        """ 
        List the children for the given family.
        """
        if not family.get_child_ref_list():
            return

        mother_name, father_name = self.__get_mate_names(family)

        self.doc.start_paragraph("DDR-ChildTitle")
        self.doc.write_text(
                        self._("Children of %(mother_name)s and %(father_name)s") % 
                            {'father_name': father_name,
                             'mother_name': mother_name
                             } )
        self.doc.end_paragraph()

        cnt = 1
        for child_ref in family.get_child_ref_list():
            child_handle = child_ref.ref
            child = self.database.get_person_from_handle(child_handle)
            child_name = _nd.display(child)
            child_mark = ReportUtils.get_person_mark(self.database, child)

            if self.childref and self.prev_gen_handles.get(child_handle):
                value = str(self.prev_gen_handles.get(child_handle))
                child_name += " [%s]" % value

            if self.inc_ssign:
                prefix = " "
                for family_handle in child.get_family_handle_list():
                    family = self.database.get_family_from_handle(family_handle)
                    if family.get_child_ref_list():
                        prefix = "+ "
                        break
            else:
                prefix = ""

            if child_handle in self.dnumber:
                self.doc.start_paragraph("DDR-ChildList",
                        prefix
                        + str(self.dnumber[child_handle])
                        + " "
                        + ReportUtils.roman(cnt).lower()
                        + ".")
            else:
                self.doc.start_paragraph("DDR-ChildList",
                              prefix + ReportUtils.roman(cnt).lower() + ".")
            cnt += 1

            self.doc.write_text("%s. " % child_name, child_mark)
            self.__narrator.set_subject(child)
            self.doc.write_text_citation(self.__narrator.get_born_string() or
                                         self.__narrator.get_christened_string() or
                                         self.__narrator.get_baptised_string(), links=self.links )
            self.doc.write_text_citation(self.__narrator.get_died_string() or
                                         self.__narrator.get_buried_string(), links=self.links ) 
            self.doc.end_paragraph()

    def __write_family_notes(self, family):
        """ 
        Write the notes for the given family.
        """
        notelist = family.get_note_list()
        if len(notelist) > 0:
            mother_name, father_name = self.__get_mate_names(family)

            self.doc.start_paragraph("DDR-NoteHeader")
            self.doc.write_text(
                self._('Notes for %(mother_name)s and %(father_name)s:') % {
                'mother_name' : mother_name,
                'father_name' : father_name })
            self.doc.end_paragraph()
            for notehandle in notelist:
                note = self.database.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(),
                                           note.get_format(),"DDR-Entry",
                                           links=self.links)

    def __write_family_events(self, family):
        """ 
        List the events for the given family.
        """
        if not family.get_event_ref_list():
            return

        mother_name, father_name = self.__get_mate_names(family)

        first = 1
        for event_ref in family.get_event_ref_list():
            if first:
                self.doc.start_paragraph('DDR-MoreHeader')
                self.doc.write_text(
                    self._('More about %(mother_name)s and %(father_name)s:') % { 
                    'mother_name' : mother_name,
                    'father_name' : father_name })
                self.doc.end_paragraph()
                first = 0
            self.write_event(event_ref)
            return first

    def __write_family_attrs(self, family, first):
        """ 
        List the attributes for the given family.
        """
        attrs = family.get_attribute_list()

        if first and attrs:
            mother_name, father_name = self.__get_mate_names(family)

            self.doc.start_paragraph('DDR-MoreHeader')
            self.doc.write_text(
                self._('More about %(mother_name)s and %(father_name)s:') % { 
                'mother_name' : mother_name,
                'father_name' : father_name })
            self.doc.end_paragraph()

        for attr in attrs:
            self.doc.start_paragraph('DDR-MoreDetails')
            attrName = self.__get_type(attr.get_type())
            text = self._("%(type)s: %(value)s%(endnotes)s") % {
                'type'     : self._(attrName),
                'value'    : attr.get_value(),
                'endnotes' : self.endnotes(attr) }
            self.doc.write_text_citation( text , links=self.links )
            self.doc.end_paragraph()

            if self.inc_notes:
                # if the attr or attr reference has a note attached to it,
                # get the text and format it correctly
                notelist = attr.get_note_list()
                for notehandle in notelist:
                    note = self.database.get_note_from_handle(notehandle)
                    self.doc.write_styled_note(note.get_styledtext(), 
                                               note.get_format(),"DDR-MoreDetails",
                                               links=self.links)

    def write_person_info(self, person):
        name = _nd.display_formal(person)
        self.__narrator.set_subject(person)
        
        plist = person.get_media_list()
        if self.addimages and len(plist) > 0:
            photo = plist[0]
            if self.inc_captions:
                subst = SubstKeywords(self.database, person.get_handle())

                # Performing the following steps to get a caption array (each elem = 1 line):
                #
                # 1. Substitute any markers that need to get substituted
                # 2. Remove empty strings from the resultant list
                caption = subst.replace_and_clean(self.caption_fmt)
                caption = filter(lambda x: len(x)>0, caption)

                ReportUtils.insert_image(self.database, self.doc, photo, self._user, alt=caption)
            else:
                ReportUtils.insert_image(self.database, self.doc, photo, self._user)

        self.doc.start_paragraph("DDR-Entry")
        
        if not self.verbose:
            self.__write_parents(person)

        text = self.__narrator.get_born_string()
        if text:
            self.doc.write_text_citation(text, links=self.links )

        text = self.__narrator.get_baptised_string()
        if text:
            self.doc.write_text_citation(text, links=self.links )
            
        text = self.__narrator.get_christened_string()
        if text:
            self.doc.write_text_citation(text, links=self.links )
    
        text = self.__narrator.get_died_string(self.calcageflag)
        if text:
            self.doc.write_text_citation(text, links=self.links )

        text = self.__narrator.get_buried_string()
        if text:
            self.doc.write_text_citation(text, links=self.links )

        if self.verbose:
            self.__write_parents(person)
        self.write_marriage(person)
        self.doc.end_paragraph()

        notelist = person.get_note_list()
        if len(notelist) > 0 and self.inc_notes:
            self.doc.start_paragraph("DDR-NoteHeader")
            self.doc.write_text(self._("Notes for %s") % name)
            self.doc.end_paragraph()
            for notehandle in notelist:
                note = self.database.get_note_from_handle(notehandle)
                self.doc.write_styled_note(note.get_styledtext(), 
                        note.get_format(),"DDR-Entry",
                        contains_html= note.get_type() == NoteType.HTML_CODE,
                        links=self.links)

        first = True
        if self.inc_names:
            for alt_name in person.get_alternate_names():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:') % { 
                        'person_name' : name })
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DDR-MoreDetails')
                atype = self.__get_type(alt_name.get_type())
                aname = alt_name.get_regular_name()
                self.doc.write_text_citation(self._('%(name_kind)s: %(name)s%(endnotes)s') % {
                    'name_kind' : self._(atype),
                    'name' : aname,
                    'endnotes' : self.endnotes(alt_name),
                    }, links=self.links)
                self.doc.end_paragraph()

        if self.inc_events:
            for event_ref in person.get_primary_event_ref_list():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:') % { 
                        'person_name' : _nd.display(person) })
                    self.doc.end_paragraph()
                    first = 0

                self.write_event(event_ref)
                
        if self.inc_addr:
            for addr in person.get_address_list():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(self._('More about %(person_name)s:') % { 
                        'person_name' : name })
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DDR-MoreDetails')
                
                text = ReportUtils.get_address_str(addr)

                if self.fulldate:
                    date = self.__get_date(addr.get_date_object())
                else:
                    date = addr.get_date_object().get_year()

                self.doc.write_text(self._('Address: '))
                if date:
                    self.doc.write_text( '%s, ' % date )
                self.doc.write_text( text )
                self.doc.write_text_citation( self.endnotes(addr) , links=self.links )
                self.doc.end_paragraph()
                
        if self.inc_attrs:
            attrs = person.get_attribute_list()
            if first and attrs:
                self.doc.start_paragraph('DDR-MoreHeader')
                self.doc.write_text(self._('More about %(person_name)s:') % { 
                    'person_name' : name })
                self.doc.end_paragraph()
                first = False

            for attr in attrs:
                # Don't write out private attributes if honoring the flag
                if self.honor_private and attr.get_privacy() == True:
                    continue

                self.doc.start_paragraph('DDR-MoreDetails')
                attrName = self.__get_type(attr.get_type())
                text = self._("%(type)s: %(value)s%(endnotes)s") % {
                    'type'     : self._(attrName),
                    'value'    : attr.get_value(),
                    'endnotes' : self.endnotes(attr) }
                self.doc.write_text_citation( text , links=self.links )
                self.doc.end_paragraph()

    def endnotes(self, obj):
        if not obj or not self.inc_sources:
            return ""
        
        txt = endnotes.cite_source(self.bibli, obj)
        if txt:
            txt = '<super>' + txt + '</super>'
        return txt

    def _create_person_list(self):
        """
        Merge the results of each query in the filter to come up with a single list (in order)
        """

        people = self.filter.get_filter().apply(self.database)

        if len(people) > 1:
            rules = self.filter.get_filter().get_rules()

            if len(rules) > 1:
                # This will wind up to be an intersection of all filter rules
                common_people = None

                # Find a person common to all the filter rules that we can use
                # to synchronize generation info on (the synchronized person is
                # generation 0, everybody else will be relative to that person)
                for rule in rules:
                    filter = GenericFilter()
                    filter.add_rule(rule)

                    if common_people:
                        common_people &= set(filter.apply(self.database))
                    else:
                        # First time through, start with the filtered list
                        common_people = set(filter.apply(self.database))

                if len(common_people) == 0:
                    raise ReportError(_("no common person found between filter rules to synchronize generations"))

                sync_handle = common_people.pop()
            else:
                # Only have the 1 rule, so everybody is common
                sync_handle = people[0]

            # Find connections between people so that we know what generation
            # they are in
            sync_person = self.database.get_person_from_handle(sync_handle)

            import Relationship
            relationship = Relationship.get_relationship_calculator()
        
            from Filters.Rules.Person._DeepRelationshipPathBetween import find_deep_relations

            self.gen_info = {sync_handle: 0}
            min_gen = 0

            for handle in people:
                person = self.database.get_person_from_handle(handle)

                gen = 0
                prev = sync_person

                connections = find_deep_relations(self.database, None, sync_person, [], [], [handle])

                # Problem if somebody isn't connected
                if len(connections) == 0:
                    raise ReportError(_("can't determine generation for '%s'" % \
                        name_displayer.display(person)))

                for connection_handle in connections[0]:
                    person = self.database.get_person_from_handle(connection_handle)

                    if person != sync_person:
                        (str, d_orig, d_other) = relationship.get_one_relationship(self.database,
                                                                                   prev, person,
                                                                                   extra_info=True)

                        # Returning relationships with the distance to the common ancestor
                        # from first person (d_orig) and the second person (d_other).  The
                        # first preson is the 'prev'ious person as we travel down the list of
                        # people.  The second person is 'person'.
                        #
                        # If both distances are negative, the two people are not biologically
                        # related to each other and we assume they are both in the same generation.
                        #
                        # If both distances are positive, they are family members of the same
                        # generation.
                        #
                        # If the first person distance is 1 and the second person distance is 0,
                        # then the second person is an ancestor of the first person and is one generation
                        # up.
                        #
                        # If the first person distance is 0 and the second person distance is 1,
                        # then the second person is a descendant of the first person and is one generation
                        # down.
                        gen += (d_other - d_orig)

                        self.gen_info[handle] = gen

                        if gen < min_gen: min_gen = gen

                    prev = person

            offset = abs(min_gen)+1     # Want generations to start at 1, not 0

            for handle in self.gen_info:
                self.gen_info[handle] += offset
        else:
            # Setting up for a single individual
            self.gen_info = {people[0]: 1}

        # Now that we know which generation each person is in, we can merge the people
        # from all the rules in the filter
        for rule in self.filter.get_filter().get_rules():
            person = self.database.get_person_from_gramps_id(rule.list[0])

            if person != None:
                handle = person.get_handle()

                self.apply_mod_reg_filter(handle, self.gen_info[handle])
            else:
                raise ReportError(_("no person found with ID '%s'" % rule.list[0]))

#------------------------------------------------------------------------
#
# DescendantOptions
#
#------------------------------------------------------------------------
class DescendantOptions(MenuReportOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        self.__db = dbase
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the filtered descendant report.
        """

        # Report Options
        
        add_option = partial(menu.add_option, _("Report Options"))
        
        self.filter = FilterOption(_("Filter"), 0)
        self.filter.set_help(
            _("Determines what people are included in the report"))
        add_option("filter", self.filter)

        from Filters import CustomFilters
        if len(CustomFilters.get_filters("Person")) == 0:
            from QuestionDialog import WarningDialog
            WarningDialog(_("No custom filters found"),
                    _(
                        "You do not have any custom filters.  The power of this "
                        "plugin comes from custom filters which are used to "
                        "figure out which people to include in the report.\n"
                        "\n"
                        "You can create custom filters from the "
                        "'Person Filter Editor' in the 'Edit' menu (when you "
                        "are in a person-related view like People or "
                        "Relationships).\n"
                        "\n"
                        "With no custom filters, this plugin will fallback "
                        "to using whatever filters are available and an "
                        "option to pick the center person for the filter.\n"
                        "\n"
                        "If you would like to create a descendant report "
                        "without using custom filters, you might want to "
                        "check out the 'Detailed Descendant Report' on which "
                        "this plugin is based.\n"
                     )
            )

            # No custom filters, fallback to use what's available along with
            # a center person
            from gen.plug.menu import PersonOption

            self.filter.connect("value-changed", self._filter_changed)

            self.pid = PersonOption(_("Filter Person"))
            self.pid.set_help(_("The center person for the filter"))
            add_option("pid", self.pid)
            self.pid.connect("value-changed", self._update_filters)

            self._update_filters()
        else:
            self.filter.connect("value-changed", self._customfilter_changed)
            self.filter.set_filters(CustomFilters.get_filters("Person"))
        
        generations = NumberOption(_("Generations"), 10, 1, 100)
        generations.set_help(
            _("The number of generations to include in the report")
            )
        add_option("gen", generations)
        
        pagebbg = BooleanOption(_("Page break between generations"), False)
        pagebbg.set_help(
                     _("Whether to start a new page after each generation."))
        add_option("pagebbg", pagebbg)

        pageben = BooleanOption(_("Page break before end notes"),False)
        pageben.set_help(
                     _("Whether to start a new page before the end notes."))
        add_option("pageben", pageben)

        self.title = StringOption(_("Report title"), self.filter.get_filter().get_name())
        self.title.set_help(_("This text will be used as the report title"))
        add_option("title", self.title)

        trans = EnumeratedListOption(_("Translation"),
                                      Translator.DEFAULT_TRANSLATION_STR)
        trans.add_item(Translator.DEFAULT_TRANSLATION_STR, _("Default"))
        for language in TransUtils.get_available_translations():
            trans.add_item(language, get_language_string(language))
        trans.set_help(_("The translation to be used for the report."))
        add_option("trans", trans)

        # Content
        
        add_option = partial(menu.add_option, _("Content"))

        usecall = BooleanOption(_("Use callname for common name"), False)
        usecall.set_help(_("Whether to use the call name as the first name."))
        add_option("usecall", usecall)
        
        fulldates = BooleanOption(_("Use full dates instead of only the year"),
                                  True)
        fulldates.set_help(_("Whether to use full dates instead of just year."))
        add_option("fulldates", fulldates)
        
        listc = BooleanOption(_("List children"), True)
        listc.set_help(_("Whether to list children."))
        add_option("listc", listc)
        
        computeage = BooleanOption(_("Compute death age"),True)
        computeage.set_help(_("Whether to compute a person's age at death."))
        add_option("computeage", computeage)
        
        omitda = BooleanOption(_("Omit duplicate ancestors"), True)
        omitda.set_help(_("Whether to omit duplicate ancestors."))
        add_option("omitda", omitda)
        
        verbose = BooleanOption(_("Use complete sentences"), True)
        verbose.set_help(
                 _("Whether to use complete sentences or succinct language."))
        add_option("verbose", verbose)

        desref = BooleanOption(_("Add descendant reference in child list"),
                               True)
        desref.set_help(
                    _("Whether to add descendant references in child list."))
        add_option("desref", desref)

        links = BooleanOption(_("Turn URLs into real links"), True)
        links.set_help(_("Turn any URLs starting with 'http', 'https', or 'mailto' into clickable links"))
        add_option("links", links)

        honorprivate = BooleanOption(_("Do not include information marked private"), True)
        honorprivate.set_help(_("Whether to honor the private flag setting"))
        add_option("honorprivate", honorprivate)

        add_option = partial(menu.add_option, _("Include"))
        
        incnotes = BooleanOption(_("Include notes"), True)
        incnotes.set_help(_("Whether to include notes."))
        add_option("incnotes", incnotes)

        incattrs = BooleanOption(_("Include attributes"), False)
        incattrs.set_help(_("Whether to include attributes."))
        add_option("incattrs", incattrs)
        
        self.incphotos = BooleanOption(_("Include Photo/Images from Gallery"), False)
        self.incphotos.set_help(_("Whether to include images."))
        add_option("incphotos", self.incphotos)
        self.incphotos.connect("value-changed", self._photo_changed)

        incnames = BooleanOption(_("Include alternative names"), False)
        incnames.set_help(_("Whether to include other names."))
        add_option("incnames", incnames)

        incevents = BooleanOption(_("Include events"), False)
        incevents.set_help(_("Whether to include events."))
        add_option("incevents", incevents)

        incaddresses = BooleanOption(_("Include addresses"), False)
        incaddresses.set_help(_("Whether to include addresses."))
        add_option("incaddresses", incaddresses)

        incsources = BooleanOption(_("Include sources"), False)
        incsources.set_help(_("Whether to include source references."))
        add_option("incsources", incsources)
        
        incsrcnotes = BooleanOption(_("Include sources notes"), False)
        incsrcnotes.set_help(_("Whether to include source notes in the "
            "Endnotes section. Only works if Include sources is selected."))
        add_option("incsrcnotes", incsrcnotes)

        incmates = BooleanOption(_("Include partners"), False)
        incmates.set_help(_("Whether to include detailed partner information."))
        add_option("incmates", incmates)

        incssign = BooleanOption(_("Include sign of succession ('+')"
                                   " in child-list"), True)
        incssign.set_help(_("Whether to include a sign ('+') before the"
                            " descendant number in the child-list to indicate"
                            " a child has succession."))
        add_option("incssign", incssign)

        incpaths = BooleanOption(_("Include path to start-person"), False)
        incpaths.set_help(_("Whether to include the path of descendancy "
                            "from the start-person to each descendant."))
        add_option("incpaths", incpaths)

        add_option = partial(menu.add_option, _("Caption"))

        self.inccaptions = BooleanOption(_("Add caption under image from Gallery"), False)
        self.inccaptions.set_help(_("Whether to add captions underneath images."))
        add_option("inccaptions", self.inccaptions)

        self.captionfmt = TextOption(_("Caption Format"), ["$n"] )
        self.captionfmt.set_help(_("Display format for the caption."))
        add_option("captionfmt", self.captionfmt)

        # Missing information
        
        add_option = partial(menu.add_option, _("Missing information"))      

        repplace = BooleanOption(_("Replace missing places with ______"), False)
        repplace.set_help(_("Whether to replace missing Places with blanks."))
        add_option("repplace", repplace)

        repdate = BooleanOption(_("Replace missing dates with ______"), False)
        repdate.set_help(_("Whether to replace missing Dates with blanks."))
        add_option("repdate", repdate)

    def make_default_style(self, default_style):
        """Make the default output style for the Filtered Descendant Report"""
        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=16, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_alignment(PARA_ALIGN_CENTER)
        para.set_description(_('The style used for the title of the page.'))
        default_style.add_paragraph_style("DDR-Title", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=14, italic=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_header_level(2)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the generation header.'))
        default_style.add_paragraph_style("DDR-Generation", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=10, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_left_margin(1.5)   # in centimeters
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the children list title.'))
        default_style.add_paragraph_style("DDR-ChildTitle", para)

        font = FontStyle()
        font.set(size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=-0.75, lmargin=2.25)
        para.set_top_margin(0.125)
        para.set_bottom_margin(0.125)
        para.set_description(_('The style used for the children list.'))
        default_style.add_paragraph_style("DDR-ChildList", para)

        font = FontStyle()
        font.set(face=FONT_SANS_SERIF, size=10, italic=0, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        default_style.add_paragraph_style("DDR-NoteHeader", para)

        para = ParagraphStyle()
        para.set(lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("DDR-Entry", para)

        para = ParagraphStyle()
        para.set(first_indent=-1.5, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)        
        para.set_description(_('The style used for the first personal entry.'))
        default_style.add_paragraph_style("DDR-First-Entry", para)

        font = FontStyle()
        font.set(size=10, face=FONT_SANS_SERIF, bold=1)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the More About header and '
            'for headers of mates.'))
        default_style.add_paragraph_style("DDR-MoreHeader", para)

        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0, lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for additional detail data.'))
        default_style.add_paragraph_style("DDR-MoreDetails", para)

        font = FontStyle()
        font.set(face=FONT_SERIF, size=10)
        para = ParagraphStyle()
        para.set_font(font)
        para.set_alignment(PARA_ALIGN_CENTER)
        para.set_description(_('The style used for photo captions.'))
        default_style.add_paragraph_style("DDR-Caption", para)

        endnotes.add_endnote_styles(default_style)

    def _customfilter_changed(self):
        try:
            # Update the title to match the name of the filter
            self.title.set_value(self.filter.get_filter().get_name())
        except AttributeError:
            pass

    def _filter_changed(self):
        """
        Handle filter change. If the filter is not specific to a person,
        disable the person option
        """
        filter_value = self.filter.get_value()
        if filter_value in [1, 2, 3, 4]:
            # Filters 1, 2, 3 and 4 rely on the center person
            self.pid.set_available(True)
        else:
            # The rest don't
            self.pid.set_available(False)

    def _update_filters(self):
        """
        Update the filter list based on the selected person
        """
        gid = self.pid.get_value()
        person = self.__db.get_person_from_gramps_id(gid)
        filter_list = ReportUtils.get_person_filters(person, False)
        self.filter.set_filters(filter_list)

    def _photo_changed(self):
        self.inccaptions.set_available(self.incphotos.get_value())
        self.captionfmt.set_available(self.incphotos.get_value())

