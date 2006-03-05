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
import DisplayModels
import const
import Utils
import Errors
from Editors import EditPlace, DeletePlaceQuery
from QuestionDialog import QuestionDialog, ErrorDialog

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gettext import gettext as _

column_names = [
    _('Place Name'),
    _('ID'),
    _('Church Parish'),
    _('ZIP/Postal Code'),
    _('City'),
    _('County'),
    _('State'),
    _('Country'),
    _('Longitude'),
    _('Latitude'),
    _('Last Changed'),
    ]

#-------------------------------------------------------------------------
#
# PlaceView
#
#-------------------------------------------------------------------------
class PlaceView(PageView.ListView):
    def __init__(self,dbstate,uistate):

        signal_map = {
            'place-add'     : self.row_add,
            'place-update'  : self.row_update,
            'place-delete'  : self.row_delete,
            'place-rebuild' : self.build_tree,
            }

        PageView.ListView.__init__(self,'Place View',dbstate,uistate,
                                   column_names,len(column_names),
                                   DisplayModels.PlaceModel,
                                   signal_map)

    def define_actions(self):
        PageView.ListView.define_actions(self)
        self.add_action('ColumnEdit', gtk.STOCK_PROPERTIES,
                        '_Column Editor', callback=self.column_editor),

    def column_editor(self,obj):
        import ColumnOrder

        ColumnOrder.ColumnOrder(self.dbstate.db.get_place_column_order(),
                                column_names, self.set_column_order)

    def set_column_order(self,list):
        self.dbstate.db.set_place_column_order(list)
        self.build_columns()

    def column_order(self):
        return self.dbstate.db.get_place_column_order()

    def get_stock(self):
        return 'gramps-place'

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
              <menuitem action="ColumnEdit"/>
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
        place = self.dbstate.db.get_place_from_handle(handle)
        try:
            EditPlace(self.dbstate,self.uistate,[],place)
        except Errors.WindowActiveError:
            pass

    def add(self,obj):
        try:
            EditPlace(self.dbstate,self.uistate,[],RelLib.Place())
        except Errors.WindowActiveError:
            pass

    def remove(self,obj):
        for event_handle in self.selected_handles():
            db = self.dbstate.db
            person_list = [ handle for handle in
                            db.get_person_handles(False)
                            if db.get_person_from_handle(handle).has_handle_reference('Place',event_handle) ]
            family_list = [ handle for handle in
                            db.get_family_handles()
                            if db.get_family_from_handle(handle).has_handle_reference('Place',event_handle) ]
            
            event = db.get_event_from_handle(event_handle)

            ans = DeletePlaceQuery(event,db,
                                   person_list,family_list)

            if len(person_list) + len(family_list) > 0:
                msg = _('This place is currently being used. Deleting it '
                        'will remove it from the database and from all '
                        'people and families that reference it.')
            else:
                msg = _('Deleting place will remove it from the database.')
            
            msg = "%s %s" % (msg,Utils.data_recover_msg)
            descr = event.get_description()
            if descr == "":
                descr = event.get_gramps_id()
                
            QuestionDialog(_('Delete %s?') % descr, msg,
                           _('_Delete Place'),ans.query_response)

    def edit(self,obj):
        mlist = []
        self.selection.selected_foreach(self.blist,mlist)

        for handle in mlist:
            place = self.dbstate.db.get_place_from_handle(handle)
            try:
                EditPlace(self.dbstate,self.uistate,[],place)
            except Errors.WindowActiveError:
                pass

