
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000 Bruce J. DeGrasse
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

"Generate files/Detailed Ancestral Report"

import RelLib
import const
import os
import re
import sort
import string
import utils
import intl

_ = intl.gettext

from TextDoc import *
from StyleEditor import *

import FindDoc

import gtk
import gnome.ui
import libglade

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
active_person = None
db = None
styles = StyleSheet()
style_sheet_list = None

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class DetAncestorReport:

    gen = {
        1 : _("First"),
        2 : _("Second"),
        3 : _("Third"),
        4 : _("Fourth"),
        5 : _("Fifth"),
        6 : _("Sixth"),
        7 : _("Seventh"),
        8 : _("Eighth"),
        9 : _("Ninth"),
        10: _("Tenth"),
        11: _("Eleventh"),
        12: _("Twelfth"),
        13: _("Thirteenth"),
        14: _("Fourteenth"),
        15: _("Fifteenth"),
        16: _("Sixteenth"),
        17: _("Seventeenth"),
        18: _("Eightteenth"),
        19: _("Nineteenth"),
        20: _("Twentieth"),
        21: _("Twenty-first"),
        22: _("Twenty-second"),
        23: _("Twenty-third"),
        24: _("Twenty-fourth"),
        25: _("Twenty-fifth"),
        26: _("Twenty-sixth"),
        27: _("Twenty-seventh"),
        28: _("Twenty-eighth"),
        29: _("Twenty-ninth")
        }

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def __init__(self,database,person,output,max,pgbrk,doc):
        self.map = {}
        self.database = database
        self.start = person
        self.max_generations = max
        self.pgbrk = pgbrk
        self.doc = doc

        try:
            self.doc.open(output)
        except IOError,msg:
            gnome.ui.GnomeErrorDialog(_("Could not open %s") % output + "\n" + msg)

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def filter(self,person,index):
        if person == None or index >= 2**self.max_generations:
            return
        self.map[index] = person

        family = person.getMainFamily()
        if family != None:
            self.filter(family.getFather(),index*2)
            self.filter(family.getMother(),(index*2)+1)


    def write_children(self, family):
        """ List children """

        #print "family: ", family.__dict__
        num_children= len(family.getChildList())
        #print "Children= ", len(family.getChildList())
        if num_children > 0:
            self.doc.start_paragraph("ChildTitle")
            mother= family.getMother().getPrimaryName().getRegularName()
            father= family.getFather().getPrimaryName().getRegularName()
            if num_children == 1:
                self.doc.write_text(_("Child of %s and %s is:") % (mother, father))
            else: self.doc.write_text(_("Children of %s and %s are:") % (mother, father))
            self.doc.end_paragraph()

            for child in family.getChildList():
                self.doc.start_paragraph("ChildList")
                t= child.getPrimaryName().getRegularName()
                #print "getBirth()", child.getBirth().__dict__
                if child.getBirth().getDate() != "" and \
                        child.getBirth().getPlaceName() != "":
                    #print child.getBirth().getPlace().__dict__
                    t= t+ _(" Born: ")+child.getBirth().getDate() + \
                        " "+child.getBirth().getPlaceName()
                #print "getDeath()", child.getDeath().__dict__
                if child.getDeath().getPlace() != None:
                #   print child.getDeath().getPlace().__dict__
                    if child.getDeath().getDate() != "" or \
                            child.getDeath().getPlaceName() != "":
                        t= t+ _(" Died: ")+child.getDeath().getDate() + \
                            " "+child.getDeath().getPlaceName()
                self.doc.write_text(_(t))
                self.doc.end_paragraph()


    def write_person(self, key, rptOptions):
        """Output birth, death, parentage, marriage and notes information """

        self.doc.start_paragraph("Entry","%s." % str(key))
        person = self.map[key]
        name = person.getPrimaryName().getRegularName()

        if rptOptions.firstName == reportOptions.Yes:
            firstName= person.getPrimaryName().getFirstName()
        elif person.getGender() == RelLib.Person.male:
            firstName= _("He")
        else:
            firstName= _("She")

        self.doc.start_bold()
        self.doc.write_text(name)
        self.doc.end_bold()

        # Check birth record
        birth = person.getBirth()
        if birth:
            self.write_birth(person, rptOptions)
        self.write_death(person, firstName, rptOptions)
        self.write_parents(person, firstName)
        self.write_marriage(person, rptOptions)
        self.doc.end_paragraph()

        if key == 1:  self.write_mate(person, rptOptions)

        if person.getNote() != "" and rptOptions.includeNotes == reportOptions.Yes:
            self.doc.start_paragraph("Entry")
            self.doc.write_text(_("Notes for %s" % name))
            self.doc.end_paragraph()
            self.doc.start_paragraph("Entry")
            self.doc.write_text(person.getNote())
            self.doc.end_paragraph()

    def write_birth(self, person, rptOptions):
        # Check birth record
        #   Statement formats name precedes this
        #       was born on DATE.
        #       was born on ________.
        #       was born on Date in Place.
        #       was born on ________ in PLACE.
        #       was born in ____________.
        #       was born in the year YEAR.
        #       was born in PLACE.
        #       was born in ____________.
        #       .
        birth = person.getBirth()
        if birth:
            date = birth.getDateObj().get_start_date()
            if birth.getPlaceName() != "":
                place = birth.getPlaceName()
                if place[-1:] == '.':
                    place = place[:-1]
            elif rptOptions.blankDate == reportOptions.Yes:
                place= "______________"
            else: place= ""

            if date.getDate() != "":
                if date.getDayValid() and date.getMonthValid() and \
                        rptOptions.fullDate == reportOptions.Yes:
                    if place != "":
                        self.doc.write_text(_(" was born on %s in %s.") % (date.getDate(), place))
                    else:
                        self.doc.write_text(_(" was born on %s.") % date.getDate())
                elif place != "":
                    self.doc.write_text(_(" was born in the year %s in %s.") % \
                              (date.getYear(), place))
                else:
                    self.doc.write_text(_(" was born in the year %s.") % date.getYear())
            elif place != "":
                self.doc.write_text(_(" in %s.") % place)
            else:
                self.doc.write_text(_("."))

            return
        self.doc.write_text(_("."))
        return

    def write_death(self, person, firstName, rptOptions):
        t= ""
        death = person.getDeath()
        #print "death=", death, death.__dict__
        if death != None:
            date = death.getDateObj().get_start_date()
            place = death.getPlaceName()
            #print "date=", date.getDate(), "place=", place, "day= ", date.getDay(), \
            #            "month= ", date.getMonth(), "year= ", date.getYear()
            if place[-1:] == '.':
                place = place[:-1]
            elif place == "" and rptOptions.blankPlace == reportOptions.Yes:
                place= "_____________"

            if date.getDate() != "":
                if date.getDay() > 0 and date.getMonth() > 0 and \
                            rptOptions.fullDate == reportOptions.Yes:
                    fulldate= date.getDate()
                elif date.getMonth() > 0 and rptOptions.fullDate == reportOptions.Yes:
                    fulldate= "%s %s" % (date.getMonth(), date.getYear())
                else: fulldate= ""
            elif rptOptions.blankDate == reportOptions.Yes:
                fulldate= "_____________"
            else: fulldate= ""

            if fulldate != "":
                if place != "":
                    t= _("  %s died on %s in %s") % (firstName, fulldate, place)
                else: t= _("  %s died on %s") % (firstName, fulldate)
            elif date.getYear() > 0:
                if place != "":
                    t= _("  %s died in %s in %s") % (firstName, date.getYear(), place)
                else: t= _("  %s died in %s") % (firstName, date.getYear())
            elif place != "":
                t= _("  %s died in %s") % (firstName, place)


            if rptOptions.calcAgeFlag == reportOptions.Yes:
                t= t + rptOptions.calcAge(person)

            if t != "":
                self.doc.write_text(t+".")
                t= ""

        famList= person.getFamilyList()
        if len(famList) > 0:
            for fam in famList:
                #print "fam event=", fam.__dict__
                buried= None
                if buried:
                    date = buried.getDateObj().get_start_date()
                    place = buried.getPlaceName()
                    if place[-1:] == '.':
                        place = place[:-1]
                    fulldate= ""
                    if date.getDate() != "":
                        if date.getDayValid() and date.getMonthValid() and \
                                        rptOptions.fullDate == reportOptions.Yes:
                            fulldate= date.getDate()
                    elif rptOptions.blankDate == reportOptions.Yes:
                            fulldate= "___________"

                    if fulldate != "" and place != "":
                        t= _("  And %s was buried on %s in %s.") % (firstName, fulldate, place)
                    elif fulldate != "" and place == "":
                        t= _("  And %s was buried on %s.") % (firstName, fulldate)
                    elif fulldate == "" and place != "":
                        t= _("  And %s was buried in %s.") % (firstName, place)

                if t != "":
                    self.doc.write_text(t)
                    t= ""

    def write_parents(self, person, firstName):
        ext_family= person.getMainFamily()
        if ext_family != None:
            if ext_family.getFather() != None:
                father= ext_family.getFather().getPrimaryName().getRegularName()
            else: father= ""
            if ext_family.getMother() != None:
                mother= ext_family.getMother().getPrimaryName().getRegularName()
            else: mother= ""

            if father != "" or mother != "":
                if person.getGender() == RelLib.Person.male:
                    if father != "":
                        if mother != "":
                            self.doc.write_text(_(" %s was the son of %s and %s." % \
                                (firstName, father, mother)))
                        else:
                            self.doc.write_text(_(" %s was the son of %s." % \
                                (firstName, father)))
                    else:
                        self.doc.write_text(_(" %s was the son of %s." % \
                                (firstName, mother)))
                else:
                    if father != "":
                        if mother != "":
                            self.doc.write_text(_(" %s was the daughter of %s and %s." % \
                                (firstName, father, mother)))
                        else:
                            self.doc.write_text(_(" %s was the daughter of %s." % \
                                (firstName, father)))
                    else:
                        self.doc.write_text(_(" %s was the daughter of %s." % \
                                (firstName, mother)))


    def write_marriage(self, person, rptOptions):
        famList= person.getFamilyList()
        #print "Marriage: len of famList=", len(famList)
        if len(famList) > 0:
            for fam in famList:
                #print "Marriage:fam", fam.__dict__
                if person.getGender() == RelLib.Person.male:
                    if fam.getMother() != None:
                        spouse= fam.getMother().getPrimaryName().getRegularName()
                        heshe= _("He")
                else:
                    heshe= _("She")
                    if fam.getFather() != None:
                        spouse= fam.getFather().getPrimaryName().getRegularName()

                marriage= fam.getMarriage()
                if marriage != None:
                    if marriage.getPlace() != None and \
                            marriage.getPlaceName() != "":
                        place= marriage.getPlaceName()
                    elif rptOptions.blankPlace == reportOptions.Yes:
                        place= "____________"
                    else: place= ""

                    date= marriage.getDateObj()
                    fulldate= ""
                    if date != None:
                        if date.getYearValid():
                            if date.getDayValid() and date.getMonthValid() and \
                                    rptOptions.fullDate == reportOptions.Yes:
                                fulldate= date.getDate()
                            elif rptOptions.blankDate == reportOptions.Yes:
                                fulldate= "__________"

                    if spouse != "":
                        if fulldate == "" and place == "":
                            t= _("  %s married %s." % (heshe, spouse))
                        elif fulldate == "" and place != "":
                            t= _("  %s married %s in %s." % (heshe, spouse, place))
                        elif fulldate != "" and place == "":
                            t= _("  %s married %s on %s" % (heshe, spouse, fulldate))
                        else: t= _("  %s married %s on %s in %s." % \
                                (heshe, spouse, fulldate, place))
                    else:
                        if fulldate == "" and place == "":
                            t= _("  %s married.")
                        elif fulldate == "" and place != "":
                            t= _("  %s married in %s." % (heshe, place))
                        elif fulldate != "" and place == "":
                            t= _("  %s married on %s" % (heshe, fulldate))
                        else: t= _("  %s married on %s in %s." % \
                                (heshe, fulldate, place))

                    self.doc.write_text(t)

    def write_mate(self, mate, rptOptions):
        """Output birth, death, parentage, marriage and notes information """

        famList= mate.getFamilyList()
        #print "len of famList=", len(famList)
        if len(famList) > 0:
            for fam in famList:
                person= ""
                if mate.getGender() == RelLib.Person.male:
                    if fam.getMother() != None:
                        ind= fam.getMother()
                        person= fam.getMother().getPrimaryName().getRegularName()
                        firstName= fam.getMother().getPrimaryName().getFirstName()
                        heshe= _("He")
                else:
                    heshe= _("She")
                    if fam.getFather() != None:
                        ind= fam.getFather()
                        person= fam.getFather().getPrimaryName().getRegularName()
                        firstName= fam.getFather().getPrimaryName().getFirstName()

                if person != "":
                    self.doc.start_paragraph("Entry")
                    if rptOptions.firstName == reportOptions.No:
                        firstName= heshe

                    self.doc.write_text(person)

                    self.write_birth(ind, rptOptions)

                    self.write_death(ind, firstName, rptOptions)

                    self.write_parents(ind, firstName)

                    self.doc.end_paragraph()

                    if rptOptions.listChildren == reportOptions.Yes:
                        self.write_children(fam)

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def write_report(self):

        self.filter(self.start,1)
        rptOpt= reportOptions()

        name = self.start.getPrimaryName().getRegularName()
        self.doc.start_paragraph("Title")
        title = _("Detailed Ancestral Report for %s") % name
        self.doc.write_text(title)
        self.doc.end_paragraph()

        keys = self.map.keys()
        keys.sort()
        generation = 0
        need_header = 1

        for key in keys :
            if generation == 0 or key >= 2**generation:
                if self.pgbrk and generation > 0:
                    self.doc.page_break()
                self.doc.start_paragraph("Generation")
                t = _("%s Generation") % DetAncestorReport.gen[generation+1]
                self.doc.write_text(t)
                self.doc.end_paragraph()
                generation = generation + 1

            self.write_person(key, rptOpt)

            person = self.map[key]
            if person.getGender() == RelLib.Person.female and  \
                     rptOpt.listChildren == reportOptions.Yes and  \
                     len(person.getFamilyList()) > 0:
                family= person.getFamilyList()[0]
                self.write_children(family)

        self.doc.close()

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def report(database,person):
    import PaperMenu

    global active_person
    global topDialog
    global glade_file
    global db
    global style_sheet_list

    active_person = person
    db = database

    base = os.path.dirname(__file__)
    glade_file = base + os.sep + "ancestorreport.glade"
    topDialog = libglade.GladeXML(glade_file,"dialog1")

    name = person.getPrimaryName().getRegularName()

    PaperMenu.make_paper_menu(topDialog.get_widget("papersize"))
    PaperMenu.make_orientation_menu(topDialog.get_widget("orientation"))
    FindDoc.get_text_doc_menu(topDialog.get_widget("format"),0,option_switch)

    styles.clear()
    font = FontStyle()
    font.set(face=FONT_SANS_SERIF,size=16,bold=1)
    para = ParagraphStyle()
    para.set_font(font)
    para.set_header_level(1)
    para.set(pad=0.5)
    styles.add_style("Title",para)

    font = FontStyle()
    font.set(face=FONT_SANS_SERIF,size=14,italic=1)
    para = ParagraphStyle()
    para.set_font(font)
    para.set_header_level(2)
    para.set(pad=0.5)
    styles.add_style("Generation",para)

    font = FontStyle()
    font.set(face=FONT_SANS_SERIF,size=12,italic=1)
    para = ParagraphStyle()
    para.set_font(font)
    para.set_header_level(3)
    para.set_left_margin(1.0)   # in centimeters
    para.set(pad=0.5)
    styles.add_style("ChildTitle",para)

    para = ParagraphStyle()
    para.set(first_indent=1.0,lmargin=0.0,pad=0.25)
    styles.add_style("ChildList",para)

    para = ParagraphStyle()
    para.set(first_indent=-1.0,lmargin=1.0,pad=0.25)
    styles.add_style("Entry",para)

    table = TableStyle()
    table.set_width(1000)
    table.set_columns(3)
    table.set_column_width(1,"30%")
    #add_table_style("Images",table)

    style_sheet_list = StyleSheetList("det_ancestor_report.xml",styles)
    build_menu(None)

    topDialog.get_widget("labelTitle").set_text(_("Detailed Ancestral Report for %s") % name)
    topDialog.signal_autoconnect({
        "destroy_passed_object" : utils.destroy_passed_object,
        "on_style_edit_clicked" : on_style_edit_clicked,
        "on_save_clicked" : on_save_clicked
        })

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def build_menu(object):
    menu = topDialog.get_widget("style_menu")

    myMenu = gtk.GtkMenu()
    for style in style_sheet_list.get_style_names():
        menuitem = gtk.GtkMenuItem(style)
        menuitem.set_data("d",style_sheet_list.get_style_sheet(style))
        menuitem.show()
        myMenu.append(menuitem)
    menu.set_menu(myMenu)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def option_switch(obj):
    val = obj.get_data("paper")
    st = obj.get_data("styles")
    notebook = topDialog.get_widget("option_notebook")
    if val == 1:
        notebook.set_page(0)
    else:
        notebook.set_page(1)
    topDialog.get_widget("style_frame").set_sensitive(st)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def on_style_edit_clicked(obj):
    StyleListDisplay(style_sheet_list,build_menu,None)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def on_save_clicked(obj):
    global active_person
    global db

    outputName = topDialog.get_widget("fileentry1").get_full_path(0)
    if not outputName:
        return

    max_gen = topDialog.get_widget("generations").get_value_as_int()
    pgbrk = topDialog.get_widget("pagebreak").get_active()
    template = topDialog.get_widget("htmltemplate").get_full_path(0)
    paper_obj = topDialog.get_widget("papersize").get_menu().get_active()
    paper = paper_obj.get_data("i")
    orien_obj = topDialog.get_widget("orientation").get_menu().get_active()
    orien = orien_obj.get_data("i")

    item = topDialog.get_widget("format").get_menu().get_active()
    format = item.get_data("name")

    styles = topDialog.get_widget("style_menu").get_menu().get_active().get_data("d")

    doc = FindDoc.make_text_doc(styles,format,paper,orien,template)

    MyReport = DetAncestorReport(db,active_person,outputName,max_gen,pgbrk,doc)
    MyReport.write_report()

    utils.destroy_passed_object(obj)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def get_xpm_image():
    return [
        "48 48 4 1",
        " 	c None",
        ".	c #FFFFFF",
        "+	c #C0C0C0",
        "@	c #000000",
        "                                                ",
        "                                                ",
        "                                                ",
        "       ++++++++++++++++++++++++++++++++++       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +...@@@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +...@@@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +.....@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +........@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +................................+       ",
"       +.....@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +........@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +.....@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +.........@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +.....@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +.........@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +.........@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +.....@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +.........@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +.....@@@@@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +.........@@@@@@@@@@@@@@@@@@@@...+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       +................................+       ",
        "       ++++++++++++++++++++++++++++++++++       ",
        "                                                ",
        "                                                ",
        "                                                "]
#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
from Plugins import register_report

register_report(
    report,
    _("Detailed Ancestral Report"),
    category=_("Generate Files"),
    description= _("Produces a detailed ancestral report"),
    xpm= get_xpm_image()
    )


#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class reportOptions:
    Yes=1
    No= 0
    Left= 2
    Right= 3

    def __init__(self):
        ### Initialize report options###

        #Use first name in place of he or she in text
        self.firstName= reportOptions.Yes

        #Use year only, not full date/month
        self.fullDate= reportOptions.Yes

        #Do not list children
        self.listChildren= reportOptions.Yes

        #Add stepchildren to the list of children
        #self.addStepChildren= reportOptions.Yes

        #Print notes
        self.includeNotes= reportOptions.Yes

        #Selectively print notes (omit private information)
        #self.omitPrivInfo= reportOptions.No

        #generate header for each page, specify text
        #self.noHeader= reportOptions.Yes

        #Inculde reference notes
        #self.noRefNotes= reportOptions.Yes

        #Include source notes
        #self.noSourceNotes= reportOptions.Yes

        #Replace missing Place with ___________
        self.blankPlace= reportOptions.No

        #Replace missing dates with __________
        self.blankDate= reportOptions.No

        #Omit country code
        #self.noCountryInfo= reportOptions.No

        #Put title before or after name (Dr., Lt., etc.)
        #self.titleAfter= reportOptions.Yes

        #Add "Died at the age of NN" in text
        self.calcAgeFlag= reportOptions.Yes

        #Add Photos and Images to report
        self.addImages= reportOptions.Yes

        #Omit sensitive information such as birth, christening, marriage
        #   for living after XXXXX date.

        #Add photos/images
        #self.images.append(key, kname, align, width, height)
        #self.images= []
        #self.images.append(1, "TMDeG_72.pjg", Right, 144, 205)

    #def addImages(self, key= 0, fname= "", align= Right, Width= none, height= None):
        #if key == 0 or fname == "" or (align != Left and align != Right):
            #print Invalid Image Specification: ke= %s, fname= %s width %s % key, fname, align
        #else:
            #self.images.append(key, fname, align, width, height)

    def calcAge(self, ind):
        ### Calulate age ###

        birth= ind.getBirth().getDateObj().get_start_date()
        death= ind.getDeath().getDateObj().get_start_date()
        #print "birth=", birth.__dict__
        #print "death=", death.__dict__
        self.t= ""
        if birth.getYearValid() and death.getYearValid():
            self.age= death.getYear() - birth.getYear()
            self.units= "year"
            if birth.getMonthValid() and death.getMonthValid():
                if birth.getMonth() > death.getMonth():
                    self.age= self.age -1
                if birth.getDayValid() and death.getDayValid():
                    if birth.getMonth() == death.getMonth() and birth.getDay() > death.getDay():
                        self.age= self.age -1
                        self.units= "month"
                    if self.age == 0:
                        self.age= death.getMonth() - birth.getMonth()   # calc age in months
                        if birth.getDay() > death.getDay():
                            self.age= self.age - 1
                        if self.age == 0:
                            self.age= death.getDay() + 31 - birth.getDay() # calc age in days
                            self.units= "day"
            self.t= _(" at the age of %d %s") % (self.age, self.units)
            if self.age > 1:  self.t= self.t + "s"
        return self.t
