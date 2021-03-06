#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
make.py for Gramps addons.

Examples: 
   python make.py init AddonDirectory

      Creates the initial directories for the addon.

   python make.py init AddonDirectory fr

      Creates the initial empty AddonDirectory/po/fr-local.po file
      for the addon.

   python make.py update AddonDirectory fr

      Updates AddonDirectory/po/fr-local.po with the latest
      translations.

   python make.py build AddonDirectory

      Build ../download/AddonDirectory.addon.tgz

   python make.py build all

      Build ../download/*.addon.tgz

   python make.py compile AddonDirectory
   python make.py compile all

      Compiles AddonDirectory/po/*-local.po and puts the resulting
      .mo file in AddonDirectory/locale/*/LC_MESSAGES/addon.mo

   python make.py listing AddonDirectory
   python make.py listing all

   python make.py dist-clean
   python make.py dist-clean AddonDirectory
   python make.py clean
   python make.py clean AddonDirectory
"""
import shutil
import glob
import sys
import os

if "GRAMPSPATH" in os.environ:
    GRAMPSPATH = os.environ["GRAMPSPATH"]
else:
    GRAMPSPATH = "../../.."

if (("LANGUAGE" not in os.environ) or 
    (not os.environ["LANGUAGE"].startswith("en"))):
    raise ValueError("LANGUAGE should explicitly be english; Use 'LANGUAGE=en_US.UTF-8 python make.py...' or similar")
else:
    print("make.py: LANGUAGE is %s... good!" % os.environ["LANGUAGE"])

command = sys.argv[1]
if len(sys.argv) >= 3:
    addon = sys.argv[2]

def system(scmd, **kwargs):
    """
    Replace and call system with scmd.
    """
    cmd = r(scmd, **kwargs)
    #print(cmd)
    os.system(cmd)

def echo(scmd, **kwargs):
    """
    Replace and echo.
    """
    cmd = r(scmd, **kwargs)
    print(cmd)

def r(scmd, **kwargs):
    """
    Replace scmd with variables from kwargs, or globals.
    """
    keywords = globals()
    keywords.update(kwargs)
    cmd = scmd % keywords
    return cmd

def mkdir(dirname):
    """
    Create a directory, if doesn't already exists.
    Note: os.system("mkdir ...") cannot be used on Windows (mkdir mismatches with integrated cmd.exe command)
    """
    dirname = r(dirname)
    if (os.path.isdir(dirname)): return
    os.makedirs(dirname)

def increment_target(filenames):
    for filename in filenames:
        fp = open(filename, "r", encoding="utf-8")
        newfp = open("%s.new" % filename, "w", encoding="utf-8")
        for line in fp:
            if ((line.lstrip().startswith("version")) and 
                ("=" in line)):
                #print("orig = %s" % line.rstrip())
                line, stuff = line.rsplit(",", 1)
                line = line.rstrip()
                pos = line.index("version")
                indent = line[0:pos]
                var, gtv = line[pos:].split('=', 1)
                lyst = version(gtv.strip()[1:-1])
                lyst[2] += 1
                newv = ".".join(map(str, lyst))
                newline = "%sversion = '%s',\n" % (indent, newv)
                newfp.write(newline)
            else:
                newfp.write(line)
        fp.close()
        newfp.close()
        system('''mv -f "%(file1)s" "%(file2)s" ''',
               file1="%s.new" % filename, file2=filename)


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

if command == "clean":
    if len(sys.argv) == 2:
        for addon in [name for name in os.listdir(".") 
                      if os.path.isdir(name) and not name.startswith(".")]:
            system('''rm -rf -v '''
                   '''"%(addon)s"/*~ '''
                   '''"%(addon)s"/po/*~ '''
                   '''"%(addon)s"/po/template.pot '''
                   '''"%(addon)s"/po/*-global.po '''
                   '''"%(addon)s"/po/*-temp.po '''
                   '''"%(addon)s"/locale '''
                   '''"%(addon)s"/*.pyc '''
                   '''"%(addon)s"/*.pyo ''')
    else:
        system('''rm -rf -v '''
               '''"%(addon)s"/*~ '''
               '''"%(addon)s"/po/*~ '''
               '''"%(addon)s"/po/template.pot '''
               '''"%(addon)s"/po/*-global.po '''
               '''"%(addon)s"/po/*-temp.po '''
               '''"%(addon)s"/locale '''
               '''"%(addon)s"/*.pyc '''
               '''"%(addon)s"/*.pyo ''')
elif command == "init":
    # # Get all of the strings from the addon and create template.po:
    # #intltool-extract --type=gettext/glade *.glade
    if len(sys.argv) == 3:
        mkdir(r("%(addon)s/po"))
        mkdir("%(addon)s/locale")
        system('''intltool-extract --type=gettext/glade "%(addon)s"/*.glade''')
        system('''intltool-extract --type=gettext/xml "%(addon)s"/*.xml''')
        system('''xgettext --language=Python --keyword=_ --keyword=N_'''
               ''' -o "%(addon)s/po/template.pot" "%(addon)s"/*.py ''')
        system('''xgettext -j --keyword=_ --keyword=N_'''
               ''' -o "%(addon)s/po/template.pot" '''
               '''"%(addon)s"/*.glade.h''')
        system('''xgettext -j --keyword=_ --keyword=N_'''
               ''' -o "%(addon)s/po/template.pot" '''
               '''"%(addon)s"/*.xml.h''')
        system('''sed -i 's/charset=CHARSET/charset=UTF-8/' '''
               '''"%(addon)s/po/template.pot"''')
    elif len(sys.argv) > 3:
        locale = sys.argv[3]
        # make a copy for locale
        if os.path.isfile(r('''%(addon)s/po/%(locale)s-local.po''')):
            raise ValueError(r('''%(addon)s/po/%(locale)s-local.po''') + 
                             " already exists!")
        system('''msginit --locale=%(locale)s ''' 
               '''--input="%(addon)s/po/template.pot" '''
               '''--output="%(addon)s/po/%(locale)s-local.po"''')
        echo('''You can now edit "%(addon)s/po/%(locale)s-local.po"''')
    else:
        raise AttributeError("init what?")
elif command == "update":
    locale = sys.argv[3]
    # Update the template file:
    if not os.path.isfile(r('''%(addon)s/po/template.pot''')):
        raise ValueError(r('''%(addon)s/po/template.pot'''
                           ''' is missing!\n  run '''
                           '''./make.py init %(addon)s'''))
    # Check existing translation
    if not os.path.isfile(r('''%(addon)s/po/%(locale)s-local.po''')):
        raise ValueError(r('''%(addon)s/po/%(locale)s-local.po'''
                           ''' is missing!\n run '''
                           '''./make.py init %(addon)s %(locale)s'''))
    # Retrieve updated data for locale:
    system('''msginit --locale=%(locale)s '''
               '''--input="%(addon)s/po/template.pot" '''
               '''--output="%(addon)s/po/%(locale)s.po"''')
    # Merge existing local translation with last data:
    system('''msgmerge --no-fuzzy-matching %(addon)s/po/%(locale)s-local.po '''
           '''%(addon)s/po/%(locale)s.po'''
           ''' -o %(addon)s/po/%(locale)s-local.po''')
    # Start with Gramps main PO file:
    if not os.path.isdir(GRAMPSPATH + "/po"):
        raise ValueError("Where is GRAMPSPATH/po: '%s/po'? Use 'GRAMPSPATH=path python make.py update'" % GRAMPSPATH)
    locale_po_files = [r("%(GRAMPSPATH)s/po/%(locale)s.po")]
    # Next, get all of the translations from other addons:
    for module in [name for name in os.listdir(".") if os.path.isdir(name)]:
        # skip the addon we are updating:
        if module == addon:
            continue
        po_file = r("%(module)s/po/%(locale)s-local.po", module=module)
        if os.path.isfile(po_file):
            locale_po_files.append(po_file)
    # Concat those together:
    system('''msgcat --use-first %(list)s '''
           '''-o "%(addon)s/po/%(locale)s-global.po"''', 
           list=" ".join(['''"%s"''' % name for name in locale_po_files]))
    # Merge the local and global:
    #locale_local = r("%(module)s/po/%(locale)s-local.po", module=module)
    #if os.path.isfile(locale_local):
    system('''msgmerge --no-fuzzy-matching -U "%(addon)s/po/%(locale)s-global.po" '''
           '''"%(addon)s/po/%(locale)s-local.po" ''')
    # Get all of the addon strings out of the catalog:
    system('''msggrep --location=%(addon)s/* '''
           '''"%(addon)s/po/%(locale)s-global.po" '''
           '''--output-file="%(addon)s/po/%(locale)s-temp.po"''')
    # Finally, add back any updates to the local version:
    system('''msgcat --use-first '''
           '''"%(addon)s/po/%(locale)s-temp.po" '''
           '''"%(addon)s/po/%(locale)s-local.po" '''
           '''-o "%(addon)s/po/%(locale)s-local.po.2" ''')
    system('''cp "%(addon)s/po/%(locale)s-local.po" '''
           '''"%(addon)s/po/%(locale)s-local.po.1" ''')
    system('''cp "%(addon)s/po/%(locale)s-local.po.2" '''
           '''"%(addon)s/po/%(locale)s-local.po" ''')
    system('''rm -v "%(addon)s/po/%(locale)s-local.po.1" '''
           '''"%(addon)s/po/%(locale)s-local.po.2" ''')
    # # Done!
    echo('''\nYou can edit "%(addon)s/po/%(locale)s-local.po"''')
elif command in ["compile"]:
    if addon == "all":
        dirs = [file for file in glob.glob("*") if os.path.isdir(file)]
        for addon in dirs:
            for po in glob.glob(r('''%(addon)s/po/*.po''')):
                locale = os.path.basename(po[:-9])
                mkdir("%(addon)s/locale/%(locale)s/LC_MESSAGES/")
                system('''msgfmt %(po)s '''
                       '''-o "%(addon)s/locale/%(locale)s/LC_MESSAGES/addon.mo"''')
    else:
        for po in glob.glob(r('''%(addon)s/po/*.po''')):
            locale = os.path.basename(po[:-9])
            mkdir("%(addon)s/locale/%(locale)s/LC_MESSAGES/")
            system('''msgfmt %(po)s '''
                   '''-o "%(addon)s/locale/%(locale)s/LC_MESSAGES/addon.mo"''')
elif command == "build":
    files = sys.argv[3:]
    if addon == "all":
        dirs = [file for file in glob.glob("*") if os.path.isdir(file)]
        # Compile all:
        for addon in dirs:
            for po in glob.glob(r('''%(addon)s/po/*.po''')):
                locale = os.path.basename(po[:-9])
                mkdir("%(addon)s/locale/%(locale)s/LC_MESSAGES/")
                system('''msgfmt %(po)s '''
                       '''-o "%(addon)s/locale/%(locale)s/LC_MESSAGES/addon.mo"''')
        # Build all:
        for addon in dirs:
            if os.path.isfile(r('''%(addon)s/setup.py''')):
                system('''cd %s; python setup.py --build''' % r('''%(addon)s'''))
                continue
            files = []
            files += glob.glob(r('''%(addon)s/*.py'''))
            files += glob.glob(r('''%(addon)s/*.glade'''))
            files += glob.glob(r('''%(addon)s/*.xml'''))
            files += glob.glob(r('''%(addon)s/*.txt'''))
            files += glob.glob(r('''%(addon)s/locale/*/LC_MESSAGES/*.mo'''))
            files_str = " ".join(files)
            files_str = files_str.replace("\\", "/") # tar on Windows wants '/' and not '\'
            mkdir("../download")
            increment_target(glob.glob(r('''%(addon)s/*gpr.py''')))
            system('''tar cfz "../download/%(addon)s.addon.tgz" %(files)s''',
                   files=files_str)
    else:
        for po in glob.glob(r('''%(addon)s/po/*.po''')):
                locale = os.path.basename(po[:-9])
                mkdir("%(addon)s/locale/%(locale)s/LC_MESSAGES/")
                system('''msgfmt %(po)s '''
                       '''-o "%(addon)s/locale/%(locale)s/LC_MESSAGES/addon.mo"''')
        files += glob.glob(r('''%(addon)s/*.py'''))
        files += glob.glob(r('''%(addon)s/*.glade'''))
        files += glob.glob(r('''%(addon)s/*.xml'''))
        files += glob.glob(r('''%(addon)s/*.txt'''))
        files += glob.glob(r('''%(addon)s/locale/*/LC_MESSAGES/*.mo'''))
        files_str = " ".join(files)
        files_str = files_str.replace("\\", "/") # tar on Windows wants '/' and not '\'
        mkdir("../download")
        increment_target(glob.glob(r('''%(addon)s/*gpr.py''')))
        system('''tar cfz "../download/%(addon)s.addon.tgz" %(files)s''',
               files=files_str)
elif command == "listing":
    try:
        sys.path.insert(0, GRAMPSPATH)
        os.environ['GRAMPS_RESOURCES'] = os.path.abspath(GRAMPSPATH)
        from gramps.gen.const import GRAMPS_LOCALE as glocale
        from gramps.gen.plug import make_environment, PTYPE_STR
    except ImportError:
        raise ValueError("Where is GRAMPSPATH: '%s'? Use 'GRAMPSPATH=path python make.py listing'" % GRAMPSPATH)
    def register(ptype, **kwargs):
        global plugins
        kwargs["ptype"] = PTYPE_STR[ptype] # need to take care of translated types
        plugins.append(kwargs)
    cmd_arg = addon
    # first, get a list of all of the possible languages
    if cmd_arg == "all":
        dirs = [file for file in glob.glob("*") if os.path.isdir(file)]
    else:
        dirs = [addon]
    # Make the locale for for any local languages for Addon:
    for addon in dirs:
        for po in glob.glob(r('''%(addon)s/po/*-local.po''')):
            # Compile
            locale = os.path.basename(po[:-9])
            mkdir("%(addon)s/locale/%(locale)s/LC_MESSAGES/")
            system('''msgfmt %(po)s '''
                   '''-o "%(addon)s/locale/%(locale)s/LC_MESSAGES/addon.mo"''')
    # Get all languages from all addons:
    languages = set(['en'])
    for addon in [file for file in glob.glob("*") if os.path.isdir(file)]:
        for po in glob.glob(r('''%(addon)s/po/*-local.po''')):
            length= len(po)
            locale = po[length-11:length-9]
            locale_path, locale = po.rsplit(os.sep, 1)
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
                    exec(code, make_environment(_=local_gettext),
                         {"register": register})
                for p in plugins:
                    tgz_file = "%s.addon.tgz" % gpr.split(os.sep, 1)[0]
                    tgz_exists = os.path.isfile("../download/" + tgz_file)
                    if p.get("include_in_listing", True) and tgz_exists:
                        plugin = {"n": p["name"].replace("'", "\\'"),
                                  "i": p["id"].replace("'", "\\'"),
                                  "t": p["ptype"].replace("'", "\\'"),
                                  "d": p["description"].replace("'", "\\'"),
                                  "v": p["version"].replace("'", "\\'"),
                                  "g": p["gramps_target_version"].replace("'", "\\'"),
                                  "z": (tgz_file),
                                  }
                        listings.append(plugin)
                    else:
                        print("   ignoring '%s'" % (p["name"]))
        # Write out new listing:
        if cmd_arg == "all":
            # Replace it!
            fp = open("../listings/addons-%s.txt" % lang, "w", encoding="utf-8")
            for plugin in sorted(listings, key=lambda p: (p["t"], p["i"])):
                print("""{"t":'%(t)s',"i":'%(i)s',"n":'%(n)s',"v":'%(v)s',"g":'%(g)s',"d":'%(d)s',"z":'%(z)s'}""" % plugin, file=fp)
            fp.close()
        else:
            # just update the lines from these addons:
            for plugin in sorted(listings, key=lambda p: (p["t"], p["i"])):
                already_added = []
                fp_in = open("../listings/addons-%s.txt" % lang, "r", encoding="utf-8")
                fp_out = open("../listings/addons-%s.new" % lang, "w", encoding="utf-8")
                added = False
                for line in fp_in:
                    if line in already_added:
                        continue
                    dictionary = eval(line)
                    if cmd_arg + ".addon.tgz" in line and plugin["t"] == dictionary["t"] and not added:
                        #print("UPDATED")
                        print("""{"t":'%(t)s',"i":'%(i)s',"n":'%(n)s',"v":'%(v)s',"g":'%(g)s',"d":'%(d)s',"z":'%(z)s'}""" % plugin, file=fp_out)
                        added = True
                        already_added.append("""{"t":'%(t)s',"i":'%(i)s',"n":'%(n)s',"v":'%(v)s',"g":'%(g)s',"d":'%(d)s',"z":'%(z)s'}""" % plugin)
                    elif ((plugin["t"], plugin["i"]) < (dictionary["t"], dictionary["i"])) and not added:
                        #print("ADDED in middle")
                        print("""{"t":'%(t)s',"i":'%(i)s',"n":'%(n)s',"v":'%(v)s',"g":'%(g)s',"d":'%(d)s',"z":'%(z)s'}""" % plugin, file=fp_out)
                        added = True
                        print(line, end="", file=fp_out)
                        already_added.append("""{"t":'%(t)s',"i":'%(i)s',"n":'%(n)s',"v":'%(v)s',"g":'%(g)s',"d":'%(d)s',"z":'%(z)s'}""" % plugin)
                    else:
                        print(line, end="", file=fp_out)
                        already_added.append(line)
                if not added:
                    if ("""{"t":'%(t)s',"i":'%(i)s',"n":'%(n)s',"v":'%(v)s',"g":'%(g)s',"d":'%(d)s',"z":'%(z)s'}""" % plugin) not in already_added:
                        #print("ADDED at end")
                        print("""{"t":'%(t)s',"i":'%(i)s',"n":'%(n)s',"v":'%(v)s',"g":'%(g)s',"d":'%(d)s',"z":'%(z)s'}""" % plugin, file=fp_out)
                fp_in.close()
                fp_out.close()
                shutil.move("../listings/addons-%s.new" % lang, "../listings/addons-%s.txt" % lang)
                    
else:
    raise AttributeError("unknown command")
