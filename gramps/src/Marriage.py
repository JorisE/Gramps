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

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gtk import *
from gnome.ui import *
import GDK

import libglade
import os
import intl
import Sources

_ = intl.gettext

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------

import const
import Config
import utils
from RelLib import *
import RelImage
import ImageSelect

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
MARRIAGE   = "m"

#-------------------------------------------------------------------------
#
# Marriage class
#
#-------------------------------------------------------------------------
class Marriage:

    #-------------------------------------------------------------------------
    #
    # Initializes the class, and displays the window
    #
    #-------------------------------------------------------------------------
    def __init__(self,family,db):
        self.family = family
        self.db = db
        self.path = db.getSavePath()

        self.top = libglade.GladeXML(const.marriageFile,"marriageEditor")
        top_window = self.get_widget("marriageEditor")
        fid = "f%s" % family.getId()
        plwidget = self.top.get_widget("photolist")
        self.gallery = ImageSelect.Gallery(family, self.path, fid, plwidget, db)
        self.top.signal_autoconnect({
            "destroy_passed_object" : on_cancel_edit,
            "on_add_attr_clicked" : on_add_attr_clicked,
            "on_addphoto_clicked" : self.gallery.on_add_photo_clicked,
            "on_attr_list_select_row" : on_attr_list_select_row,
            "on_close_marriage_editor" : on_close_marriage_editor,
            "on_delete_attr_clicked" : on_delete_attr_clicked,
            "on_delete_event" : on_delete_event,
            "on_deletephoto_clicked" : self.gallery.on_delete_photo_clicked,
            "on_marriageAddBtn_clicked" : on_add_clicked,
            "on_marriageDeleteBtn_clicked" : on_delete_clicked,
            "on_marriageEventList_select_row" : on_select_row,
            "on_marriageUpdateBtn_clicked" : on_update_clicked,
            "on_photolist_button_press_event" : self.gallery.on_photolist_button_press_event,
            "on_photolist_select_icon" : self.gallery.on_photo_select_icon,
            "on_update_attr_clicked" : on_update_attr_clicked,
            })

        text_win = self.get_widget("marriageTitle")
        title = _("%s and %s") % (Config.nameof(family.getFather()),
                                  Config.nameof(family.getMother()))
        text_win.set_text(title)
        
        self.event_list = self.get_widget("marriageEventList")

        # widgets
        self.date_field  = self.get_widget("marriageDate")
        self.place_field = self.get_widget("marriagePlace")
        self.cause_field = self.get_widget("marriageCause")
        self.name_field  = self.get_widget("marriageEventName")
        self.descr_field = self.get_widget("marriageDescription")
        self.type_field  = self.get_widget("marriage_type")
        self.notes_field = self.get_widget("marriageNotes")
        self.gid = self.get_widget("gid")
        self.attr_list = self.get_widget("attr_list")
        self.attr_type = self.get_widget("attr_type")
        self.attr_value = self.get_widget("attr_value")
        self.event_details = self.get_widget("event_details")
        self.attr_details_field = self.get_widget("attr_details")

        self.event_list.set_column_visibility(3,Config.show_detail)
        self.attr_list.set_column_visibility(2,Config.show_detail)

        self.elist = family.getEventList()[:]
        self.alist = family.getAttributeList()[:]
        self.lists_changed = 0

        # set initial data
        self.gallery.load_images()

        self.type_field.set_popdown_strings(const.familyRelations)
        frel = const.display_frel(family.getRelationship())
        self.type_field.entry.set_text(frel)
        self.gid.set_text(family.getId())
        self.gid.set_editable(Config.id_edit)
        
        # stored object data
        top_window.set_data(MARRIAGE,self)
        self.event_list.set_data(MARRIAGE,self)
        self.attr_list.set_data(MARRIAGE,self)

        # set notes data
        self.notes_field.set_point(0)
        self.notes_field.insert_defaults(family.getNote())
        self.notes_field.set_word_wrap(1)

        # Typing CR selects OK button
        top_window.editable_enters(self.notes_field);
        top_window.editable_enters(self.get_widget("combo-entry1"));
        
        self.redraw_events()
        self.redraw_attr_list()
        top_window.show()

    #-------------------------------------------------------------------------
    #
    #
    #
    #-------------------------------------------------------------------------
    def update_lists(self):
        self.family.setEventList(self.elist)
        self.family.setAttributeList(self.alist)

    #---------------------------------------------------------------------
    #
    # redraw_attr_list - redraws the attribute list for the person
    #
    #---------------------------------------------------------------------
    def redraw_attr_list(self):
        utils.redraw_list(self.alist,self.attr_list,disp_attr)

    #-------------------------------------------------------------------------
    #
    # redraw_events - redraws the event list by deleting all the entries and
    # reconstructing the list
    #
    #-------------------------------------------------------------------------
    def redraw_events(self):
        utils.redraw_list(self.elist,self.event_list,disp_event)

    #-------------------------------------------------------------------------
    #
    # get_widget - returns the widget associated with the specified name
    #
    #-------------------------------------------------------------------------
    def get_widget(self,name):
        return self.top.get_widget(name)


#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def did_data_change(obj):
    family_obj = obj.get_data(MARRIAGE)

    changed = 0
    relation = family_obj.type_field.entry.get_text()
    if const.save_frel(relation) != family_obj.family.getRelationship():
        changed = 1

    text = family_obj.notes_field.get_chars(0,-1)
    if text != family_obj.family.getNote():
        changed = 1
        
    if family_obj.lists_changed:
        changed = 1

    idval = family_obj.gid.get_text()
    if family_obj.family.getId() != idval:
        changed = 1

    return changed

#-------------------------------------------------------------------------
#
# on_cancel_edit
#
#-------------------------------------------------------------------------
def on_cancel_edit(obj):

    if did_data_change(obj):
        global quit
        q = _("Data was modified. Are you sure you want to abandon your changes?")
        quit = obj
        GnomeQuestionDialog(q,cancel_callback)
    else:
        utils.destroy_passed_object(obj)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def cancel_callback(a):
    if a==0:
        utils.destroy_passed_object(quit)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def on_delete_event(obj,b):
    global quit

    if did_data_change(obj):
        q = _("Data was modified. Are you sure you want to abandon your changes?")
        quit = obj
        GnomeQuestionDialog(q,cancel_callback)
        return 1
    else:
        utils.destroy_passed_object(obj)
        return 0

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_close_marriage_editor(obj):
    family_obj = obj.get_data(MARRIAGE)

    idval = family_obj.gid.get_text()
    family = family_obj.family
    if idval != family.getId():
        m = family_obj.db.getFamilyMap() 
        if not m.has_key(idval):
            if m.has_key(family.getId()):
                del m[family.getId()]
                m[idval] = family
            family.setId(idval)
            utils.modified()
        else:
            msg1 = _("GRAMPS ID value was not changed.")
            GnomeWarningDialog("%s" % msg1)

    relation = family_obj.type_field.entry.get_text()
    if const.save_frel(relation) != family_obj.family.getRelationship():
        father = family_obj.family.getFather()
        mother = family_obj.family.getMother()
        if father.getGender() == mother.getGender():
            family_obj.family.setRelationship("Partners")
        else:
            val = const.save_frel(relation)
            if val == "Partners":
                val = "Unknown"
            if father.getGender() == Person.female or \
               mother.getGender() == Person.male:
                family_obj.family.setFather(mother)
                family_obj.family.setMother(father)
            family_obj.family.setRelationship(val)
        utils.modified()

    text = family_obj.notes_field.get_chars(0,-1)
    if text != family_obj.family.getNote():
        family_obj.family.setNote(text)
        utils.modified()

    utils.destroy_passed_object(family_obj.get_widget("marriageEditor"))

    family_obj.update_lists()
    if family_obj.lists_changed:
        utils.modified()

#-------------------------------------------------------------------------
#
# on_add_clicked - creates a new event from the data displayed in the
# window. Special care has to be take for the marriage and divorce
# events, since they are not stored in the event list. 
#
#-------------------------------------------------------------------------
def on_add_clicked(obj):
    EventEditor(obj.get_data(MARRIAGE),None)

#-------------------------------------------------------------------------
#
# on_update_clicked - updates the selected event with the values in the
# current display
#
#-------------------------------------------------------------------------
def on_update_clicked(obj):
    if len(obj.selection) > 0:
        row = obj.selection[0]
        EventEditor(obj.get_data(MARRIAGE),obj.get_row_data(row))

#-------------------------------------------------------------------------
#
# on_delete_clicked - deletes the currently displayed event from the
# marriage event list.  Special care needs to be taken for the Marriage
# and Divorce events, since they are not stored in the event list
#
#-------------------------------------------------------------------------
def on_delete_clicked(obj):
    family_obj = obj.get_data(MARRIAGE)
    if utils.delete_selected(obj,family_obj.elist):
        family_obj.lists_changed = 1
        family_obj.redraw_events()

#-------------------------------------------------------------------------
#
# on_select_row - updates the internal data attached to the passed object,
# then updates the display.
#
#-------------------------------------------------------------------------
def on_select_row(obj,row,b,c):
    family_obj = obj.get_data(MARRIAGE)
    event = obj.get_row_data(row)
    
    family_obj.date_field.set_text(event.getDate())
    family_obj.place_field.set_text(event.getPlaceName())
    family_obj.cause_field.set_text(event.getCause())
    family_obj.name_field.set_label(const.display_fevent(event.getName()))
    family_obj.event_details.set_text(utils.get_detail_text(event))
    family_obj.descr_field.set_text(event.getDescription())

#-------------------------------------------------------------------------
#
# update_attrib
# 
# Updates the specified event with the specified date.  Compares against
# the previous value, so the that modified flag is not set if nothing has
# actually changed.
#
#-------------------------------------------------------------------------
def update_attrib(attr,type,value,note,priv):
    changed = 0
        
    if attr.getType() != const.save_pattr(type):
        attr.setType(const.save_pattr(type))
        changed = 1
        
    if attr.getValue() != value:
        attr.setValue(value)
        changed = 1

    if attr.getNote() != note:
        attr.setNote(note)
        changed = 1

    if attr.getPrivacy() != priv:
        attr.setPrivacy(priv)
        changed = 1

    return changed

#-------------------------------------------------------------------------
#
# update_event
# 
# Updates the specified event with the specified date.  Compares against
# the previous value, so the that modified flag is not set if nothing has
# actually changed.
#
#-------------------------------------------------------------------------
def update_event(event,name,date,place,desc,note,priv,cause):
    changed = 0
    if event.getPlace() != place:
        event.setPlace(place)
        changed = 1
        
    if event.getName() != const.save_pevent(name):
        event.setName(const.save_pevent(name))
        changed = 1
        
    if event.getDescription() != desc:
        event.setDescription(desc)
        changed = 1

    if event.getNote() != note:
        event.setNote(note)
        changed = 1

    if event.getDate() != date:
        event.setDate(date)
        changed = 1

    if event.getCause() != cause:
        event.setCause(cause)
        changed = 1

    if event.getPrivacy() != priv:
        event.setPrivacy(priv)
        changed = 1

    return changed

#-------------------------------------------------------------------------
#
# on_attr_list_select_row - sets the row object attached to the passed
# object, and then updates the display with the data corresponding to
# the row.
#
#-------------------------------------------------------------------------
def on_attr_list_select_row(obj,row,b,c):
    family_obj = obj.get_data(MARRIAGE)
    attr = obj.get_row_data(row)

    family_obj.attr_type.set_label(const.display_fattr(attr.getType()))
    family_obj.attr_value.set_text(attr.getValue())
    family_obj.attr_details_field.set_text(utils.get_detail_text(attr))

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_update_attr_clicked(obj):
    if len(obj.selection) > 0:
        row = obj.selection[0]
        AttributeEditor(obj.get_data(MARRIAGE),obj.get_row_data(row))

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_delete_attr_clicked(obj):
    family_obj = obj.get_data(MARRIAGE)
    if utils.delete_selected(obj,family_obj.alist):
        family_obj.lists_changed = 1
        family_obj.redraw_attr_list()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_add_attr_clicked(obj):
    AttributeEditor(obj.get_data(MARRIAGE),None)

#-------------------------------------------------------------------------
#
# EventEditor class
#
#-------------------------------------------------------------------------
class EventEditor:

    def __init__(self,parent,event):
        self.parent = parent
        self.event = event
        self.srcreflist = self.event.getSourceRefList()
        self.top = libglade.GladeXML(const.dialogFile, "event_edit")
        self.window = self.top.get_widget("event_edit")
        self.name_field  = self.top.get_widget("eventName")
        self.place_field = self.top.get_widget("eventPlace")
        self.cause_field = self.top.get_widget("eventCause")
        self.place_combo = self.top.get_widget("eventPlace_combo")
        self.date_field  = self.top.get_widget("eventDate")
        self.cause_field  = self.top.get_widget("eventCause")
        self.descr_field = self.top.get_widget("eventDescription")
        self.note_field = self.top.get_widget("eventNote")
        self.event_menu = self.top.get_widget("personalEvents")
        self.priv = self.top.get_widget("priv")

        father = parent.family.getFather()
        mother = parent.family.getMother()
        if father and mother:
            name = _("%s and %s") % (father.getPrimaryName().getName(),
                                     mother.getPrimaryName().getName())
        elif father:
            name = father.getPrimaryName().getName()
        else:
            name = mother.getPrimaryName().getName()
            
        self.top.get_widget("eventTitle").set_text(name) 
        self.event_menu.set_popdown_strings(const.marriageEvents)

        # Typing CR selects OK button
        self.window.editable_enters(self.name_field);
        self.window.editable_enters(self.place_field);
        self.window.editable_enters(self.date_field);
        self.window.editable_enters(self.cause_field);
        self.window.editable_enters(self.descr_field);

        values = self.parent.db.getPlaceMap().values()
        if event != None:
            self.name_field.set_text(event.getName())

            utils.attach_places(values,self.place_combo,event.getPlace())
            self.place_field.set_text(event.getPlaceName())
            self.date_field.set_text(event.getDate())
            self.cause_field.set_text(event.getCause())
            self.descr_field.set_text(event.getDescription())
            self.priv.set_active(event.getPrivacy())
            
            self.note_field.set_point(0)
            self.note_field.insert_defaults(event.getNote())
            self.note_field.set_word_wrap(1)
        else:
            utils.attach_places(values,self.place_combo,None)

        self.window.set_data("o",self)
        self.top.signal_autoconnect({
            "destroy_passed_object" : utils.destroy_passed_object,
            "on_event_edit_ok_clicked" : on_event_edit_ok_clicked,
            "on_source_clicked" : on_edit_source_clicked
            })

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_edit_source_clicked(obj):
    ee = obj.get_data("o")
    Sources.SourceSelector(ee.srcreflist,ee.parent,src_changed)

def src_changed(parent):
    parent.list_changed = 1
            
#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_event_edit_ok_clicked(obj):
    ee = obj.get_data("o")
    event = ee.event

    ename = ee.name_field.get_text()
    edate = ee.date_field.get_text()
    ecause = ee.cause_field.get_text()
    eplace = string.strip(ee.place_field.get_text())
    eplace_obj = utils.get_place_from_list(ee.place_combo)
    enote = ee.note_field.get_chars(0,-1)
    edesc = ee.descr_field.get_text()
    epriv = ee.priv.get_active()

    if event == None:
        event = Event()
        event.setSourceRefList(ee.srcreflist)
        ee.parent.elist.append(event)
        
    if eplace_obj == None and eplace != "":
        eplace_obj = Place()
        eplace_obj.set_title(eplace)
        ee.parent.db.addPlace(eplace_obj)

    if update_event(event,ename,edate,eplace_obj,edesc,enote,epriv,ecause):
        ee.parent.lists_changed = 1
        
    ee.parent.redraw_events()
    utils.destroy_passed_object(obj)

#-------------------------------------------------------------------------
#
# AttributeEditor class
#
#-------------------------------------------------------------------------
class AttributeEditor:

    def __init__(self,parent,attrib):
        self.parent = parent
        self.attrib = attrib
        self.top = libglade.GladeXML(const.dialogFile, "attr_edit")
        self.window = self.top.get_widget("attr_edit")
        self.type_field  = self.top.get_widget("attr_type")
        self.value_field = self.top.get_widget("attr_value")
        self.note_field = self.top.get_widget("attr_note")
        self.attrib_menu = self.top.get_widget("attr_menu")
        self.source_field = self.top.get_widget("attr_source")
        self.priv = self.top.get_widget("priv")
        
        if attrib:
            self.srcreflist = self.attrib.getSourceRefList()
        else:
            self.srcreflist = []

        # Typing CR selects OK button
        self.window.editable_enters(self.type_field);
        self.window.editable_enters(self.value_field);

        father = parent.family.getFather()
        mother = parent.family.getMother()
        if father and mother:
            name = _("%s and %s") % (father.getPrimaryName().getName(),
                                     mother.getPrimaryName().getName())
        elif father:
            name = father.getPrimaryName().getName()
        else:
            name = mother.getPrimaryName().getName()

        title = _("Attribute Editor for %s") % name
        self.top.get_widget("attrTitle").set_text(title)
        if len(const.familyAttributes) > 0:
            self.attrib_menu.set_popdown_strings(const.familyAttributes)

        if attrib != None:
            self.type_field.set_text(attrib.getType())
            self.value_field.set_text(attrib.getValue())
            self.priv.set_active(attrib.getPrivacy())

            self.note_field.set_point(0)
            self.note_field.insert_defaults(attrib.getNote())
            self.note_field.set_word_wrap(1)

        self.window.set_data("o",self)
        self.top.signal_autoconnect({
            "destroy_passed_object" : utils.destroy_passed_object,
            "on_attr_edit_ok_clicked" : on_attrib_edit_ok_clicked,
            "on_source_clicked" : on_attrib_source_clicked
            })

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_attrib_source_clicked(obj):
    ee = obj.get_data("o")
    Sources.SourceSelector(ee.srcreflist,ee.parent,src_changed)
            
#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def on_attrib_edit_ok_clicked(obj):
    ee = obj.get_data("o")
    attrib = ee.attrib

    type = ee.type_field.get_text()
    value = ee.value_field.get_text()
    note = ee.note_field.get_chars(0,-1)
    priv = ee.priv.get_active()

    if attrib == None:
        attrib = Attribute()
        attrib.setSourceRefList(ee.srcreflist)
        ee.parent.alist.append(attrib)
        
    if update_attrib(attrib,type,value,note,priv):
        ee.parent.lists_changed = 1
        
    ee.parent.redraw_attr_list()
    utils.destroy_passed_object(obj)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def disp_attr(attr):
    detail = utils.get_detail_flags(attr)
    return [const.display_pattr(attr.getType()),attr.getValue(),detail]

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def disp_event(event):
    return [const.display_fevent(event.getName()), event.getQuoteDate(),
            event.getPlaceName(), utils.get_detail_flags(event)]
