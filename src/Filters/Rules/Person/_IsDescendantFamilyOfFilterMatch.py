#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2007  Donald N. Allingham
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

# $Id: _IsDescendantOfFilterMatch.py 15855 2010-09-03 22:54:40Z bmcage $

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from _IsDescendantFamilyOf import IsDescendantFamilyOf
from _MatchesFilter import MatchesFilter

#-------------------------------------------------------------------------
#
# IsDescendantFamilyOfFilterMatch
#
#-------------------------------------------------------------------------
class IsDescendantFamilyOfFilterMatch(IsDescendantFamilyOf):
    """Rule that checks for a person that is a descendant
    of someone matched by a filter"""

    labels      = [ _('Filter name:') ]
    name        = _('Descendant family members of <filter> match')
    category    = _('Descendant filters')
    description = _("Matches people that are descendants or the spouse "
                    "of anybody matched by a filter")
    
    def prepare(self,db):
        self.db = db
        self.matches = set()

        filt = MatchesFilter(self.list[0:1])
        filt.requestprepare(db)
        for person in db.iter_people():
            if filt.apply(db, person):
                self.add_matches(person)
        filt.requestreset()

