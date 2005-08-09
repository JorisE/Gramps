# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2003  Donald N. Allingham
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

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------

from gettext import gettext as _

#-------------------------------------------------------------------------
#
# gtk
#
#-------------------------------------------------------------------------
import gtk
from gtk.gdk import ACTION_COPY, BUTTON1_MASK

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import PeopleModel
import PageView
import GenericFilter
import EditPerson
import NameDisplay
import Utils
import QuestionDialog

from DdTargets import DdTargets

column_names = [
    _('Name'),
    _('ID') ,
    _('Gender'),
    _('Birth Date'),
    _('Birth Place'),
    _('Death Date'),
    _('Death Place'),
    _('Spouse'),
    _('Last Change'),
    _('Cause of Death'),
    ]


class PersonView(PageView.PageView):

    def __init__(self,state):
        PageView.PageView.__init__(self,'Person View',state)
        self.inactive = False
        state.connect('database-changed',self.change_db)
        state.connect('active-changed',self.goto_active_person)

    def setup_filter(self):
        all = GenericFilter.GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(GenericFilter.Everyone([]))

        self.DataFilter = None
        self.init_filters()

    def define_actions(self):
        self.add_action('Add',    gtk.STOCK_ADD,       "_Add",     callback=self.add)
        self.add_action('Edit',   gtk.STOCK_EDIT,      "_Edit",    callback=self.edit)
        self.add_action('Remove', gtk.STOCK_REMOVE,    "_Remove",  callback=self.remove)
        self.add_action('Forward',gtk.STOCK_GO_FORWARD,"_Forward", callback=self.fwd_clicked)
        self.add_action('Back',   gtk.STOCK_GO_BACK,   "_Back",    callback=self.back_clicked)
        self.add_action('HomePerson', gtk.STOCK_HOME,  "_Home",    callback=self.home)
        self.add_toggle_action('Filter',  None,        '_Filter',  callback=self.filter_toggle)

    def get_stock(self):
        return 'gramps-person'

    def build_tree(self):
        self.person_model = PeopleModel.PeopleModel(
            self.state.db, self.DataFilter, self.filter_invert.get_active())
        self.person_tree.set_model(self.person_model)

    def build_widget(self):
        self.vbox = gtk.VBox()
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(4)
        
        self.filterbar = gtk.HBox()
        self.filterbar.set_spacing(4)
        self.filter_text = gtk.Entry()
        self.filter_label = gtk.Label('Label:')
        self.filter_list = gtk.ComboBox()
        self.filter_invert = gtk.CheckButton('Invert')
        self.filter_button = gtk.Button('Apply')
        self.filterbar.pack_start(self.filter_list,False)
        self.filterbar.pack_start(self.filter_label,False)
        self.filterbar.pack_start(self.filter_text,True)
        self.filterbar.pack_start(self.filter_invert,False)
        self.filterbar.pack_end(self.filter_button,False)

        self.filter_text.hide()
        self.filter_text.set_sensitive(0)
        self.filter_label.hide()

        self.person_tree = gtk.TreeView()
        self.person_tree.set_rules_hint(True)
        self.person_tree.set_headers_visible(True)

        scrollwindow = gtk.ScrolledWindow()
        scrollwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwindow.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrollwindow.add(self.person_tree)

        self.vbox.pack_start(self.filterbar,False)
        self.vbox.pack_start(scrollwindow,True)

        # temporary hack

        self.renderer = gtk.CellRendererText()
        self.inactive = False

        self.columns = []
        self.build_columns()
        self.person_tree.connect('row_activated', self.alpha_event)
        self.person_tree.connect('button-press-event',
                                 self.on_plist_button_press)
        self.person_tree.connect('drag_data_get', self.person_drag_data_get)


        self.person_selection = self.person_tree.get_selection()
        self.person_selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.person_selection.connect('changed',self.row_changed)

        self.vbox.set_focus_chain([self.person_tree,self.filter_list, self.filter_text,
                                   self.filter_invert, self.filter_button])

        a = gtk.ListStore(str,str)
        self.person_tree.set_model(a)

        self.setup_filter()

        return self.vbox
    
    def ui_definition(self):
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="ViewMenu">
              <menuitem action="Filter"/>
            </menu>
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
                <menuitem action="HomePerson"/>
                <separator/>
              </placeholder>
            </menu>
            <menu action="EditMenu">
              <placeholder name="CommonEdit">
                <menuitem action="Add"/>
                <menuitem action="Edit"/>
                <menuitem action="Remove"/>
              </placeholder>
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
              <toolitem action="HomePerson"/>
            </placeholder>
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
            </placeholder>
          </toolbar>
        </ui>'''

    def filter_toggle(self,obj):
        if obj.get_active():
            self.filterbar.show()
        else:
            self.filterbar.hide()

    def add(self,obj):
        person = RelLib.Person()
        EditPerson.EditPerson(self, person, self.state.db,
                              None)

    def edit(self,obj):
        EditPerson.EditPerson(self, self.state.active, self.state.db,
                              None)

    def remove(self,obj):
        mlist = self.get_selected_objects()
        if len(mlist) == 0:
            return
        
        for sel in mlist:
            p = self.state.db.get_person_from_handle(sel)
            self.active_person = p
            name = NameDisplay.displayer.display(p) 

            msg = _('Deleting the person will remove the person '
                             'from the database.')
            msg = "%s %s" % (msg,Utils.data_recover_msg)
            QuestionDialog.QuestionDialog(_('Delete %s?') % name,msg,
                                          _('_Delete Person'),
                                          self.delete_person_response)

    def delete_person_response(self):
        #self.disable_interface()
        trans = self.state.db.transaction_begin()
        
        n = NameDisplay.displayer.display(self.active_person)

        if self.state.db.get_default_person() == self.active_person:
            self.state.db.set_default_person_handle(None)

        for family_handle in self.active_person.get_family_handle_list():
            if not family_handle:
                continue
            family = self.state.db.get_family_from_handle(family_handle)
            family_to_remove = False
            if self.active_person.get_handle() == family.get_father_handle():
                if family.get_mother_handle():
                    family.set_father_handle(None)
                else:
                    family_to_remove = True
            else:
                if family.get_father_handle():
                    family.set_mother_handle(None)
                else:
                    family_to_remove = True
            if family_to_remove:
                for child_handle in family.get_child_handle_list():
                    child = self.state.db.get_person_from_handle(child_handle)
                    child.remove_parent_family_handle(family_handle)
                    self.db.commit_person(child,trans)
                self.state.db.remove_family(family_handle,trans)
            else:
                self.state.db.commit_family(family,trans)

        for (family_handle,mrel,frel) in self.active_person.get_parent_family_handle_list():
            if family_handle:
                family = self.db.get_family_from_handle(family_handle)
                family.remove_child_handle(self.active_person.get_handle())
                self.db.commit_family(family,trans)

        handle = self.active_person.get_handle()

        person = self.active_person
        self.remove_from_person_list(person)
        self.people_view.remove_from_history(handle)
        self.state.db.remove_person(handle, trans)

        if self.state.phistory.index >= 0:
            self.active_person = self.state.db.get_person_from_handle(self.state.phistory.history[self.index])
        else:
            self.state.change_active_person(None)
        self.state.db.transaction_commit(trans,_("Delete Person (%s)") % n)
        #self.redraw_histmenu()
        #self.enable_interface()

    def build_columns(self):
        for column in self.columns:
            self.person_tree.remove_column(column)
            
        column = gtk.TreeViewColumn(_('Name'), self.renderer,text=0)
        column.set_resizable(True)
        #column.set_clickable(True)
        #column.connect('clicked',self.sort_clicked)
        column.set_min_width(225)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.person_tree.append_column(column)
        self.columns = [column]

        for pair in self.state.db.get_person_column_order():
            if not pair[0]:
                continue
            name = column_names[pair[1]]
            column = gtk.TreeViewColumn(name, self.renderer, markup=pair[1])
            column.set_resizable(True)
            column.set_min_width(60)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
            self.columns.append(column)
            self.person_tree.append_column(column)

    def row_changed(self,obj):
        """Called with a row is changed. Check the selected objects from
        the person_tree to get the IDs of the selected objects. Set the
        active person to the first person in the list. If no one is
        selected, set the active person to None"""

        selected_ids = self.get_selected_objects()
        try:
            person = self.state.db.get_person_from_handle(selected_ids[0])
            self.state.change_active_person(person)
            self.goto_active_person()
        except:
            self.state.change_active_person(None)

        if len(selected_ids) == 1:
            self.person_tree.drag_source_set(BUTTON1_MASK,
                                             [DdTargets.PERSON_LINK.target()],
                                             ACTION_COPY)
        elif len(selected_ids) > 1:
            self.person_tree.drag_source_set(BUTTON1_MASK,
                                             [DdTargets.PERSON_LINK_LIST.target()],
                                             ACTION_COPY)
        self.state.modify_statusbar()
        
    def alpha_event(self,*obj):
        pass
        #self.parent.load_person(self.parent.active_person)

    def on_plist_button_press(self,obj,event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.build_people_context_menu(event)

    def person_drag_data_get(self, widget, context, sel_data, info, time):
        selected_ids = self.get_selected_objects()

        if len(selected_ids) == 1:
            sel_data.set(sel_data.target, 8, selected_ids[0])
        elif len(selected_ids) > 1:
            sel_data.set(DdTargets.PERSON_LINK_LIST.drag_type,8,
                         pickle.dumps(selected_ids))

    def apply_filter_clicked(self):
        index = self.filter_list.get_active()
        self.DataFilter = self.filter_model.get_filter(index)
        if self.DataFilter.need_param:
            qual = unicode(self.filter_text.get_text())
            self.DataFilter.set_parameter(qual)
        self.apply_filter()
        self.goto_active_person()

    def goto_active_person(self,obj=None):
        if not self.state.active or self.inactive:
            return
        self.inactive = True
        p = self.state.active
        try:
            path = self.person_model.on_get_path(p.get_handle())
            group_name = p.get_primary_name().get_group_name()
            top_name = self.state.db.get_name_group_mapping(group_name)
            top_path = self.person_model.on_get_path(top_name)
            self.person_tree.expand_row(top_path,0)

            current = self.person_model.on_get_iter(path)
            selected = self.person_selection.path_is_selected(path)
            if current != p.get_handle() or not selected:
                self.person_selection.unselect_all()
                self.person_selection.select_path(path)
                self.person_tree.scroll_to_cell(path,None,1,0.5,0)
        except KeyError:
            self.person_selection.unselect_all()
            print "Person not currently available due to filter"
            self.state.active = p
        self.inactive = False

    def redisplay_person_list(self):
        self.build_tree()

    def person_added(self,handle_list):
        for node in handle_list:
            person = self.state.db.get_person_from_handle(node)
            top = person.get_primary_name().get_group_name()
            self.person_model.rebuild_data(self.DataFilter)
            if not self.person_model.is_visable(node):
                continue
            if (not self.person_model.sname_sub.has_key(top) or 
                len(self.person_model.sname_sub[top]) == 1):
                path = self.person_model.on_get_path(top)
                pnode = self.person_model.get_iter(path)
                self.person_model.row_inserted(path,pnode)
            path = self.person_model.on_get_path(node)
            pnode = self.person_model.get_iter(path)
            self.person_model.row_inserted(path,pnode)

    def person_removed(self,handle_list):
        for node in handle_list:
            person = self.state.db.get_person_from_handle(node)
            if not self.person_model.is_visable(node):
                continue
            top = person.get_primary_name().get_group_name()
            mylist = self.person_model.sname_sub.get(top,[])
            if mylist:
                try:
                    path = self.person_model.on_get_path(node)
                    self.person_model.row_deleted(path)
                    if len(mylist) == 1:
                        path = self.person_model.on_get_path(top)
                        self.person_model.row_deleted(path)
                except KeyError:
                    pass
        self.person_model.rebuild_data(self.DataFilter,skip=node)

    def person_updated(self,handle_list):
        for node in handle_list:
            person = self.state.db.get_person_from_handle(node)
            try:
                oldpath = self.person_model.iter2path[node]
            except:
                return
            pathval = self.person_model.on_get_path(node)
            pnode = self.person_model.get_iter(pathval)

            # calculate the new data

            if person.primary_name.group_as:
                surname = person.primary_name.group_as
            else:
                surname = self.state.db.get_name_group_mapping(person.primary_name.surname)


            if oldpath[0] == surname:
                self.person_model.build_sub_entry(surname)
            else:
                self.person_model.calculate_data(self.DataFilter)
            
            # find the path of the person in the new data build
            newpath = self.person_model.temp_iter2path[node]
            
            # if paths same, just issue row changed signal

            if oldpath == newpath:
                self.person_model.row_changed(pathval,pnode)
            else:
                # paths different, get the new surname list
                
                mylist = self.person_model.temp_sname_sub.get(oldpath[0],[])
                path = self.person_model.on_get_path(node)
                
                # delete original
                self.person_model.row_deleted(pathval)
                
                # delete top node of original if necessar
                if len(mylist)==0:
                    self.person_model.row_deleted(pathval[0])
                    
                # determine if we need to insert a new top node',
                insert = not self.person_model.sname_sub.has_key(newpath[0])

                # assign new data
                self.person_model.assign_data()
                
                # insert new row if needed
                if insert:
                    path = self.person_model.on_get_path(newpath[0])
                    pnode = self.person_model.get_iter(path)
                    self.person_model.row_inserted(path,pnode)

                # insert new person
                path = self.person_model.on_get_path(node)
                pnode = self.person_model.get_iter(path)
                self.person_model.row_inserted(path,pnode)
                
        self.goto_active_person()

    def change_db(self,db):
        self.build_columns()
        db.connect('person-add', self.person_added)
        db.connect('person-update', self.person_updated)
        db.connect('person-delete', self.person_removed)
        db.connect('person-rebuild', self.redisplay_person_list)
        self.apply_filter()

    def init_filters(self):

        cell = gtk.CellRendererText()
        self.filter_list.clear()
        self.filter_list.pack_start(cell,True)
        self.filter_list.add_attribute(cell,'text',0)

        filter_list = []

        all = GenericFilter.GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(GenericFilter.Everyone([]))
        filter_list.append(all)
        
        all = GenericFilter.GenericFilter()
        all.set_name(_("Females"))
        all.add_rule(GenericFilter.IsFemale([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("Males"))
        all.add_rule(GenericFilter.IsMale([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with unknown gender"))
        all.add_rule(GenericFilter.HasUnknownGender([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("Disconnected individuals"))
        all.add_rule(GenericFilter.Disconnected([]))
        filter_list.append(all)

        all = GenericFilter.ParamFilter()
        all.set_name(_("People with names containing..."))
        all.add_rule(GenericFilter.SearchName([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("Adopted people"))
        all.add_rule(GenericFilter.HaveAltFamilies([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with images"))
        all.add_rule(GenericFilter.HavePhotos([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with incomplete names"))
        all.add_rule(GenericFilter.IncompleteNames([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with children"))
        all.add_rule(GenericFilter.HaveChildren([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with no marriage records"))
        all.add_rule(GenericFilter.NeverMarried([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with multiple marriage records"))
        all.add_rule(GenericFilter.MultipleMarriages([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People without a known birth date"))
        all.add_rule(GenericFilter.NoBirthdate([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with incomplete events"))
        all.add_rule(GenericFilter.PersonWithIncompleteEvent([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("Families with incomplete events"))
        all.add_rule(GenericFilter.FamilyWithIncompleteEvent([]))
        filter_list.append(all)

        all = GenericFilter.ParamFilter()
        all.set_name(_("People probably alive"))
        all.add_rule(GenericFilter.ProbablyAlive([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People marked private"))
        all.add_rule(GenericFilter.PeoplePrivate([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("Witnesses"))
        all.add_rule(GenericFilter.IsWitness([]))
        filter_list.append(all)

        all = GenericFilter.ParamFilter()
        all.set_name(_("People with records containing..."))
        all.add_rule(GenericFilter.HasTextMatchingSubstringOf([]))
        filter_list.append(all)

        all = GenericFilter.ParamFilter()
        all.set_name(_("People with records matching regular expression..."))
        all.add_rule(GenericFilter.HasTextMatchingRegexpOf([]))
        filter_list.append(all)

        all = GenericFilter.GenericFilter()
        all.set_name(_("People with notes"))
        all.add_rule(GenericFilter.HasNote([]))
        filter_list.append(all)

        all = GenericFilter.ParamFilter()
        all.set_name(_("People with notes containing..."))
        all.add_rule(GenericFilter.HasNoteMatchingSubstringOf([]))
        filter_list.append(all)

        self.filter_model = GenericFilter.FilterStore(filter_list)
        self.filter_list.set_model(self.filter_model)
        self.filter_list.set_active(self.filter_model.default_index())
        self.filter_list.connect('changed',self.on_filter_name_changed)
        self.filter_text.set_sensitive(0)
        
    def on_filter_name_changed(self,obj):
        index = self.filter_list.get_active()
        mime_filter = self.filter_model.get_filter(index)
        qual = mime_filter.need_param
        if qual:
            self.filter_text.show()
            self.filter_text.set_sensitive(1)
            self.filter_label.show()
            self.filter_label.set_text(mime_filter.get_rules()[0].labels[0])
        else:
            self.filter_text.hide()
            self.filter_text.set_sensitive(0)
            self.filter_label.hide()

    def apply_filter(self,current_model=None):
        #self.parent.status_text(_('Updating display...'))
        self.build_tree()
        #self.parent.modify_statusbar()

    def get_selected_objects(self):
        (mode,paths) = self.person_selection.get_selected_rows()
        mlist = []
        for path in paths:
            node = self.person_model.on_get_iter(path)
            mlist.append(self.person_model.on_get_value(node, PeopleModel.COLUMN_INT_ID))
        return mlist

    def remove_from_person_list(self,person):
        """Remove the selected person from the list. A person object is
        expected, not an ID"""
        path = self.person_model.on_get_path(person.get_handle())
        (col,row) = path
        if row > 0:
            self.person_selection.select_path((col,row-1))
        elif row == 0 and self.person_model.on_get_iter(path):
            self.person_selection.select_path(path)

    def build_backhistmenu(self,event):
        """Builds and displays the menu with the back portion of the history"""
        hobj = self.state.phistory
        if hobj.index > 0:
            backhistmenu = gtk.Menu()
            backhistmenu.set_title(_('Back Menu'))
            pids = hobj.history[:hobj.index]
            pids.reverse()
            num = 1
            for pid in pids:
                if num <= 10:
                    f,r = divmod(num,10)
                    hotkey = "_%d" % r
                elif num <= 20:
                    hotkey = "_%s" % chr(ord('a')+num-11)
                elif num >= 21:
                    break
                person = self.state.db.get_person_from_handle(pid)
                item = gtk.MenuItem("%s. %s [%s]" % 
                    (hotkey,
                     NameDisplay.displayer.display(person),
                     person.get_gramps_id()))
                item.connect("activate",self.back_clicked,num)
                item.show()
                backhistmenu.append(item)
                num = num + 1
            backhistmenu.popup(None,None,None,event.button,event.time)

    def back_pressed(self,obj,event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.build_backhistmenu(event)

    def build_fwdhistmenu(self,event):
        """Builds and displays the menu with the forward portion of the history"""
        if self.hindex < len(self.history)-1:
            fwdhistmenu = gtk.Menu()
            fwdhistmenu.set_title(_('Forward Menu'))
            pids = self.history[self.hindex+1:]
            num = 1
            for pid in pids:
                if num <= 10:
                    f,r = divmod(num,10)
                    hotkey = "_%d" % r
                elif num <= 20:
                    hotkey = "_%s" % chr(ord('a')+num-11)
                elif num >= 21:
                    break
                person = self.db.get_person_from_handle(pid)
                item = gtk.MenuItem("%s. %s [%s]" % 
                    (hotkey,
                     NameDisplay.displayer.display(person),
                     person.get_gramps_id()))
                item.connect("activate",self.fwd_clicked,num)
                item.show()
                fwdhistmenu.append(item)
                num = num + 1
            fwdhistmenu.popup(None,None,None,event.button,event.time)

    def fwd_pressed(self,obj,event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.build_fwdhistmenu(event)

    def fwd_clicked(self,obj,step=1):
        print "fwd clicked"
        hobj = self.state.phistory
        hobj.lock = True
        print hobj.history
        if hobj.index+1 < len(hobj.history):
            try:
                hobj.index += step
                handle = str(hobj.history[hobj.index])
                self.state.active = self.state.db.get_person_from_handle(handle)
                self.state.modify_statusbar()
                self.state.change_active_handle(handle)
                hobj.mhistory.append(self.history[hobj.index])
                #self.redraw_histmenu()
                self.set_buttons(True)
                if hobj.index == len(hobj.history)-1:
                    self.fwdbtn.set_sensitive(False)
                    self.forward.set_sensitive(False)
                else:
                    self.fwdbtn.set_sensitive(True)
                    self.forward.set_sensitive(True)
                self.backbtn.set_sensitive(True)
                self.back.set_sensitive(True)
            except:
                self.clear_history()
        else:
            self.fwdbtn.set_sensitive(False)
            self.forward.set_sensitive(False)
            self.backbtn.set_sensitive(True)
            self.back.set_sensitive(True)
        self.goto_active_person()
        hobj.lock = False

    def back_clicked(self,obj,step=1):
        hobj = self.state.phistory
        hobj.lock = True
        if hobj.index > 0:
            try:
                hobj.index -= step
                handle = str(hobj.history[hobj.hindex])
                self.active = self.db.get_person_from_handle(handle)
                self.modify_statusbar()
                self.change_active_handle(handle)
                hobj.mhistory.append(hobj.history[hobj.index])
                self.redraw_histmenu()
                self.set_buttons(1)
                if hobj.index == 0:
                    self.backbtn.set_sensitive(False)
                    self.back.set_sensitive(False)
                else:
                    self.backbtn.set_sensitive(True)
                    self.back.set_sensitive(True)
                self.fwdbtn.set_sensitive(True)
                self.forward.set_sensitive(True)
            except:
                hobj.clear_history()
        else:
            self.backbtn.set_sensitive(False)
            self.back.set_sensitive(False)
            self.fwdbtn.set_sensitive(True)
            self.forward.set_sensitive(True)
        self.goto_active_person()
        hobj.lock = False

    def home(self,obj):
        defperson = self.state.db.get_default_person()
        if defperson:
            self.state.change_active_person(defperson)
            self.goto_active_person()
