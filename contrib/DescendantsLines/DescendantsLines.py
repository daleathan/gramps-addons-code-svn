#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010 ats-familytree@offog.org
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
# This program is based on the program located at
# http://offog.org/darcs/misccode/familytree. The license for that
# program is found at http://offog.org/darcs/misccode/NOTES.
# Distributed under the terms of the X11 license:
#
#  Copyright 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007,
#    2008, 2009, 2010, 2011 Adam Sampson <ats@offog.org>
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the
#  "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to
#  the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL ADAM SAMPSON BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#
"""
Print Descendants Lines (experimental migration, UNSTABLE)
"""
#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import cairo
import gtk
import gzip
import xml.dom.minidom
import xml.sax.saxutils
import getopt
import sys
import codecs
import os.path
#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------

import DateHandler
from gen.plug.menu import NumberOption, PersonOption, FilterOption, \
                            DestinationOption, BooleanOption
from gen.plug.report import Report
from gen.plug.report import utils as ReportUtils
from gui.plug.report import MenuReportOptions
# libsubstkeyword
from TransUtils import get_addon_translator
_ = get_addon_translator().gettext
from gen.plug.docgen import (IndexMark, FontStyle, ParagraphStyle, 
                             FONT_SANS_SERIF, FONT_SERIF, 
                             INDEX_TYPE_TOC, PARA_ALIGN_LEFT)
from gen.display.name import displayer as name_displayer
from Filters import GenericFilterFactory, Rules
import const
import gen.lib

#-------------------------------------------------------------------------
#
# variables
#
#-------------------------------------------------------------------------
S_DOWN = 20
S_UP = 10
S_VPAD = 10
FL_PAD = 20
OL_PAD = 10
O_DOWN = 30
C_PAD = 10
F_PAD = 20
C_UP = 15
SP_PAD = 10
MIN_C_WIDTH = 40
TEXT_PAD = 2
TEXT_LINE_PAD = 2
INC_PLACES = False

ctx = None
font_name = 'sans-serif'
base_font_size = 12

_event_cache = {}

def find_event(database, handle):
    if handle in _event_cache:
        obj = _event_cache[handle]
    else:
        obj = database.get_event_from_handle(handle)
        _event_cache[handle] = obj
    return obj
    
    
class DescendantsLinesReport(Report):
    """
    DescendantsLines Report class
    """
    def __init__(self, database, options_class):
        """
        Create the object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options_class   - instance of the Options class for this report
        
        This report needs the following parameters (class variables)
        that come in the options class.

        S_DOWN - The length of the vertical edge from descendant to spouse-bar
        S_UP - The length of the vertical edge from spouse-bar to spouse
        S_VPAD
        FL_PAD
        OL_PAD
        O_DOWN - The length of the vertical edge from spouse-bar to child-bar
        C_PAD
        F_PAD
        C_UP - The length of the vertical edge from child to child-bar
        SP_PAD
        MIN_C_WIDTH
        TEXT_PAD
        TEXT_LINE_PAD
        """

        Report.__init__(self, database, options_class)
        self.options = {}
        menu = options_class.menu
        self.database = database
        for name in menu.get_all_option_names():
            self.options[name] = menu.get_option_by_name(name).get_value()

        global S_DOWN
        global S_UP
        global S_VPAD
        global FL_PAD
        global OL_PAD
        global O_DOWN
        global C_PAD
        global F_PAD
        global C_UP
        global SP_PAD
        global MIN_C_WIDTH
        global TEXT_PAD
        global TEXT_LINE_PAD
        S_DOWN = self.options["S_DOWN"]
        S_UP = self.options["S_UP"]
        S_VPAD = self.options["S_VPAD"]
        FL_PAD = self.options["FL_PAD"]
        OL_PAD = self.options["OL_PAD"]
        O_DOWN = self.options["O_DOWN"]
        C_PAD = self.options["C_PAD"]
        F_PAD = self.options["F_PAD"]
        C_UP = self.options["C_UP"]
        SP_PAD = self.options["SP_PAD"]
        MIN_C_WIDTH = self.options["MIN_C_WIDTH"]
        TEXT_PAD = self.options["TEXT_PAD"]
        TEXT_LINE_PAD = self.options["TEXT_LINE_PAD"]

        self.output_fn = self.options['output_fn']
        self.inc_places = self.options['inc_places']
        global INC_PLACES
        INC_PLACES = self.inc_places

    def write_report(self):
        """
        This routine actually creates the report. At this point, the document
        is opened and ready for writing.
        """
        
        pid = self.options_class.menu.get_option_by_name('pid').get_value()
        
        self.center_person = self.database.get_person_from_gramps_id(pid)
        
        # Who is missing on filter ?
        # Descendant Families of ID
        #filter_class = GenericFilterFactory('Person')
        #filter = filter_class()
        #filter.add_rule(Rules.Person.IsDescendantFamilysOf([pid, 1]))
        #filter.add_rule(Rules.Person.IsDescendantOf([pid, 1]))
        
        plist = self.database.get_person_handles()
        
        #ind_list = filter.apply(self.database, plist)
        #filter.add_rule(Rules.Person.IsSpouseOfFilterMatch(ind_list))
        #slist = filter.apply(self.database, ind_list)
        #filter.add_rule(Rules.Person.IsAncestorOf([pid, 0]))
        #alist = filter.apply(self.database, ind_list)
        #filter.add_rule(Rules.Person.IsAncestorOfFilterMatch(slist))
        #blist = filter.apply(self.database, slist)
        #ind_list = ind_list + slist + alist + blist
        
        ind_list = plist
                
        # Pass 1
        
        self.write_tmp_data(ind_list)
        
        # For printing something !
        
#        self.doc.start_paragraph('DL-name')
#        text = _("List of persons in the database:\n")
#        self.doc.write_text(text)
#        self.doc.end_paragraph()
#        nbr = 0
#        for child in ind_list:
#            nbr += 1
#            person = self.database.get_person_from_handle(child)
#            self.doc.start_paragraph('DL-name')
#            text = ("%(nbr)s. %(id)s - %(name)s" % 
#                                {'nbr' : nbr,
#                                 'id'  : person.get_gramps_id(),
#                                 'name' : name_displayer.display(person)})
#            self.doc.write_text(text)
#            self.doc.end_paragraph()
            
        # end of print test
            
        #PYTHONPATH
        
        input_fn = os.path.join(const.USER_PLUGINS, 'DescendantsLines', 'DescendantsLines.xml')
        #output_fn = os.path.join(const.USER_HOME, 'DescendantsLines.png')
        
        # Pass 2  
          
        global font_name, base_font_size

        p = load_gramps(input_fn, pid)
        draw_file(p, self.output_fn, PNGWriter())
        
    def write_tmp_data(self, ind_list):
        """
        This routine generates a tmp XML database with only descendant families
        (if that's what ind_list contains).
        """
        
        filename = os.path.join(const.USER_PLUGINS, 'DescendantsLines', 'DescendantsLines.xml')
                  
        xml_file = open(filename, "w")
        self.xml_file = codecs.getwriter("utf8")(xml_file)
        self.write_xml_head()
        
        self.xml_file.write('<events>\n')
        for child in ind_list:
            person = self.database.get_person_from_handle(child)
            for event_ref in person.get_event_ref_list():
                if event_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
                    self.write_xml_event(event_ref)
        self.xml_file.write('</events>\n')
        
        self.xml_file.write('<people>\n')
        for child in ind_list:
            person = self.database.get_person_from_handle(child)
            identifiant = person.get_gramps_id()
            if person.get_gender() == gen.lib.Person.MALE:
                gender = 'M'
            elif person.get_gender() == gen.lib.Person.FEMALE:
                gender = 'F'
            else:
                gender = 'U'
            name = person.get_primary_name()
            first = name.get_first_name()
            surname = name.get_surname()
            event_list = person.get_event_ref_list()
            self.write_xml_person(identifiant, child, gender, first, surname, event_list)
        self.xml_file.write('</people>\n')
        
        self.xml_file.write('<families>\n')
        
        # avoid duplicated families
        
        fams = self.database.get_family_handles()
        for child in ind_list:
            person = self.database.get_person_from_handle(child)
            
            for handle in person.get_family_handle_list():
                fam = self.database.get_family_from_handle(handle)
                if handle in fams:
                    self.write_xml_family(fam)
                    fams.remove(handle)
        self.xml_file.write('</families>\n')
        
        self.write_xml_end()
        xml_file.close()
    
    def write_xml_head(self):
        """
        Writes the header part of the xml file.
        """
        self.xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.xml_file.write('<!DOCTYPE database PUBLIC "-//GRAMPS//DTD GRAMPS XML 1.4.0//EN"\n')
        self.xml_file.write('"http://gramps-project.org/xml/1.4.0/grampsxml.dtd">\n')
        self.xml_file.write('<database xmlns="http://gramps-project.org/xml/1.4.0/">\n')

    def write_xml_event(self, event_ref):
        """
        Writes the event part of the xml file.
        """
        
        event = find_event(self.database, event_ref.ref)
        etype = event.get_type().xml_str()
        date = event.get_date_object()
        if self.inc_places:
            placeh = event.get_place_handle()
            place_title = None
            if placeh:
                place_title = self.database.get_place_from_handle(placeh).get_title()
        local_date = DateHandler.displayer.display(date)
        
        self.xml_file.write('<event id="%s" handle="%s">\n' % (event.get_gramps_id(), event.handle))
        self.xml_file.write('<type>%s</type>\n' % etype)
        if date:
            
            # DTD needs date object, use translated date for report 
            
            self.xml_file.write('<dateval val=%s/>\n' % \
                    xml.sax.saxutils.quoteattr(local_date))
        if self.inc_places and place_title:
            self.xml_file.write('<placetval val=%s/>\n' % \
                    xml.sax.saxutils.quoteattr(place_title))
        self.xml_file.write('</event>\n')
        
    def write_xml_person(self, identifiant, child, gender, first, surname, event_list):
        """
        Writes the person part of the xml file.
        """
                 
        self.xml_file.write('<person id="%s" handle="%s">\n' % (identifiant, child))
        self.xml_file.write('<gender>%s</gender>\n' % gender)
        self.xml_file.write('<name>\n')
        if first:
            self.xml_file.write('<first>%s</first>\n' % \
                    xml.sax.saxutils.escape(first))
        if surname:
            self.xml_file.write('<last>%s</last>\n' % \
                    xml.sax.saxutils.escape(surname))
        self.xml_file.write('</name>\n')
        for event_ref in event_list:
                if event_ref.get_role() == gen.lib.EventRoleType.PRIMARY:
                    event = find_event(self.database, event_ref.ref)
                    self.xml_file.write('<eventref hlink="%s"/>\n' % event.handle)
        self.xml_file.write('</person>\n')
        
    def write_xml_family(self, fam):
        """
        Writes the family part of the xml file.
        """
        fhandle = fam.get_father_handle()
        mhandle = fam.get_mother_handle()
        children = fam.get_child_ref_list()
        
        self.xml_file.write('<family id="%s" handle="%s">\n' % (fam.get_gramps_id(), fam.handle))
        if fhandle:
            self.xml_file.write('<father hlink="%s"/>\n' % fhandle)
        if mhandle:
            self.xml_file.write('<mother hlink="%s"/>\n' % mhandle)
        for handle in children:
            child = self.database.get_person_from_handle(handle.ref)
            self.xml_file.write('<childref hlink="%s"/>\n' % child.handle)
        self.xml_file.write('</family>\n')
        
    def write_xml_end(self):
        """
        Writes the close part of the xml file.
        """
        self.xml_file.write('</database>\n')
        
def draw_text(text, x, y):
    (total_w, total_h) = size_text(text)
    for (size, color, line) in text:
        ctx.select_font_face(font_name)
        ctx.set_font_size(base_font_size * size)
        (ascent, _, height, _, _) = ctx.font_extents()
        (
            lx,
            _,
            width,
            _,
            _,
            _,
            ) = ctx.text_extents(line)
        ctx.move_to(x - lx + TEXT_PAD + (total_w - width + lx) / 2, y
                     + ascent + TEXT_PAD)
        ctx.set_source_rgb(*color)
        ctx.show_text(line)
        y += height + TEXT_LINE_PAD


def size_text(text):
    text_width = 0
    text_height = 0
    first = True
    for (size, color, line) in text:
        if first:
            first = False
        else:
            text_height += TEXT_LINE_PAD
        ctx.select_font_face(font_name)
        ctx.set_font_size(base_font_size * size)
        (_, _, height, _, _) = ctx.font_extents()
        (
            lx,
            _,
            width,
            _,
            _,
            _,
            ) = ctx.text_extents(line)
        text_width = max(text_width, width - lx)
        text_height += height
    text_width += 2 * TEXT_PAD
    text_height += 2 * TEXT_PAD
    return (text_width, text_height)


mem_depth = 0


class Memorised:

    def get(self, name):
        try:
            getattr(self, '_memorised')
        except:
            self._memorised = {}

        global mem_depth
        mem_depth += 1
        if name in self._memorised:
            cached = '*'
            v = self._memorised[name]
        else:
            cached = ' '
            v = getattr(self, name)()
            self._memorised[name] = v

        mem_depth -= 1
        return v


class Person(Memorised):

    def __init__(self, text):
        self.text = text

        self.families = []
        self.from_family = None
        self.prevsib = None
        self.nextsib = None

        self.generation = None

    def __str__(self):
        return '[' + self.text + ']'

    def add_family(self, fam):
        if self.families != []:
            self.families[-1].nextfam = fam
            fam.prevfam = self.families[-1]
        self.families.append(fam)

    def draw(self):
        set_bg_style(ctx)
        ctx.rectangle(self.get('x'), self.get('y'), self.get('w'),
                      self.get('h'))
        ctx.fill()

        draw_text(self.text, self.get('tx'), self.get('y'))

        for f in self.families:
            f.draw()

    def x(self):
        if self.from_family is None:
            return 0
        else:
            return self.from_family.get('cx') + self.get('o')

    def tx(self):
        return (self.get('x') + self.get('go')) - self.get('tw') / 2

    def y(self):
        if self.from_family is None:
            return 0
        else:
            return self.from_family.get('cy')

    def tw(self):
        return size_text(self.text)[0]

    def th(self):
        return size_text(self.text)[1]

    def glh(self):
        return reduce(lambda a, b: a + b, [f.get('glh') for f in
                      self.families], 0)

    def o(self):
        if self.prevsib is None:
            return 0
        else:
            return self.prevsib.get('o') + self.prevsib.get('w') + C_PAD

    def ch(self):
        ch = reduce(max, [f.get('ch') for f in self.families], 0)
        if ch != 0:
            ch += O_DOWN + C_UP
        return ch

    def w(self):
        w = self.get('go') + self.get('tw') / 2
        w = max(w, MIN_C_WIDTH)
        if self.families != []:
            ff = self.families[0]
            to_sp = self.get('go') + ff.get('flw')
            w = max(w, to_sp + ff.spouse.get('tw') / 2)
            w = max(w, (to_sp - FL_PAD + ff.get('cw')) - ff.get('oloc'))
        return w

    def h(self):
        return self.get('th') + self.get('glh') + self.get('ch')

    def go(self):
        go = self.get('tw') / 2
        if self.families != []:
            lf = self.families[-1]
            if lf.children != []:
                go = max(go, lf.get('oloc') - (lf.get('flw') - FL_PAD))
        return go

    def to(self):
        return self.get('go') - self.get('tw') / 2

    def glx(self):
        return self.get('x') + self.get('go')


class Family(Memorised):

    def __init__(self, main, spouse):
        self.main = main
        self.spouse = spouse

        self.children = []
        self.prevfam = None
        self.nextfam = None

        main.add_family(self)

        self.generation = None

    def __str__(self):
        return '(:' + str(self.main) + '+' + str(self.spouse) + ':)'

    def add_child(self, child):
        if self.children != []:
            self.children[-1].nextsib = child
            child.prevsib = self.children[-1]
        self.children.append(child)
        child.from_family = self

    def draw(self):
        (px, py) = (self.main.get('x'), self.main.get('y'))

        set_line_style(ctx)
        ctx.new_path()
        ctx.move_to(self.get('glx'), self.get('gly'))
        ctx.rel_line_to(0, self.get('glh'))
        ctx.rel_line_to(self.get('flw'), 0)
        ctx.rel_line_to(0, -S_UP)
        ctx.stroke()

        draw_text(self.spouse.text, self.get('spx'), self.get('spy'))

        if self.children != []:
            set_line_style(ctx)
            ctx.new_path()
            ctx.move_to(self.get('olx'), self.get('oly'))
            ctx.rel_line_to(0, self.get('olh'))
            ctx.stroke()

            ctx.new_path()
            ctx.move_to(self.children[0].get('glx'), self.get('cly'))
            ctx.line_to(self.children[-1].get('glx'), self.get('cly'))
            ctx.stroke()

            for c in self.children:
                set_line_style(ctx)
                ctx.new_path()
                ctx.move_to(c.get('glx'), self.get('cly'))
                ctx.rel_line_to(0, C_UP)
                ctx.stroke()

                c.draw()

    def glx(self):
        return self.main.get('glx')

    def gly(self):
        if self.prevfam is None:
            return self.main.get('y') + self.main.get('th')
        else:
            return self.prevfam.get('gly') + self.prevfam.get('glh')

    def spx(self):
        return (self.get('glx') + self.get('flw'))\
             - self.spouse.get('tw') / 2

    def spy(self):
        return ((self.get('gly') + self.get('glh')) - S_UP)\
             - self.spouse.get('th')

    def olx(self):
        return (self.get('glx') + self.get('flw')) - FL_PAD

    def oly(self):
        return self.get('gly') + self.get('glh')

    def cx(self):
        return ((self.main.get('x') + self.main.get('go')
                 + self.get('flw')) - FL_PAD) - self.get('oloc')

    def cly(self):
        return self.get('oly') + self.get('olh')

    def cy(self):
        return self.get('cly') + C_UP

    def glh(self):
        if self.prevfam is None:
            return S_DOWN
        else:
            return S_VPAD + self.spouse.get('th') + S_UP

    def flw(self):
        flw = 2 * FL_PAD
        flw = max(flw, self.main.get('tw') / 2 + self.spouse.get('tw')
                   / 2 + SP_PAD)
        if self.nextfam is not None:
            flw = max(flw, self.nextfam.get('flw')
                       + self.nextfam.spouse.get('tw') + OL_PAD)
            flw = max(flw, self.nextfam.get('flw')
                       - self.nextfam.get('oloc')
                       + self.nextfam.get('cw') + F_PAD
                       + self.get('oloc'))
        return flw

    def olh(self):
        if self.nextfam is None:
            return O_DOWN
        else:
            return self.nextfam.get('olh') + self.nextfam.get('glh')

    def cw(self):
        if self.children == []:
            return 0
        else:
            return self.children[-1].get('o')\
                 + self.children[-1].get('w')

    def ch(self):
        return reduce(max, [c.get('h') for c in self.children], 1)

    def oloc(self):
        if self.children == []:
            return 0
        else:
            return reduce(lambda a, b: a + b, [c.get('o') + c.get('go')
                          for c in self.children]) / len(self.children)


def load_gramps(fn, start):
    f = open(fn, 'r')
    #f = gzip.open(fn, 'r')
    x = xml.dom.minidom.parse(f)
    f.close()

    def get_text(nodes):
        if nodes == []:
            return None
        for cn in nodes[0].childNodes:
            if cn.nodeType == nodes[0].TEXT_NODE:
                return cn.data
        return None


    class InPerson:

        def __init__(self):
            self.gender = None
            self.first = None
            self.prefix = None
            self.last = None
            self.birth = None
            self.death = None

        def text(self, expected_last=None):
            first_size = 1.0
            last_size = 0.95
            life_size = 0.90

            if self.gender == 'M':
                col = (0, 0, 0.5)
            elif self.gender == 'F':
                col = (0.5, 0, 0)
            else:
                col = (0, 0.5, 0)
            last_col = (0, 0, 0)
            life_col = (0.2, 0.2, 0.2)

            last = self.last
#            if last == expected_last:
#                last = None
            if last is not None:
                if self.prefix is not None:
                    last = self.prefix + ' ' + last
#                last = last.upper()
            if self.first is None and last is None:
                s = []
            elif self.first is None:
                s = [(first_size, col, '?'), (last_size, last_col,
                     last)]
            elif last is None:
                s = [(first_size, col, self.first)]
            else:
                s = [(first_size, col, self.first), (last_size,
                     last_col, last)]

            if self.birth is not None:
                s.append((life_size, life_col, _('b. ') + self.birth))
            if self.death is not None:
                s.append((life_size, life_col, _('d. ') + self.death))

            return s


    Unknown = InPerson()
    Unknown.first = _('Unknown')

    handletoid = {}
    eventtoid = {}
    tpeople = {}
    people = x.getElementsByTagName('people')[0]
    for p in people.getElementsByTagName('person'):
        id = p.getAttribute('id')
        handle = p.getAttribute('handle')
        handletoid[handle] = id
        name = p.getElementsByTagName('name')[0]
        po = InPerson()
        po.gender = get_text(p.getElementsByTagName('gender'))
        po.first = get_text(name.getElementsByTagName('first'))
        po.last = get_text(name.getElementsByTagName('last'))
        ls = name.getElementsByTagName('last')
        if ls != []:
            po.prefix = ls[0].getAttribute('prefix')
        for er in p.getElementsByTagName('eventref'):
            eventtoid[er.getAttribute('hlink')] = id
        tpeople[id] = po

    events = x.getElementsByTagName('events')[0]
    for ev in events.getElementsByTagName('event'):
        p_id = eventtoid.get(ev.getAttribute('handle'))
        if p_id is None:
            continue
        po = tpeople[p_id]
        etype = get_text(ev.getElementsByTagName('type'))
        dvs = ev.getElementsByTagName('dateval')
        date = None
        if len(dvs) > 0:
            date = ev.getElementsByTagName('dateval')[0].getAttribute('val')
        else:
            print 'Undated event: ' + ev.getAttribute('handle')

        if INC_PLACES:
            ptv = ev.getElementsByTagName('placetval')
            placet = None
            if len(ptv) > 0:
                placet = ev.getElementsByTagName('placetval')[0].getAttribute('val')
            else:
                print 'Unplacetd event: ' + ev.getAttribute('handle')

            if len(dvs) == 0 and len(ptv) == 0:
                continue

        elif len(dvs) == 0:
            continue

        if etype == 'Birth':
            po.birth = date
            if INC_PLACES:
                if placet:
                    po.birth += ' - ' + placet
        elif etype == 'Death':
            po.death = date
            if INC_PLACES:
                if placet:
                    po.death += ' - ' + placet
        else:
            print 'Unknown event type: ' + etype


    class InFamily:

        def __init__(self):
            self.a = None
            self.b = None
            self.children = []

        def spouse(self, s):
            if s == self.a:
                return self.b
            else:
                return self.a


    parents = {}
    tfamilies = {}
    families = x.getElementsByTagName('families')[0]
    
    # TODO: need to use new filter rules for matching this on tmp XML file
    
    for f in families.getElementsByTagName('family'):
        id = f.getAttribute('id')
        fo = InFamily()
        for p in f.getElementsByTagName('father'):
            fo.a = handletoid[p.getAttribute('hlink')]
            parents.setdefault(fo.a, []).append(id)
        for p in f.getElementsByTagName('mother'):
            fo.b = handletoid[p.getAttribute('hlink')]
            parents.setdefault(fo.b, []).append(id)
        for p in f.getElementsByTagName('childref'):
            fo.children.append(handletoid[p.getAttribute('hlink')])
        tfamilies[id] = fo

    def do_person(p_id, expected_last=None):
        po = tpeople[p_id]
        p = Person(po.text(expected_last))
        if p_id in parents:
            for fid in parents[p_id]:
                fo = tfamilies[fid]
                last = po.last
                if fo.spouse(p_id):
                    spo = tpeople[fo.spouse(p_id)]
                    fm = Family(p, Person(spo.text()))
                    if spo.gender == 'M':
                        last = spo.last
                else:
                    print 'Unknown spouse:', p_id
                    fm = Family(p, Person(Unknown.text()))
                for cpid in fo.children:
                    cpo = tpeople[cpid]
                    fm.add_child(do_person(cpid, last))
        return p

    return do_person(start)


def set_bg_style(ctx):
    ctx.set_source_rgb(1.0, 1.0, 1.0)


def set_line_style(ctx):
    ctx.set_source_rgb(0.3, 0.3, 0.3)


def draw_tree(head):
    ctx.select_font_face(font_name)
    ctx.set_font_size(base_font_size)
    ctx.set_line_width(2)
    ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
    ctx.set_line_join(cairo.LINE_JOIN_MITER)
    set_line_style(ctx)
    head.draw()

class PNGWriter:

    def start(
        self,
        fn,
        w,
        h,
        ):
        self.fn = fn
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w
                 + 1), int(h + 1))
        return self.surface

    def finish(self):
        self.surface.write_to_png(self.fn)


def draw_file(p, fn, writer):
    global ctx

    surface = writer.start(fn, 10, 10)
    ctx = cairo.Context(surface)
    draw_tree(p)
    (w, h) = (p.get('w'), p.get('h'))

    surface = writer.start(fn, w, h)
    ctx = cairo.Context(surface)
    draw_tree(p)
    ctx.show_page()
    writer.finish()
 

#------------------------------------------------------------------------
#
# DescendantsLines
#
#------------------------------------------------------------------------
class DescendantsLinesOptions(MenuReportOptions):

    """
    Defines options.
    """

    def __init__(self, name, dbase):
        self.__db = dbase
        self.__pid = None
        MenuReportOptions.__init__(self, name, dbase)

    def add_menu_options(self, menu):
        """
        Add options to the menu for the report.
        """

        category_name = _('Report Options')

        pid = PersonOption(_('Center Person'))
        pid.set_help(_('The center person for the report'))
        menu.add_option(category_name, 'pid', pid)

        output_fn = DestinationOption(_("Destination"),
            os.path.join(const.USER_HOME,"DescendantsLines.png"))
        output_fn.set_help(_("The destination file for the png-content."))
        menu.add_option(category_name, "output_fn", output_fn)

        inc_places = BooleanOption(_('Include event places'), False)
        inc_places.set_help(_('Whether to include event places in the output.'))
        menu.add_option(category_name, 'inc_places', inc_places)

        category_name = _('Options S')
       
        s_down = NumberOption(_("S_DOWN"), 20, 0, 50)
        s_down.set_help(_("The length of the vertical edge from descendant to spouse-bar."))
        menu.add_option(category_name, "S_DOWN", s_down)
        
        s_up = NumberOption(_("S_UP"), 10, 0, 50)
        s_up.set_help(_("The length of the vertical edge from spouse-bar to spouse."))
        menu.add_option(category_name, "S_UP", s_up)
        
        s_vpad = NumberOption(_("S_VPAD"), 10, 0, 50)
        s_vpad.set_help(_("The number of ??? vpad"))
        menu.add_option(category_name, "S_VPAD", s_vpad)
        
        sp_pad = NumberOption(_("SP_PAD"), 10, 0, 50)
        sp_pad.set_help(_("The number of ??? pad"))
        menu.add_option(category_name, "SP_PAD", sp_pad)
        
        category_name = _('Options F')
        
        f_pad = NumberOption(_("F_PAD"), 20, 0, 50)
        f_pad.set_help(_("The number of ??? pad"))
        menu.add_option(category_name, "F_PAD", f_pad)
        
        fl_pad = NumberOption(_("FL_PAD"), 20, 0, 50)
        fl_pad.set_help(_("The number of ??? pad"))
        menu.add_option(category_name, "FL_PAD", fl_pad)
        
        category_name = _('Options O')
        
        ol_pad = NumberOption(_("OL_PAD"), 10, 0, 50)
        ol_pad.set_help(_("The number of ??? pad"))
        menu.add_option(category_name, "OL_PAD", ol_pad)
        
        o_down = NumberOption(_("O_DOWN"), 30, 0, 50)
        o_down.set_help(_("The length of the vertical edge from spouse-bar to child-bar."))
        menu.add_option(category_name, "O_DOWN", o_down)
        
        category_name = _('Options C')
        
        c_pad = NumberOption(_("C_PAD"), 10, 0, 50)
        c_pad.set_help(_("The number of ??? pad"))
        menu.add_option(category_name, "C_PAD", c_pad)
    
        c_up = NumberOption(_("C_UP"), 15, 0, 50)
        c_up.set_help(_("The length of the vertical edge from child to child-bar."))
        menu.add_option(category_name, "C_UP", c_up)
        
        min_c_width = NumberOption(_("MIN_C_WIDTH"), 40, 0, 50)
        min_c_width.set_help(_("The number of ??? min width"))
        menu.add_option(category_name, "MIN_C_WIDTH", min_c_width)
        
        category_name = _('Options Text')
        
        text_pad = NumberOption(_("TEXT_PAD"), 2, 0, 50)
        text_pad.set_help(_("The number of text pad ???"))
        menu.add_option(category_name, "TEXT_PAD", text_pad)
        
        text_line_pad = NumberOption(_("TEXT_LINE_PAD"), 2, 0, 50)
        text_line_pad.set_help(_("The number of text line pad ??? "))
        menu.add_option(category_name, "TEXT_LINE_PAD", text_line_pad)
        
    def make_default_style(self, default_style):
        """Make the default output style"""

        font = FontStyle()
        font.set_size(12)
        font.set_type_face(FONT_SANS_SERIF)
        font.set_bold(1)
        para = ParagraphStyle()
        para.set_top_margin(ReportUtils.pt2cm(base_font_size))
        para.set_font(font)
        para.set_alignment(PARA_ALIGN_LEFT)
        para.set_description(_('The style used for the name of person.'))
        default_style.add_paragraph_style('DL-name', para)
