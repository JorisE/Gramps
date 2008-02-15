#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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

from gettext import gettext as _
import gtk 

import ManagedWindow
import DateHandler
from BasicUtils import name_displayer
import Config
import GrampsDisplay
from QuestionDialog import SaveDialog

class EditPrimary(ManagedWindow.ManagedWindow):

    QR_CATEGORY = -1
    
    def __init__(self, state, uistate, track, obj, get_from_handle, 
                 get_from_gramps_id, callback=None):
        """Creates an edit window.  Associates a person with the window."""

        self.dp  = DateHandler.parser
        self.dd  = DateHandler.displayer
        self.name_displayer  = name_displayer
        self.obj = obj
        self.dbstate = state
        self.uistate = uistate
        self.db = state.db
        self.callback = callback
        self.signal_keys = []
        self.ok_button = None
        self.get_from_handle = get_from_handle
        self.get_from_gramps_id = get_from_gramps_id
        self.contexteventbox = None

        ManagedWindow.ManagedWindow.__init__(self, uistate, track, obj)

        self._local_init()

        self._create_tabbed_pages()
        self._setup_fields()
        self._connect_signals()
        self.show()
        self._post_init()

    def _local_init(self):
        """
        Derived class should do any pre-window initalization in this task.
        """
        pass

    def _post_init(self):
        """
        Derived class should do any post-window initalization in this task.
        """
        pass

    def _add_db_signal(self, name, callback):
        self.signal_keys.append(self.db.connect(name, callback))
        
    def _connect_signals(self):
        pass

    def _setup_fields(self):
        pass

    def _create_tabbed_pages(self):
        pass

    def build_window_key(self, obj):
        if obj and obj.get_handle():
            return obj.get_handle()
        else:
            return id(self)

    def _setup_notebook_tabs(self, notebook):
        for child in notebook.get_children():
            label = notebook.get_tab_label(child)
            page_no = notebook.page_num(child)
            label.drag_dest_set(0, [], 0)
            label.connect('drag_motion',
                          self._switch_page_on_dnd,
                          notebook,
                          page_no)
            child.set_parent_notebook(notebook)

    def _switch_page_on_dnd(self, widget, context, x, y, time, notebook, 
                            page_no):
        if notebook.get_current_page() != page_no:
            notebook.set_current_page(page_no)

    def _add_tab(self, notebook, page):
        notebook.insert_page(page, page.get_tab_widget())
        page.add_db_signal_callback(self._add_db_signal)
        return page

    def _cleanup_on_exit(self):
        pass

    def object_is_empty(self):
        return cmp(self.obj.serialize()[1:],
                   self.empty_object().serialize()[1:]) == 0

    def define_ok_button(self, button, function):
        self.ok_button = button
        button.connect('clicked', function)
        button.set_sensitive(not self.db.readonly)

    def define_cancel_button(self, button):
        button.connect('clicked', self.close)

    def define_help_button(self, button, tag, webpage='', section=''):
        button.connect('clicked', lambda x: GrampsDisplay.help(tag, webpage, 
                                                               section))

    def _do_close(self, *obj):
        for key in self.signal_keys:
            self.db.disconnect(key)
        self._cleanup_on_exit()
        ManagedWindow.ManagedWindow.close(self)

    def close(self, *obj):
        """If the data has changed, give the user a chance to cancel
        the close window"""
        if not Config.get(Config.DONT_ASK) and self.data_has_changed():
            SaveDialog(
                _('Save Changes?'),
                _('If you close without saving, the changes you '
                  'have made will be lost'),
                self._do_close,
                self.save)
            return True
        else:
            self._do_close()
            return False

    def empty_object(self):
        return None

    def data_has_changed(self):

        if self.db.readonly:
            return False
        elif self.obj.handle:
            orig = self.get_from_handle(self.obj.handle)
            if orig:
                cmp_obj = orig
            else:
                cmp_obj = self.empty_object()
            return cmp(cmp_obj.serialize()[1:],
                       self.obj.serialize()[1:]) != 0
        else:
            cmp_obj = self.empty_object()
            return cmp(cmp_obj.serialize()[1:],
                       self.obj.serialize()[1:]) != 0

    def save(self, *obj):
        pass
        
    def set_contexteventbox(self, eventbox):
        '''Set the contextbox that grabs button presses if not grabbed
            by overlying widgets.
        '''
        self.contexteventbox = eventbox
        self.contexteventbox.connect('button-press-event',
                                self._contextmenu_button_press)
                                
    def _contextmenu_button_press(self, obj, event) :
        """
        Button press event that is caught when a mousebutton has been
        pressed while on contexteventbox
        It opens a context menu with possible actions
        """
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3 :
            if self.obj.get_handle() == 0 :
                return False
            
            #build the possible popup menu
            self._build_popup_ui()
            #set or unset sensitivity in popup
            self._post_build_popup_ui()
                
            menu = self.popupmanager.get_widget('/Popup')
            if menu:
                menu.popup(None, None, None, event.button, event.time)
                return True
        return False

    def _build_popup_ui(self):
        """
        Create actions and ui of context menu
        """
        from QuickReports import create_quickreport_menu
        
        self.popupmanager = gtk.UIManager()
        #add custom actions
        (ui_top, action_groups) = self._top_contextmenu()
        for action in action_groups :
            self.popupmanager.insert_action_group(action, -1)
        #see which quick reports are available now:
        ui_qr = ''
        if self.QR_CATEGORY > -1 :
            (ui_qr, reportactions) = create_quickreport_menu(self.QR_CATEGORY,
                                    self.dbstate, self.uistate, 
                                    self.obj.get_handle())
            self.report_action = gtk.ActionGroup("/PersonReport")
            self.report_action.add_actions(reportactions)
            self.report_action.set_visible(True)
            self.popupmanager.insert_action_group(self.report_action, -1)
        
        popupui = '''
        <ui>
          <popup name="Popup">''' + ui_top + '''
            <separator/>''' + ui_qr + '''
          </popup>
        </ui>'''
        
        self.popupmanager.add_ui_from_string(popupui)
        
    def _top_contextmenu(self):
        """
        Derived class can create a ui with menuitems and corresponding list of 
        actiongroups
        """
        return "", []
        
    def _post_build_popup_ui(self):
        """
        Derived class should do extra actions here on the menu
        """
        pass

    def _uses_duplicate_id(self):
        """
        Fix problem for now
        """
        return (False, 0)

