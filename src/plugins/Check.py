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

"Database Processing/Check and repair database"

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import os
import cStringIO
from gettext import gettext as _

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
from QuestionDialog import OkDialog, MissingMediaDialog

#-------------------------------------------------------------------------
#
# runTool
#
#-------------------------------------------------------------------------
def runTool(database,active_person,callback,parent=None):

    try:
        trans = database.transaction_begin()
        checker = CheckIntegrity(database,parent,trans)
        checker.check_for_broken_family_links()
        checker.cleanup_missing_photos(0)
        checker.check_parent_relationships()
        checker.cleanup_empty_families(0)
        database.transaction_commit(trans, _("Check Integrity"))

        errs = checker.build_report(0)
        if errs:
            Report(checker.text.getvalue(),parent)
    except:
        import DisplayTrace
        DisplayTrace.DisplayTrace()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class CheckIntegrity:
    
    def __init__(self,db,parent,trans):
        self.db = db
        self.trans = trans
        self.parent = parent
        self.bad_photo = []
        self.replaced_photo = []
        self.removed_photo = []
        self.empty_family = []
        self.broken_links = []
        self.broken_parent_links = []
        self.fam_rel = []

    def check_for_broken_family_links(self):
        self.broken_links = []
        for family_handle in self.db.get_family_handles():
            family = self.db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            if father_handle:
                father = self.db.get_person_from_handle(father_handle)
                if not father:
                    family.set_father_handle(None)
                    self.db.commit_family(family,self.trans)
                    self.broken_parent_links.append((father_handle,family_handle))
                    father_handle = None
            if mother_handle:
                mother = self.db.get_person_from_handle(mother_handle)
                if not mother:
                    family.set_father_handle(None)
                    self.db.commit_family(family,self.trans)
                    self.broken_parent_links.append((mother_handle,family_handle))
                    mother_handle = None

            if father_handle and father and family_handle not in father.get_family_handle_list():
                self.broken_parent_links.append((father_handle,family_handle))
                father.add_family_handle(family_handle)
                self.db.commit_person(father,self.trans)
            if mother_handle and mother and family_handle not in mother.get_family_handle_list():
                self.broken_parent_links.append((mother_handle,family_handle))
                mother.add_family_handle(family_handle)
                self.db.commit_person(mother,self.trans)
            for child_handle in family.get_child_handle_list():
                child = self.db.get_person_from_handle(child_handle)
                if child:
                    if family_handle == child.get_main_parents_family_handle():
                       continue
                    for family_type in child.get_parent_family_handle_list():
                        if family_type[0] == family_handle:
                            break
                    else:
                        family.remove_child_handle(child_handle)
                        self.db.commit_family(family,self.trans)
                        self.broken_links.append((child_handle,family_handle))
                else:
                    family.remove_child_handle(child_handle)
                    self.db.commit_family(family,self.trans)
                    self.broken_links.append((child_handle,family_handle))
                    

    def cleanup_missing_photos(self,cl=0):
        missmedia_action = 0
        #-------------------------------------------------------------------------
        def remove_clicked():
            # File is lost => remove all references and the object itself
            
            for handle in self.db.get_person_handles(sort_handles=False):
                person = self.db.get_person_from_handle(handle)
                if person.has_media_reference(ObjectId):
                    person.remove_media_references([ObjectId])
                    self.db.commit_person(person,self.trans)

            for handle in self.db.get_family_handles():
                family = self.db.get_family_from_handle(handle)
                if family.has_media_reference(ObjectId):
                    family.remove_media_references([ObjectId])
                    self.db.commit_family(family,self.trans)
                    
            for handle in self.db.get_event_handles():
                event = self.db.get_event_from_handle(handle)
                if event.has_media_reference(ObjectId):
                    event.remove_media_references([ObjectId])
                    self.db.commit_event(event,self.trans)
                
            for handle in self.db.get_source_handles():
                source = self.db.get_source_from_handle(handle)
                if source.has_media_reference(ObjectId):
                    source.remove_media_references([ObjectId])
                    self.db.commit_source(source,self.trans)
                
            for handle in self.db.get_place_handles():
                place = self.db.get_place_from_handle(handle)
                if place.has_media_reference(ObjectId):
                    place.remove_media_references([ObjectId])
                    self.db.commit_place(p,self.trans)

            self.removed_photo.append(ObjectId)
            self.db.remove_object(ObjectId,self.trans) 
    
        def leave_clicked():
            self.bad_photo.append(ObjectId)

        def select_clicked():
            # File is lost => select a file to replace the lost one
            def fs_close_window(obj):
                self.bad_photo.append(ObjectId)

            def fs_ok_clicked(obj):
                name = fs_top.get_filename()
                if os.path.isfile(name):
                    obj = self.db.get_object_from_handle(ObjectId)
                    obj.set_path(name)
                    self.db.commit_media_object(obj,self.trans)
                    self.replaced_photo.append(ObjectId)
                else:
                    self.bad_photo.append(ObjectId)

            fs_top = gtk.FileSelection("%s - GRAMPS" % _("Select file"))
            fs_top.hide_fileop_buttons()
            fs_top.ok_button.connect('clicked',fs_ok_clicked)
            fs_top.cancel_button.connect('clicked',fs_close_window)
            fs_top.run()
            fs_top.destroy()

        #-------------------------------------------------------------------------
        
        for ObjectId in self.db.get_media_object_handles():
            obj = self.db.get_object_from_handle(ObjectId)
            photo_name = obj.get_path()
            if not os.path.isfile(photo_name):
                if cl:
                    print "Warning: media file %s was not found." \
                        % os.path.basename(photo_name)
                    self.bad_photo.append(ObjectId)
                else:
                    if missmedia_action == 0:
                        mmd = MissingMediaDialog(_("Media object could not be found"),
                        _("The file:\n %(file_name)s \nis referenced in the database, but no longer exists. " 
                        "The file may have been deleted or moved to a different location. " 
                        "You may choose to either remove the reference from the database, " 
                        "keep the reference to the missing file, or select a new file." 
                        ) % { 'file_name' : '<b>%s</b>' % photo_name },
                            remove_clicked, leave_clicked, select_clicked)
                        missmedia_action = mmd.default_action
                    elif missmedia_action == 1:
                        remove_clicked()
                    elif missmedia_action == 2:
                        leave_clicked()
                    elif missmedia_action == 3:
                        select_clicked()

    def cleanup_empty_families(self,automatic):
        for family_handle in self.db.get_family_handles():
            family = self.db.get_family_from_handle(family_handle)
            if not family.get_father_handle() and not family.get_mother_handle():
                self.empty_family.append(family_handle)
                self.delete_empty_family(family_handle)

    def delete_empty_family(self,family_handle):
        for key in self.db.get_person_handles(sort_handles=False):
            child = self.db.get_person_from_handle(key)
            child.remove_parent_family_handle(family_handle)
            child.remove_family_handle(family_handle)
        self.db.remove_family(family_handle,self.trans)

    def check_parent_relationships(self):
        for family_handle in self.db.get_family_handles():
            family = self.db.get_family_from_handle(family_handle)
            mother_handle = family.get_mother_handle()
            father_handle = family.get_father_handle()
            father = None
            if father_handle:
                father = self.db.get_person_from_handle(father_handle)
            mother = None
            if mother_handle:
                mother = self.db.get_person_from_handle(mother_handle)
            rel_type = family.get_relationship()

            if not father_handle and not mother_handle:
                continue
            elif not father_handle:
                if mother and mother.get_gender() == RelLib.Person.MALE:
                    family.set_father_handle(mother_handle)
                    family.set_mother_handle(None)
                    self.db.commit_family(family,self.trans)
            elif not mother_handle:
                if father and father.get_gender() == RelLib.Person.FEMALE:
                    family.set_mother_handle(father_handle)
                    family.set_father_handle(None)
                    self.db.commit_family(family,self.trans)
            else:
                fgender = father.get_gender()
                mgender = mother.get_gender()
                if rel_type != RelLib.Family.CIVIL_UNION:
                    if fgender == mgender and fgender != RelLib.Person.UNKNOWN:
                        family.set_relationship(RelLib.Family.CIVIL_UNION)
                        self.fam_rel.append(family_handle)
                        self.db.commit_family(family,self.trans)
                    elif fgender == RelLib.Person.FEMALE or mgender == RelLib.Person.MALE:
                        family.set_father_handle(mother_handle)
                        family.set_mother_handle(father_handle)
                        self.fam_rel.append(family_handle)
                        self.db.commit_family(family,self.trans)
                elif fgender != mgender:
                    family.set_relationship(RelLib.Family.UNKNOWN)
                    self.fam_rel.append(family_handle)
                    if fgender == RelLib.Person.FEMALE or mgender == RelLib.Person.MALE:
                        family.set_father_handle(mother_handle)
                        family.set_mother_handle(father_handle)
                    self.db.commit_family(family,self.trans)

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
                         _('The database has passed internal checks'),
                         self.parent.topWindow)
            return 0

        self.text = cStringIO.StringIO()
        if blink > 0:
            if blink == 1:
                self.text.write(_("1 broken child/family link was fixed\n"))
            else:
                self.text.write(_("%d broken child/family links were found\n") % blink)
            for (person_handle,family_handle) in self.broken_links:
                person = self.db.get_person_from_handle(person_handle)
                family = self.db.get_family_from_handle(family_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing child")
                f = self.db.get_person_from_handle(family.get_father_handle())
                m = self.db.get_person_from_handle(family.get_mother_handle())
                if f and m:
                    pn = _("%s and %s") % (f.get_primary_name().get_name(),\
                                           m.get_primary_name().get_name())
                elif f:
                    pn = f.get_primary_name().get_name()
                elif m:
                    pn = m.get_primary_name().get_name()
                else:
                    pn = _("unknown")
                self.text.write('\t')
                self.text.write(_("%s was removed from the family of %s\n") % (cn,pn))

        if plink > 0:
            if plink == 1:
                self.text.write(_("1 broken spouse/family link was fixed\n"))
            else:
                self.text.write(_("%d broken spouse/family links were found\n") % plink)
            for (person_handle,family_handle) in self.broken_parent_links:
                person = self.db.get_person_from_handle(person_handle)
                family = self.db.get_family_from_handle(family_handle)
                if person:
                    cn = person.get_primary_name().get_name()
                else:
                    cn = _("Non existing person")
                f = self.db.get_person_from_handle(family.get_father_handle())
                m = self.db.get_person_from_handle(family.get_mother_handle())
                if f and m:
                    pn = _("%s and %s") % (f.get_primary_name().get_name(),\
                                           m.get_primary_name().get_name())
                elif f:
                    pn = f.get_primary_name().get_name()
                elif m:
                    pn = m.get_primary_name().get_name()
                else:
                    pn = "Non existing person"
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

#-------------------------------------------------------------------------
#
# Display the results
#
#-------------------------------------------------------------------------
class Report:
    def __init__(self,text,parent,cl=0):
        if cl:
            print text
            return
        self.text = text
        self.parent = parent

        self.win_key = self

        base = os.path.dirname(__file__)
        glade_file = base + os.sep + "summary.glade"
        topDialog = gtk.glade.XML(glade_file,"summary","gramps")
        topDialog.signal_autoconnect({
            "destroy_passed_object"  : self.close_result,
            "on_result_delete_event" : self.on_result_delete_event,
        })
        
        self.title = _("Integrity Check Results")
        self.window = topDialog.get_widget("summary")
        self.window.set_icon(self.parent.topWindow.get_icon())
        textwindow = topDialog.get_widget("textwindow")
        textwindow.get_buffer().set_text(self.text)

        Utils.set_titles(self.window,topDialog.get_widget("title"),self.title)

        self.add_result_to_menu()
        self.window.show()

    def on_result_delete_event(self,obj,b):
        self.remove_result_from_menu()

    def close_result(self,obj):
        self.remove_result_from_menu()
        self.window.destroy()

    def add_result_to_menu(self):
        self.parent.child_windows[self.win_key] = self.window
        self.result_parent_menu_item = gtk.MenuItem(self.title)
        self.result_parent_menu_item.connect("activate",self.present_result)
        self.result_parent_menu_item.show()
        self.parent.winsmenu.append(self.result_parent_menu_item)

    def remove_result_from_menu(self):
        del self.parent.child_windows[self.win_key]
        self.result_parent_menu_item.destroy()

    def present_result(self,obj):
        self.window.present()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
from PluginMgr import register_tool

register_tool(
    runTool,
    _("Check and repair database"),
    category=_("Database Processing"),
    description=_("Checks the database for integrity problems, fixing the problems that it can")
    )
