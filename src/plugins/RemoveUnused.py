#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

# $Id: Check.py 7321 2006-09-13 02:57:45Z dallingham $

"Database Processing/Check and repair database"

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import os
import cStringIO
import sets
from gettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".RemoveUnused")

#-------------------------------------------------------------------------
#
# gtk modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import RelLib
import Utils
import const
import ManagedWindow

from PluginUtils import Tool, register_tool
from QuestionDialog import OkDialog, MissingMediaDialog

#-------------------------------------------------------------------------
#
# runTool
#
#-------------------------------------------------------------------------
class RemoveUnused:
    def __init__(self, dbstate, uistate, options_class, name, callback=None):

        self.db = dbstate.db
        self.dbstate = dbstate
        self.uistate = uistate

        if self.db.readonly:
            return
        self.init_gui()

    def init_gui(self):
        a = gtk.Dialog("%s - GRAMPS" % _('Remove unused objects'),
                       flags=gtk.DIALOG_MODAL,
                       buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        a.set_size_request(400, 200)
        a.set_border_width(12)
        a.set_has_separator(False)

        self.event  = gtk.CheckButton(_('Remove unused events'))
        self.source = gtk.CheckButton(_('Remove unused sources'))
        self.place  = gtk.CheckButton(_('Remove unused places'))

        self.event.set_active(True)
        self.source.set_active(True)
        self.place.set_active(True)

        label = gtk.Label('<span size="larger" weight="bold">%s</span>' % _('Remove unused objects'))
        label.set_use_markup(True)

        a.vbox.add(label)
        a.vbox.add(self.event)
        a.vbox.add(self.source)
        a.vbox.add(self.place)
        a.vbox.show_all()
        result = a.run()
        a.destroy()

        if result == gtk.RESPONSE_ACCEPT:
            self.run_tool(self.event.get_active(), 
                          self.source.get_active(),
                          self.place.get_active())

    def run_tool(self, clean_events, clean_sources, clean_places):
        trans = self.db.transaction_begin("",batch=False)
        self.db.disable_signals()
        checker = CheckIntegrity(self.dbstate, self.uistate, trans)
        if clean_events:
            checker.cleanup_events()
        if clean_sources:
            checker.cleanup_sources()
        if clean_places:
            checker.cleanup_places()

        self.db.transaction_commit(trans, _("Remove unused objects"))
        self.db.enable_signals()
        self.db.request_rebuild()

        errs = checker.build_report()
        if errs:
            Report(self.uistate, checker.text.getvalue())

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class CheckIntegrity:
    
    def __init__(self, dbstate, uistate, trans):
        self.db = dbstate.db
	self.uistate = uistate
        self.trans = trans
	self.place_cnt = 0
	self.source_cnt = 0
	self.event_cnt = 0
        self.progress = Utils.ProgressMeter(_('Checking database'),'')

    def _cleanup_map(self, title, no_events, db_map, remove_func):
        self.progress.set_pass(title, no_events)

        cnt = 0
        for handle in db_map.keys():
            hlist = [ x for x in self.db.find_backlink_handles(handle)]
            if len(hlist) == 0:
                remove_func(handle, self.trans)
                cnt += 1
        return cnt

    def cleanup_events(self):
        self.event_cnt = self._cleanup_map(
            _('Removing unused events'), 
            self.db.get_number_of_events(),
            self.db.event_map, 
            self.db.remove_event)

    def cleanup_sources(self):
        self.source_cnt = self._cleanup_map(
            _('Removing unused sources'), 
            self.db.get_number_of_sources(),
            self.db.source_map, 
            self.db.remove_source)

    def cleanup_places(self):
        self.place_cnt = self._cleanup_map(
            _('Removing unused places'),
            self.db.get_number_of_places(),
            self.db.place_map,
            self.db.remove_place)

    def build_report(self):
        self.progress.close()

        errors = self.event_cnt + self.source_cnt + self.place_cnt
        
        if errors == 0:
            OkDialog(_("No unreferenced objects were found."),
                     _('The database has passed internal checks'))
            return 0

        self.text = cStringIO.StringIO()

        if self.event_cnt == 1:
            self.text.write(_("1 non-referenced event removed\n"))
        elif self.event_cnt > 1:
            self.text.write(_("%d non-referenced events removed\n") % self.event_cnt)

        if self.source_cnt == 1:
            self.text.write(_("1 non-referenced source removed\n"))
        elif self.source_cnt > 1:
            self.text.write(_("%d non-referenced sources removed\n") % self.source_cnt)

        if self.place_cnt == 1:
            self.text.write(_("1 non-referenced place removed\n"))
        elif self.place_cnt > 1:
            self.text.write(_("%d non-referenced places removed\n") % self.place_cnt)

        return errors

#-------------------------------------------------------------------------
#
# Display the results
#
#-------------------------------------------------------------------------
class Report(ManagedWindow.ManagedWindow):
    
    def __init__(self, uistate, text, cl=0):
        if cl:
            print text
            return

        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self)
        
        base = os.path.dirname(__file__)
        glade_file = base + os.sep + "summary.glade"
        topDialog = gtk.glade.XML(glade_file,"summary","gramps")
        topDialog.get_widget("close").connect('clicked',self.close)

        window = topDialog.get_widget("summary")
        textwindow = topDialog.get_widget("textwindow")
        textwindow.get_buffer().set_text(text)

        self.set_window(window,
                        topDialog.get_widget("title"),
                        _("Integrity Check Results"))

        self.show()

    def build_menu_names(self, obj):
        return (_('Remove unused objects'), None)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class CheckOptions(Tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self,name,person_id=None):
        Tool.ToolOptions.__init__(self,name,person_id)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
register_tool(
    name = 'remove_unused',
    category = Tool.TOOL_DBFIX,
    tool_class = RemoveUnused,
    options_class = CheckOptions,
    modes = Tool.MODE_GUI,
    translated_name = _("Remove unused objects"),
    status = _("Stable"),
    author_name = "Donald N. Allingham",
    author_email = "don@gramps-project.org",
    description=_("Removes unused objects from the database")
    )
