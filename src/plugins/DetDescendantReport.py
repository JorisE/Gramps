#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2002 Bruce J. DeGrasse
# Copyright (C) 2000-2007 Donald N. Allingham
# Copyright (C) 2007-2008 Brian G. Matherly
# Copyright (C) 2007      Robert Cawley  <rjc@cawley.id.au>
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

"Generate files/Detailed Descendant Report"

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
from gettext import gettext as _

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import gen.lib
from PluginUtils import register_report, NumberOption, \
    BooleanOption, PersonOption
from ReportBase import Report, ReportUtils, MenuReportOptions, \
     CATEGORY_TEXT, MODE_GUI, MODE_BKI, MODE_CLI
from ReportBase import Bibliography, Endnotes
import BaseDoc
import DateHandler
from BasicUtils import name_displayer as _nd

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
EMPTY_ENTRY = "_____________"
HENRY = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class DetDescendantReport(Report):

    def __init__(self,database,person,options_class):
        """
        Creates the DetDescendantReport object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options_class   - instance of the Options class for this report

        This report needs the following parameters (class variables)
        that come in the options class.
        
        gen           - Maximum number of generations to include.
        pagebgg       - Whether to include page breaks between generations.
        firstName     - Whether to use first names instead of pronouns.
        fullDate      - Whether to use full dates instead of just year.
        listChildren  - Whether to list children.
        includeMates  - Whether to include information about spouses
        includeNotes  - Whether to include notes.
        includeAttrs  - Whether to include attributes
        blankPlace    - Whether to replace missing Places with ___________.
        blankDate     - Whether to replace missing Dates with ___________.
        calcAgeFlag   - Whether to compute age.
        dupPerson     - Whether to omit duplicate ancestors (e.g. when distant cousins mary).
        verbose       - Whether to use complete sentences
        childRef      - Whether to add descendant references in child list.
        addImages     - Whether to include images.
        pid           - The Gramps ID of the center person for the report.
        """
        Report.__init__(self,database,person,options_class)

        self.map = {}

        self.max_generations = options_class.handler.options_dict['gen']
        self.pgbrk         = options_class.handler.options_dict['pagebbg']
        self.fullDate      = options_class.handler.options_dict['fulldates']
        self.listChildren  = options_class.handler.options_dict['listc']
        self.includeNotes  = options_class.handler.options_dict['incnotes']
        self.usecall       = options_class.handler.options_dict['usecall']
        self.blankPlace    = options_class.handler.options_dict['repplace']
        self.blankDate     = options_class.handler.options_dict['repdate']
        self.calcAgeFlag   = options_class.handler.options_dict['computeage']
        self.dupPerson     = options_class.handler.options_dict['omitda']
        self.verbose       = options_class.handler.options_dict['verbose']
        self.childRef      = options_class.handler.options_dict['desref']
        self.addImages     = options_class.handler.options_dict['incphotos']
        self.includeNames  = options_class.handler.options_dict['incnames']
        self.includeEvents = options_class.handler.options_dict['incevents']
        self.includeAddr   = options_class.handler.options_dict['incaddresses']
        self.includeSources= options_class.handler.options_dict['incsources']
        self.includeMates  = options_class.handler.options_dict['incmates']
        self.includeAttrs  = options_class.handler.options_dict['incattrs']
        pid = options_class.handler.options_dict['pid']
        self.center_person = database.get_person_from_gramps_id(pid)

        self.gen_handles = {}
        self.prev_gen_handles= {}
        self.gen_keys = []
        self.henry = {}

        if self.blankDate:
            self.EMPTY_DATE = EMPTY_ENTRY
        else:
            self.EMPTY_DATE = ""

        if self.blankPlace:
            self.EMPTY_PLACE = EMPTY_ENTRY
        else:
            self.EMPTY_PLACE = ""

        self.bibli = Bibliography(Bibliography.MODE_PAGE)

    def apply_filter(self,person_handle,index,pid,cur_gen=1):
        if (not person_handle) or (cur_gen > self.max_generations):
            return
        self.henry[person_handle] = pid
        self.map[index] = person_handle

        if len(self.gen_keys) < cur_gen:
            self.gen_keys.append([index])
        else: 
            self.gen_keys[cur_gen-1].append(index)

        person = self.database.get_person_from_handle(person_handle)
        index = 0
        for family_handle in person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                ix = max(self.map.keys())
                self.apply_filter(child_ref.ref, ix+1,
                                  pid+HENRY[index], cur_gen+1)
                index += 1

    def write_report(self):
        self.apply_filter(self.center_person.get_handle(),1,"1")

        name = _nd.display_name(self.center_person.get_primary_name())

        spouseName = ""
        nspouses = 0
        for family_handle in self.center_person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)
            if self.center_person.get_gender() == gen.lib.Person.MALE:
                spouse_handle = family.get_mother_handle()
            else:
                spouse_handle = family.get_father_handle()
            if spouse_handle:
                nspouses += 1
                spouse = self.database.get_person_from_handle(spouse_handle)
                spouseName = _nd.display(spouse)

        self.doc.start_paragraph("DDR-Title")

        title = _("Descendant Report for %(person_name)s") % {
                    'person_name' : name }
        mark = BaseDoc.IndexMark(title,BaseDoc.INDEX_TYPE_TOC,1)
        self.doc.write_text(title,mark)
        self.doc.end_paragraph()

        keys = self.map.keys()
        keys.sort()
        generation = 0
        need_header = 1

        for generation in xrange(len(self.gen_keys)):
            if self.pgbrk and generation > 0:
                self.doc.page_break()
            self.doc.start_paragraph("DDR-Generation")
            text = _("Generation %d") % (generation+1)
            mark = BaseDoc.IndexMark(text,BaseDoc.INDEX_TYPE_TOC,2)
            self.doc.write_text(text,mark)
            self.doc.end_paragraph()
            if self.childRef:
                self.prev_gen_handles = self.gen_handles.copy()
                self.gen_handles.clear()

            for key in self.gen_keys[generation]:
                person_handle = self.map[key]
                person = self.database.get_person_from_handle(person_handle)
                self.gen_handles[person_handle] = key
                self.write_person(key)

        if self.includeSources:
            Endnotes.write_endnotes(self.bibli,self.database,self.doc)

    def write_person(self, key):
        """Output birth, death, parentage, marriage and notes information """

        person_handle = self.map[key]
        person = self.database.get_person_from_handle(person_handle)

        val = self.henry[person_handle]
        self.doc.start_paragraph("DDR-First-Entry","%s." % val)

        name = _nd.display_formal(person)
        mark = ReportUtils.get_person_mark(self.database, person)

        self.doc.start_bold()
        self.doc.write_text(name,mark)
        if name[-1:] == '.':
            self.doc.write_text("%s " % self.endnotes(person))
        else:
            self.doc.write_text("%s. " % self.endnotes(person))
        self.doc.end_bold()
        
        if self.dupPerson:
            # Check for duplicate record (result of distant cousins marrying)
            keys = self.map.keys()
            keys.sort()
            for dkey in keys:
                if dkey >= key: 
                    break
                if self.map[key] == self.map[dkey]:
                    self.doc.write_text(_("%(name)s is the same person as [%(id_str)s].") % 
                                        { 'name' : '', 'id_str' : str(dkey) })
                    self.doc.end_paragraph()
                    return

        self.doc.end_paragraph()
       
        self.write_person_info(person)

        if self.listChildren or self.includeEvents or self.includeMates:
            for family_handle in person.get_family_handle_list():
                family = self.database.get_family_from_handle(family_handle)
                if self.includeMates:
                    if person.get_gender() == gen.lib.Person.MALE:
                        mate_handle = family.get_mother_handle()
                    else:
                        mate_handle = family.get_father_handle()
                    if mate_handle:
                        mate = self.database.get_person_from_handle(mate_handle)
                        self.write_person_info(mate)
                if self.listChildren:
                    self.write_children(family)
                if self.includeEvents:
                    self.write_family_events(family)

    def write_event(self, event_ref):
        text = ""
        event = self.database.get_event_from_handle(event_ref.ref)
        date = DateHandler.get_date(event)
        ph = event.get_place_handle()
        if ph:
            place = self.database.get_place_from_handle(ph).get_title()
        else:
            place = u''

        self.doc.start_paragraph('DDR-MoreDetails')
        evtName = str( event.get_type() )
        if date and place:
            text +=  _('%(event_name)s: %(date)s, %(place)s') % {
                       'event_name' : _(evtName),
                       'date' : date,
                       'place' : place }
        elif date:
            text += _('%(event_name)s: %(date)s') % {
                      'event_name' : _(evtName),
                      'date' : date}
        elif place:
            text += _('%(event_name)s: %(place)s') % {
                      'event_name' : _(evtName),
                      'place' : place }
        else:
            text += _('%(event_name)s: ') % {'event_name' : _(evtName)}

        if event.get_description():
            if text and (date or place):
                text += ". "
            text += event.get_description()

        text += "%s. " % self.endnotes(event)

        self.doc.write_text(text)

        if self.includeAttrs:
            text = ""
            attr_list = event.get_attribute_list()
            attr_list.extend(event_ref.get_attribute_list())
            for attr in attr_list:
                if text:
                    text += "; "
                text += _("%(type)s: %(value)s%(endnotes)s") % {
                    'type'     : attr.get_type(),
                    'value'    : attr.get_value(),
                    'endnotes' : self.endnotes(attr) }
            text = " " + text
            self.doc.write_text(text)

        self.doc.end_paragraph()

        if self.includeNotes:
            # if the event or event reference has a note attached to it,
            # get the text and format it correctly
            notelist = event.get_note_list()
            notelist.extend(event_ref.get_note_list())
            for notehandle in notelist:
                note = self.database.get_note_from_handle(notehandle)
                self.doc.start_paragraph('DDR-MoreDetails')
                self.doc.write_text(note.get())
                self.doc.end_paragraph()

    def write_parents(self, person, firstName):
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.database.get_family_from_handle(family_handle)
            mother_handle = family.get_mother_handle()
            father_handle = family.get_father_handle()
            if mother_handle:
                mother = self.database.get_person_from_handle(mother_handle)
                mother_name = _nd.display_name(mother.get_primary_name())
                mother_mark = ReportUtils.get_person_mark(self.database, mother)
            else:
                mother_name = ""
                mother_mark = ""
            if father_handle:
                father = self.database.get_person_from_handle(father_handle)
                father_name = _nd.display_name(father.get_primary_name())
                father_mark = ReportUtils.get_person_mark(self.database, father)
            else:
                father_name = ""
                father_mark = ""
                
            text = ReportUtils.child_str(person, father_name, mother_name,
                                         bool(person.get_death_ref()),
                                         firstName,self.verbose)
            if text:
                self.doc.write_text(text)
                if father_mark:
                    self.doc.write_text("",father_mark)
                if mother_mark:
                    self.doc.write_text("",mother_mark)

    def write_marriage(self, person):
        """ 
        Output marriage sentence.
        """
        is_first = True
        for family_handle in person.get_family_handle_list():
            family = self.database.get_family_from_handle(family_handle)
            spouse_handle = ReportUtils.find_spouse(person,family)
            spouse = self.database.get_person_from_handle(spouse_handle)
            text = ""
            spouse_mark = ReportUtils.get_person_mark(self.database, spouse)
            
            text = ReportUtils.married_str(self.database,person,family,
                                            self.verbose,
                                            self.endnotes,
                                            self.EMPTY_DATE,self.EMPTY_PLACE,
                                            is_first)
            
            if text:
                self.doc.write_text(text,spouse_mark)
                is_first = False

    def write_children(self, family):
        """ List children.
        """

        if not family.get_child_ref_list():
            return

        mother_handle = family.get_mother_handle()
        if mother_handle:
            mother = self.database.get_person_from_handle(mother_handle)
            mother_name = _nd.display(mother)
        else:
            mother_name = _("unknown")

        father_handle = family.get_father_handle()
        if father_handle:
            father = self.database.get_person_from_handle(father_handle)
            father_name = _nd.display(father)
        else:
            father_name = _("unknown")

        self.doc.start_paragraph("DDR-ChildTitle")
        self.doc.write_text(
                        _("Children of %(mother_name)s and %(father_name)s") % 
                            {'father_name': father_name,
                             'mother_name': mother_name
                             } )
        self.doc.end_paragraph()

        cnt = 1
        for child_ref in family.get_child_ref_list():
            child_handle = child_ref.ref
            child = self.database.get_person_from_handle(child_handle)
            child_name = _nd.display(child)
            child_mark = ReportUtils.get_person_mark(self.database,child)

            if self.childRef and self.prev_gen_handles.get(child_handle):
                value = str(self.prev_gen_handles.get(child_handle))
                child_name += " [%s]" % value

            self.doc.start_paragraph("DDR-ChildList",
                                     ReportUtils.roman(cnt).lower() + ".")
            cnt += 1

            if self.henry.has_key(child_handle):
                self.doc.write_text("%s [%s]. " % (child_name,
                                                   self.henry[child_handle]),
                                    child_mark )
            else:
                self.doc.write_text("%s. " % child_name,child_mark)
                
            self.doc.write_text(ReportUtils.born_str( self.database, child, 0, 
                          self.verbose, self.EMPTY_DATE, self.EMPTY_PLACE))
            self.doc.write_text(ReportUtils.died_str( self.database, child, 0, 
                          self.verbose, self.EMPTY_DATE, self.EMPTY_PLACE))
            self.doc.end_paragraph()

    def write_family_events(self,family):
        
        if not family.get_event_ref_list():
            return

        mother_handle = family.get_mother_handle()
        if mother_handle:
            mother = self.database.get_person_from_handle(mother_handle)
            mother_name = _nd.display(mother)
        else:
            mother_name = _("unknown")

        father_handle = family.get_father_handle()
        if father_handle:
            father = self.database.get_person_from_handle(father_handle)
            father_name = _nd.display(father)
        else:
            father_name = _("unknown")

        first = 1
        for event_ref in family.get_event_ref_list():
            if first:
                self.doc.start_paragraph('DDR-MoreHeader')
                self.doc.write_text(
                    _('More about %(mother_name)s and %(father_name)s:') % { 
                    'mother_name' : mother_name,
                    'father_name' : father_name })
                self.doc.end_paragraph()
                first = 0
            self.write_event(event_ref)

    def write_person_info(self,person):
        name = _nd.display_formal(person)
        
        plist = person.get_media_list()
        if self.addImages and len(plist) > 0:
            photo = plist[0]
            ReportUtils.insert_image(self.database,self.doc,photo)
        
        self.doc.start_paragraph("DDR-Entry")
        # Check birth record
        first = ReportUtils.common_name(person,self.usecall)
        
        if not self.verbose:
            self.write_parents(person, first)

        text = ReportUtils.born_str(self.database,person,first, self.verbose,
                                    self.EMPTY_DATE,self.EMPTY_PLACE)
        if text:
            birth_ref = person.get_birth_ref()
            if birth_ref:
                birth = self.database.get_event_from_handle(birth_ref.ref)
                text = text.rstrip(". ")
                text = text + self.endnotes(birth) + ". "
            self.doc.write_text(text)
            first = 0
    
        age,units = self.calc_age(person)
        text = ReportUtils.died_str(self.database,person,first,self.verbose,
                                    self.EMPTY_DATE,self.EMPTY_PLACE,age,units)
        if text:
            death_ref = person.get_death_ref()
            if death_ref:
                death = self.database.get_event_from_handle(death_ref.ref)
                text = text.rstrip(". ")
                text = text + self.endnotes(death) + ". "
            self.doc.write_text(text)
            first = 0

        text = ReportUtils.buried_str(self.database,person,first,
                                      self.EMPTY_DATE,self.EMPTY_PLACE)
        if text:
            self.doc.write_text(text)

        first = ReportUtils.common_name(person,self.usecall)

        if self.verbose:
            self.write_parents(person, first)
        self.write_marriage(person)
        self.doc.end_paragraph()

        notelist = person.get_note_list()
        if len(notelist) > 0 and self.includeNotes:
            self.doc.start_paragraph("DDR-NoteHeader")
            self.doc.write_text(_("Notes for %s") % name)
            self.doc.end_paragraph()
            for notehandle in notelist:
                note = self.database.get_note_from_handle(notehandle)
                self.doc.write_note(note.get(),note.get_format(),"DDR-Entry")

        first = True
        if self.includeNames:
            for alt_name in person.get_alternate_names():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(_('More about %(person_name)s:') % { 
                        'person_name' : name })
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DDR-MoreDetails')
                atype = str( alt_name.get_type() )
                aname = alt_name.get_regular_name()
                self.doc.write_text(_('%(name_kind)s: %(name)s%(endnotes)s') % {
                    'name_kind' : atype,
                    'name' : aname,
                    'endnotes' : self.endnotes(alt_name),
                    })
                self.doc.end_paragraph()

        if self.includeEvents:
            for event_ref in person.get_primary_event_ref_list():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(_('More about %(person_name)s:') % { 
                        'person_name' : _nd.display(person) })
                    self.doc.end_paragraph()
                    first = 0

                self.write_event(event_ref)
                
        if self.includeAddr:
            for addr in person.get_address_list():
                if first:
                    self.doc.start_paragraph('DDR-MoreHeader')
                    self.doc.write_text(_('More about %(person_name)s:') % { 
                        'person_name' : name })
                    self.doc.end_paragraph()
                    first = False
                self.doc.start_paragraph('DDR-MoreDetails')
                
                text = ReportUtils.get_address_str(addr)
                date = DateHandler.get_date(addr)
                self.doc.write_text(_('Address: '))
                if date:
                    self.doc.write_text( '%s, ' % date )
                self.doc.write_text( text )
                self.doc.write_text( self.endnotes(addr) )
                self.doc.end_paragraph()
                
        if self.includeAttrs:
            attrs = person.get_attribute_list()
            if first and attrs:
                self.doc.start_paragraph('DDR-MoreHeader')
                self.doc.write_text(_('More about %(person_name)s:') % { 
                    'person_name' : name })
                self.doc.end_paragraph()
                first = False

            for attr in attrs:
                self.doc.start_paragraph('DDR-MoreDetails')
                text = _("%(type)s: %(value)s%(endnotes)s") % {
                    'type'     : attr.get_type(),
                    'value'    : attr.get_value(),
                    'endnotes' : self.endnotes(attr) }
                self.doc.write_text( text )
                self.doc.end_paragraph()

    def calc_age(self,ind):
        """
        Calulate age. 
        
        Returns a tuple (age,units) where units is an integer representing
        time units:
            no age info:    0
            years:          1
            months:         2
            days:           3
        """
        if self.calcAgeFlag:
            return ReportUtils.old_calc_age(self.database,ind)
        else:
            return (0,0)

    def endnotes(self,obj):
        if not obj or not self.includeSources:
            return ""
        
        txt = Endnotes.cite_source(self.bibli,obj)
        if txt:
            txt = '<super>' + txt + '</super>'
        return txt

#------------------------------------------------------------------------
#
# DetDescendantOptions
#
#------------------------------------------------------------------------
class DetDescendantOptions(MenuReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self,name,dbstate=None):
        MenuReportOptions.__init__(self,name,dbstate)
        
    def add_menu_options(self,menu,dbstate):
        """
        Add options to the menu for the detailed descendant report.
        """
        category_name = _("Report Options")
        
        pid = PersonOption(_("Center Person"))
        pid.set_help(_("The center person for the report"))
        menu.add_option(category_name, "pid", pid)
        
        gen = NumberOption(_("Generations"),10,1,100)
        gen.set_help(_("The number of generations to include in the report"))
        menu.add_option(category_name,"gen",gen)
        
        pagebbg = BooleanOption(_("Page break between generations"),False)
        pagebbg.set_help(
                     _("Whether to start a new page after each generation."))
        menu.add_option(category_name,"pagebbg",pagebbg)
        
        category_name = _("Content")

        usecall = BooleanOption(_("Use callname for common name"),False)
        usecall.set_help(_("Whether to use the call name as the first name."))
        menu.add_option(category_name,"usecall",usecall)
        
        fulldates = BooleanOption(
                              _("Use full dates instead of only the year"),True)
        fulldates.set_help(_("Whether to use full dates instead of just year."))
        menu.add_option(category_name,"fulldates",fulldates)
        
        listc = BooleanOption(_("List children"),True)
        listc.set_help(_("Whether to list children."))
        menu.add_option(category_name,"listc",listc)
        
        computeage = BooleanOption(_("Compute age"),True)
        computeage.set_help(_("Whether to compute age."))
        menu.add_option(category_name,"computeage",computeage)
        
        omitda = BooleanOption(_("Omit duplicate ancestors"),True)
        omitda.set_help(_("Whether to omit duplicate ancestors."))
        menu.add_option(category_name,"omitda",omitda)
        
        verbose = BooleanOption(_("Use Complete Sentences"),True)
        verbose.set_help(
                 _("Whether to use complete sentences or succinct language."))
        menu.add_option(category_name,"verbose",verbose)

        desref = BooleanOption(_("Add descendant reference in child list"),True)
        desref.set_help(
                    _("Whether to add descendant references in child list."))
        menu.add_option(category_name,"desref",desref)

        category_name = _("Include")
        
        incnotes = BooleanOption(_("Include notes"),True)
        incnotes.set_help(_("Whether to include notes."))
        menu.add_option(category_name,"incnotes",incnotes)

        incattrs = BooleanOption(_("Include attributes"),False)
        incattrs.set_help(_("Whether to include attributes."))
        menu.add_option(category_name,"incattrs",incattrs)
        
        incphotos = BooleanOption(_("Include Photo/Images from Gallery"),False)
        incphotos.set_help(_("Whether to include images."))
        menu.add_option(category_name,"incphotos",incphotos)

        incnames = BooleanOption(_("Include alternative names"),False)
        incnames.set_help(_("Whether to include other names."))
        menu.add_option(category_name,"incnames",incnames)

        incevents = BooleanOption(_("Include events"),False)
        incevents.set_help(_("Whether to include events."))
        menu.add_option(category_name,"incevents",incevents)

        incaddresses = BooleanOption(_("Include addresses"),False)
        incaddresses.set_help(_("Whether to include addresses."))
        menu.add_option(category_name,"incaddresses",incaddresses)

        incsources = BooleanOption(_("Include sources"),False)
        incsources.set_help(_("Whether to include source references."))
        menu.add_option(category_name,"incsources",incsources)

        incmates = BooleanOption(_("Include spouses"),False)
        incmates.set_help(_("Whether to include detailed spouse information."))
        menu.add_option(category_name,"incmates",incmates)

        category_name = _("Missing information")        

        repplace = BooleanOption(_("Replace missing places with ______"),False)
        repplace.set_help(_("Whether to replace missing Places with blanks."))
        menu.add_option(category_name,"repplace",repplace)

        repdate = BooleanOption(_("Replace missing dates with ______"),False)
        repdate.set_help(_("Whether to replace missing Dates with blanks."))
        menu.add_option(category_name,"repdate",repdate)

    def make_default_style(self,default_style):
        """Make the default output style for the Detailed Ancestral Report"""
        font = BaseDoc.FontStyle()
        font.set(face=BaseDoc.FONT_SANS_SERIF,size=16,bold=1)
        para = BaseDoc.ParagraphStyle()
        para.set_font(font)
        para.set_header_level(1)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_alignment(BaseDoc.PARA_ALIGN_CENTER)
        para.set_description(_('The style used for the title of the page.'))
        default_style.add_paragraph_style("DDR-Title",para)

        font = BaseDoc.FontStyle()
        font.set(face=BaseDoc.FONT_SANS_SERIF,size=14,italic=1)
        para = BaseDoc.ParagraphStyle()
        para.set_font(font)
        para.set_header_level(2)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the generation header.'))
        default_style.add_paragraph_style("DDR-Generation",para)

        font = BaseDoc.FontStyle()
        font.set(face=BaseDoc.FONT_SANS_SERIF,size=10,italic=0, bold=1)
        para = BaseDoc.ParagraphStyle()
        para.set_font(font)
        para.set_left_margin(1.5)   # in centimeters
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the children list title.'))
        default_style.add_paragraph_style("DDR-ChildTitle",para)

        font = BaseDoc.FontStyle()
        font.set(size=10)
        para = BaseDoc.ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=-0.75,lmargin=2.25)
        para.set_top_margin(0.125)
        para.set_bottom_margin(0.125)
        para.set_description(_('The style used for the children list.'))
        default_style.add_paragraph_style("DDR-ChildList",para)

        font = BaseDoc.FontStyle()
        font.set(face=BaseDoc.FONT_SANS_SERIF,size=10,italic=0, bold=1)
        para = BaseDoc.ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0,lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        default_style.add_paragraph_style("DDR-NoteHeader",para)

        para = BaseDoc.ParagraphStyle()
        para.set(lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("DDR-Entry",para)

        para = BaseDoc.ParagraphStyle()
        para.set(first_indent=-1.5,lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)        
        para.set_description(_('The style used for the first personal entry.'))
        default_style.add_paragraph_style("DDR-First-Entry",para)

        font = BaseDoc.FontStyle()
        font.set(size=10,face=BaseDoc.FONT_SANS_SERIF,bold=1)
        para = BaseDoc.ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0,lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for the More About header.'))
        default_style.add_paragraph_style("DDR-MoreHeader",para)

        font = BaseDoc.FontStyle()
        font.set(face=BaseDoc.FONT_SERIF,size=10)
        para = BaseDoc.ParagraphStyle()
        para.set_font(font)
        para.set(first_indent=0.0,lmargin=1.5)
        para.set_top_margin(0.25)
        para.set_bottom_margin(0.25)
        para.set_description(_('The style used for additional detail data.'))
        default_style.add_paragraph_style("DDR-MoreDetails",para)

        Endnotes.add_endnote_styles(default_style)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
register_report(
    name = 'det_descendant_report',
    category = CATEGORY_TEXT,
    report_class = DetDescendantReport,
    options_class = DetDescendantOptions,
    modes = MODE_GUI | MODE_BKI | MODE_CLI,
    translated_name = _("Detailed Descendant Report"),
    status=(_("Beta")),
    description= _("Produces a detailed descendant report"),
    author_name="Bruce DeGrasse",
    author_email="bdegrasse1@attbi.com"
    )
