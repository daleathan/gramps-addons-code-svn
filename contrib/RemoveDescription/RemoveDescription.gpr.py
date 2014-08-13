#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013 Nick Hall
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

#------------------------------------------------------------------------
#
# Remove Generated Event Descriptions
#
#------------------------------------------------------------------------

register(TOOL, 
id    = 'remove_description',
name  = _("Remove Event Description"),
description =  _("Remove generated event descriptions"),
version = '1.0.1',
gramps_target_version = '3.4',
status = STABLE,
fname = 'RemoveDescription.py',
authors = ["Nick Hall"],
authors_email = ["nick-h@gramps-project.org"],
category = TOOL_DBPROC,
toolclass = 'RemoveDescription',
optionclass = 'RemoveDescriptionOptions',
tool_modes = [TOOL_MODE_GUI]
)