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

# $Id$

from string import strip

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade
import gnome

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import Sources
import Witness
import const
import Utils
import GrampsCfg
import AutoComp
import Calendar
import RelLib
import Date

from DateEdit import DateEdit
from gettext import gettext as _

from QuestionDialog import WarningDialog
#-------------------------------------------------------------------------
#
# EventEditor class
#
#-------------------------------------------------------------------------
class EventEditor:

    def __init__(self,parent,name,list,trans,event,def_placename,read_only,cb,
                 def_event=None):
        self.parent = parent
        self.db = self.parent.db
        self.event = event
        self.trans = trans
        self.callback = cb
        self.plist = []
        self.pmap = {}
        self.elist = list
        
        for key in self.parent.db.getPlaceKeys():
            p = self.parent.db.getPlaceDisplay(key)
            self.pmap[p[0]] = key

        if event:
            self.srcreflist = self.event.getSourceRefList()
            self.witnesslist = self.event.get_witness_list()
            if not self.witnesslist:
                self.witnesslist = []
            self.date = Date.Date(self.event.getDateObj())
            transname = const.display_event(event.getName())
            # add the name to the list if it is not already there. This tends to occur
            # in translated languages with the 'Death' event, which is a partial match
            # to other events
            if not transname in list:
                list.append(transname)
        else:
            self.srcreflist = []
            self.witnesslist = []
            self.date = Date.Date(None)

        self.top = gtk.glade.XML(const.dialogFile, "event_edit","gramps")

        self.window = self.top.get_widget("event_edit")
        title_label = self.top.get_widget('title')

        if name == ", ":
            etitle = _('Event Editor')
        else:
            etitle = _('Event Editor for %s') % name

        Utils.set_titles(self.window,title_label, etitle,
                         _('Event Editor'))
        
        self.name_field  = self.top.get_widget("eventName")
        self.place_field = self.top.get_widget("eventPlace")
        self.cause_field = self.top.get_widget("eventCause")
        self.slist = self.top.get_widget("slist")
        self.wlist = self.top.get_widget("wlist")
        self.place_combo = self.top.get_widget("eventPlace_combo")
        self.date_field  = self.top.get_widget("eventDate")
        self.cause_field  = self.top.get_widget("eventCause")
        self.descr_field = self.top.get_widget("event_description")
        self.note_field = self.top.get_widget("eventNote")
        self.event_menu = self.top.get_widget("personalEvents")
        self.priv = self.top.get_widget("priv")
        self.calendar = self.top.get_widget("calendar")
        self.sources_label = self.top.get_widget("sourcesEvent")
        self.notes_label = self.top.get_widget("notesEvent")
        self.flowed = self.top.get_widget("eventflowed")
        self.preform = self.top.get_widget("eventpreform")
        self.witnesses_label = self.top.get_widget("witnessesEvent")

        if GrampsCfg.calendar:
            self.calendar.show()
        else:
            self.calendar.hide()
        
        if read_only:
            self.event_menu.set_sensitive(0)
            self.date_field.grab_focus()

        self.sourcetab = Sources.SourceTab(self.srcreflist,self,
                                           self.top,self.window,self.slist,
                                           self.top.get_widget('add_src'),
                                           self.top.get_widget('edit_src'),
                                           self.top.get_widget('del_src'))

        self.witnesstab = Witness.WitnessTab(self.witnesslist,self,
                                           self.top,self.window,self.wlist,
                                           self.top.get_widget('add_witness'),
                                           self.top.get_widget('edit_witness'),
                                           self.top.get_widget('del_witness'))

        AutoComp.AutoCombo(self.event_menu,list)
        AutoComp.AutoEntry(self.place_field,self.pmap.keys())

        if event != None:
            self.name_field.set_text(transname)
            if (def_placename):
                self.place_field.set_text(def_placename)
            else:
                self.place_field.set_text(event.getPlaceName())

            self.date_field.set_text(self.date.getDate())
            self.cause_field.set_text(event.getCause())
            self.descr_field.set_text(event.getDescription())
            self.priv.set_active(event.getPrivacy())
            
            self.note_field.get_buffer().set_text(event.getNote())
            if event.getNote():
            	self.note_field.get_buffer().set_text(event.getNote())
                Utils.bold_label(self.notes_label)
            	if event.getNoteFormat() == 1:
                    self.preform.set_active(1)
            	else:
                    self.flowed.set_active(1)
        else:
            if def_event:
                self.name_field.set_text(def_event)
            if def_placename:
                self.place_field.set_text(def_placename)
        self.date_check = DateEdit(self.date_field,self.top.get_widget("date_stat"))

        self.top.signal_autoconnect({
            "on_add_src_clicked" : self.add_source,
            "on_del_src_clicked" : self.del_source,
            "on_switch_page" : self.on_switch_page,
            "on_help_event_clicked" : self.on_help_clicked
            })

        menu = gtk.Menu()
        index = 0
        for cobj in Calendar.calendar_names():
            item = gtk.MenuItem(cobj.TNAME)
            item.set_data("d",cobj)
            item.connect("activate",self.on_menu_changed)
            item.show()
            menu.append(item)
            if self.date.get_calendar().NAME == cobj.NAME:
                menu.set_active(index)
                self.date_check.set_calendar(cobj())
            index = index + 1
        self.calendar.set_menu(menu)

        self.window.set_transient_for(self.parent.window)
        self.val = self.window.run()
        if self.val == gtk.RESPONSE_OK:
            self.on_event_edit_ok_clicked()
        self.window.destroy()

    def on_help_clicked(self,obj):
        """Display the relevant portion of GRAMPS manual"""
        gnome.help_display('gramps-manual','gramps-edit-complete')
        self.val = self.window.run()

    def add_source(self,obj):
        pass

    def del_source(self,obj):
        pass

    def on_menu_changed(self,obj):
        cobj = obj.get_data("d")
        self.date.set(unicode(self.date_field.get_text()))
        self.date.set_calendar(cobj)
        self.date_field.set_text(self.date.getDate())
        self.date_check.set_calendar(cobj())
        
    def get_place(self,field,makenew=0):
        text = strip(unicode(field.get_text()))
        if text:
            if self.pmap.has_key(text):
                return self.parent.db.getPlaceMap()[self.pmap[text]]
            elif makenew:
                place = RelLib.Place()
                place.set_title(text)
                self.parent.db.addPlace(place)
                self.pmap[text] = place.getId()
                self.plist.append(place)
                Utils.modified()
                return place
            else:
                return None
        else:
            return None

    def on_event_edit_ok_clicked(self):

        ename = unicode(self.name_field.get_text())
        self.date.set(unicode(self.date_field.get_text()))
        ecause = unicode(self.cause_field.get_text())
        eplace_obj = self.get_place(self.place_field,1)
        buf = self.note_field.get_buffer()

        enote = unicode(buf.get_text(buf.get_start_iter(),buf.get_end_iter(),gtk.FALSE))
        eformat = self.preform.get_active()
        edesc = unicode(self.descr_field.get_text())
        epriv = self.priv.get_active()

        if not ename in self.elist:
            WarningDialog(_('New event type created'),
                          _('The "%s" event type has been added to this database.\n'
                            'It will now appear in the event menus for this database') % ename)
            self.elist.append(ename)
            self.elist.sort()

        if self.event == None:
            self.event = RelLib.Event()
            self.event.setSourceRefList(self.srcreflist)
            self.event.set_witness_list(self.witnesslist)
            self.parent.elist.append(self.event)
        
        self.update_event(ename,self.date,eplace_obj,edesc,enote,eformat,epriv,ecause)
        self.parent.redraw_event_list()
        self.callback(self.event)

    def update_event(self,name,date,place,desc,note,format,priv,cause):
        if self.event.getPlace() != place:
            self.event.setPlace(place)
            self.parent.lists_changed = 1
        
        if self.event.getName() != self.trans(name):
            self.event.setName(self.trans(name))
            self.parent.lists_changed = 1
        
        if self.event.getDescription() != desc:
            self.event.setDescription(desc)
            self.parent.lists_changed = 1

        if self.event.getNote() != note:
            self.event.setNote(note)
            self.parent.lists_changed = 1

        if self.event.getNoteFormat() != format:
            self.event.setNoteFormat(format)
            self.parent.lists_changed = 1

        dobj = self.event.getDateObj()

        self.event.setSourceRefList(self.srcreflist)
        self.event.set_witness_list(self.witnesslist)
        
        if Date.compare_dates(dobj,date) != 0:
            self.event.setDateObj(date)
            self.parent.lists_changed = 1

        if self.event.getCause() != cause:
            self.event.setCause(cause)
            self.parent.lists_changed = 1

        if self.event.getPrivacy() != priv:
            self.event.setPrivacy(priv)
            self.parent.lists_changed = 1

    def on_switch_page(self,obj,a,page):
        buf = self.note_field.get_buffer()
        text = unicode(buf.get_text(buf.get_start_iter(),buf.get_end_iter(),gtk.FALSE))
        if text:
            Utils.bold_label(self.notes_label)
        else:
            Utils.unbold_label(self.notes_label)
