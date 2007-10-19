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

#-------------------------------------------------------------------------
#
# Python classes
#
#-------------------------------------------------------------------------
from gettext import gettext as _
import cPickle as pickle

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import Spell
import Errors
import gen.lib
from DisplayTabs import log
from _NoteModel import NoteModel
from _EmbeddedList import EmbeddedList
from DdTargets import DdTargets

#-------------------------------------------------------------------------
#
# NoteTab
#
#-------------------------------------------------------------------------
class NoteTab(EmbeddedList):

    _HANDLE_COL = 2
    _DND_TYPE = DdTargets.NOTE_LINK

    _MSG = {
        'add'   : _('Create and add a new note'),
        'del'   : _('Remove the existing note'),
        'edit'  : _('Edit the selected note'),
        'share' : _('Add an existing note'),
        'up'    : _('Move the selected note upwards'),
        'down'  : _('Move the selected note downwards'),
    }

    _column_names = [
        (_('Type'), 0, 100), 
        (_('Preview'), 1, 200), 
    ]

    def __init__(self, dbstate, uistate, track, data, callertitle=None, 
                    notetype=None):
        self.data = data
        self.callertitle = callertitle
        self.notetype = notetype
        EmbeddedList.__init__(self, dbstate, uistate, track, 
                              _("Notes"), NoteModel, share=True, move=True)

    def get_editor(self):
        pass

    def get_user_values(self):
        return []

    def get_data(self):
        return self.data

    def column_order(self):
        return ((1, 0), (1, 1))

    def add_button_clicked(self, obj):
        note = gen.lib.Note()
        if self.notetype :
            note.set_type(self.notetype)
        try:
            from Editors import EditNote
            EditNote(self.dbstate, self.uistate, self.track, 
                            note, self.add_callback,
                            self.callertitle, extratype = [self.notetype])
        except Errors.WindowActiveError:
            pass

    def add_callback(self, name):
        self.get_data().append(name)
        self.changed = True
        self.rebuild()

    def edit_button_clicked(self, obj):
        handle = self.get_selected()
        if handle:
            note = self.dbstate.db.get_note_from_handle(handle)
            try:
                from Editors import EditNote
                EditNote(self.dbstate, self.uistate, self.track, note,
                        self.edit_callback, self.callertitle,
                        extratype = [self.notetype] )
            except Errors.WindowActiveError:
                pass
    
    def share_button_clicked(self, obj):
        from Selectors import selector_factory
        SelectNote = selector_factory('Note')

        sel = SelectNote(self.dbstate,self.uistate,self.track)
        note = sel.run()
        if note:
            self.add_callback(note.handle)
    
    def get_icon_name(self):
        return 'gramps-notes'

    def edit_callback(self, name):
        self.changed = True
        self.rebuild()
