# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2005  Donald N. Allingham
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
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.gdk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import RelLib
import PageView
import EditRepository
import DisplayModels
import const
import Utils

from QuestionDialog import QuestionDialog, ErrorDialog

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gettext import gettext as _

column_names = [
    _('Name'),
    _('ID'),
    _('Type'),
    _('Home URL'),
    _('Street'),
    _('ZIP/Postal Code'),
    _('City'),
    _('County'),
    _('State'),
    _('Country'),
    _('Email'),
    _('Search URL'),
    ]

#-------------------------------------------------------------------------
#
# RepositoryView
#
#-------------------------------------------------------------------------
class RepositoryView(PageView.ListView):
    def __init__(self,dbstate,uistate):

        signal_map = {
            'repository-add'     : self.row_add,
            'repository-update'  : self.row_update,
            'repository-delete'  : self.row_delete,
            'repository-rebuild' : self.build_tree,
            }
        
        PageView.ListView.__init__(self,'Repository View',dbstate,uistate,
                                   column_names,len(column_names),
                                   DisplayModels.RepositoryModel,
                                   signal_map)


    def column_order(self):
        return self.dbstate.db.get_repository_column_order()


    def get_stock(self):
        return 'gramps-repository'

    def ui_definition(self):
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="ViewMenu">
              <menuitem action="Filter"/>
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
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
            </placeholder>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Add"/>
            <menuitem action="Edit"/>
            <menuitem action="Remove"/>
          </popup>
        </ui>'''

    def on_double_click(self,obj,event):
        handle = self.first_selected()
        repos = self.dbstate.db.get_repository_from_handle(handle)
        EditRepository.EditRepository(repos,self.dbstate, self.uistate)

    def add(self,obj):
        EditRepository.EditRepository(RelLib.Repository(),self.dbstate, self.uistate)

    def remove(self,obj):
        db = self.dbstate.db
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)

        for repos_handle in mlist:

            source_list = [ src_handle for src_handle \
                            in db.get_source_handles() \
                            if db.get_source_from_handle(src_handle).has_repo_reference(repos_handle)]

            repository = db.get_repository_from_handle(repos_handle)

            ans = EditRepository.DelRepositoryQuery(repository,db,source_list)

            if len(source_list) > 0:
                msg = _('This repository is currently being used. Deleting it '
                        'will remove it from the database and from all '
                        'sources that reference it.')
            else:
                msg = _('Deleting repository will remove it from the database.')
            
            msg = "%s %s" % (msg,Utils.data_recover_msg)
            QuestionDialog(_('Delete %s?') % repository.get_name(), msg,
                           _('_Delete Repository'),ans.query_response)
            

    def edit(self,obj):
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)

        for handle in mlist:
            repos = self.dbstate.db.get_repository_from_handle(handle)
            EditRepository.EditRepository(repos, self.dbstate, self.uistate)

