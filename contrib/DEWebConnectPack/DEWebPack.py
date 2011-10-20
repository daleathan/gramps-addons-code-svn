# -*- coding: UTF-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011  Doug Blank <doug.blank@gmail.com>
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

# $Id: $

from libwebconnect import *
from TransUtils import get_addon_translator
_ = get_addon_translator(__file__).ugettext

# Format: [[nav_type, id, name, url_pattern], ...]

# http://gramps-project.org/wiki/index.php?title=Resources_and_related_sites#German_information_sites

WEBSITES = [
    ["Person", u"Bielefeld Academic Search", _("Bielefeld Academic Search"), u"http://www.base-search.net/Search/Results?lookfor=%(surname)s,+%(given)s&type=all&lem=0&lem=1&refid=dcbasde"],
    ["Person", "Geneanet", "Geneanet", u"http://search.geneanet.org/result.php?lang=de&name=%(surname)s"],
    ["Person", "FamilySearch", _("FamilySearch.org"), u"https://www.familysearch.org/s/search/index/record-search#searchType=records&filtered=false&fed=true&collectionId=&advanced=false&givenName=%(given)s&surname=%(surname)s&birthYear=%(birth)s&birthLocation=&deathYear=%(death)s&deathLocation="],
    ["Person", "Archive.org", "Archive.org", u'''http://www.archive.org/search.php?query="%(surname)s,+%(given)s"'''],
    ["Person", "GeneaBook", "GeneaBook", u"http://www.geneabook.org/genealogie/1/ouvrages.php?nom=%(surname)s&x=20&y=1"],
    ["Person", "Google Archives", _("Google Archives"), u"http://news.google.de/archivesearch?q=%(surname)s"],
    ["Person", "DE-Google", _("DE Google"), u'''http://www.google.de/#hl=de&q="%(surname)s,+%(given)s"'''],
    ]

def load_on_reg(dbstate, uistate, pdata):
    # do things at time of load
    # now return functions that take:
    #     dbstate, uistate, nav_type, handle
    # and that returns a function that takes a widget
    return lambda nav_type: \
        make_search_functions(nav_type, WEBSITES)

