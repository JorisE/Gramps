#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2008 Douglas S. Blank
# Copyright (C) 2004-2007 Donald N. Allingham
# Copyright (C) 2008      Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2011       Tim G L Lyons
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

"Export to CSV Spreadsheet."

#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------
import os
import sys
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.sgettext
import csv
if sys.version_info[0] < 3:
    from cStringIO import StringIO
else:
    from io import StringIO
import codecs

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
import collections
LOG = logging.getLogger(".ExportCSV")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gramps.gen.lib import EventType, Person
from gramps.gen.lib.eventroletype import EventRoleType
from gramps.gui.plug.export import WriterOptionBox
from gramps.gen.utils.string import gender as gender_map
from gramps.gen.datehandler import get_date
from gramps.gui.glade import Glade

#-------------------------------------------------------------------------
#
# The function that does the exporting
#
#-------------------------------------------------------------------------
def exportData(database, filename, user, option_box=None):
    gw = CSVWriter(database, filename, user, option_box)
    return gw.export_data()

#-------------------------------------------------------------------------
#
# Support Functions
#
#-------------------------------------------------------------------------
def sortable_string_representation(text):
    numeric = ""
    alpha   = ""
    for s in text:
        if s.isdigit():
            numeric += s
        else:
            alpha += s
    return alpha + (("0" * 10) + numeric)[-10:]

def get_primary_event_ref_from_type(db, person, event_name):
    """
    >>> get_primary_event_ref_from_type(db, Person(), "Baptism"):
    """
    for ref in person.event_ref_list:
        if ref.get_role() == EventRoleType.PRIMARY:
            event = db.get_event_from_handle(ref.ref)
            if event and event.type.is_type(event_name):
                return ref
    return None

def get_primary_source_title(db, obj):
    for citation_handle in obj.get_citation_list():
        citation = db.get_citation_from_handle(citation_handle)
        source = db.get_source_from_handle(citation.get_reference_handle())
        if source:
            return source.get_title()
    return ""

#-------------------------------------------------------------------------
#
# Encoding support for CSV, from http://docs.python.org/lib/csv-examples.html
#
#-------------------------------------------------------------------------
class UTF8Recoder(object):
    """Iterator that reads an encoded stream and reencodes the input to UTF-8."""
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def __next__(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f", which is 
    encoded in the given encoding.
    
    """

    def __init__(self, f, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, **kwds)

    def __next__(self):
        row = next(self.reader)
        return [str(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f", which is encoded in 
    the given encoding.
    
    """

    def __init__(self, f, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, **kwds)
        self.stream = f
        self.encoder = codecs.getencoder(encoding)

    def writerow(self, row):
        if sys.version_info[0] < 3:
            self.writer.writerow([s.encode('utf-8') for s in row])
            # Fetch UTF-8 output from the queue ...
            data = self.queue.getvalue()
            data = data.decode('utf-8')
        else:
            self.writer.writerow(row)
            data = self.queue.getvalue()
            #in python3, StringIO self.queue returns unicode!
        #data now contains the csv data in unicode
        # ... and reencode it into the target encoding
        data, length = self.encoder(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue, go to start position, then truncate
        self.queue.seek(0)
        self.queue.truncate(0)

    def writerows(self, rows):
        list(map(self.writerow, rows))

    def close(self):
        self.stream.close()

#-------------------------------------------------------------------------
#
# CSVWriter Options
#
#-------------------------------------------------------------------------
class CSVWriterOptionBox(WriterOptionBox):
    """
    Create a VBox with the option widgets and define methods to retrieve
    the options. 
    
    """
    def __init__(self, person, dbstate, uistate):
        WriterOptionBox.__init__(self, person, dbstate, uistate)
        self.include_individuals = 1
        self.include_marriages = 1
        self.include_children = 1
        self.translate_headers = 1
        self.include_individuals_check = None
        self.include_marriages_check = None
        self.include_children_check = None
        self.translate_headers_check = None

    def get_option_box(self):
        from gi.repository import Gtk
        option_box = WriterOptionBox.get_option_box(self)

        self.include_individuals_check = Gtk.CheckButton(_("Include people"))
        self.include_marriages_check = Gtk.CheckButton(_("Include marriages"))
        self.include_children_check = Gtk.CheckButton(_("Include children"))
        self.translate_headers_check = Gtk.CheckButton(_("Translate headers"))

        self.include_individuals_check.set_active(1) 
        self.include_marriages_check.set_active(1) 
        self.include_children_check.set_active(1) 
        self.translate_headers_check.set_active(1) 

        option_box.pack_start(self.include_individuals_check, False, True, 0)
        option_box.pack_start(self.include_marriages_check, False, True, 0)
        option_box.pack_start(self.include_children_check, False, True, 0)
        option_box.pack_start(self.translate_headers_check, False, True, 0)

        return option_box

    def parse_options(self):
        WriterOptionBox.parse_options(self)
        if self.include_individuals_check:
            self.include_individuals = self.include_individuals_check.get_active()
            self.include_marriages = self.include_marriages_check.get_active()
            self.include_children = self.include_children_check.get_active()
            self.translate_headers = self.translate_headers_check.get_active()

#-------------------------------------------------------------------------
#
# CSVWriter class
#
#-------------------------------------------------------------------------
class CSVWriter(object):
    def __init__(self, database, filename, user, option_box=None):
        self.db = database
        self.option_box = option_box
        self.filename = filename
        self.user = user
        if isinstance(self.user.callback, collections.Callable): # callback is really callable
            self.update = self.update_real
        else:
            self.update = self.update_empty

        self.plist = {}
        self.flist = {}
        
        self.persons_details_done = []
        self.persons_notes_done = []
        self.person_ids = {}
        
        if not option_box:
            self.include_individuals = 1
            self.include_marriages = 1
            self.include_children = 1
            self.translate_headers = 1
        else:
            self.option_box.parse_options()
            self.db = option_box.get_filtered_database(self.db)

            self.include_individuals = self.option_box.include_individuals
            self.include_marriages = self.option_box.include_marriages
            self.include_children = self.option_box.include_children
            self.translate_headers = self.option_box.translate_headers
            
        self.plist = [x for x in self.db.iter_person_handles()]
        # get the families for which these people are spouses:
        self.flist = {}
        for key in self.plist:
            p = self.db.get_person_from_handle(key)
            if p:
                for family_handle in p.get_family_handle_list():
                    self.flist[family_handle] = 1
        # now add the families for which these people are a child:
        for family_handle in self.db.iter_family_handles():
            family = self.db.get_family_from_handle(family_handle)
            if family:
                for child_ref in family.get_child_ref_list():
                    if child_ref:
                        child_handle = child_ref.ref
                        if child_handle in self.plist:
                            self.flist[family_handle] = 1
                        
    def update_empty(self):
        pass

    def update_real(self):
        self.count += 1
        newval = int(100*self.count/self.total)
        if newval != self.oldval:
            self.user.callback(newval)
            self.oldval = newval

    def writeln(self):
        self.g.writerow([])

    def write_csv(self, *items):
        self.g.writerow(items)

    def export_data(self):
        self.dirname = os.path.dirname (self.filename)
        try:
            self.g = open(self.filename,"w")
            self.fp = open(self.filename, "wb")
            self.g = UnicodeWriter(self.fp)
        except IOError as msg:
            msg2 = _("Could not create %s") % self.filename
            self.user.notify_error(msg2,str(msg))
            return False
        except:
            self.user.notify_error(_("Could not create %s") % self.filename)
            return False
        ######################### initialize progress bar
        self.count = 0
        self.total = 0
        self.oldval = 0
        if self.include_individuals:
            self.total += len(self.plist)
        if self.include_marriages:
            self.total += len(self.flist)
        if self.include_children:
            self.total += len(self.flist)
        ######################## 
        LOG.debug("Possible people to export: %s", len(self.plist))
        LOG.debug("Possible families to export: %s", len(self.flist))
        ########################### sort:
        sortorder = []
        for key in self.plist:
            person = self.db.get_person_from_handle(key)
            if person:
                primary_name = person.get_primary_name()
                first_name = primary_name.get_first_name()
                surname_obj = primary_name.get_primary_surname()
                surname = surname_obj.get_surname()
                sortorder.append( (surname, first_name, key) )
        sortorder.sort() # will sort on tuples
        plist = [data[2] for data in sortorder]
        ###########################
        if self.include_individuals:
            if self.translate_headers:
                self.write_csv(
                    _("Person"), _("Surname"), _("Given"), 
                    _("Call"), _("Suffix"), _("Prefix"), 
                    _("Person|Title"), _("Gender"), 
                    _("Birth date"), _("Birth place"), _("Birth source"),
                    _("Baptism date"), _("Baptism place"), _("Baptism source"),
                    _("Death date"), _("Death place"), _("Death source"), 
                    _("Burial date"), _("Burial place"), _("Burial source"),
                    _("Note"))
            else:
                self.write_csv(
                    "Person", "Surname", "Given", 
                    "Call", "Suffix", "Prefix", 
                    "Title", "Gender", 
                    "Birth date", "Birth place", "Birth source",
                    "Baptism date", "Baptism place", "Baptism source",
                    "Death date", "Death place", "Death source", 
                    "Burial date", "Burial place", "Burial source",
                    "Note")
            for key in plist:
                person = self.db.get_person_from_handle(key)
                if person:
                    primary_name = person.get_primary_name()
                    first_name = primary_name.get_first_name()
                    surname_obj = primary_name.get_primary_surname()
                    surname = surname_obj.get_surname()
                    prefix = surname_obj.get_prefix()
                    suffix = primary_name.get_suffix()
                    title = primary_name.get_title()
                    grampsid = person.get_gramps_id()
                    grampsid_ref = ""
                    if grampsid != "":
                        grampsid_ref = "[" + grampsid + "]"
                    note = '' # don't export notes
                    callname = primary_name.get_call_name()
                    gender = person.get_gender()
                    if gender == Person.MALE:
                        gender = gender_map[Person.MALE]
                    elif gender == Person.FEMALE:
                        gender = gender_map[Person.FEMALE]
                    else:
                        gender = gender_map[Person.UNKNOWN]
                    # Birth:
                    birthdate = ""
                    birthplace = ""
                    birthsource = ""
                    birth_ref = person.get_birth_ref()
                    if birth_ref:
                        birth = self.db.get_event_from_handle(birth_ref.ref)
                        if birth:
                            birthdate = self.format_date( birth)
                            place_handle = birth.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                birthplace = place.get_title()
                            birthsource = get_primary_source_title(self.db, birth)
                    # Baptism:
                    baptismdate = ""
                    baptismplace = ""
                    baptismsource = ""
                    baptism_ref = get_primary_event_ref_from_type(
                        self.db, person, "Baptism")
                    if baptism_ref:
                        baptism = self.db.get_event_from_handle(baptism_ref.ref)
                        if baptism:
                            baptismdate = self.format_date( baptism)
                            place_handle = baptism.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                baptismplace = place.get_title()
                            baptismsource = get_primary_source_title(self.db, baptism)
                    # Death:
                    deathdate = ""
                    deathplace = ""
                    deathsource = ""
                    death_ref = person.get_death_ref()
                    if death_ref:
                        death = self.db.get_event_from_handle(death_ref.ref)
                        if death:
                            deathdate = self.format_date( death)
                            place_handle = death.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                deathplace = place.get_title()
                            deathsource = get_primary_source_title(self.db, death)
                    # Burial:
                    burialdate = ""
                    burialplace = ""
                    burialsource = ""
                    burial_ref = get_primary_event_ref_from_type(
                        self.db, person, "Burial")
                    if burial_ref:
                        burial = self.db.get_event_from_handle(burial_ref.ref)
                        if burial:
                            burialdate = self.format_date( burial)
                            place_handle = burial.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                burialplace = place.get_title()
                            burialsource = get_primary_source_title(self.db, burial)
                    # Write it out:
                    self.write_csv(grampsid_ref, surname, first_name, callname,
                                   suffix, prefix, title, gender,
                                   birthdate, birthplace, birthsource,
                                   baptismdate, baptismplace, baptismsource,
                                   deathdate, deathplace, deathsource,
                                   burialdate, burialplace, burialsource,
                                   note)
                self.update()
            self.writeln()
        ########################### sort:
        sortorder = []
        for key in self.flist:
            family = self.db.get_family_from_handle(key)
            if family:
                marriage_id = family.get_gramps_id()
                sortorder.append(
                    (sortable_string_representation(marriage_id), key)
                    )
        sortorder.sort() # will sort on tuples
        flist = [data[1] for data in sortorder]
        ########################### 
        if self.include_marriages:
            if self.translate_headers:
                self.write_csv(_("Marriage"), _("Husband"), _("Wife"), 
                               _("Date"), _("Place"), _("Source"), _("Note"))
            else:
                self.write_csv("Marriage", "Husband", "Wife", 
                               "Date", "Place", "Source", "Note")
            for key in flist:
                family = self.db.get_family_from_handle(key)
                if family:
                    marriage_id = family.get_gramps_id()
                    if marriage_id != "":
                        marriage_id = "[" + marriage_id + "]"
                    mother_id = ''
                    father_id = ''
                    father_handle = family.get_father_handle()
                    if father_handle:
                        father = self.db.get_person_from_handle(father_handle)
                        father_id = father.get_gramps_id()
                        if father_id != "":
                            father_id = "[" + father_id + "]"
                    mother_handle = family.get_mother_handle()
                    if mother_handle:
                        mother = self.db.get_person_from_handle(mother_handle)
                        mother_id = mother.get_gramps_id()
                        if mother_id != "":
                            mother_id = "[" + mother_id + "]"
                    # get mdate, mplace
                    mdate, mplace, source = '', '', ''
                    event_ref_list = family.get_event_ref_list()
                    for event_ref in event_ref_list:
                        event = self.db.get_event_from_handle(event_ref.ref)
                        if event.get_type() == EventType.MARRIAGE:
                            mdate = self.format_date( event)
                            place_handle = event.get_place_handle()
                            if place_handle:
                                place = self.db.get_place_from_handle(place_handle)
                                mplace = place.get_title()
                                source = get_primary_source_title(self.db, event)
                    note = ''
                    self.write_csv(marriage_id, father_id, mother_id, mdate,
                                   mplace, source, note)
                self.update()
            self.writeln()
        if self.include_children:
            if self.translate_headers:
                self.write_csv(_("Family"), _("Child"))
            else:
                self.write_csv("Family", "Child")
            for key in flist:
                family = self.db.get_family_from_handle(key)
                if family:
                    family_id = family.get_gramps_id()
                    if family_id != "":
                        family_id = "[" + family_id + "]"
                    for child_ref in family.get_child_ref_list():
                        child_handle = child_ref.ref
                        child = self.db.get_person_from_handle(child_handle)
                        grampsid = child.get_gramps_id()
                        grampsid_ref = ""
                        if grampsid != "":
                            grampsid_ref = "[" + grampsid + "]"
                        self.write_csv(family_id, grampsid_ref)
                self.update()
            self.writeln()
        self.g.close()
        return True 
    
    def format_date(self, date):
        return get_date(date)
