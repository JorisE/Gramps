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

"""
The AttrEdit module provides the AttributeEditor class. This provides a
mechanism for the user to edit attribute information.
"""

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk.glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Utils
import RelLib
import GrampsDisplay
import EditSecondary

from QuestionDialog import WarningDialog
from DisplayTabs import *
from GrampsWidgets import *

#-------------------------------------------------------------------------
#
# AttributeEditor class
#
#-------------------------------------------------------------------------
class AttributeEditor(EditSecondary.EditSecondary):
    """
    Displays a dialog that allows the user to edit an attribute.
    """
    def __init__(self, state, uistate, track, attrib, title, data_list, callback):
        """
        Displays the dialog box.

        parent - The class that called the Address editor.
        attrib - The attribute that is to be edited
        title - The title of the dialog box
        list - list of options for the pop down menu
        """
        self.alist = data_list
        EditSecondary.EditSecondary.__init__(self, state, uistate, track,
                                             attrib, callback)
        
    def _local_init(self):
        self.top = gtk.glade.XML(const.gladeFile, "attr_edit","gramps")
        self.define_top_level(self.top.get_widget("attr_edit"),
                              self.top.get_widget('title'),
                              _('Attribute Editor'))

    def _connect_signals(self):
        self.define_cancel_button(self.top.get_widget('cancel'))
        self.define_help_button(self.top.get_widget('help'),'adv-at')
        self.define_ok_button(self.top.get_widget('ok'),self.save)

    def _setup_fields(self):
        self.value_field = MonitoredEntry(
            self.top.get_widget("attr_value"),
            self.obj.set_value, self.obj.get_value,
            self.db.readonly)
        
        self.priv = PrivacyButton(
            self.top.get_widget("private"),
            self.obj)

        self.type_selector = MonitoredType(
            self.top.get_widget("attr_menu"),
            self.obj.set_type, self.obj.get_type,
            dict(Utils.personal_attributes),
            RelLib.Attribute.CUSTOM)

    def _create_tabbed_pages(self):
        notebook = gtk.Notebook()
        self.srcref_list = self._add_tab(
            notebook,
            SourceEmbedList(self.dbstate,self.uistate, self.track,
                            self.obj.source_list))
        
        self.note_tab = self._add_tab(
            notebook,
            NoteTab(self.dbstate, self.uistate, self.track,
                    self.obj.get_note_object()))
        
        notebook.show_all()
        vbox = self.top.get_widget('vbox').pack_start(notebook,True)

    def build_menu_names(self, attrib):
        if not attrib:
            label = _("New Attribute")
        else:
            label = attrib.get_type()[1]
        if not label.strip():
            label = _("New Attribute")
        label = "%s: %s" % (_('Attribute'),label)
        return (label, _('Attribute Editor'))

    def save(self,*obj):
        """
        Called when the OK button is pressed. Gets data from the
        form and updates the Attribute data structure.
        """

        attr_data = self.obj.get_type()
        if (attr_data[0] == RelLib.Attribute.CUSTOM and
            not attr_data[1] in self.alist):
            WarningDialog(
                _('New attribute type created'),
                _('The "%s" attribute type has been added to this database.\n'
                  'It will now appear in the attribute menus for this database') % attr_data[1])
            self.alist.append(attr_data[1])
            self.alist.sort()

        if self.callback:
            self.callback(self.obj)
        self.close_window(obj)

