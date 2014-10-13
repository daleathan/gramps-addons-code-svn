# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2009  Douglas S. Blank
# Copyright (C) 2012  Jerome Rapinat
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

#! /usr/bin/env python
"""
setup.py for Gramps addons.

Examples: 
   python setup.py init AddonDirectory

      Creates the initial directories for the addon.

   python setup.py init AddonDirectory fr

      Creates the initial empty AddonDirectory/po/fr-local.po file
      for the addon.

   python setup.py update AddonDirectory fr

      Updates AddonDirectory/po/fr-local.po with the latest
      translations.

   python setup.py build AddonDirectory

      Build ../download/AddonDirectory.addon.tgz

   python setup.py build all

      Build ../download/*.addon.tgz

   python setup.py compile AddonDirectory
   python setup.py compile all

      Compiles AddonDirectory/po/*-local.po and puts the resulting
      .mo file in AddonDirectory/locale/*/LC_MESSAGES/addon.mo

   python setup.py listing AddonDirectory
   python setup.py listing all

   python setup.py clean
   python setup.py clean AddonDirectory
"""

from __future__ import print_function
import shutil
import glob
import os
import sys
from argparse import ArgumentParser

ADDONS = sorted([name for name in os.listdir(".") 
                      if os.path.isdir(name) and not name.startswith(".")])
                      	
ALL_LINGUAS=["en", # translation template
             "all", # all entries
             "bg",
             "ca",
             "cs",
             "da",
             "de",
             "es",
             "en_GB",
             "fi",
             "fr",
             "he",
             "hr",
             "hu",
             "it",
             "ja",
             "lt",
             "mk",
             "nb",
             "nl",
             "nn",
             "pl",
             "pt_BR",
             "pt_PT",
             "ru",            
             "sk",
             "sl",
             "sq",
             "sv",           
             "uk",
             "vi",
             "zh_CN",
             ]

arguments = sys.argv[2:]

for argument in arguments:
    if argument in ADDONS:
        ADDON = argument
    else:
        ADDON = '.'

for argument in arguments:
    if argument in ALL_LINGUAS:
        LANG = argument
    else:
        LANG = 'en'

if sys.platform == 'win32':    
      
    # GetText Win 32 obtained from http://gnuwin32.sourceforge.net/packages/gettext.htm
    # ....\gettext\bin\msgmerge.exe needs to be on the path
    
    msginitCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'msginit.exe')
    msgmergeCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'msgmerge.exe')
    msgfmtCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'msgfmt.exe')
    msgcatCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'msgcat.exe')
    msggrepCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'msggrep.exe')
    msgcmpCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'msgcmp.exe')
    msgattribCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'msgattrib.exe')
    xgettextCmd = os.path.join('C:', 'Program Files(x86)', 'gettext', 'bin', 'xgettext.exe')
    
    pythonCmd = os.path.join(sys.prefix, 'bin', 'python.exe')
    
    # GNU tools
    # see http://gnuwin32.sourceforge.net/packages.html
    
    sedCmd = os.path.join('C:', 'Program Files(x86)', 'sed.exe') # sed
    mkdirCmd = os.path.join('C:', 'Program Files(x86)', 'mkdir.exe') # CoreUtils
    rmCmd = os.path.join('C:', 'Program Files(x86)', 'rm.exe') # CoreUtils
    tarCmd = os.path.join('C:', 'Program Files(x86)', 'tar.exe') # tar
    
elif sys.platform in ['linux2', 'darwin', 'cygwin']:
    
    msginitCmd = 'msginit'
    msgmergeCmd = 'msgmerge'
    msgfmtCmd = 'msgfmt'
    msgcatCmd = 'msgcat'
    msggrepCmd = 'msggrep'
    msgcmpCmd = 'msgcmp'
    msgattribCmd = 'msgattrib'
    xgettextCmd = 'xgettext'
    
    pythonCmd = os.path.join(sys.prefix, 'bin', 'python')
    
    sedCmd = 'sed'
    mkdirCmd = 'mkdir'
    rmCmd = 'rm'
    tarCmd = 'tar'
    
else:
    print ("ERROR: unknown system, don't know commands")
    sys.exit(0)
    
GNU = [sedCmd, mkdirCmd, rmCmd, tarCmd]

def tests():
    """
    Testing installed programs.
    We made tests (-t flag) by displaying versions of tools if properly
    installed. Cannot run all commands without 'gettext' and 'python'.
    """
    
    try:
        print("\n====='msginit'=(create your translation)===============\n")
        os.system('''%(program)s -V''' % {'program': msginitCmd})
    except:
        raise ValueError('Please, install %(program)s for creating your translation' % {'program': msginitCmd})
    
    try:
        print("\n====='msgmerge'=(merge your translation)===============\n")
        os.system('''%(program)s -V''' % {'program': msgmergeCmd})
    except:
        raise ValueError('Please, install %(program)s for updating your translation' % {'program': msgmergeCmd})
        
    try:
        print("\n=='msgfmt'=(format your translation for installation)==\n")
        os.system('''%(program)s -V''' % {'program': msgfmtCmd})
    except:
        raise ValueError('Please, install %(program)s for checking your translation' % {'program': msgfmtCmd})
    
    try:
        print("\n==='msgcat'=(concate translations)=====================\n")
        os.system('''%(program)s -V''' % {'program': msgcatCmd})
    except:
        raise ValueError('Please, install %(program)s for concating translations' % {'program': msgcatCmd})
    
    try:
        print("\n===='msggrep'==(extract messages from catalog)=========\n")
        os.system('''%(program)s -V''' % {'program': msggrepCmd})
    except:
        raise ValueError('Please, install %(program)s for extracting messages' % {'program': msggrepCmd})

    try:
        print("\n===='msgcmp'==(compare two gettext files)===============\n")
        os.system('''%(program)s -V''' % {'program': msgcmpCmd})
    except:
        raise ValueError('Please, install %(program)s for comparing gettext files' % {'program': msgcmpCmd})
        
    try:
        print("\n===='msgattrib'==(list groups of messages)=============\n")
        os.system('''%(program)s -V''' % {'program': msgattribCmd})
    except:
        raise ValueError('Please, install %(program)s for listing groups of messages' % {'program': msgattribCmd})
        
    try:
        print("\n===='xgettext' =(generate a new template)==============\n")
        os.system('''%(program)s -V''' % {'program': xgettextCmd})
    except:
        raise ValueError('Please, install %(program)s for generating a new template' % {'program': xgettextCmd})
    
    try:
        print("\n=================='python'=============================\n")
        os.system('''%(program)s -V''' % {'program': pythonCmd})
    except:
        raise ValueError('Please, install python')
     
    for program in GNU:
        try:
            print("\n=================='%s'=============================\n" % program)
            os.system('''%s --version''' % program)
        except:
            raise ValueError('Please, install or set path for GNU tool: %s' % program)
        
    
def main():
    """
    The utility for handling addon.
    """
    
    parser = ArgumentParser( 
                         description='This specific script build addon', 
                         )
                         
    #parser.add_argument("-t", "--test",
    #action="store_true", dest="test", default=True,
    #help="test if programs are properly installed")
              
    translating = parser.add_argument_group(
                                           "Translations Options", 
                                           "Everything around translations for addon."
                                           )
    building = parser.add_argument_group(
                                        "Build Options", 
                                        "Everything around package."
                                        )
                                           
    translating.add_argument("-i", choices=ADDONS+ALL_LINGUAS, dest="init", default=False,
              help="create the environment")
    translating.add_argument("-u", choices=ADDONS+ALL_LINGUAS, dest="update", default=False,
              help="update the translation")
              
    building.add_argument("-c", "--compile",
              action="store_true", dest="compilation", default=False,
              help="compile translation files for generating package")
    building.add_argument("-b", "--build",
              action="store_true", dest="build", default=False,
              help="build package")
    building.add_argument("-l", "--listing",
              action="store_true", dest="listing", default=False,
              help="list packages")
    building.add_argument("-r", "--clean",
              action="store_true", dest="clean", default=False,
              help="remove files generated by building process")
    
    args = parser.parse_args()
    
    #if args.test:
        #tests()
       
    if args.init and len(sys.argv) > 2:
        init(ADDON, LANG)
        
    if args.update and len(sys.argv) > 2:
        update(ADDON, LANG)
        
    if args.compilation and len(sys.argv) > 2:
        compilation(ADDON, LANG)
        
    if args.build and len(sys.argv) > 2:
        build(ADDON, LANG)
        
    if args.listing:
        listing()
        
    if args.clean and len(sys.argv) > 2:
        clean(ADDON)
        
        
def versioning(ADDON):
    """
    Update gpr.py version
    """
    
    if ADDON:
        f = open('%s/%s.gpr.py' % (ADDON, ADDON), "r")
        lines = [file.strip() for file in f]
        f.close() 
    
        upf = open('%s/%s.gpr.py' % (ADDON, ADDON), "w")
    
        for line in lines:
            if ((line.lstrip().startswith("version")) and 
                ("=" in line)):
                print("orig %s" % line.rstrip())
            
                line, stuff = line.rsplit(",", 1)
                line = line.rstrip()
                pos = line.index("version")
            
                indent = line[0:pos]
                var, gtv = line[pos:].split('=', 1)
                lyst = version(gtv.strip()[1:-1])
                lyst[2] += 1
            
                newv = ".".join(map(str, lyst))
                newline = "%sversion = '%s'," % (indent, newv)
                print("new %s" % newline.rstrip())
                upf.write('%s\n' % newline)
            else:
                upf.write('%s\n' % line)
        upf.close()
        
        
def myint(s):
    """
    Protected version of int()
    """
    try:
        v = int(s)
    except:
        v = s
    return v
        
        
def version(sversion):
    """
    Return the tuple version of a string version.
    """
    return [myint(x or "0") for x in (sversion + "..").split(".")][0:3]
       
                
def init(ADDON, LANG):
    """
    Creates the initial empty po/x-local.po file and generates the 
    template.pot for the addon.
    """    
        
    template(ADDON, LANG)

    os.system('''%(mkdir)s -pv "%(addon)s/po"''' % {'mkdir': mkdirCmd, 'addon': ADDON})
    
    if os.path.isfile('''%s/po/%s-local.po''' % (ADDON, LANG)):
        print('''"%s/po/%s-local.po" already exists!''' % (ADDON, LANG))
    else:
        os.system('''%(msginit)s --locale=%(lang)s ''' 
                  '''--input="%(addon)s/po/template.pot" '''
                  '''--output="%(addon)s/po/%(lang)s-local.po"'''
                  % {'msginit': msginitCmd, 'addon': ADDON, 'lang': LANG} 
                  )
        print('''You can now edit "%s/po/%s-local.po"!''' % (ADDON, LANG))


def template(ADDON, LANG):
    """
    Generates the template.pot for the addon.
    """

    os.system('''%(xgettext)s --language=Python --keyword=_ --keyword=N_'''
              ''' --from-code=UTF-8 -o "%(addon)s/po/template.pot" %(addon)s/*.py''' 
              % {'xgettext': xgettextCmd, 'addon': ADDON}
             )
             
    if os.path.isfile('%(addon)s/%(addon)s.glade' % {'addon': ADDON}):
        os.system('''%(xgettext)s --add-comments -j -L Glade '''
                  '''--from-code=UTF-8 -o "%(addon)s/po/template.pot" %(addon)s/*.glade'''
                  % {'xgettext': xgettextCmd, 'addon': ADDON}
                 )
    
    if os.path.isfile('%s/census.xml' % ADDON):        
        xml(ADDON)
        os.system('''%(xgettext)s --keyword=N_ --add-comments -j'''
                  ''' --from-code=UTF-8 -o "%(addon)s/po/template.pot" %(addon)s/*.xml.h''' 
                  % {'xgettext': xgettextCmd, 'addon': ADDON}
                  )
                                      
    os.system('''%(sed)s -i 's/charset=CHARSET/charset=UTF-8/' '''
              '''"%(addon)s/po/template.pot"''' % {'sed': sedCmd, 'addon': ADDON}
             )
             

def xml(ADDON):
    """
    Experimental alternative to 'intltool-extract' for 'census.xml'.
    """
    

    # in progress ...
    from xml.etree import ElementTree
    
    tree = ElementTree.parse('%s/census.xml' % ADDON)
    root = tree.getroot()
       
    '''
    <?xml version="1.0" encoding="UTF-8"?>
    <censuses>
        <census id='UK1841' title='1841 UK Census' date='6 Jun 1841'>
            <heading>
                <_attribute>City or Borough</_attribute>
            </heading>
            <heading>
                <_attribute>Parish or Township</_attribute>
            </heading>
            <column>
                <_attribute>Name</_attribute>
                <size>25</size>
            </column>
            <column>
                <_attribute>Age</_attribute>
                <size>5</size>
            </column>
        
    char *s = N_("City or Borough");
    
    template.pot:
    msgid "City or Borough"
    '''
    
    catalog = open('%(addon)s/%(addon)s.xml.h' % {'addon': ADDON}, 'w')
    
    for key in root.iter('_attribute'):
        catalog.write('char *s = N_("%s");\n' % key.text)
        
    catalog.close()
        
    root.clear()
    
    
def update(ADDON, LANG):
    """
    Updates po/x-local.po with the latest translations.
    """
            
    template(ADDON, LANG)
                 
    os.system('''%(mkdir)s -pv "%(addon)s/po"''' % {'mkdir': mkdirCmd, 'addon': ADDON})
                
    # create a temp header file (time log)
                
    temp(ADDON, LANG)
                              
    # create the locale-local.po file
                
    init(ADDON, LANG)
                
    # create a temp header file (time log)
                
    temp(ADDON, LANG)
                
    # merge data from previous translation to the temp one
            
    print('Merge "%(addon)s/po/%(lang)s.po" with "%(addon)s/po/%(lang)s-local.po":' % {'addon': ADDON, 'lang': LANG})
    
    os.system('''%(msgmerge)s %(addons)s/po/%(lang)s-local.po %(addons)s/po/%(lang)s.po'''
              ''' -o %(addons)s/po/%(lang)s.po --no-location -v'''
              % {'msgmerge': msgmergeCmd, 'addon': ADDON, 'lang': LANG} 
              )
                        
    memory(ADDON, LANG)
            
    # like template (msgid) with last message strings (msgstr)
            
    print('Merge "%s/po/%s.po" with "po/template.pot":' % (ADDON, LANG))
            
    os.system('''%(msgmerge)s -U %(addon)s/po/%(lang)s.po'''
              ''' %(addon)s/po/template.pot -v'''
              % {'msgmerge': msgmergeCmd, 'addon': ADDON, 'lang': LANG} 
              )
                      
    # only used messages (need) and merge back
            
    print('Move content to "po/%s-local.po".' % arg)
            
    os.system('''%(msgattrib)s --no-obsolete'''
              ''' %(addon)s/po/%(lang)s.po -o %(addon)s/po/%(lang)s-local.po'''
              % {'msgattrib': msgattribCmd, 'addon': ADDON, 'lang': LANG} 
              )
            
    # remove temp locale.po file
            
    os.system('''%(rm)s -rf -v %(addon)s/po/%(lang)s.po'''
              % {'rm': rmCmd, 'addon': ADDON, 'lang': LANG}
              ) 
                      
    print('''You can now edit "%s/po/%s-local.po"!''' % (ADDON, LANG))
                      
            
def temp(addon, lang):
    """
    Generate a temp file for header (time log) and Translation Memory
    """
    
    os.system('''%(msginit)s --locale=%(lang)s ''' 
              '''--input="%(addons)s/po/template.pot" '''
              '''--output="%(addon)s/po/%(lang)s.po" --no-translator'''
              % {'msginit': msginitCmd, 'addon': addon, 'lang': lang} 
              )
    
            
def memory(addon, lang):
    """
    Translation memory for Gramps (own dictionary: msgid/msgstr)
    """
    
    if "GRAMPSPATH" in os.environ:
        GRAMPSPATH = os.environ["GRAMPSPATH"]
    else:
        GRAMPSPATH = "../../../.."

    if not os.path.isdir(GRAMPSPATH + "/po"):
        raise ValueError("Where is GRAMPSPATH/po: '%s/po'? Use 'GRAMPSPATH=path python setup.py ...'" % GRAMPSPATH)
                               
    # Get all of the addon strings out of the catalog
        
    os.system('''%(msggrep)s --location=../*'''
              ''' %(addon)s/po/template.pot --output-file=%(addon)s/po/%(lang)s-temp.po'''
              % {'msggrep': msggrepCmd, 'addon': addon, 'lang': lang} 
              )
    
    # start with Gramps main PO file
    
    locale_po_files = "%(GRAMPSPATH)s/%(addon)s/po/%(lang)s.po" % {'GRAMPSPATH': GRAMPSPATH, 'addon': addon, 'lang': lang}
    
    # concat global dict as temp file
    
    if os.path.isfile(locale_po_files):
        print('Concat temp data: "%(addon)s/po/%(lang)s.po" with "%(global)s".' % {'global': locale_po_files, 'addon': addon, 'lang': lang})
            
        os.system('''%(msgcat)s --use-first %(addon)s/po/%(lang)s.po'''
                  ''' %(global)s -o %(addon)s/po/%(lang)s.po --no-location'''
                  % {'msgcat': msgcatCmd, 'global': locale_po_files, 'addon': addon, 'lang': lang} 
                  )
        os.system('''%(msgcmp)s -m --use-fuzzy --use-untranslated'''
                  ''' %(addon)s/po/%(lang)s.po %(global)s'''
                  % {'msgcmp': msgcmpCmd, 'global': locale_po_files , 'addon': addon, 'lang': lang} 
                  )
                
    if os.path.isfile('%s/po/%s-temp.po' % (addon, lang)):
        print('Concat temp data: "%(addon)s/po/%(lang)s.po" with "%(addon)s/po/%(lang)s-temp.po".' % {'addon': addon, 'lang': lang})
                  
        os.system('''%(msgcat)s --use-first %(addon)s/po/%(lang)s.po'''
                  ''' %(addon)s/po/%(lang)s-temp.po -o %(addon)s/po/%(lang)s.po --no-location'''
                  % {'msgcat': msgcatCmd, 'addon': addon, 'lang': lang} 
                  )
                  
        print('''Remove temp "%s/po/%s-temp.po".''' % (addon, lang))
            
        os.system('''%(rm)s -rf -v %(addon)s/po/%(lang)s-temp.po'''
                  % {'rm': rmCmd, 'addon': addon, 'lang': lang}
                 )
                                  
    
def compilation(ADDON, LANG):
    """
    Compile translations
    """
    
    os.system('''%(mkdir)s -pv "%(addon)s/locale"''' % {'mkdir': mkdirCmd, 'addon': ADDON})
    
    for po in glob.glob(os.path.join(ADDON, 'po', '*-local.po')):
        f = os.path.basename(po[:-3])
        mo = os.path.join(ADDON, 'locale', f[:-6], 'LC_MESSAGES', 'addon.mo')
        directory = os.path.dirname(mo)
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.system('%s %s/po/%s.po -o %s' % (msgfmtCmd, ADDON, f, mo)
                 )
           
               
def build(ADDON, LANG):
    """
    Build ../download/AddonDirectory.addon.tgz
    """
        
    compilation(ADDON, LANG)
    versioning(ADDON)
    
    files = []
    files += glob.glob('''%s/*.py''' % ADDON)
    files += glob.glob('''%s/*.gpr.py''' % ADDON)
    files += glob.glob('''%s/*.py''' % ADDON)
    files += glob.glob('''%s/*.gpr.py''' % ADDON)
    files += glob.glob('''%s/locale/*/LC_MESSAGES/*.mo''' % ADDON)
    files += glob.glob('''%s/*.glade''' % ADDON)
    files += glob.glob('''%s/*.xml''' % ADDON)
    files_str = " ".join(files)
    os.system('''%(mkdir)s -pv ../download/%(addon)s ''' % {'mkdir': mkdirCmd, 'addon': ADDON}
             )
    os.system('''%(tar)s cfzv "../download/%(addon)s.addon.tgz" %(files_list)s''' 
              % {'tar': tarCmd, 'files_list': files_str, 'addon': ADDON}
              )


def was_listing():
    """
    Listing files ../listing/{lang}.fr
    """
        
    try:
        sys.path.insert(0, GRAMPSPATH)
        os.environ['GRAMPS_RESOURCES'] = os.path.abspath(GRAMPSPATH)
        from gramps.gen.const import GRAMPS_LOCALE as glocale
        from gramps.gen.plug import make_environment, PTYPE_STR
    except ImportError:
        raise ValueError("Where is GRAMPSPATH: '%s'? Use 'GRAMPSPATH=path python make.py listing'" % GRAMPSPATH)
    def register(ptype, **kwargs):
        global plugins
        kwargs["ptype"] = PTYPE_STR[ptype]
        plugins.append(kwargs)
    # first, get a list of all of the possible languages
    if addon == "all":
        dirs = [file for file in glob.glob("*") if os.path.isdir(file)]
    else:
        dirs = [addon]
    # Make the locale for for any local languages for Addon:
    for addon in dirs:
        for po in glob.glob(r('''%(addon)s/po/*-local.po''')):
            # Compile
            locale = os.path.basename(po[:-9])
            system('''mkdir -p "%(addon)s/locale/%(locale)s/LC_MESSAGES/"''')
            system('''msgfmt %(po)s '''
                   '''-o "%(addon)s/locale/%(locale)s/LC_MESSAGES/addon.mo"''')
    # Get all languages from all addons:
    languages = set(['en'])
    for addon in [file for file in glob.glob("*") if os.path.isdir(file)]:
        for po in glob.glob(r('''%(addon)s/po/*-local.po''')):
            length= len(po)
            locale = po[length-11:length-9]
            locale_path, locale = po.rsplit("/", 1)
            languages.add(locale[:-9])
    # next, create/edit a file for all languages listing plugins
    for lang in languages:
        print("Building listing for '%s'..." % lang)
        listings = []
        for addon in dirs:
            for gpr in glob.glob(r('''%(addon)s/*.gpr.py''')):
                # Make fallback language English (rather than current LANG)
                local_gettext = glocale.get_addon_translator(
                    gpr, languages=[lang, "en.UTF-8"]).gettext
                plugins = []
                with open(gpr.encode("utf-8", errors="backslashreplace")) as f:
                    code = compile(f.read(),
                                   gpr.encode("utf-8", errors="backslashreplace"),
                                   'exec')
                    #exec(code, make_environment(_=local_gettext),
                         #{"register": register})
                for p in plugins:
                    tgz_file = "%s.addon.tgz" % gpr.split("/", 1)[0]
                    tgz_exists = os.path.isfile("../download/" + tgz_file)
                    if p.get("include_in_listing", True) and tgz_exists:
                        plugin = {"n": repr(p["name"]),
                                  "i": repr(p["id"]),
                                  "t": repr(p["ptype"]),
                                  "d": repr(p["description"]),
                                  "v": repr(p["version"]),
                                  "g": repr(p["gramps_target_version"]),
                                  "z": repr(tgz_file),
                                  }
                        listings.append(plugin)
                    else:
                        print("   ignoring '%s'" % (p["name"]))
        # Write out new listing:
        if addon == "all":
            # Replace it!
            fp = open("../listings/addons-%s.txt" % lang, "w")
            for plugin in sorted(listings, key=lambda p: (p["t"], p["i"])):
                print('{"t":%(t)s,"i":%(i)s,"n":%(n)s,"v":%(v)s,"g":%(g)s,"d":%(d)s,"z":%(z)s}' % plugin, file=fp)
            fp.close()
        else:
            # just update the lines from these addons:
            added = False
            for plugin in sorted(listings, key=lambda p: (p["t"], p["i"])):
                fp_in = open("../listings/addons-%s.txt" % lang, "r")
                fp_out = open("../listings/addons-%s.new" % lang, "w")
                for line in fp_in:
                    dictionary = eval(line)
                    if addon + ".addon.tgz" in line:
                        print('{"t":%(t)s,"i":%(i)s,"n":%(n)s,"v":%(v)s,"g":%(g)s,"d":%(d)s,"z":%(z)s}' % plugin, file=fp_out)
                        added = True
                    else:
                        if plugin["t"] > dictionary["t"] and not added:
                            print('{"t":%(t)s,"i":%(i)s,"n":%(n)s,"v":%(v)s,"g":%(g)s,"d":%(d)s,"z":%(z)s}' % plugin, file=fp_out)
                            added = True
                        print(line, end="", file=fp_out)
                fp_in.close()
                fp_out.close()
                shutil.move("../listings/addons-%s.new" % lang, "../listings/addons-%s.txt" % lang)


def listing():
    """
    Listing files ../listing/{lang}.fr
    """
    
    if "GRAMPSPATH" in os.environ:
        GRAMPSPATH = os.environ["GRAMPSPATH"]
    else:
        GRAMPSPATH = "../../../.."

    try:
        sys.path.insert(0, GRAMPSPATH)
        os.environ['GRAMPS_RESOURCES'] = os.path.abspath(GRAMPSPATH)
        from gramps.gen.utils.grampslocale import GrampsLocale
        from gramps.gen.const import GRAMPS_LOCALE as glocale
        from gramps.gen.plug import make_environment, PTYPE_STR
    except ImportError:
        raise ValueError("Where is GRAMPSPATH: '%s'? Use 'GRAMPSPATH=path python setup.py listing'" % GRAMPSPATH)
    def register(ptype, **kwargs):
        global plugins
        kwargs["ptype"] = PTYPE_STR[ptype]
        plugins.append(kwargs)

    listings = []
    need = False
    
    # Replace all!
    #for lang in ALL_LINGUAS:
        #if lang == 'all':
            #continue

        #print("Building listing for '%s'..." % lang)
        #fp = open("../listings/addons-%s.txt" % lang, "w")

        #for addon in sorted(ADDONS):

            #tgz_file = "%s.addon.tgz" % addon
            #tgz_exists = os.path.isfile("../download/" + tgz_file)
            #gpr_file = "%s/%s.gpr.py" % (addon, addon)
            #gpr_exists = os.path.isfile(gpr_file)
            #mo_file = "%s/locale/%s/LC_MESSAGES/addon.mo" % (addon, lang)
            #mo_exists = os.path.isfile(mo_file)
            
            #local_gettext = glocale.get_addon_translator(gpr_file, languages=[lang, "en.UTF-8"]).gettext
            #_ = local_gettext

            #if tgz_exists and gpr_exists:
                #gpr = open(gpr_file.encode("utf-8", errors="backslashreplace"))

                #plug = dict([file.strip(), None] for file in gpr if file.strip())

                #name = ident = ptype = description = version = target = ''

                #if mo_exists and lang == 'fr':
                    #test = open(mo_file)
                    #trans_dict = [test.read()]

                

                #for p in plug:

                    #if (repr(p)).startswith("'name"):
                        #name = p.replace('name', '')
                        #name = name.replace('=', '')
                        #name = name.replace(',', '')
                        #name = repr(_(name))

                    #if (repr(p)).startswith("'id"):
                        #need = True
                        #ident = p.replace('id', '')
                        #ident = ident.replace('=', '')
                        #ident = ident.replace(',', '')

                    #elif (repr(p)).startswith("'ptype"):
                        #ptype = p.replace('ptype', '')
                        #ptype = ptype.replace('=', '')
                        #ptype = repr(ptype)

                    #elif (repr(p)).startswith("'description"):
                        #description = p.replace('description', '')
                        #description = description.replace('=', '')
                        #description = description.replace(',', '')
                        #description = repr(_(description))
                
                    #elif (repr(p)).startswith('"version'):
                        #version = p.replace('version', '')
                        #version = version.replace('=', '')
                        #version = version.replace(',', '')
                        #version = repr(version)
                    
                    #elif (repr(p)).startswith('"gramps_target_version'):
                        #target = p.replace('gramps_target_version', '')
                        #target = target.replace('=', '')
                        #target = repr(target)

                    #if (repr(p)).startswith('"include_in_listing'):
                        #need = False  

                #code = compile(gpr.read(),
                                   #gpr_file.encode("utf-8", errors="backslashreplace"),
                                   #'exec')
                #exec(code, make_environment(_=local_gettext),
                         #{"register": register})

                
                #if need:
                    #plugin = {
                            #"n": name,
                            #"i": ident,
                            #"t": ptype,
                            #"d": description,
                            #"v": version,
                            #"g": target,
                            #"z": repr(tgz_file),
                            #}
                        
                    #print(plugin)
                    #listings.append(plugin)

        #for plugin in sorted(listings, key=lambda p: p["z"]):
            #fp.write('{"t":%(t)s,"i":%(i)s,"n":%(n)s,"v":%(v)s,"g":%(g)s,"d":%(d)s,"z":%(z)s}\n' % plugin)
        #fp.close()
      
        # change the method

    fp = open("../listings/addons-en.txt", "w")

    for addon in sorted(ADDONS):

        tgz_file = "%s.addon.tgz" % addon
        tgz_exists = os.path.isfile("../download/" + tgz_file)
        gpr_file = "%s/%s.gpr.py" % (addon, addon)
        gpr_exists = os.path.isfile(gpr_file)
        #mo_file = "%s/locale/%s/LC_MESSAGES/addon.mo" % (addon, lang)
        #mo_exists = os.path.isfile(mo_file)
            
        #local_gettext = glocale.get_addon_translator(gpr_file, languages=[lang, "en.UTF-8"]).gettext
        #_ = local_gettext

        if tgz_exists and gpr_exists:
            gpr = open(gpr_file.encode("utf-8", errors="backslashreplace"))

            plug = dict([file.strip(), None] for file in gpr if file.strip())

            name = ident = ptype = description = version = target = ''

            #if mo_exists and lang == 'fr':
                #test = open(mo_file)
                #trans_dict = [test.read()]

            #print(plug)

            for p in plug:

                #print(repr(p))

                if (repr(p)).startswith("'register("):
                    ptype = p.replace('register(', '')
                    ptype = repr(ptype)

                if not ((repr(p)).startswith("'include_in_listing = False,") or \
                       (repr(p)).startswith("'status = UNSTABLE,")):
                    need = True
                else:
                    print(addon)

                if (repr(p)).startswith("'id") or (repr(p)).startswith('"id'):
                    ident = p.replace('id', '')
                    ident = ident.replace('=', '')
                    ident = ident.replace(',', '')
                    ident = ident.strip()
                    #ident = repr(ident)

                if (repr(p)).startswith("'name") or (repr(p)).startswith('"name'):
                    name = p.replace('name', '')
                    name = name.replace('=', '')
                    name = name.replace(',', '')
                    name = name.strip()
                    name = repr(name)                 

                if (repr(p)).startswith("'description"):
                    description = p.replace('description', '')
                    description = description.replace('=', '')
                    description = description.replace(',', '')
                    description = description.strip()
                    description = repr(description)
                
                if (repr(p)).startswith('"version'):
                    version = p.replace('version', '')
                    version = version.replace('=', '')
                    version = version.replace(',', '')
                    version = version.strip()
                    version = repr(version)
                    
                if (repr(p)).startswith('"gramps_target_version'):
                    target = p.replace('gramps_target_version', '')
                    target = target.replace('=', '')
                    target = target.strip()
                    target = repr(target)

                #code = compile(gpr.read(),
                                   #gpr_file.encode("utf-8", errors="backslashreplace"),
                                   #'exec')
                #exec(code, make_environment(_=local_gettext),
                         #{"register": register})
                
            if need:
                plugin = {
                        "n": name,
                        "i": ident,
                        "t": ptype,
                        "d": description,
                        "v": version,
                        "g": target,
                        "z": repr(tgz_file),
                        }
                fp.write('{"t":%(t)s,"i":%(i)s,"n":%(n)s,"v":%(v)s,"g":%(g)s,"d":%(d)s,"z":%(z)s}\n' % plugin)
                        
                #print(plugin)
                listings.append(plugin)

        #for plugin in sorted(listings, key=lambda p: p["z"]):
            #fp.write('{"t":%(t)s,"i":%(i)s,"n":%(n)s,"v":%(v)s,"g":%(g)s,"d":%(d)s,"z":%(z)s}\n' % plugin)
    fp.close()


def clean(ADDON):
    """
    Remove created files
    """

    
    os.system('''%(addon)s/%(rm)s -rfv '''
              '''%(addon)s/*~ '''
              '''%(addon)s/po/*~ '''
              '''%(addon)s/po/template.pot '''
              '''%(addon)s/locale '''
              '''%(addon)s/*.pyc '''
              '''%(addon)s/*.pyo '''
              '''%(addon)s/xml.h '''
              % {'rm': rmCmd, 'addon': ADDON}
              ) 
    
     
if __name__ == "__main__":
    main()
