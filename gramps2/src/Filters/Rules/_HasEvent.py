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
import DateHandler
from _Rule import Rule
from _RuleUtils import date_cmp

#-------------------------------------------------------------------------
#
# HasEvent
#
#-------------------------------------------------------------------------
class HasEvent(Rule):
    """Rule that checks for a person with a particular value"""

    labels      = [ _('Personal event:'), 
                    _('Date:'), 
                    _('Place:'), 
                    _('Description:') ]
    name        =  _('People with the personal <event>')
    description = _("Matches people with a personal event of a particular value")
    category    = _('Event filters')
    
    def prepare(self,db):
        self.date = None
        try:
            if self.list[1]:
                self.date = DateHandler.parser.parse(self.list[1])
        except: pass

    def apply(self,db,person):
        for event_handle in person.get_event_list():
            if not event_handle:
                continue
            event = db.get_event_from_handle(event_handle)
            val = 1
            if self.list[0] and event.get_name() != self.list[0]:
                val = 0
            if self.list[3] and event.get_description().upper().find(
                                            self.list[3].upper())==-1:
                val = 0
            if self.date:
                if date_cmp(self.date,event.get_date_object()):
                    val = 0
            if self.list[2]:
                pl_id = event.get_place_handle()
                if pl_id:
                    pl = db.get_place_from_handle(pl_id)
                    pn = pl.get_title()
                    if pn.upper().find(self.list[2].upper()) == -1:
                        val = 0
            if val == 1:
                return True
        return False
