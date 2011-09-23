# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009       Brian G. Matherly
# Copyright (C) 2010  Douglas S. Blank <doug.blank@gmail.com>
# Copyright (C) 2011       Jerome Rapinat
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
import codecs
import sys
import os
import gtk

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gen.plug import Gramplet
from gen.lib import date
from TransUtils import get_addon_translator
_ = get_addon_translator(__file__).ugettext
import const
import Utils

#-------------------------------------------------------------------------
#
# Try to detect the presence of gzip
#
#-------------------------------------------------------------------------
try:
    import gzip
    GZIP_OK = True
except:
    GZIP_OK = False
    
#-------------------------------------------------------------------------
#
# Try to detect the presence of lxml (only for using XSL)
# else import elementtree.ElementTree as etree
#
#-------------------------------------------------------------------------
try:
    from lxml import etree
    LXML_OK = True
except:
    LXML_OK = False
    print(_('Please, install python lxml package.'))
    
#-------------------------------------------------------------------------
#
# The gramplet
#
#-------------------------------------------------------------------------

class lxmlGramplet(Gramplet):
    """
    Gramplet for testing lxml
    """
    def init(self):
        """
        Constructs the GUI, consisting of an entry, and 
        a Run button.
        """       
        # filename and selector
        self.__base_path = const.USER_HOME
        self.__file_name = "test.gramps"
        self.entry = gtk.Entry()
        self.entry.set_text(os.path.join(self.__base_path, self.__file_name))
        self.button = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        self.button.add(image)
        self.button.connect('clicked', self.__select_file)
        
        # GUI setup:
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        # button
        button = gtk.Button(_("Run"))
        button.connect("clicked", self.run)
        hbox.pack_start(self.entry, True)
        hbox.pack_end(self.button, False, False)
        vbox.pack_start(hbox, False)
        vbox.pack_start(button, False)
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(vbox)
        vbox.show_all()
        
    def __select_file(self, obj):
        """ Call back function to handle the open button press """
        my_action = gtk.FILE_CHOOSER_ACTION_SAVE
        
        dialog = gtk.FileChooserDialog('lxml',
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
        """ Set the currently selected dialog. """
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
        self.ReadXML(entry)
        
    def ReadXML(self, entry):
        """
        Read and parse the .gramps
        """
        
        #if GZIP_OK:
            #use_gzip = 1
            #try:
                #test = gzip.open(entry, "r")
                #test.read(1)
                #test.close()
            #except IOError, msg:
                #use_gzip = 0
            #except ValueError, msg:
                #use_gzip = 1
        #else:
            #use_gzip = 0
         
        # lazy ... only compressed .gramps !
        if os.name != 'posix':
            print(_('Sorry, no support for your OS yet!'))
        
        filename = os.path.join(const.USER_PLUGINS, 'lxml', 'test.xml')
        if LXML_OK and os.name == 'posix':
            print('###################################################')
            sys.stdout.write(_('From:\n %s\n to:\n %s.') % (entry, filename))
            os.system('gunzip < %s > %s' % (entry, filename))
            print('\n###################################################')
        else:
            return
        
        # TODO    
        #self.check_valid(entry)
        
        tree = etree.ElementTree(file=filename)
        root = tree.getroot()

        # namespace issues and 'surname' only on 1.4.0!
        surname_tag = etree.SubElement(root, '{http://gramps-project.org/xml/1.4.0/}surname')
        ptitle_tag = etree.SubElement(root, '{http://gramps-project.org/xml/1.4.0/}ptitle')
        
        # variable
        expr = "//*[local-name() = $name]"
        
        # find text function
        find_text = etree.XPath("//text()", smart_strings=False)

        # count function
        # float and seems to also count the parent tag: name[0] !
        count_elements = etree.XPath("count(//*[local-name() = $name])")
        
        # textual children strings function
        desc = etree.XPath('descendant-or-self::text()')
        
        
        # TODO: cleanup !
        # quick but not a nice method ...
        
        msg = []
        #tags = []
        places = []
        surnames = []
        for kid in root.getchildren():
            #(tag, item) = kid.tag, kid.items()
            #print(tag, item)
            
            for greatchild in kid.getchildren():
                #tags.append(greatchild.tag)  
                msg.append(greatchild.items())
                
                # search ptitle
                for three in greatchild.getchildren():
                    
                    # with namespace ...
                    if three.tag == '{http://gramps-project.org/xml/1.4.0/}ptitle':
                        places.append(three.text)
                        
                    # search last name
                    for four in three.getchildren():
                        
                        # with namespace ...
                        if four.tag == '{http://gramps-project.org/xml/1.4.0/}surname':
                            surnames.append(four.text)  
                    
        #print(etree.tostring(root, pretty_print=True))

        # All tags
        #print(tags)
        
        # keys, values; no textual data; 
        # root child level items as keys for revision control ???
        #revision = msg
        
        #print(revision)
        
        log = msg[0]
        
        # dirty XML write method ...
        # need to create a fake entry !
        
        if count_elements(root, name = 'surname') > 1.0:
            nb_surnames = count_elements(root, name = 'surname') - float(1.0)
        else:
            nb_surnames = surnames = [_('No surname')]
            
        if count_elements(root, name = 'ptitle') > 1.0:
            nb_ptitles = count_elements(root, name = 'ptitle') - float(1.0)
        else:
            nb_ptitles = places = [_('No place title')]
            
        if count_elements(root, name = 'note') > 1.0:
            nb_notes = count_elements(root, name = 'note') - float(1.0)
        else:
            nb_notes = _('No note')
            
        # Some print statements !
        
        print(_('log'), log)
        print(_('Surnames'), nb_surnames)
        print(_('Place titles'), nb_ptitles)
        print(_('Note objects'), nb_notes)
                
        self.WriteXML(log, surnames, places)
        
    def check_valid(self, entry):
        """
        Look at schema, validation, conform, etc...
        Code for 1.4.0 and later (previous versions 'surname' was 'last')
        """    
        
        # TODO: validity check against scheme for file format    
                    
    def WriteXML(self, log, surnames, places):
        """
        Write the result of the query for distibued, shared protocols
        """
        
        # TODO: to look at etree for XML generation ...
        
        time = date.Today()
        query = os.path.join(const.USER_PLUGINS, 'lxml', str(time) + '_query.xml')
        g = open(query,"w")
        self.g = codecs.getwriter("utf8")(g)
        self.g.write('<?xml version="1.0" encoding="UTF-8"?>')
        self.g.write('\n<query>\n')
        [(k1, v1),(k2, v2)] = log
        self.g.write('    <log date="%s" version="%s"/>\n' % (v1, v2))
        self.g.write('    <surnames>\n')
        for surname in surnames:
            self.g.write('        <surname>')
            self.g.write(str(surname))
            self.g.write('</surname>\n')
        self.g.write('    </surnames>\n')
        self.g.write('    <places>\n')
        for place in places:
            self.g.write('        <place>')
            self.g.write(str(place))
            self.g.write('</place>\n')
        self.g.write('    </places>\n')
        self.g.write('</query>\n')
        self.g.close()
        
        print('#######################################################')
        sys.stdout.write(_('Generate:\n %s.') % query)
        print('\n#######################################################')
        
        self.XSLTransform(query)
        
    def XSLTransform(self, query):
        """
        Transform the result of the query; Formatting
        see samples on http://www.rexx.com/~dkuhlman, 
        pyxmlfaq-python-xml-frequently-asked-questions
        """
        
        # simple quick testing
        
        xslt_doc = etree.parse(os.path.join(const.USER_PLUGINS, 'lxml', 'query_html.xsl'))
        transform = etree.XSLT(xslt_doc)
        indoc = etree.parse(query)
        outdoc = transform(indoc)
        html = os.path.join(const.USER_PLUGINS, 'lxml', 'query.html')
        outfile = open(html, 'w')
        outdoc.write(outfile)
        outfile.close()
    
        # This is the end !
        
        sys.stdout.write(_('Generate:\n %s.') % html)
        print('\n#######################################################')
        print(_('End'))

        

