#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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

"Export to GRAMPS package"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import time
import os
from cStringIO import StringIO

#-------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import WriteXML
import TarFile
import Utils
from QuestionDialog import MissingMediaDialog

from intl import gettext as _

#-------------------------------------------------------------------------
#
# writeData
#
#-------------------------------------------------------------------------
def writeData(database,person):
    try:
        PackageWriter(database)
    except:
        import DisplayTrace
        DisplayTrace.DisplayTrace()
    
#-------------------------------------------------------------------------
#
# PackageWriter
#
#-------------------------------------------------------------------------
class PackageWriter:

    def __init__(self,database):
        self.db = database
        
        base = os.path.dirname(__file__)
        glade_file = "%s/%s" % (base,"pkgexport.glade")
        
        
        dic = {
            "destroy_passed_object" : Utils.destroy_passed_object,
            "on_ok_clicked" : self.on_ok_clicked
            }
        
        self.top = gtk.glade.XML(glade_file,"packageExport")

        Utils.set_titles(self.top.get_widget('packageExport'),
                         self.top.get_widget('title'),
                         _('Package export'))
        
        self.top.signal_autoconnect(dic)
        self.top.get_widget("packageExport").show()

    def on_ok_clicked(self,obj):
        name = self.top.get_widget("filename").get_text()
        Utils.destroy_passed_object(obj)
        self.export(name)

    def export(self, filename):
        #--------------------------------------------------------------
        def remove_clicked():
            # File is lost => remove all references and the object itself
            mobj = ObjectMap[ObjectId]
            for p in self.db.getFamilyMap().values():
                nl = p.getPhotoList()
                for o in nl:
                    if o.getReference() == mobj:
                        nl.remove(o) 
                p.setPhotoList(nl)
            for key in self.db.getPersonKeys():
                p = self.db.getPerson(key)
                nl = p.getPhotoList()
                for o in nl:
                    if o.getReference() == mobj:
                        nl.remove(o) 
                p.setPhotoList(nl)
            for key in self.db.getSourceKeys():
                p = self.db.getSource(key)
                nl = p.getPhotoList()
                for o in nl:
                    if o.getReference() == mobj:
                        nl.remove(o) 
                p.setPhotoList(nl)
            for key in self.db.getPlaceKeys():
                p = self.db.getPlace(key)
                nl = p.getPhotoList()
                for o in nl:
                    if o.getReference() == mobj:
                        nl.remove(o) 
                p.setPhotoList(nl)
            self.db.removeObject(ObjectId)
            Utils.modified() 

        def leave_clicked():
            # File is lost => do nothing, leave as is
            pass


        def select_clicked():
            # File is lost => select a file to replace the lost one
            def fs_close_window(obj):
                pass

            def fs_ok_clicked(obj):
                name = fs_top.get_filename()
                if os.path.isfile(name):
                    g = open(name,"rb")
                    t.add_file(base,mtime,g)
                    g.close()

            fs_top = gtk.FileSelection("%s - GRAMPS" % _("Select file"))
            fs_top.hide_fileop_buttons()
            fs_top.ok_button.connect('clicked',fs_ok_clicked)
            fs_top.cancel_button.connect('clicked',fs_close_window)
            fs_top.run()
            fs_top.destroy()
        #---------------------------------------------------------------

        t = TarFile.TarFile(filename)
        mtime = time.time()
        
        # Write media files first, since the database may be modified 
        # during the process (i.e. when removing object)
        ObjectMap = self.db.getObjectMap()
        for ObjectId in ObjectMap.keys():
            oldfile = ObjectMap[ObjectId].getPath()
            base = os.path.basename(oldfile)
            if os.path.isfile(oldfile):
                g = open(oldfile,"rb")
                t.add_file(base,mtime,g)
                g.close()
            else:
                # File is lost => ask what to do
                MissingMediaDialog(_("Media object could not be found"),
	            _("%(file_name)s is referenced in the database, but no longer exists. " 
                        "The file may have been deleted or moved to a different location. " 
                        "You may choose to either remove the reference from the database, " 
                        "keep the reference to the missing file, or select a new file." 
                        ) % { 'file_name' : oldfile },
                    remove_clicked, leave_clicked, select_clicked)
        
        # Write XML now
        g = StringIO()
        gfile = WriteXML.XmlWriter(self.db,None,1)
        gfile.write_handle(g)
        mtime = time.time()
        t.add_file("data.gramps",mtime,g)
        g.close()

        t.close()
    
#-------------------------------------------------------------------------
#
# Register the plugin
#
#-------------------------------------------------------------------------
from Plugins import register_export

register_export(writeData,_("Export to GRAMPS package"))
