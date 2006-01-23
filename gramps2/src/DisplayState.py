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
from cStringIO import StringIO

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
import GrampsDb
import GrampsKeys
import NameDisplay
import GrampsMime
import const

#-------------------------------------------------------------------------
#
# History manager
#
#-------------------------------------------------------------------------
class History(GrampsDb.GrampsDBCallback):

    __signals__ = {
        'changed'      : (list,),
        'menu-changed' : (list,),
        }

    def __init__(self):
        GrampsDb.GrampsDBCallback.__init__(self)
        self.history = []
        self.mhistory = []
        self.index = -1
        self.lock = False

    def clear(self):
        self.history = []
        self.mhistory = []
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
        self.emit('changed',(self.history,))
        self.emit('menu-changed',(self.mhistory,))

    def push(self,person_handle):
        self.prune()
        if len(self.history) == 0 or person_handle != self.history[-1]:
            self.history.append(person_handle)
            if person_handle in self.mhistory:
                self.mhistory.remove(person_handle)
            self.mhistory.append(person_handle)
            self.index += 1
        self.emit('menu-changed',(self.mhistory,))
        self.emit('changed',(self.history,))

    def forward(self,step=1):
        self.index += step
        person_handle = self.history[self.index]
        if person_handle not in self.mhistory:
            self.mhistory.append(person_handle)
            self.emit('menu-changed',(self.mhistory,))
        return str(self.history[self.index])

    def back(self,step=1):
        self.index -= step
        person_handle = self.history[self.index]
        if person_handle not in self.mhistory:
            self.mhistory.append(person_handle)
            self.emit('menu-changed',(self.mhistory,))
        return str(self.history[self.index])

    def at_end(self):
        return self.index+1 == len(self.history)

    def at_front(self):
        return self.index <= 0

    def prune(self):
        if not self.at_end():
            self.history = self.history[0:self.index+1]

#-------------------------------------------------------------------------
#
# Window manager
#
#-------------------------------------------------------------------------

_win_top = '<ui><menubar name="MenuBar"><menu action="WindowsMenu">'
_win_btm = '</menu></menubar></ui>'
DISABLED = -1

class GrampsWindowManager:
    """
    Manage hierarchy of open GRAMPS windows.

    This class's purpose is to manage the hierarchy of open windows.
    The idea is to maintain the tree of branches and leaves.
    A leaf does not have children and corresponds to a single open window.
    A branch has children and corresponds to a group of windows.

    We will follow the convention of having first leaf in any given
    branch represent a parent window of the group, and the rest of the
    children leaves/branches represent windows spawned from the parent.

    The tree structure is maintained as a list of items.
    Items which are lists are branches.
    Items which are not lists are leaves.

    Lookup of an item is done via track sequence. The elements of
    the track sequence specify the lookup order: [2,3,1] means
    'take the second item of the tree, take its third child, and
    then the first child of that child'.

    Lookup can be also done by ID for windows that are identifiable.
    """

    def __init__(self,uimanager):
        # initialize empty tree and lookup dictionary
        self.uimanager = uimanager
        self.window_tree = []
        self.id2item = {}
        self.action_group = gtk.ActionGroup('WindowManger')
        self.active = DISABLED
        self.ui = _win_top + _win_btm
        
    def disable(self):
        """
        Removes the UI and action groups if the navigation is enabled
        """
        if self.active != DISABLED:
            self.uimanager.remove_ui(self.active)
            self.uimanager.remove_action_group(self.action_group)
            self.active = DISABLED

    def enable(self):
        """
        Enables the UI and action groups
        """
        self.uimanager.insert_action_group(self.action_group, 1)
        self.active = self.uimanager.add_ui_from_string(self.ui)

    def get_item_from_track(self,track):
        # Recursively find an item given track sequence
        item = self.window_tree
        for index in track:
            item = item[index]
        return item

    def get_item_from_id(self,item_id):
        # Find an item given its ID
        # Return None if the ID is not found
        return self.id2item.get(item_id,None)
    
    def close_track(self,track):
        # This is called when item needs to be closed
        # Closes all its children and then removes the item from the tree.
        item = self.get_item_from_track(track)
        self.recursive_action(item,self.close_item)
        # This only needs to be run once for the highest level point
        # to remove.
        self.remove_item(track)

    def recursive_action(self,item,func,*args):
        # This function recursively calls itself over the child items
        # starting with the given item.
        # Eventualy, every non-list item (leaf) will be reached
        # and the func(item,*args) will be called on that item.
        if type(item) == list:
            # If this item is a branch
            # close the children except for the first one
            for sub_item in item[1:]:
                self.recursive_action(sub_item,func,*args)
            # return the first child
            last_item = item[0]
        else:
            # This item is a leaf -- no children to close
            # return itself
            last_item = item
        func(last_item,*args)

    def close_item(self,item,*args):
        # Given an item, close its window and remove it's ID from the dict
        if item.window_id:
            del self.id2item[item.window_id]
        item.window.destroy()

    def remove_item(self,track):
        # We need the whole gymnastics below because our item
        # may actually be a list consisting of a single real
        # item and empty lists.
        
        # find the track corresponding to the parent item
        parent_track = track[:-1]
        # find index of our item in parent
        child_in_parent = track[-1:][0]
        # obtain parent item and remove our item from it
        parent_item = self.get_item_from_track(parent_track)
        parent_item.pop(child_in_parent)
        # Adjust each item following the removed one
        # so that it's track is down by one on this level
        for ix in range(child_in_parent,len(parent_item)):
            item = parent_item[ix]
            self.recursive_action(item,self.move_item_down,len(track)-1)
        # Rebuild menu
        self.build_windows_menu()

    def move_item_down(self,item,*args):
        # Given an item and an index, adjust the item's track
        # by subtracting 1 from that index's level
        index = args[0]
        item.track[index] -= 1

    def add_item(self,track,item):
        # if the item is identifiable then we need to remember
        # its id so that in the future we recall this window
        # instead of spawning a new one
        if item.window_id:
            self.id2item[item.window_id] = item

        # Make sure we have a track
        parent_item = self.get_item_from_track(track)
        assert type(parent_item) == list or track == [], \
               "Gwm: add_item: Incorrect track."

        # Prepare a new item, depending on whether it is branch or leaf
        if item.submenu_label:
            # This is an item with potential children -- branch
            new_item = [item]
        else:
            # This is an item without children -- leaf
            new_item = item

        # append new item to the parent
        parent_item.append(new_item)

        # rebuild the Windows menu based on the new tree
        self.build_windows_menu()

        # prepare new track corresponding to the added item and return it
        new_track = track + [len(parent_item)-1]
        return new_track

    def call_back_factory(self,item):
        if type(item) != list:
            def f(obj):
                if item.window_id and self.id2item.get(item.window_id):
                    self.id2item[item.window_id].present()
        else:
            def f(obj):
                pass
        return f

    def generate_id(self,item):
        return str(item.window_id)

    def display_menu_list(self,data,action_data,mlist):
        i = mlist[0]
        idval = self.generate_id(i)
        data.write('<menu action="M:%s">' % idval)
        data.write('<menuitem action="%s"/>' % idval)

        action_data.append(("M:"+idval,None,i.submenu_label,None,None,None))
        action_data.append((idval,None,i.menu_label,None,None,
                            self.call_back_factory(i)))

        if len(mlist) > 1:
            for i in mlist[1:]:
                if type(i) == list:
                    self.display_menu_list(data,action_data,i)
                else:
                    idval = self.generate_id(i)
                    data.write('<menuitem action="%s"/>'
                               % self.generate_id(i))        
                    action_data.append((idval,None,i.menu_label,None,None,
                                        self.call_back_factory(i)))
        data.write('</menu>')
        
    def build_windows_menu(self):
        if self.active != DISABLED:
            self.uimanager.remove_ui(self.active)
            self.uimanager.remove_action_group(self.action_group)

        self.action_group = gtk.ActionGroup('WindowManger')
        action_data = []

        data = StringIO()
        data.write(_win_top)
        for i in self.window_tree:
            self.display_menu_list(data,action_data,i)
        data.write(_win_btm)
        self.ui = data.getvalue()
        data.close()
        self.action_group.add_actions(action_data)
        self.enable()


#-------------------------------------------------------------------------
#
# Recent Docs Menu
#
#-------------------------------------------------------------------------

_rct_top = '<ui><menubar name="MenuBar"><menu action="FileMenu"><menu action="OpenRecent">'
_rct_btm = '</menu></menu></menubar></ui>'

import RecentFiles
import os

class RecentDocsMenu:
    def __init__(self,uistate, state, fileopen):
        self.action_group = gtk.ActionGroup('RecentFiles')
        self.active = DISABLED
        self.uistate = uistate
        self.uimanager = uistate.uimanager
        self.fileopen = fileopen
        self.state = state

        menu_item = self.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent')
        self.uistate.set_open_recent_menu(menu_item.get_submenu())

    def load(self,item):
        name = item.get_path()
        dbtype = item.get_mime()
        
        db = GrampsDb.gramps_db_factory(dbtype)()
        self.state.change_database(db)
        self.fileopen(name)
        RecentFiles.recent_files(name,dbtype)
        self.build()

    def build(self):
        f = StringIO()
        f.write(_rct_top)
        gramps_rf = RecentFiles.GrampsRecentFiles()

        count = 0
        
        if self.active != DISABLED:
            self.uimanager.remove_ui(self.active)
            self.uimanager.remove_action_group(self.action_group)
            self.active = DISABLED
            
        actions = []
        rfiles = gramps_rf.gramps_recent_files
        rfiles.sort(by_time)
        for item in rfiles:
            try:
                filename = os.path.basename(item.get_path()).replace('_','__')
                filetype = GrampsMime.get_type(item.get_path())
                action_id = "RecentMenu%d" % count
                f.write('<menuitem action="%s"/>' % action_id)
                actions.append((action_id,None,filename,None,None,
                                make_callback(item,self.load)))
            except RuntimeError:
                pass    # ignore no longer existing files
            
            count +=1
        f.write(_rct_btm)
        self.action_group.add_actions(actions)
        self.uimanager.insert_action_group(self.action_group,1)
        self.active = self.uimanager.add_ui_from_string(f.getvalue())
        f.close()

        menu_item = self.uistate.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent')
        self.uistate.set_open_recent_menu(menu_item.get_submenu())

def make_callback(n,f):
    return lambda x: f(n)

def by_time(a,b):
    return cmp(b.get_time(),a.get_time())

#-------------------------------------------------------------------------
#
# Gramps Managed Window class
#
#-------------------------------------------------------------------------
class ManagedWindow:
    """
    Managed window base class.
    
    This class provides all the goodies necessary for user-friendly window
    management in GRAMPS: registering the menu item under the Windows
    menu, keeping track of child windows, closing them on close/delete
    event, and presenting itself when selected or attempted to create again.
    """

    def __init__(self,uistate,track,obj):
        """
        Create child windows and add itself to menu, if not there already.
        
        
        The usage from derived classes is envisioned as follows:
        
        
        import DisplayState
        class SomeWindowClass(DisplayState.ManagedWindow):
            def __init__(self,uistate,dbstate,track):
                window_id = self        # Or e.g. window_id = person.handle
                submenu_label = None    # This window cannot have children
                menu_label = 'Menu label for this window'
                DisplayState.ManagedWindow.__init__(self,
                                                    uistate,
                                                    track,
                                                    window_id,
                                                    submenu_label,
                                                    menu_label)
                if self.already_exist:
                    return
                
                # Proceed with the class.
                ...
                
        """

        window_key = self.build_window_key(obj)
        menu_label,submenu_label = self.build_menu_names(obj)
            
        if uistate.gwm.get_item_from_id(window_key):
            uistate.gwm.get_item_from_id(window_key).present()
            self.already_exist = True
        else:
            self.already_exist = False
            self.window_id = window_key
            self.submenu_label = submenu_label
            self.menu_label = menu_label
            self.uistate = uistate
            self.track = self.uistate.gwm.add_item(track,self)
            # Work out parent_window
            if len(self.track) > 1:
            # We don't belong to the lop level
                if self.track[-1] > 0:
                # If we are not the first in the group,
                # then first in that same group is our parent
                    parent_item_track = self.track[:-1]
                    parent_item_track.append(0)
                else:
                # If we're first in the group, then our parent
                # is the first in the group one level up
                    parent_item_track = self.track[:-2]
                    parent_item_track.append(0)

                # Based on the track, get item and then window object
                self.parent_window = self.uistate.gwm.get_item_from_track(
                    parent_item_track).window
            else:
                # On the top level: we use gramps top window
                self.parent_window = self.uistate.window

    def build_menu_names(self,obj):
        return ('Undefined Menu','Undefined Submenu')

    def build_window_key(self,obj):
        return id(self)

    def show(self):
        self.window.set_transient_for(self.parent_window)
        self.window.show()

    def close(self,obj=None,obj2=None):
        """
        Close itself.

        Takes care of closing children and removing itself from menu.
        """
        self.uistate.gwm.close_track(self.track)

    def present(self):
        """
        Present window (unroll/unminimize/bring to top).
        """
        self.window.present()

#-------------------------------------------------------------------------
#
# Gramps Display State class
#
#-------------------------------------------------------------------------

import logging
from GrampsLogger import RotateHandler

class WarnHandler(RotateHandler):
    def __init__(self,capacity,button):
        RotateHandler.__init__(self,capacity)
        self.setLevel(logging.WARN)
        self.button = button
        button.on_clicked(self.display)
        self.timer = None

    def emit(self,record):
        if self.timer:
            gobject.source_remove(self.timer)
        gobject.timeout_add(180*1000,self._clear)
        RotateHandler.emit(self,record)
        self.button.show()

    def _clear(self):
        self.button.hide()
        self.set_capacity(self._capacity)
        self.timer = None
        return False

    def display(self,obj):
        obj.hide()
        g = gtk.glade.XML(const.gladeFile,'scrollmsg')
        top = g.get_widget('scrollmsg')
        msg = g.get_widget('msg')
        buf = msg.get_buffer()
        for i in self.get_formatted_log():
            buf.insert_at_cursor(i + '\n')
        self.set_capacity(self._capacity)
        top.run()
        top.destroy()

class DisplayState(GrampsDb.GrampsDBCallback):

    __signals__ = {
        }

    def __init__(self,window,status,warnbtn,uimanager,dbstate):
        self.dbstate = dbstate
        self.uimanager = uimanager
        self.window = window
        GrampsDb.GrampsDBCallback.__init__(self)
        self.status = status
        self.status_id = status.get_context_id('GRAMPS')
        self.phistory = History()
        self.gwm = GrampsWindowManager(uimanager)
        self.widget = None
        self.warnbtn = warnbtn

        formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')
        self.rh = WarnHandler(capacity=400,button=warnbtn)
        self.rh.setFormatter(formatter)
        self.log = logging.getLogger()
        self.log.setLevel(logging.WARN)
        self.log.addHandler(self.rh)

    def set_open_widget(self,widget):
        self.widget = widget

    def set_open_recent_menu(self,menu):
        self.widget.set_menu(menu)

    def push_message(self, text):
        self.status_text(text)
        gobject.timeout_add(5000,self.modify_statusbar)

    def modify_statusbar(self,active=None):
        self.status.pop(self.status_id)
        if self.dbstate.active == None:
            self.status.push(self.status_id,"")
        else:
            if GrampsKeys.get_statusbar() <= 1:
                pname = NameDisplay.displayer.display(self.dbstate.active)
                name = "[%s] %s" % (self.dbstate.active.get_gramps_id(),pname)
            else:
                name = "" #self.display_relationship()
            self.status.push(self.status_id,name)

        while gtk.events_pending():
            gtk.main_iteration()

    def status_text(self,text):
        self.status.pop(self.status_id)
        self.status.push(self.status_id,text)
        while gtk.events_pending():
            gtk.main_iteration()


if __name__ == "__main__":

    import GrampsWidgets
    
    rh = WarnHandler(capacity=400,button=GrampsWidgets.WarnButton())
    log = logging.getLogger()
    log.setLevel(logging.WARN)
    log.addHandler(rh)

