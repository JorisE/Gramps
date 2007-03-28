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

# $Id: Bookmarks.py 8197 2007-02-20 20:56:48Z hippy $

"Handle bookmarks for the gramps interface"

__author__ = "Donald N. Allingham"
__version__ = "$Revision: 8197 $"

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import const
import os
import time
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".DbManager")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import QuestionDialog


DEFAULT_DIR   = os.path.expanduser("~/grampsdb")
DEFAULT_TITLE = _("Database")
NAME_FILE     = "name.txt"
META_NAME     = "meta_data.db"

NAME_COL  = 0
PATH_COL  = 1
FILE_COL  = 2
DATE_COL  = 3
OPEN_COL  = 5

class DbManager:
    
    def __init__(self, dbstate):
        
        self.glade = gtk.glade.XML(const.gladeFile, "dbmanager", "gramps")
        self.top = self.glade.get_widget('dbmanager')

        self.connect = self.glade.get_widget('ok')
        self.cancel  = self.glade.get_widget('cancel')
        self.new     = self.glade.get_widget('new')
        self.remove  = self.glade.get_widget('remove')
        self.dblist  = self.glade.get_widget('dblist')
        self.model   = None
        if dbstate:
            self.active  = dbstate.db.get_save_path()
        else:
            self.active = None

        self.selection = self.dblist.get_selection()

        self.current_names = []

        self.connect_signals()
        self.build_interface()
        self.populate()

    def connect_signals(self):
        self.remove.connect('clicked', self.remove_db)
        self.new.connect('clicked', self.new_db)
        self.selection.connect('changed', self.selection_changed)

    def selection_changed(self, selection):
        store, iter = selection.get_selected()
        if not iter or store.get_value(iter, OPEN_COL):
            self.remove.set_sensitive(False)
            self.connect.set_sensitive(False)
        else:
            self.remove.set_sensitive(True)
            self.connect.set_sensitive(True)

    def build_interface(self):
        render = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn('', render, stock_id=6)
        self.dblist.append_column(column)

        render = gtk.CellRendererText()
        render.set_property('editable',True)
        render.connect('edited', self.change_name)
        self.column = gtk.TreeViewColumn(_('Database name'), render, 
                                         text=NAME_COL)
        self.dblist.append_column(self.column)

        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Last modified'), render, text=DATE_COL)
        self.dblist.append_column(column)
        self.dblist.set_rules_hint(True)

    def populate(self):
        self.model = gtk.ListStore(str, str, str, str, int, bool, str)

	try:
	    if not os.path.isdir(DEFAULT_DIR):
		os.mkdir(DEFAULT_DIR)
	except:
	    print "did not make default dir"

        self.current_names = []
        for dpath in os.listdir(DEFAULT_DIR):
            dirpath = os.path.join(DEFAULT_DIR, dpath)
            path_name = os.path.join(dirpath, NAME_FILE)
            if os.path.isfile(path_name):
                name = file(path_name).readline().strip()

                meta = os.path.join(dirpath, META_NAME)
                if os.path.isfile(meta):
                    tval = os.stat(meta)[9]
                    last = time.asctime(time.localtime(tval))
                else:
                    tval = 0
                    last = _("Never")

                if dirpath == self.active:
                    enable = True
                    stock_id = gtk.STOCK_CONNECT
                else:
                    enable = False
                    stock_id = ""

                self.current_names.append((name, 
                                           os.path.join(DEFAULT_DIR, dpath),
                                           path_name,
                                           last,
                                           tval,
                                           enable,
                                           stock_id))

        self.current_names.sort()
        for items in self.current_names:
            data = [items[0], items[1], items[2], items[3], items[4], items[5], items[6]]
            self.model.append(data)
        self.dblist.set_model(self.model)

    def run(self):
        value = self.top.run()
        if value == gtk.RESPONSE_OK:
            (model, node) = self.selection.get_selected()
            if node:
                self.top.destroy()
                return (self.model.get_value(node, PATH_COL),
                        self.model.get_value(node, NAME_COL))
            else:
                self.top.destroy()
                return None
        else:
            self.top.destroy()
            return None

    def change_name(self, text, path, new_text):
        if len(new_text) > 0:
            iter = self.model.get_iter(path)
            filename = self.model.get_value(iter, FILE_COL)
            try:
                f = open(filename, "w")
                f.write(new_text)
                f.close()
                self.model.set_value(iter, NAME_COL, new_text)
            except:
                pass

    def remove_db(self, obj):
        store, iter = self.selection.get_selected()
        path = store.get_path(iter)
        row = store[path]
        if row[OPEN_COL]:
            return
        self.data_to_delete = (row[0], row[1], row[2])

        QuestionDialog.QuestionDialog(
            _("Remove the '%s' database?") % self.data_to_delete[0],
            _("Removing this database will permanently destroy "
              "the data."),
            _("Remove database"),
            self.really_delete_db)
        self.populate()

    def really_delete_db(self):
        for (top, dirs, files) in os.walk(self.data_to_delete[1]):
            for f in files:
                os.unlink(os.path.join(top,f))
        os.rmdir(top)

    def new_db(self, obj):
        while True:
            base = "%x" % int(time.time())
            new_path = os.path.join(DEFAULT_DIR, base)
            if not os.path.isdir(new_path):
                break

        os.mkdir(new_path)
        path_name = os.path.join(new_path, NAME_FILE)

        i = 1
        while True:
            title = "%s %d" % (DEFAULT_TITLE, i)
            if title not in self.current_names:
                break
            i += 1

        f = open(path_name, "w")
        f.write(title)
        f.close()

        self.current_names.append(title)
        node = self.model.append([title, new_path, path_name, _("Never"), 0, False, ''])
        self.selection.select_iter(node)

        path = self.model.get_path(node)
        self.dblist.set_cursor(path, focus_column=self.column, start_editing=True)
        
if __name__ == "__main__":
    a = DbManager()
    a.run()
