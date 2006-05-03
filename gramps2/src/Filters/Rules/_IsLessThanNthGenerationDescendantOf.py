#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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

# $Id$

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from _Rule import Rule

#-------------------------------------------------------------------------
#
# IsLessThanNthGenerationDescendantOf
#
#-------------------------------------------------------------------------
class IsLessThanNthGenerationDescendantOf(Rule):
    """Rule that checks for a person that is a descendant of a specified person
    not more than N generations away"""

    labels      = [ _('ID:'), _('Number of generations:') ]
    name        = _('Descendants of <person> not more than '
                    '<N> generations away')
    category    = _('Descendant filters')
    description = _("Matches people that are descendants of a "
                    "specified person not more than N generations away")

    def prepare(self,db):
        self.db = db
        self.map = {}
        try:
            root_person = db.get_person_from_gramps_id(self.list[0])
            self.init_list(root_person,0)
        except:
            pass

    def reset(self):
        self.map = {}

    def apply(self,db,person):
        return self.map.has_key(person.handle)

    def init_list(self,person,gen):
        if not person:
            return
        if gen:
            self.map[person.handle] = 1
            if gen >= int(self.list[1]):
                return

        for fam_id in person.get_family_handle_list():
            fam = self.db.get_family_from_handle(fam_id)
            for child_handle in fam.get_child_handle_list():
                self.init_list(self.db.get_person_from_handle(child_handle),gen+1)
