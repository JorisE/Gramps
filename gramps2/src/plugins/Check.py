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

"Database Processing/Check and repair database"

import RelLib
import Utils
from intl import gettext as _

import os
import cStringIO
import gtk
import gtk.glade
from QuestionDialog import OkDialog, MissingMediaDialog
import shutil

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def runTool(database,active_person,callback):

    try:
        checker = CheckIntegrity(database)
        checker.check_for_broken_family_links()
        checker.cleanup_missing_photos(0)
        checker.check_parent_relationships()
        checker.cleanup_empty_families(0)
        errs = checker.build_report(0)
        if errs:
            checker.report(0)
    except:
        import DisplayTrace
        DisplayTrace.DisplayTrace()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class CheckIntegrity:
    
    def __init__(self,db):
        self.db = db
        self.bad_photo = []
        self.replaced_photo = []
        self.removed_photo = []
        self.empty_family = []
        self.broken_links = []
        self.broken_parent_links = []
        self.fam_rel = []

    def check_for_broken_family_links(self):
        self.broken_links = []
        for key in self.db.getFamilyMap().keys():
            family = self.db.getFamily(key)
            father = family.getFather()
            mother = family.getMother()

            if father and family not in father.getFamilyList():
                Utils.modified()
                self.broken_parent_links.append((father,family))
                father.addFamily(family)
            if mother and family not in mother.getFamilyList():
                Utils.modified()
                self.broken_parent_links.append((mother,family))
                mother.addFamily(family)
            for child in family.getChildList():
                if family == child.getMainParents():
                    continue
                for family_type in child.getParentList():
                    if family_type[0] == family:
                        break
                else:
                    family.removeChild(child)
                    Utils.modified()
                    self.broken_links.append((child,family))

    def cleanup_missing_photos(self,cl=0):
        #-------------------------------------------------------------------------
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
            self.removed_photo.append(ObjectMap[ObjectId])
            self.db.removeObject(ObjectId) 
            Utils.modified()
    
        def leave_clicked():
            self.bad_photo.append(ObjectMap[ObjectId])


        def select_clicked():
            # File is lost => select a file to replace the lost one
            def fs_close_window(obj):
                fs_top.destroy()

            def fs_ok_clicked(obj):
                name = fs_top.get_filename()
                if os.path.isfile(name):
                    shutil.copy2(name,photo_name)
                    self.replaced_photo.append(ObjectMap[ObjectId])
                else:
                    self.bad_photo.append(ObjectMap[ObjectId])
                Utils.destroy_passed_object(fs_top)

            fs_top = gtk.FileSelection("%s - GRAMPS" % _("Select file"))
            fs_top.hide_fileop_buttons()
            fs_top.ok_button.connect('clicked',fs_ok_clicked)
            fs_top.cancel_button.connect('clicked',fs_close_window)
            fs_top.show()
            fs_top.run()

        #-------------------------------------------------------------------------
        ObjectMap = self.db.getObjectMap()
        for ObjectId in ObjectMap.keys():
            photo_name = ObjectMap[ObjectId].getPath()
            if not os.path.isfile(photo_name):
                if cl:
                    print "Warning: media file %s was not found." \
                        % os.path.basename(photo_name)
                    self.bad_photo.append(ObjectMap[ObjectId])
                else:
                    MissingMediaDialog(_("Media object could not be found"),
                        _("%(file_name)s is referenced in the database, but no longer exists. " 
                        "The file may have been deleted or moved to a different location. " 
                        "You may choose to either remove the reference from the database, " 
                        "keep the reference to the missing file, or select a new file." 
                        ) % { 'file_name' : photo_name },
                    remove_clicked, leave_clicked, select_clicked)

    def cleanup_empty_families(self,automatic):
        for key in self.db.getFamilyMap().keys():
            family = self.db.getFamily(key)
            if family.getFather() == None and family.getMother() == None:
                Utils.modified()
                self.empty_family.append(family)
                self.delete_empty_family(family)

    def delete_empty_family(self,family):
        for key in self.db.getPersonKeys():
            child = self.db.getPerson(key)
            child.removeAltFamily(family)
        self.db.deleteFamily(family)

    def check_parent_relationships(self):
        for key in self.db.getFamilyMap().keys():
            family = self.db.getFamily(key)
            father = family.getFather()
            mother = family.getMother()
            type = family.getRelationship()

            if father == None or mother == None:
                continue
            if type != "Partners":
                if father.getGender() == mother.getGender():
                    family.setRelationship("Partners")
                    self.fam_rel.append(family)
                elif father.getGender() != RelLib.Person.male or \
                     mother.getGender() != RelLib.Person.female:
                    family.setFather(mother)
                    family.setMother(father)
                    self.fam_rel.append(family)
            else:
                if father.getGender() != mother.getGender():
                    family.setRelationship("Unknown")
                    self.fam_rel.append(family)
                    if father.getGender() == RelLib.Person.female:
                        family.setFather(mother)
                        family.setMother(father)

    def build_report(self,cl=0):
        bad_photos = len(self.bad_photo)
        replaced_photos = len(self.replaced_photo)
        removed_photos = len(self.removed_photo)
        photos = bad_photos + replaced_photos + removed_photos
        efam = len(self.empty_family)
        blink = len(self.broken_links)
        plink = len(self.broken_parent_links)
        rel = len(self.fam_rel)

        errors = blink + efam + photos + rel
        
        if errors == 0:
            if cl:
                print "No errors were found: the database has passed internal checks."
            else:
                OkDialog(_("No errors were found"),
                         _('The database has passed internal checks'))
            return 0

        self.text = cStringIO.StringIO()
        if blink > 0:
            if blink == 1:
                self.text.write(_("1 broken child/family link was fixed\n"))
            else:
                self.text.write(_("%d broken child/family links were found\n") % blink)
            for c in self.broken_links:
                cn = c[0].getPrimaryName().getName()
                f = c[1].getFather()
                m = c[1].getMother()
                if f and m:
                    pn = _("%s and %s") % (f.getPrimaryName().getName(),\
                                           m.getPrimaryName().getName())
                elif f:
                    pn = f.getPrimaryName().getName()
                elif m:
                    pn = m.getPrimaryName().getName()
                else:
                    pn = _("unknown")
                self.text.write('\t')
                self.text.write(_("%s was removed from the family of %s\n") % (cn,pn))

        if plink > 0:
            if plink == 1:
                self.text.write(_("1 broken spouse/family link was fixed\n"))
            else:
                self.text.write(_("%d broken spouse/family links were found\n") % plink)
            for c in self.broken_parent_links:
                cn = c[0].getPrimaryName().getName()
                f = c[1].getFather()
                m = c[1].getMother()
                if f and m:
                    pn = _("%s and %s") % (f.getPrimaryName().getName(),\
                                           m.getPrimaryName().getName())
                elif f:
                    pn = f.getPrimaryName().getName()
                else:
                    pn = m.getPrimaryName().getName()
                    self.text.write('\t')
                    self.text.write(_("%s was restored to the family of %s\n") % (cn,pn))

        if efam == 1:
            self.text.write(_("1 empty family was found\n"))
        elif efam > 1:
            self.text.write(_("%d empty families were found\n") % efam)
        if rel == 1:
            self.text.write(_("1 corrupted family relationship fixed\n"))
        elif rel > 1:
            self.text.write(_("%d corrupted family relationship fixed\n") % rel)
        if photos == 1:
            self.text.write(_("1 media object was referenced, but not found\n"))
        elif photos > 1:
            self.text.write(_("%d media objects were referenced, but not found\n") % photos)
        if bad_photos == 1:
            self.text.write(_("Reference to 1 missing media object was kept\n"))
        elif bad_photos > 1:
            self.text.write(_("References to %d media objects were kept\n") % bad_photos)
        if replaced_photos == 1:
            self.text.write(_("1 missing media object was replaced\n"))
        elif replaced_photos > 1:
            self.text.write(_("%d missing media objects were replaced\n") % replaced_photos)
        if removed_photos == 1:
            self.text.write(_("1 missing media object was removed\n"))
        elif removed_photos > 1:
            self.text.write(_("%d missing media objects were removed\n") % removed_photos)

        return errors

    def report(self,cl=0):
	if cl:
            print self.text.getvalue()
	else:
            base = os.path.dirname(__file__)
            glade_file = base + os.sep + "summary.glade"
            topDialog = gtk.glade.XML(glade_file,"summary")
            topDialog.signal_autoconnect({
                "destroy_passed_object" : Utils.destroy_passed_object,
                })
            title = _("Check Integrity")
            top = topDialog.get_widget("summary")
            textwindow = topDialog.get_widget("textwindow")

            Utils.set_titles(top,topDialog.get_widget("title"),title)
	    textwindow.get_buffer().set_text(self.text.getvalue())
            self.text.close()
            top.show()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
from Plugins import register_tool

register_tool(
    runTool,
    _("Check and repair database"),
    category=_("Database Processing"),
    description=_("Checks the database for integrity problems, fixing the problems that it can")
    )
    
