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
# python modules
#
#-------------------------------------------------------------------------
import cPickle as pickle
import os
import sys
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# 2.4 provides a built in set. We want to use this, but need to handle 
# older versions of python as well
#
#-------------------------------------------------------------------------
try:
    set()
except:
    from sets import Set as set

#-------------------------------------------------------------------------
#
# enable logging for error handling
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gobject
import gtk
import gtk.glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Utils
import NameDisplay
import DisplayState
import Spell
import GrampsDisplay
import RelLib
import ReportUtils
import AutoComp
import GrampsWidgets

from DdTargets import DdTargets
from WindowUtils import GladeIf
from DisplayTabs import *
from GrampsWidgets import *
from ObjectSelector import PersonSelector,PersonFilterSpec

class ChildEmbedList(EmbeddedList):
    """
    The child embed list is specific to the Edit Family dialog, so it
    is contained here instead of in DisplayTabs.
    """

    _HANDLE_COL = 10
    _DND_TYPE = DdTargets.PERSON_LINK

    _column_names = [
        (_('#'),0) ,
        (_('ID'),1) ,
        (_('Name'),9),
        (_('Gender'),3),
        (_('Paternal'),12),
        (_('Maternal'),13),
        (_('Birth Date'),10),
        (_('Death Date'),11),
        (_('Birth Place'),6),
        (_('Death Place'),7),
        ]
    
    def __init__(self,dbstate,uistate,track,family):
        """
        Create the object, storing the passed family value
        """
        self.family = family
        EmbeddedList.__init__(self, dbstate, uistate, track,
                              _('Children'), ChildModel)

    def build_columns(self):
        """
        We can't use the default build_columns in the base class, because
        we are using the custom TypeCellRenderer to handle father parent
        relationships. The Paternal and Maternal columns (columns 4 and 5)
        use this.
        """
        for column in self.columns:
            self.tree.remove_column(column)
        self.columns = []

        for pair in self.column_order():
            if not pair[0]:
                continue
            name = self._column_names[pair[1]][0]
            if pair[1] == 4 or pair[1] == 5:
                render = TypeCellRenderer(Utils.child_relations)
                column = gtk.TreeViewColumn(name, render, text=pair[1])
            else:
                render = gtk.CellRendererText()
                column = gtk.TreeViewColumn(name, render, text=pair[1])

            column.set_resizable(True)
            column.set_min_width(40)
            column.set_sort_column_id(self._column_names[pair[1]][1])
            self.columns.append(column)
            self.tree.append_column(column)

    def get_icon_name(self):
        return 'gramps-family'

    def is_empty(self):
        """
        The list is considered empty if the child list is empty.
        """
        return len(self.family.get_child_handle_list()) == 0

    def get_data(self):
        """
        Normally, get_data returns a list. However, we return family
        object here instead.
        """
        return self.family

    def column_order(self):
        return [(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(0,8),(0,9)]

    def add_button_clicked(self,obj):
        # we could workout the death years of the parents here and
        # set a suitable filter_spec on the PersonSelector
        # we might also be able to set a filter that only includes
        # people that are not already listed as children in another
        # family.
        selector = PersonSelector(self.dbstate,self.uistate,self.track)

        # this need the window handle of the main EditFamily window
        # to make the PersonSelector transient to it. I am not sure
        # want the best way is to get that handle from here.
        #selector.set_transient_for(self.window)

        # Connect this to the method used to add a new child.
        #selector.connect('add-object',self.on_add_child)
        

    def del_button_clicked(self,obj):
        handle = self.get_selected()
        if handle:
            self.family.remove_child_handle(handle)
            self.rebuild()

    def edit_button_clicked(self,obj):
        handle = self.get_selected()
        if handle:
            import EditPerson
            person = self.dbstate.db.get_person_from_handle(handle)
            EditPerson.EditPerson(self.dbstate,self.uistate,self.track,person)

#-------------------------------------------------------------------------
#
# EditFamily
#
#-------------------------------------------------------------------------
class EditFamily(DisplayState.ManagedWindow):

    def __init__(self,dbstate,uistate,track,family):
        self.dbstate = dbstate
        self.uistate = uistate
        self.family  = family

        DisplayState.ManagedWindow.__init__(self, uistate, track, family)
        if self.already_exist:
            return
        
        self.build_interface()
        self.load_data()

        self.mname  = None
        self.fname  = None

        self.signal_keys = []
        self.signal_keys.append(self.dbstate.db.connect('person-update',
                                                        self.check_for_change))
        self.signal_keys.append(self.dbstate.db.connect('person-delete',
                                                        self.check_for_change))
        self.signal_keys.append(self.dbstate.db.connect('person-rebuild',
                                                        self.reload_people))
        
        self.show()

    def check_for_change(self,handles):
        for node in handles:
            if node in self.phandles:
                self.reload_people()
                break;

    def reload_people(self):
        fhandle = self.family.get_father_handle()
        self.update_father(fhandle)

        mhandle = self.family.get_mother_handle()
        self.update_mother(mhandle)
        self.child_list.rebuild()

    def build_menu_names(self,obj):
        return ('Edit Family','Undefined Submenu')

    def build_window_key(self,obj):
        if self.family.handle:
            return id(self.family.handle)
        else:
            return id(self)

    def build_interface(self):

        self.top = gtk.glade.XML(const.gladeFile,"marriageEditor","gramps")
        self.gladeif = GladeIf(self.top)
        self.window = self.top.get_widget("marriageEditor")

        self.fbirth = self.top.get_widget('fbirth')
        self.fdeath = self.top.get_widget('fdeath')
        
        self.mbirth = self.top.get_widget('mbirth')
        self.mdeath = self.top.get_widget('mdeath')

        self.mbutton= self.top.get_widget('mbutton')
        self.fbutton= self.top.get_widget('fbutton')

        self.mbox   = self.top.get_widget('mbox')
        self.fbox   = self.top.get_widget('fbox')

        self.ok     = self.top.get_widget('ok')
        self.cancel = self.top.get_widget('cancel')

        self.vbox   = self.top.get_widget('vbox')
        self.child_list = self.top.get_widget('child_list')

        self.notebook = gtk.Notebook()
        self.notebook.show()
        self.vbox.pack_start(self.notebook,True)

        self._setup_monitored_values()

        self.cancel.connect('clicked', self.close_window)
        self.ok.connect('clicked', self.apply_changes)

    def _setup_monitored_values(self):
        self.private= GrampsWidgets.PrivacyButton(self.top.get_widget('private'),
                                                  self.family)
                             
        self.gid = GrampsWidgets.MonitoredEntry(self.top.get_widget('gid'),
                                                self.family.set_gramps_id,
                                                self.family.get_gramps_id)
        
        rel_types = dict(Utils.family_relations)

        mtype = self.family.get_relationship()
        if mtype:
            defval = mtype[0]
        else:
            defval = None

        reltype = self.top.get_widget('marriage_type')
        self.type_sel = AutoComp.StandardCustomSelector(
            rel_types, reltype, RelLib.Family.CUSTOM, defval)
        reltype.connect('changed',
                        lambda x: self.family.set_relationship(self.type_sel.get_values()))
        
    def load_data(self):
        fhandle = self.family.get_father_handle()
        self.update_father(fhandle)

        mhandle = self.family.get_mother_handle()
        self.update_mother(mhandle)

        self.phandles = [mhandle, fhandle] + self.family.get_child_handle_list()
        self.phandles = [handle for handle in self.phandles if handle]

        self.mbutton.connect('clicked',self.mother_clicked)
        self.fbutton.connect('clicked',self.father_clicked)

        self.child_list = ChildEmbedList(self.dbstate,self.uistate,
                                         self.track, self.family)
        self.event_list = EventEmbedList(self.dbstate,self.uistate,
                                         self.track,self.family)
        self.src_list = SourceEmbedList(self.dbstate,self.uistate,
                                        self.track,self.family.source_list)
        self.attr_list = AttrEmbedList(self.dbstate, self.uistate, self.track,
                                       self.family.get_attribute_list())
        self.note_tab = NoteTab(self.dbstate, self.uistate, self.track,
                                self.family.get_note_object())
        self.gallery_tab = GalleryTab(self.dbstate, self.uistate, self.track,
                                      self.family.get_media_list())

        self.notebook.insert_page(self.child_list)
        self.notebook.set_tab_label(self.child_list,
                                    self.child_list.get_tab_widget())

        self.notebook.insert_page(self.event_list)
        self.notebook.set_tab_label(self.event_list,
                                    self.event_list.get_tab_widget())

        self.notebook.insert_page(self.src_list)
        self.notebook.set_tab_label(self.src_list,
                                    self.src_list.get_tab_widget())

        self.notebook.insert_page(self.attr_list)
        self.notebook.set_tab_label(self.attr_list,
                                    self.attr_list.get_tab_widget())

        self.notebook.insert_page(self.note_tab)
        self.notebook.set_tab_label(self.note_tab,
                                    self.note_tab.get_tab_widget())

        self.notebook.insert_page(self.gallery_tab)
        self.notebook.set_tab_label(self.gallery_tab,
                                    self.gallery_tab.get_tab_widget())

    def update_father(self,handle):
        self.load_parent(handle, self.fbox, self.fbirth,
                         self.fdeath, self.fbutton)

    def update_mother(self,handle):
        self.load_parent(handle, self.mbox, self.mbirth,
                         self.mdeath, self.mbutton)

    def on_change_mother(self, selector_window, select_result):
        print select_result
        if select_result.is_person():
            try:
                gid = select_result.get_gramps_id()
                person = self.dbstate.db.get_person_from_gramps_id(gid)
                self.family.set_mother_handle(person.get_handle()) 
                self.update_mother(person.get_handle())                    
            except:
                log.warn(
                    "Failed to update mother: \n"
                    "gramps_id returned from selector was: %s\n"
                    "person returned from get_person_from_gramps_id: %s"
                    % (select_result.get_gramps_id(),
                       repr(self.dbstate.db.get_person_from_gramps_id(
                    select_result.get_gramps_id()))))
                raise
        else:
            log.warn(
                "Object selector returned a result of type = %s, it should "
                "have been of type PERSON." % (str(select_result.get_object_type())))
            
        selector_window.close()
            
    def mother_clicked(self,obj):
        handle = self.family.get_mother_handle()
        if handle:
            self.family.set_mother_handle(None)
            self.update_mother(None)
        else:
            filter_spec = PersonFilterSpec()
            filter_spec.set_gender(RelLib.Person.FEMALE)
            
            child_birth_years = []
            for person_handle in self.family.get_child_handle_list():
                person = self.dbstate.db.get_person_from_handle(person_handle)
                event_ref = person.get_birth_ref()
                event_handle = event_ref.ref
                if event_handle:
                    event = self.dbstate.db.get_event_from_handle(event_handle)
                    child_birth_years.append(event.get_date_object().get_year())
                    
            if len(child_birth_years) > 0:
                filter_spec.set_birth_year(min(child_birth_years))
                filter_spec.set_birth_criteria(PersonFilterSpec.BEFORE)
                

            selector = PersonSelector(self.dbstate,self.uistate,
                                      self.track,filter_spec=filter_spec)
            selector.set_transient_for(self.window)
            selector.connect('add-object',self.on_change_mother)
            

    def on_change_father(self, selector_window, select_result):
        if select_result.is_person():
            try:
                gid = select_result.get_gramps_id()
                person = self.dbstate.db.get_person_from_gramps_id(gid)
                self.family.set_father_handle(person.get_handle()) 
                self.update_father(person.get_handle())                    
            except:
                log.warn("Failed to update father: \n"
                         "gramps_id returned from selector was: %s\n"
                         "person returned from get_person_from_gramps_id: %s"
                         % (select_result.get_gramps_id(),
                            repr(self.dbstate.db.get_person_from_gramps_id(
                                    select_result.get_gramps_id()))))
                raise
        else:
            log.warn("Object selector returned a result of type = %s, it should "
                     "have been of type PERSON." % (str(select_result.get_object_type())))
            
        selector_window.close()

    def father_clicked(self,obj):
        handle = self.family.get_father_handle()
        if handle:
            self.family.set_father_handle(None)
            self.update_father(None)
        else:
            filter_spec = PersonFilterSpec()
            filter_spec.set_gender(RelLib.Person.MALE)

            child_birth_years = []
            for person_handle in self.family.get_child_handle_list():
                person = self.dbstate.db.get_person_from_handle(person_handle)
                event_ref = person.get_birth_ref()
                event_handle = event_ref.ref
                if event_handle:
                    event = self.dbstate.db.get_event_from_handle(event_handle)
                    child_birth_years.append(event.get_date_object().get_year())
                    
            if len(child_birth_years) > 0:
                filter_spec.set_birth_year(min(child_birth_years))
                filter_spec.set_birth_criteria(PersonFilterSpec.BEFORE)
                
            selector = PersonSelector(self.dbstate,self.uistate,
                                      self.track,filter_spec=filter_spec)
            selector.set_transient_for(self.window)
            selector.connect('add-object',self.on_change_father)


    def edit_person(self,obj,event,handle):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            import EditPerson
            person = self.dbstate.db.get_person_from_handle(handle)
            EditPerson.EditPerson(self.dbstate, self.uistate,
                                  self.track, person)

    def load_parent(self,handle,box,birth_obj,death_obj,btn_obj):

        is_used = handle != None

        for i in box.get_children():
            box.remove(i)
        
        btn_obj.remove(btn_obj.get_children()[0])
        
        if is_used:
            db = self.dbstate.db
            person = db.get_person_from_handle(handle)
            name = "%s [%s]" % (NameDisplay.displayer.display(person),
                                person.gramps_id)
            data = ReportUtils.get_birth_death_strings(db,person)
            birth = data[0]
            death = data[4]

            del_image = gtk.Image()
            del_image.show()
            del_image.set_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_BUTTON)
            btn_obj.add(del_image)

            box.pack_start(GrampsWidgets.LinkBox(
                GrampsWidgets.BasicLabel(name),
                GrampsWidgets.IconButton(self.edit_person,person.handle)
                ))
        else:
            name = ""
            birth = ""
            death = ""

            add_image = gtk.Image()
            add_image.show()
            add_image.set_from_stock(gtk.STOCK_ADD,gtk.ICON_SIZE_BUTTON)
            btn_obj.add(add_image)

        birth_obj.set_text(birth)
        death_obj.set_text(death)

    def fix_parent_handles(self,orig_handle, new_handle, trans):
        if orig_handle != new_handle:
            if orig_handle:
                person = self.dbstate.db.get_person_from_handle(orig_handle)
                person.family_list.remove(self.family.handle)
                self.dbstate.db.commit_person(person,trans)
            if new_handle:
                person = self.dbstate.db.get_person_from_handle(orig_handle)
                if self.family.handle not in self.person.family_list:
                    person.family_list.append(self.family.handle)
                self.dbstate.db.commit_person(person,trans)

    def apply_changes(self,obj):
        if self.family.handle:
            original = self.dbstate.db.get_family_from_handle(self.family.handle)
        else:
            original = None

        if not original:
            print self.family.serialize()
            trans = self.dbstate.db.transaction_begin()
            self.dbstate.db.add_family(self.family,trans)
            self.dbstate.db.transaction_commit(trans,_("Edit Family"))
        elif cmp(original.serialize(),self.family.serialize()):

            trans = self.dbstate.db.transaction_begin()

            self.fix_parent_handles(original.get_father_handle(),
                                    self.family.get_father_handle(),trans)
            self.fix_parent_handles(original.get_mother_handle(),
                                    self.family.get_mother_handle(),trans)

            orig_set = set(original.get_child_handle_list())
            new_set = set(self.family.get_child_handle_list())

            # remove the family from children which have been removed
            for handle in orig_set.difference(new_set):
                person = self.dbstate.db.get_person_from_handle(handle)
                print person.get_primary_name().get_name()
                print person.get_parent_family_handle_list()
                person.remove_parent_family_handle(self.family.handle)
                print person.get_parent_family_handle_list()
                self.dbstate.db.commit_person(person,trans)
            
            # add the family from children which have been removed
            for handle in new_set.difference(orig_set):
                person = self.dbstate.db.get_person_from_handle(handle)
                #person.remove_parent_family_handle(self.family.handle)
                #self.dbstate.db.commit_person(person,trans)

            self.dbstate.db.commit_family(self.family,trans)
            self.dbstate.db.transaction_commit(trans,_("Edit Family"))
        self.close_window()

    def close_window(self,*obj):
        for key in self.signal_keys:
            self.dbstate.db.disconnect(key)
        self.close()
