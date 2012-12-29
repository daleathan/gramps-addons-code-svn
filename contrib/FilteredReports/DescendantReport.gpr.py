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

#------------------------------------------------------------------------
#
# Filtered Descendant Report
#
#------------------------------------------------------------------------

register(REPORT,
         id = 'fil_descendant_report',
         name = _("Filtered Descendant Report"),
         description =  _("Produces a descendant report using a filter"),
         version = '0.2.1',
         gramps_target_version = '3.4',
         status = STABLE,
         fname = 'DescendantReport.py',
         authors = ["Adam Stein"],
         authors_email = ["adam@csh.rit.edu"],
         category = CATEGORY_TEXT,
         reportclass = 'DescendantReport',
         optionclass = 'DescendantOptions',
         report_modes = [REPORT_MODE_GUI, REPORT_MODE_BKI, REPORT_MODE_CLI]
        )
