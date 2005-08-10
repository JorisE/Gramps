#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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
# Standard python modules
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# GNOME python modules
#
#-------------------------------------------------------------------------
import gobject
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import GrampsDbBase
import GrampsDBCallback
import GrampsKeys
import NameDisplay

class History:

    def __init__(self):
        self.history = []
        self.mhistory = []
        self.index = -1
        self.lock = False

    def clear(self):
        self.history = []
        self.mistory = []
        self.index = -1
        self.lock = False

    def remove(self,person_handle,old_id=None):
        """Removes a person from the history list"""
        if old_id:
            del_id = old_id
        else:
            del_id = person_handle

        hc = self.history.count(del_id)
        for c in range(hc):
            self.history.remove(del_id)
            self.index -= 1
        
        mhc = self.mhistory.count(del_id)
        for c in range(mhc):
            self.mhistory.remove(del_id)

    def push(self,person_handle):
        self.prune()
        if len(self.history) == 0 or person_handle != self.history[-1]:
            self.history.append(person_handle)
            self.mhistory.append(person_handle)
            self.index += 1

    def forward(self,step=1):
        self.index += step
        self.mhistory.append(self.history[self.index])
        return str(self.history[self.index])

    def back(self,step=1):
        self.index -= step
        self.mhistory.append(self.history[self.index])
        return str(self.history[self.index])

    def at_end(self):
        return self.index+1 == len(self.history)

    def at_front(self):
        return self.index == 0

    def prune(self):
        if not self.at_end():
            self.history = self.history[0:self.index+1]

class DbState(GrampsDBCallback.GrampsDBCallback):

    __signals__ = {
        'database-changed' : (GrampsDbBase.GrampsDbBase,),
        'active-changed'   : (str,),
        'no-database'      :  None,
        }

    def __init__(self,window,status,uimanager):
        self.uimanager = uimanager
        self.window = window
        GrampsDBCallback.GrampsDBCallback.__init__(self)
        self.db     = GrampsDbBase.GrampsDbBase()
        self.active = None
        self.status = status
        self.status_id = status.get_context_id('GRAMPS')
        self.phistory = History()

    def get_widget(self,path):
        return self.uimanager.get_widget(path)

    def clear_history(self):
        self.phistory.clear()

    def change_active_person(self,person):
        self.active = person
        if person:
            try:
                self.emit('active-changed',(person.handle,))
            except:
                self.emit('active-changed',("",))

    def change_active_handle(self,handle):
        self.change_active_person(self.db.get_person_from_handle(handle))

    def get_active_person(self):
        return self.active

    def change_database(self,db):
        self.db = db
        self.emit('database-changed',(self.db,))

    def no_database(self):
        self.db = GrampsDbBase.GrampsDbBase()
        self.emit('no-database')

    def modify_statusbar(self):
        
        self.status.pop(self.status_id)
        if self.active == None:
            self.status.push(self.status_id,"")
        else:
            if GrampsKeys.get_statusbar() <= 1:
                pname = NameDisplay.displayer.display(self.active)
                name = "[%s] %s" % (self.active.get_gramps_id(),pname)
            else:
                name = self.display_relationship()
            self.status.push(self.status_id,name)

        while gtk.events_pending():
            gtk.main_iteration()

    def status_text(self,text):
        self.status.pop(self.status_id)
        self.status.push(self.status_id,text)
        while gtk.events_pending():
            gtk.main_iteration()
