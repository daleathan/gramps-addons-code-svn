# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009        Brian G. Matherly
# Copyright (C) 2009        Michiel D. Nauta
# Copyright (C) 2010        Douglas S. Blank
# Copyright (C) 2013        Jerome Rapinat
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

# $Id: $

#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
from __future__ import print_function

import codecs
import sys
import os
import gtk
from xml.etree import ElementTree
import gzip

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gen.plug import Gramplet
from gen.lib import date, note
import DateHandler
from TransUtils import get_addon_translator
_ = get_addon_translator(__file__).ugettext
import const
import Utils
import GrampsDisplay
from QuestionDialog import ErrorDialog
from Filters import GenericFilter, Rules

import diff


#from Merge.mergeevent import MergeEventQuery
#from Merge.mergeperson import MergePersonQuery
#from Merge.mergefamily import MergeFamilyQuery
#from Merge.mergesource import MergeSourceQuery
#from Merge.mergecitation import MergeCitationQuery
#from Merge.mergeplace import MergePlaceQuery
#from Merge.mergemedia import MergeMediaQuery
#from Merge.mergerepository import MergeRepoQuery
#from Merge.mergenote import MergeNoteQuery



NAMESPACE = '{http://gramps-project.org/xml/1.5.0/}'

    
#-------------------------------------------------------------------------    

# python 2.6 / 2.7 / 3.0
# name for getiterator / iter (ElementTree 1.2 vs 1.3)

if sys.version_info[0] == 3:
    raise ValueError('Not written for python 3.0 and greater!')

#-------------------------------------------------------------------------
#
# Timestamp convertor
#
#-------------------------------------------------------------------------
def epoch(t):
        """
        Try to convert timestamp
        """
        
        try:
            from datetime import datetime
            from time import strftime
        except:
            return
        
        if t == None:
            print(_('Invalid timestamp'))
            fmt = _('Unknown')
        else:
            date = int(t)
            conv = datetime.fromtimestamp(date)
            fmt = conv.strftime('%d %B %Y')
        
        return(fmt)

#-------------------------------------------------------------------------
#
# The gramplet
#
#-------------------------------------------------------------------------

class bckGramplet(Gramplet):
    """
    Gramplet for testing etree (python 2.7) and Gramps XML parsing
    """
    
    def init(self):
        """
        Constructs the GUI, consisting of an entry, a text view and 
        a Run button.
        """  
                     
        # filename and selectors
        
        self.__base_path = const.USER_HOME
        if self.dbstate.db.db_is_open:
            dbname = str(self.dbstate.db.get_dbname())
            self.__file_name = dbname + ".gramps"
        else:
            self.__file_name = "test.gramps"
        self.entry = gtk.Entry()
        self.entry.set_text(os.path.join(self.__base_path, self.__file_name))
        
        self.button = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        self.button.add(image)
        self.button.connect('clicked', self.__select_file)
        
        #self.filter_note = None
        
        #notes_cell = gtk.CellRendererText()
        #notes_cell.set_property('ellipsize', pango.ELLIPSIZE_END)
        #self.filter_note.pack_start(notes_cell, True)
        #self.filter_note.add_attribute(notes_cell, 'text', 0)
        
        # GUI setup:
        
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        
        # area
        
        self.import_text = gtk.TextView()
        
        self.import_text.set_wrap_mode(gtk.WRAP_WORD)
        self.import_text.set_editable(False)
        
        self.text = gtk.TextBuffer()
        self.text.set_text(_('No file parsed...'))
        self.import_text.set_buffer(self.text)
        
        vbox.pack_start(self.import_text, True, True, 0) # v1
        
        # button
        
        button = gtk.Button(_("Run"))
        button.connect("clicked", self.run)
        vbox.pack_start(button, False, False, 0) # v2
        
        # build
        
        hbox.pack_start(self.entry, True, True, 0)
        hbox.pack_end(self.button, False, False, 0)
        
        vbox.pack_end(hbox, False, False, 0) # v3
        
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(vbox)
        
        vbox.show_all()
        
        
    def __select_file(self, obj):
        """
        Call back function to handle the open button press
        """
        
        my_action = gtk.FILE_CHOOSER_ACTION_SAVE
        
        if self.dbstate.db.db_is_open:
            dbname = str(self.dbstate.db.get_dbname())
        else:
            dbname = 'etree'
        
        dialog = gtk.FileChooserDialog(dbname,
                                       action=my_action,
                                       buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_OPEN,
                                                gtk.RESPONSE_OK))

        name = os.path.basename(self.entry.get_text())
        dialog.set_current_name(name)
        dialog.set_current_folder(self.__base_path)
        dialog.present()
        status = dialog.run()
        if status == gtk.RESPONSE_OK:
            self.set_filename(Utils.get_unicode_path_from_file_chooser(dialog.get_filename()))
        dialog.destroy()
        

    def set_filename(self, path):
        """ 
        Set the currently selected dialog.
        """
        
        if not path:
            return
        if os.path.dirname(path):
            self.__base_path = os.path.dirname(path)
            self.__file_name = os.path.basename(path)
        else:
            self.__base_path = os.getcwd()
            self.__file_name = path
        self.entry.set_text(os.path.join(self.__base_path, self.__file_name))
        

    def post_init(self):
        self.disconnect("active-changed")
        

    def run(self, obj):
        """
        Method that is run when you click the Run button.
        """
        
        entry = self.entry.get_text()
        if ' ' in entry:
            ErrorDialog(_('Space character on filename'), _('Please fix space on "%s"') % entry)
            return
        
        self.ReadXML(entry)
                                                       
        
    def ReadXML(self, entry):
        """
        Read the .gramps
        """
        
        self.text.set_text('Reading the file...')    
        use_gzip = 1
        try:
            test = gzip.open(entry, "r")
            test.read(1)
            test.close()
        except IOError, msg:
            use_gzip = 0
         
        # lazy ...
        if os.name != 'posix':
            
            # GtkTextView
            
            self.text.set_text(_('Sorry, no support for your OS yet!'))
            return
            
        if self.dbstate.db.db_is_open and not ' ' in self.dbstate.db.get_dbname():
            filename = os.path.join(self.dbstate.db.path, self.dbstate.db.get_dbname() + '.xml')
        else:
            filename = os.path.join(const.USER_PLUGINS, 'etree.xml')
        
        #self.get_db(filename)
                
        if use_gzip == 1:
            try:
                os.system('gunzip < %s > %s' % (entry, filename))
            except:
                ErrorDialog(_('Is it a compressed .gramps?'), _('Cannot uncompress "%s"') % entry)
                return
            sys.stdout.write(_('From:\n "%(file1)s"\n to:\n "%(file2)s".\n') % {'file1': entry, 'file2': filename})
        else:
            try:
                os.system('cp %s %s' % (entry, filename))
            except:
                ErrorDialog('Is it a .gramps ?', _('Cannot copy "%s"') % entry)
                return
            sys.stdout.write(_('From:\n "%(file1)s"\n to:\n "%(file2)s".\n') % {'file1': entry, 'file2': filename})
          
        tree = ElementTree.parse(filename)
        self.ParseXML(tree, filename)
                     
        
    def ParseXML(self, tree, filename):
        """
        Parse the .gramps
        """
        
        root = tree.getroot()
        
        # GtkTextView ; buffer limitation ...
                      
        #self.text.set_text(ElementTree.tostring(root))
        
        # timestamp
        
        timestamp = []
        
        # XML attributes
        
        # CVS, RCS like
        keys = []
        
        # counters
        events = []
        eventrefs = []  
        people = []
        families = []
        sources = []
        sourcerefs = []
        citations = []
        citationrefs = []
        
        # DB: Family Tree loaded
        # see gen/plug/_gramplet.py and gen/db/read.py
        
        #if self.dbstate.db.db_is_open:
            #print('tags', self.dbstate.db.get_number_of_tags())
        
        #print(self.dbstate.db.surname_list)
        
        # XML
                
        for one in root.getchildren():
			
            # getiterator() for python 2.6
            ITERATION = one.getiterator()
            
            # iter() for python 2.7 and greater versions
            if sys.version_info[1] == 7:
                ITERATION = one.iter()
            
            # Primary objects (samples)
            
            # find() needs memory - /!\ large files
            
            # FutureWarning: 
            # The behavior of this method will change in future versions.  
            # Use specific 'len(elem)' or 'elem is not None' test instead.
            
            #if one.find(NAMESPACE + 'event'):
                #print('XML: Find all "event" records: %s' % len(one.findall(NAMESPACE + 'event')))
            
            for two in ITERATION:
                
                timestamp.append(two.get('change'))
                
                (tag, item) = two.tag, two.items()
                #print(tag)
                #print(two.attrib)
                
                # two for serialisation (complete data/sequence) and/or ElementTree
                keys.append((two, item))
                                                
                if tag == NAMESPACE + 'event':
                    events.append(two)
                if tag == NAMESPACE + 'eventref':
                    eventrefs.append(item)
                if tag == NAMESPACE + 'person':
                    people.append(two)
                if tag == NAMESPACE + 'family':
                    families.append(two)
                if tag == NAMESPACE + 'source':
                    sources.append(two)
                if tag == NAMESPACE + 'sourceref':
                    sourcerefs.append(item)
                if tag == NAMESPACE + 'citation':
                    citations.append(two)
                if tag == NAMESPACE + 'citationref':
                    citationrefs.append(item)
                    
        
        self.DummyXML(filename, root)
                            
        root.clear()
                                    
        # to see changes and match existing handles (Family Tree loaded)
        
        #for key in keys:
            #print(key)
            
        # XML
        
        timestamp.sort()
        
        # GtkTextView
         
        self.counters(events, eventrefs, people, families, sources, sourcerefs,\
                       citations, citationrefs)
        
        # DB
        
        if self.dbstate.db.db_is_open:
            self.change()
        
    
    def change(self):
        """
        obj.get_change_time(); Family Tree loaded
        """
        
        # event object
        
        tevent = []
        
        for handle in self.dbstate.db.get_event_handles():
            event = self.dbstate.db.get_event_from_handle(handle)
            tevent.append(event.get_change_time())
        
        tevent.sort()
        
        try:
            elast = epoch(tevent[-1])
            #print('DB: Last event object edition on/at:', elast)
        except IndexError:
            pass
        
        # person object; alternate method via person_map, see LastChange addon
        
        handles = sorted(self.dbstate.db.get_person_handles(), key=self._getPersonTimestamp)
    
    
    def _getPersonTimestamp(self, person_handle):
        timestamp = self.dbstate.db.person_map.get(str(person_handle))[17]
        return timestamp
    
    
    def get_note(self):
        
        notes_list = []
        notes = self.dbstate.db.get_note_handles()
        for handle in notes:
            # Note filter seems to need IDs
            notes_list.append(self.dbstate.db.note_map.get(handle)[1])
        notes_list.sort()
        
        # I do not know why these lines do not work !
        
        #self.filter_note = GenericFilter()
        #self.filter_note.add_rule(Rules.Note.HasNote(['2013', _('General')]))
        #index = self.filter_note.apply(self.dbstate.db, notes_list)
        
        note = self.dbstate.db.get_note_from_gramps_id(notes_list[-1])
        
        # My internal note handle
        #note_handle = 'c8c202feca8198236b7'
        
        return note.handle
    
    
    def get_db(self, filename):
        diff.import_as_dict(filename)
    
    
    def counters(self, events, eventrefs, people, families, sources, sourcerefs, \
                    citations, citationrefs):
        """
        Set of counters for parsed Gramps XML and loaded family tree
        """
        
        records = []
        grouped_records = []
        change_time = '000000'
        
        if self.dbstate.db.db_is_open:
            last_note_id_or_with_2013_text = self.get_note()
            for handle in self.dbstate.db.get_note_handles():
                if self.dbstate.db.note_map.get(handle)[0] == last_note_id_or_with_2013_text:
                    self.text.set_text(self.dbstate.db.note_map.get(handle)[2][0])
                    
                    change_time = self.dbstate.db.note_map.get(handle)[5]
                
                    print(self.dbstate.db.note_map.get(handle)[2][0])
                
                    handles = [citasource_handle for (object_type, citasource_handle) in
                             self.dbstate.db.find_backlink_handles(handle)]
        
        
        person = _('\n\tDiff Persons : %s\n') % (self.dbstate.db.pmap_index - len(people))
        family = _('\n\tDiff Families : %s\n') % (self.dbstate.db.fmap_index - len(families))
        
        event = _('\n\tDiff Events : %s\n') % (self.dbstate.db.emap_index - len(events))
        
        ecount = 0
        for attributes in eventrefs:
            if self.dbstate.db.event_map.get(attributes[1][1][1:]) == None:
                ecount += 1
        
        #last_eprefix = 'e0'
        for handle in self.dbstate.db.get_event_handles():
            etime = str(self.dbstate.db.event_map.get(handle)[10])
            if etime[0:8] == str(change_time)[0:8]:
                records.append("event : "+ str(handle))
                #last_eprefix = str(handle)[0:2]
            #if last_eprefix !=  str(handle)[0:2]:
                #grouped_records.append("event : " + str(handle))
        
        if ecount == len(eventrefs) or ecount == 0:
            event_refs = ''
        else:
            event_refs = '\n\t\tDiff event_refs: %s\n' % (len(eventrefs) - ecount)
        
        citation = _('\n\tDiff Citations : %s\n') % (self.dbstate.db.cmap_index - len(citations))
        
        ccount = 0
        for hlink in citationrefs:
            if self.dbstate.db.citation_map.get(hlink[0][1][1:]) == None:
                ccount += 1

        last_cprefix = 'c0'
        for handle in self.dbstate.db.get_citation_handles():
            ctime = str(self.dbstate.db.citation_map.get(handle)[9])
            if ctime[0:8] == str(change_time)[0:8]:
                records.append("citation : " + str(handle))
                last_cprefix = str(handle)[0:10]
            if last_cprefix !=  str(handle)[0:10]:
                cid = str(self.dbstate.db.citation_map.get(handle)[1])
                grouped_records.append("citation : " + cid + ": " + str(self.dbstate.db.citation_map.get(handle)[3]))
                    
        
        if ccount == len(citationrefs) or ccount == 0:
            citation_refs = ''
        else:
            citation_refs = '\n\t\tDiff citation_refs: %s\n' % (len(citationrefs) - ccount)
        
        source = _('\n\tDiff Sources : %s\n') % (self.dbstate.db.smap_index - len(sources))
        
        scount = 0
        for hlink in sourcerefs:
            if self.dbstate.db.source_map.get(hlink[0][1][1:]) == None:
                scount += 1

        back_sourcerefs = []
        last_sprefix = 's0'
        for handle in self.dbstate.db.get_source_handles():
            stime = str(self.dbstate.db.source_map.get(handle)[8])
            if stime[0:8] == str(change_time)[0:8]:
                for (object_type, sourceref) in self.dbstate.db.find_backlink_handles(handle):
                    # object_type = Citation
                    back_sourcerefs.append((handle, sourceref))
                last_sprefix = str(handle)[0:3]
            if last_sprefix !=  str(handle)[0:3]:
                sid = str(self.dbstate.db.source_map.get(handle)[1])
                grouped_records.append("source : " + sid + ": " + str(self.dbstate.db.source_map.get(handle)[2]))
        
        for (handle, sourceref) in back_sourcerefs:
            cid = str(self.dbstate.db.citation_map.get(sourceref)[1])
            sid = str(self.dbstate.db.source_map.get(handle)[1])
            records.append("source : " + str(handle) + " \t" + sid + '<=>' + cid)
        
        if scount == len(sourcerefs) or scount == 0:
            source_refs = ''
        else:
            source_refs = '\n\t\tDiff source_refs: %s\n' % (len(sourcerefs) - scount)
        
        base  = _('\nLoaded Family Tree base:\n "%s"\n' % self.dbstate.db.path)
        
        if not self.dbstate.db.db_is_open:
            handles = []
            
        data = "\n  == Handles (candidats for merging)=="
        merge_count = 0
        for merge in records:
            merge_count += 1
            data = data + "\n%s\t%s" % (merge_count, merge)
        merge_count =0
        data = data + "\n == Groups of handles (not created by batch or import) =="
        for period_record in grouped_records:
            merge_count += 1
            data = data + "\n%s\t%s" % (merge_count, period_record )
        
        records = grouped_records = []
            
        if len(handles) < 2:
            repair = ''
        else:
            repair = _("\nIt seems that %s records have been fixed recently,\n"
                "do you want to try to merge them via your backup file?\n%s") % (len(handles), data)
        
        data = []
        
        preview = person + family + event + event_refs + citation + citation_refs + \
                  source + source_refs + base + repair
        
        self.text.set_text(preview)
        
        
        
    def DummyXML(self, filename, root):
        """
        Write the content back into the XML file copy as a dummy Gramps scheme
        """
                      
        # Modify the XML copy of the .gramps
        
        outfile = open(filename, 'w')
        self.outfile = codecs.getwriter("utf8")(outfile)
        
        # events, people, families (stored as Element)
        parent_node = '/..'
        where_cit_on_events = root.findall('./' + NAMESPACE + 'events//' + NAMESPACE + 'citationref' + parent_node)
        where_cit_on_individuals = root.findall('./' + NAMESPACE + 'people//' + NAMESPACE + 'citationref' + parent_node)
        where_cit_on_families = root.findall('./' + NAMESPACE + 'families//' + NAMESPACE + 'citationref'  + parent_node)
        attributes = root.findall('.//' + NAMESPACE + 'attribute/' + NAMESPACE + 'citationref')
        
        print('Attributes with citation reference:', len(attributes))
        
        attributes = []
        
        cit_on_eatt = []
        for element in where_cit_on_events:
            if element.attrib.get('type'): # attribute(s) on event with citations
                cit_on_eatt.append(element.findall('./' + NAMESPACE + 'citationref'))
        
        print('Attributes on events with citation reference:', len(cit_on_eatt))
        
        cit_on_patt = []
        for element in where_cit_on_individuals:
            if element.attrib.get('type'): # attribute(s) on person with citations
                cit_on_patt.append(element.findall('./' + NAMESPACE + 'citationref'))
                
        print('Attributes on people with citation reference:', len(cit_on_patt))
        
        cit_on_fatt = []
        for element in where_cit_on_families:
            if element.attrib.get('type'): # attribute(s) on family with citations
                cit_on_fatt.append(element.findall('./' + NAMESPACE + 'citationref'))
                
        print('Attributes on families with citation reference:', len(cit_on_fatt))
        
        #for parent in cit_on_eatt:
            #if len(parent) < 2:
                #handle = parent[0].attrib.get('hlink')[1:]
                #if self.dbstate.db.citation_map.get(handle):
                    #key = str(self.dbstate.db.citation_map.get(handle)[0])
                    #cid = str(self.dbstate.db.citation_map.get(handle)[1])
                    #date = str(self.dbstate.db.citation_map.get(handle)[2])
                    #page = str(self.dbstate.db.citation_map.get(handle)[3])
                    #quay = str(self.dbstate.db.citation_map.get(handle)[4])
                    #print('event: ',  cid + " " + key + " " + date + " " + page + " " + quay)
                #else:
                    #print('event: ', root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle))
            #else:
                #for i in range(len(parent)):
                    #handle = parent[i].attrib.get('hlink')[1:]
                    #if self.dbstate.db.citation_map.get(handle):
                        #key = str(self.dbstate.db.citation_map.get(handle)[0])
                        #cid = str(self.dbstate.db.citation_map.get(handle)[1])
                        #date = str(self.dbstate.db.citation_map.get(handle)[2])
                        #page = str(self.dbstate.db.citation_map.get(handle)[3])
                        #quay = str(self.dbstate.db.citation_map.get(handle)[4])
                        #print('event: ',  cid + " " + key + " " + date + " " + page + " " + quay)
                    #else:
                        #print('event: ', root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle))
                        
        #for parent in cit_on_patt:
            #if len(parent) < 2:
                #handle = parent[0].attrib.get('hlink')[1:]
                #if self.dbstate.db.citation_map.get(handle):
                    #key = str(self.dbstate.db.citation_map.get(handle)[0])
                    #cid = str(self.dbstate.db.citation_map.get(handle)[1])
                    #date = str(self.dbstate.db.citation_map.get(handle)[2])
                    #page = str(self.dbstate.db.citation_map.get(handle)[3])
                    #quay = str(self.dbstate.db.citation_map.get(handle)[4])
                    #print('person: ',  cid + " " + key + " " + date + " " + page + " " + quay)
                #else:
                    #print('person: ', root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle))
            #else:
                #for i in range(len(parent)):
                    #handle = parent[i].attrib.get('hlink')[1:]
                    #if self.dbstate.db.citation_map.get(handle):
                        #key = str(self.dbstate.db.citation_map.get(handle)[0])
                        #cid = str(self.dbstate.db.citation_map.get(handle)[1])
                        #date = str(self.dbstate.db.citation_map.get(handle)[2])
                        #page = str(self.dbstate.db.citation_map.get(handle)[3])
                        #quay = str(self.dbstate.db.citation_map.get(handle)[4])
                        #print('person: ',  cid + " " + key + " " + date + " " + page + " " + quay)
                    #else:
                        #print('person: ', root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle))
                        
        #for parent in cit_on_fatt:
            #if len(parent) < 2:
                #handle = parent[0].attrib.get('hlink')[1:]
                #if self.dbstate.db.citation_map.get(handle):
                    #key = str(self.dbstate.db.citation_map.get(handle)[0])
                    #cid = str(self.dbstate.db.citation_map.get(handle)[1])
                    ##date = str(self.dbstate.db.citation_map.get(handle)[2])
                    #page = str(self.dbstate.db.citation_map.get(handle)[3])
                    #quay = str(self.dbstate.db.citation_map.get(handle)[4])
                    #print('family: ',  cid + " " + key + " " + date + " " + page + " " + quay)
                #else:
                    #print('family: ', root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle))
            #else:
                #for i in range(len(parent)):
                    #handle = parent[i].attrib.get('hlink')[1:]
                    #if self.dbstate.db.citation_map.get(handle):
                        #key = str(self.dbstate.db.citation_map.get(handle)[0])
                        #cid = str(self.dbstate.db.citation_map.get(handle)[1])
                        #date = str(self.dbstate.db.citation_map.get(handle)[2])
                        #page = str(self.dbstate.db.citation_map.get(handle)[3])
                        #quay = str(self.dbstate.db.citation_map.get(handle)[4])
                        #print('family: ',  cid + " " + key + " " + date + " " + page + " " + quay)
                    #else:
                        #print('family: ', root.find(root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle))
                        
        
        cit_on_att = cit_on_eatt + cit_on_patt + cit_on_fatt
        print('Nb of entries (could be multiple time):', len(cit_on_att))
        
        cit_on_eatt = cit_on_patt = cit_on_fatt = []
        where_cit_on_events = where_cit_on_individuals = where_cit_on_families = []
        
        for parent in cit_on_att:
            if len(parent) < 2:
                handle = parent[0].attrib.get('hlink')[1:]
                if not self.dbstate.db.citation_map.get(handle):
                    e = root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle)
                    root.append(e)
                    #children = e.itertext()
                    #for value in children:
                        #if value != '2' or value == '': # default for confidence (or empty)
                            #print(e.attrib, value) # citation handle and page/volume
            else:
                for i in range(len(parent)):
                    handle = parent[i].attrib.get('hlink')[1:]
                    if not self.dbstate.db.citation_map.get(handle):
                        e = root.find('.' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % handle)
                        root.append(e)
                        #children = e.itertext()
                        #for value in children:
                            #if value != '2' or value == '': # default for confidence (or empty)
                                #print(e.attrib, value) # citation handle and page/volume
        
        back_refs = []                    
        new_src_handles = []
        for handle in self.dbstate.db.get_source_handles():
            src = self.dbstate.db.get_source_from_handle(handle)
            for (object_type, citationref) in self.dbstate.db.find_backlink_handles(handle):
                if src and src.get_title() == _('Unknown'):
                    new_src_handles.append(citationref)
        
        print(len(new_src_handles))
        
        for src_handle in new_src_handles:
            if root.get('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % src_handle):
                root.append(root.find('./' + NAMESPACE + 'citations/' + NAMESPACE + 'citation[@handle="_%s"]' % src_handle))
        
        primary = ['header', 'tags', 'events', 'people', 'families', 'places', \
                  'objects', 'repositories', 'notes', 'namemaps', 'citations']
        
        print('*** XML copy of tables ***')
        for node in primary:
            record = NAMESPACE + node
            for r in root.findall(record):
                print('Skip %s' % node)
                root.remove(r)
                
        # citations
        
        #cit_text = ['page', 'confidence']
        #cit_attribs = ['dateval', 'data_item', 'sourceref', 'noteref', 'objref']
        
        #for tag in cit_text:
            #print(tag)
            #for entry in root[0].iter(NAMESPACE + tag):
                #print(entry.text)
        
        #for tag in cit_attribs:
            #print(tag)
            #for entry in root[0].iter(NAMESPACE + tag):
                #print(entry.attrib)
                
        # sources
        
        #src_text = ['stitle', 'spubinfo', 'sauthor', 'sabbrev']
        #src_attribs = ['objref', 'data_item', 'noteref', 'reporef']
        
        #for tag in src_text:
            #print(tag)
            #for entry in root[1].iter(NAMESPACE + tag):
                #print(entry.text)
        
        #for tag in src_attribs:
            #print(tag)
            #for entry in root[1].iter(NAMESPACE + tag):
                #print(entry.attrib)
                
        # keys
        
        #cit_handles = []
        
        #for citation_level in root[0]:
            #cit_handle = citation_level.get('handle')
            #cit_handles.append(cit_handle)
        
        
        #clocation = -1
        #for citation_level in root[0][0]:
            #clocation += 1
            
            #cit_hlink = citation_level.get('hlink')
            #if cit_hlink and cit_hlink == None:
                #print('Warning:', root[0][clocation].attrib)
        
        #src_handles = []
        
        #for source_level in root[1]:
            #src_handle = source_level.get('handle')
            #src_handles.append(src_handle)
        
        
        #slocation = -1
        #for source_level in root[1][0]:
            #slocation += 1
                
            #src_hlink = source_level.get('hlink')
            #if src_hlink and src_hlink == None:
                #print('Warning:', root[1][slocation].attrib)
        
        #ElementTree.dump(root)
        
        self.outfile.write(ElementTree.tostring(root, encoding="UTF-8"))

        # close the etree
        
        self.outfile.close()
        
        root.clear()
        
