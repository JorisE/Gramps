#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2003 Bruce J. DeGrasse
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

"Generate files/Detailed Descendant Report"

import RelLib
import os
import sort
import Errors
import string

from QuestionDialog import ErrorDialog
from gettext import gettext as _

import Report
import BaseDoc

import gtk
import gnome.ui

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class DetDescendantReport(Report.Report):

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def __init__(self,database,person,max,pgbrk,rptOpt,doc,output,newpage=0):
        self.map = {}
        self.database = database
        self.start = person
        self.max_generations = max
        self.pgbrk = pgbrk
        self.rptOpt = rptOpt
        self.doc = doc
        self.newpage = newpage
        self.genIDs = {}
        self.prevGenIDs= {}
        self.genKeys = []

        if output:
            self.standalone = 1
            try:
                self.doc.open(output)
            except IOError,msg:
                ErrorDialog(_("Could not open %s") % output + "\n" + msg)
        else:
            self.standalone = 0

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def apply_filter(self,person,index,cur_gen=1):
        if person == None or cur_gen > self.max_generations:
            return 
        self.map[index] = person

        if len(self.genKeys) < cur_gen:
            self.genKeys.append([index])
        else: 
            self.genKeys[cur_gen-1].append(index)

        for family in person.getFamilyList():
            for child in family.getChildList():
                ix = max(self.map.keys())
                self.apply_filter(child, ix+1, cur_gen+1)

    def write_children(self, family, rptOptions):
        """ List children
            Statement formats:
                Child of MOTHER and FATHER is:
                Children of MOTHER and FATHER are:

                NAME Born: DATE PLACE Died: DATE PLACE          f
                NAME Born: DATE PLACE Died: DATE                e
                NAME Born: DATE PLACE Died: PLACE               d
                NAME Born: DATE PLACE                           c
                NAME Born: DATE Died: DATE PLACE                b
                NAME Born: DATE Died: DATE                      a
                NAME Born: DATE Died: PLACE                     9
                NAME Born: DATE                                 8
                NAME Born: PLACE Died: DATE PLACE               7
                NAME Born: PLACE Died: DATE                     6
                NAME Born: PLACE Died: PLACE                    5
                NAME Born: PLACE                                4
                NAME Died: DATE                                 2
                NAME Died: DATE PLACE                           3
                NAME Died: PLACE                                1
                NAME                                            0
        """

        num_children= len(family.getChildList())
        if num_children > 0:
            self.doc.start_paragraph("DDR-ChildTitle")
            if family.getMother() != None:
                mother= family.getMother().getPrimaryName().getRegularName()
            else: mother= "unknown"
            if family.getFather() != None:
                father= family.getFather().getPrimaryName().getRegularName()
            else: father= "unknown"
            self.doc.start_bold()
            if num_children == 1:
                self.doc.write_text(_("Child of %s and %s is:") % (mother, father))
            else: self.doc.write_text(_("Children of %s and %s are:") % (mother, father))
            self.doc.end_bold()
            self.doc.end_paragraph()

            for child in family.getChildList():
                self.doc.start_paragraph("DDR-ChildList")
                name= child.getPrimaryName().getRegularName()
                birth= child.getBirth()
                death= child.getDeath()
                if rptOptions.childRef == reportOptions.Yes:
                    childID= child.getId()
                    if self.prevGenIDs.get(childID) != None:
                        name= "[" + str(self.prevGenIDs.get(childID)) + "] "+ name
                #print "Child List: <", birth.getDate(), ">", birth.getPlaceName()
                if birth.getDate() != "":
                    #print birth.getPlaceName()
                    if birth.getPlaceName() != "":
                        if death.getDate() != "":
                            if death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Born: %s %s Died: %s %s") % \
                                    (name, birth.getDate(), birth.getPlaceName(),
                                     death.getDate(), death.getPlaceName()))  # f
                            else:
                                self.doc.write_text(_("- %s Born: %s %s Died: %s") % \
                                    (name, birth.getDate(), birth.getPlaceName(),
                                     death.getDate()))                    # e
                        elif death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Born: %s %s Died: %s") % \
                                    (name, birth.getDate(), birth.getPlaceName(),
                                     death.getPlaceName()))                   # d
                        else:   self.doc.write_text(_("- %s Born: %s %s") % \
                                    (name, birth.getDate(), birth.getPlaceName())) # c
                    else:
                        if death.getDate() != "":
                            if death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Born: %s Died: %s %s") % \
                                    (name, birth.getDate(), death.getDate(), \
                                     death.getPlaceName()))                    # b
                            else:
                                self.doc.write_text(_("- %s Born: %s Died: %s") % \
                                    (name, birth.getDate(), death.getDate())) # a
                        elif death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Born: %s Died: %s") % \
                                    (name, birth.getDate(), death.getPlaceName())) # 9
                        else:   self.doc.write_text(_("- %s Born: %s") % \
                                    (name, birth.getDate()))               # 8
                else:
                    if birth.getPlaceName() != "":
                        if death.getDate() != "":
                            if death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Born: %s Died: %s %s") % \
                                    (name, birth.getPlaceName(),                  \
                                     death.getDate(), death.getPlaceName()))  # 7
                            else:
                                self.doc.write_text(_("- %s Born: %s Died: %s") % \
                                    (name, birth.getPlaceName(), death.getDate())) # 6
                        elif death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Born: %s Died: %s") % \
                                    (name, birth.getPlaceName(), death.getPlaceName())) # 5
                        else:   self.doc.write_text(_("- %s Born: %s") % \
                                    (name, birth.getPlaceName()))             # 4
                    else:
                        if death.getDate() != "":
                            if death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Died: %s %s") % \
                                    (name, death.getDate(), death.getPlaceName())) # 3
                            else:
                                self.doc.write_text(_("- %s Died: %s") % \
                                    (name, death.getDate()))               # 2
                        elif death.getPlaceName() != "":
                                self.doc.write_text(_("- %s Died: %s") % \
                                    (name, death.getPlaceName())) # 1
                        else:   self.doc.write_text(_("- %s") % name)          # 0

                self.doc.end_paragraph()

    def write_person(self, key, rptOptions):
        """Output birth, death, parentage, marriage and notes information """

        self.doc.start_paragraph("DDR-Entry","%s." % str(key))

        person = self.map[key]
        if rptOptions.addImages == reportOptions.Yes:
			self.insert_images(person, rptOptions.imageAttrTag)

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

        if rptOptions.dupPersons == reportOptions.Yes:
            # Check for duplicate record (result of distant cousins marrying)
            keys = self.map.keys()
            keys.sort()
            for dkey in keys:
                if dkey >= key: break
                if self.map[key].getId() == self.map[dkey].getId():
                    self.doc.write_text(_(" is the same person as [%s].") % str(dkey))
                    self.doc.end_paragraph()
                    return 1	# Duplicate person

        # Check birth record
        birth = person.getBirth()
        if birth:
            self.write_birth(person, rptOptions)
        self.write_death(person, firstName, rptOptions)
        self.write_parents(person, firstName)
        self.write_marriage(person, rptOptions)
        self.doc.end_paragraph()

        self.write_mate(person, rptOptions)

        if person.getNote() != "" and rptOptions.includeNotes == reportOptions.Yes:
            self.doc.start_paragraph("DDR-NoteHeader")
            self.doc.start_bold()
            self.doc.write_text(_("Notes for %s" % name))
            self.doc.end_bold()
            self.doc.end_paragraph()
            self.doc.start_paragraph("DDR-Entry")
            self.doc.write_text(person.getNote())
            self.doc.end_paragraph()

        return 0		# Not duplicate person

    def write_birth(self, person, rptOptions):
        """ Check birth record
            Statement formats name precedes this
               was born on DATE.
               was born on ________.
               was born on Date in Place.
               was born on ________ in PLACE.
               was born in ____________.
               was born in the year YEAR.
               was born in PLACE.
               was born in ____________.
        """

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
                self.doc.write_text(_(" was born in %s.") % place)
            else:
                self.doc.write_text(_("."))

            return
        self.doc.write_text(_("."))
        return

    def write_death(self, person, firstName, rptOptions):
        """ Write obit sentence
        Statement format: DPHRASE APHRASE BPHRASE
        DPHRASE=
            FIRSTNAME died on FULLDATE in PLACE
            FIRSTNAME died on FULLDATE
            FIRSTNAME died in PLACE
            FIRSTNAME died on FULLDATE in PLACE
            FIRSTNAME died in YEAR in PLACE
            FIRSTNAME died in YEAR

        APHRASE=           see calcAge
            at the age of NUMBER UNIT(S)
            null

            where
            UNIT= year | month | day
            UNITS= years | months | days

        BPHRASE=
            , and was buried on FULLDATE in PLACE.
            , and was buried on FULLDATE.
            , and was buried in PLACE.
            .
        """
        t= ""
        death = person.getDeath()
        if death != None:
            date = death.getDateObj().get_start_date()
            place = death.getPlaceName()
            if place[-1:] == '.':
                place = place[:-1]
            elif place == "" and rptOptions.blankPlace == reportOptions.Yes:
                place= "_____________"

            if date.getDate() != "":
                if date.getDay() and date.getMonth() and \
                            rptOptions.fullDate == reportOptions.Yes:
                    fulldate= date.getDate()
                elif date.getMonth() and rptOptions.fullDate == reportOptions.Yes:
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
                self.doc.write_text(t)
            else: return

        t= ""
        famList= person.getFamilyList()
        if len(famList) > 0:
            for fam in famList:
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
        else: self.doc.write_text(".")

    def write_parents(self, person, firstName):
        """ Ouptut parents sentence
        Statement format:

        FIRSTNAME was the son of FATHER and MOTHER.
        FIRSTNAME was the son of FATHER.
        FIRSTNAME was the son of MOTHER.
        FIRSTNAME was the daughter of FATHER and MOTHER.
        FIRSTNAME was the daughter of FATHER.
        FIRSTNAME was the daughter of MOTHER.
        """
        ext_family= person.getMainParents()
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
                            self.doc.write_text(_(" %s was the son of %s and %s.") % \
                                (firstName, father, mother))
                        else:
                            self.doc.write_text(_(" %s was the son of %s.") % \
                                (firstName, father))
                    else:
                        self.doc.write_text(_(" %s was the son of %s.") % \
                                (firstName, mother))
                else:
                    if father != "":
                        if mother != "":
                            self.doc.write_text(_(" %s was the daughter of %s and %s.") % \
                                (firstName, father, mother))
                        else:
                            self.doc.write_text(_(" %s was the daughter of %s.") % \
                                (firstName, father))
                    else:
                        self.doc.write_text(_(" %s was the daughter of %s.") % \
                                (firstName, mother))


    def write_marriage(self, person, rptOptions):
        """ Output marriage sentence
        HE/SHE married SPOUSE on FULLDATE in PLACE.
        HE/SHE married SPOUSE on FULLDATE.
        HE/SHE married SPOUSE in PLACE.
        HE/SHE married SPOUSE
        """
        famList= person.getFamilyList()
        if len(famList) > 0:
            fam_num= 0
            for fam in famList:
                fam_num= fam_num + 1
                spouse= ""
                if person.getGender() == RelLib.Person.male:
                    if fam.getMother() != None:
                        spouse= fam.getMother().getPrimaryName().getRegularName()
                    if fam_num == 1:
                        heshe= _("He")
                    elif fam_num < len(famList):
                        heshe= _(",")
                    else: heshe= _("and he")
                else:
                    if fam_num == 1:
                        heshe= _("She")
                    elif fam_num < len(famList):
                        heshe= _(",")
                    else: heshe= _("and she")

                    if fam.getFather() != None:
                        spouse= fam.getFather().getPrimaryName().getRegularName()

                marriage= fam.getMarriage()
                fulldate= ""
                place= ""
                if marriage != None:
                    if marriage.getPlace() != None and \
                            marriage.getPlaceName() != "":
                        place= marriage.getPlaceName()
                    elif rptOptions.blankPlace == reportOptions.Yes:
                        place= "____________"

                    date= marriage.getDateObj()
                    if date != None:
                        if date.getYearValid():
                            if date.getDayValid() and date.getMonthValid() and \
                                    rptOptions.fullDate == reportOptions.Yes:
                                fulldate= date.getDate()
                            elif rptOptions.blankDate == reportOptions.Yes:
                                fulldate= "__________"

                if spouse != "":
                    if fulldate == "" and place == "":
                        t= _("  %s married %s") % (heshe, spouse)
                    elif fulldate == "" and place != "":
                        t= _("  %s married %s in %s") % (heshe, spouse, place)
                    elif fulldate != "" and place == "":
                        t= _("  %s married %s on %s") % (heshe, spouse, fulldate)
                    else: t= _("  %s married %s on %s in %s") % \
                            (heshe, spouse, fulldate, place)
                else:
                    if fulldate == "" and place == "":
                        t= _("  %s married") % heshe
                    elif fulldate == "" and place != "":
                        t= _("  %s married in %s") % (heshe, place)
                    elif fulldate != "" and place == "":
                        t= _("  %s married on %s") % (heshe, fulldate)
                    else: t= _("  %s married on %s in %s") % \
                       (heshe, fulldate, place)

                if t != "": self.doc.write_text(t)
                if fam_num == len(famList): self.doc.write_text(".")

    def write_mate(self, person, rptOptions):
        """Output birth, death, parentage, marriage and notes information """

        for fam in person.getFamilyList():
            mate = ""
            if person.getGender() == RelLib.Person.male:
                heshe = _("She")
                if fam.getMother():
                    mate = fam.getMother()
                    mateName = mate.getPrimaryName().getRegularName()
                    mateFirstName = mate.getPrimaryName().getFirstName()
            else:
                heshe = _("He")
                if fam.getFather():
                    mate = fam.getFather()
                    mateName = mate.getPrimaryName().getRegularName()
                    mateFirstName = mate.getPrimaryName().getFirstName()

            if mate:
                self.doc.start_paragraph("DDR-Entry")

                if rptOptions.addImages == reportOptions.Yes:
                    self.insert_images(mate, rptOptions.imageAttrTag)

                if rptOptions.firstName == reportOptions.No:
                    mateFirstName = heshe

                self.doc.write_text(mateName)
                self.write_birth(mate, rptOptions)
                self.write_death(mate, mateFirstName, rptOptions)
                self.write_parents(mate, mateFirstName)
                self.doc.end_paragraph()

                #if rptOptions.listChildren == reportOptions.Yes \
                #           and mate.getGender() == RelLib.Person.male:
                #    self.write_children(fam, rptOptions)

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def insert_images(self, person, tag):

        photos= person.getPhotoList()
        for photo in photos :
            attribs= photo.getAttributeList()
            for attrib in attribs :
                if attrib.getType() == tag:
                    vlist= string.split(attrib.getValue())
                    if vlist[0] == 'left' or vlist[0] == 'right':
                        self.doc.add_photo(photo.ref.getPath(), vlist[0], \
                            float(vlist[1]), float(vlist[2]))

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def append_images(self, person, tag):

        photos= person.getPhotoList()
        numPhotos= 0                      # Number of photos
        for photo in photos :
            attribs= photo.getAttributeList()
            for attrib in attribs :
                if attrib.getType() == tag:
                    vlist= string.split(attrib.getValue())
                    if vlist[0] == 'single':
                        #if numPhotos > 0:
                        #	self.doc.end_paragraph()

                        numPhotos= numPhotos + 1
                        if numPhotos == 1:
                            self.doc.start_paragraph("DDR-Entry")
                        self.doc.add_photo(photo.ref.getPath(), vlist[0], \
							float(vlist[1]), float(vlist[2]))
						#self.doc.end_paragraph()
						#numPhotos= 0
                    elif vlist[0] == 'row':
                        numPhotos= numPhotos + 1
                        if numPhotos == 1:
                            self.doc.start_paragraph("DDR-Entry")
                        self.doc.add_photo(photo.ref.getPath(), vlist[0], \
							float(vlist[1]), float(vlist[2]))

        if numPhotos > 0 :
            self.doc.end_paragraph()


    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------
    def write_report(self):
        if self.newpage:
            self.doc.page_break()

        rptOpt = self.rptOpt

        self.cur_gen= 1
        self.apply_filter(self.start,1)

        name = self.start.getPrimaryName().getRegularName()

        famList= self.start.getFamilyList()
        spouseName= ""
        if len(famList) > 0:
            for fam in famList:
                if self.start.getGender() == RelLib.Person.male:
                    if fam.getMother() != None:
                        spouseName= fam.getMother().getPrimaryName().getFirstName()
                else:
                    if fam.getFather() != None:
                        spouseName= fam.getFather().getPrimaryName().getFirstName()

        self.doc.start_paragraph("DDR-Title")
        if spouseName != "":
            name = spouseName + " and " + name

        title = _("Detailed Descendant Report for %s") % name
        self.doc.write_text(title)
        self.doc.end_paragraph()

        keys = self.map.keys()
        keys.sort()
        generation = 0
        need_header = 1

        for generation in xrange(len(self.genKeys)):
            if self.pgbrk and generation > 0:
                self.doc.page_break()
            self.doc.start_paragraph("DDR-Generation")
            t = _("%s Generation") % DetDescendantReport.gen[generation+1]
            self.doc.write_text(t)
            self.doc.end_paragraph()
            if rptOpt.childRef == reportOptions.Yes:
                self.prevGenIDs= self.genIDs.copy()
                self.genIDs.clear()


            for key in self.genKeys[generation]:
                person = self.map[key]
                self.genIDs[person.getId()]= key
                dupPerson= self.write_person(key, rptOpt)
                if dupPerson == 0:		# Is this a duplicate ind record
                    if rptOpt.listChildren == reportOptions.Yes and  \
                         len(person.getFamilyList()) > 0:
                        family= person.getFamilyList()[0]
                        self.write_children(family, rptOpt)

                    if rptOpt.addImages == reportOptions.Yes:
                        self.append_images(person, rptOpt.imageAttrTag)

        if self.standalone:
            self.doc.close()

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
def _make_default_style(default_style):
    """Make the default output style for the Detailed Descendant Report"""
    font = BaseDoc.FontStyle()
    font.set(face=BaseDoc.FONT_SANS_SERIF,size=16,bold=1)
    para = BaseDoc.ParagraphStyle()
    para.set_font(font)
    para.set_header_level(1)
    para.set(pad=0.5)
    default_style.add_style("DDR-Title",para)

    font = BaseDoc.FontStyle()
    font.set(face=BaseDoc.FONT_SANS_SERIF,size=14,italic=1)
    para = BaseDoc.ParagraphStyle()
    para.set_font(font)
    para.set_header_level(2)
    para.set(pad=0.5)
    default_style.add_style("DDR-Generation",para)

    font = BaseDoc.FontStyle()
    font.set(face=BaseDoc.FONT_SANS_SERIF,size=10,italic=0, bold=0)
    para = BaseDoc.ParagraphStyle()
    para.set_font(font)
    #para.set_header_level(3)
    para.set_left_margin(0.0)   # in centimeters
    para.set(pad=0.5)
    default_style.add_style("DDR-ChildTitle",para)

    font = BaseDoc.FontStyle()
    font.set(face=BaseDoc.FONT_SANS_SERIF,size=9)
    para = BaseDoc.ParagraphStyle()
    para.set_font(font)
    para.set(first_indent=0.0,lmargin=0.0,pad=0.25)
    default_style.add_style("DDR-ChildList",para)

    para = BaseDoc.ParagraphStyle()
    para.set(first_indent=0.0,lmargin=0.0,pad=0.25)
    default_style.add_style("DDR-NoteHeader",para)

    para = BaseDoc.ParagraphStyle()
    para.set(first_indent=0.5,lmargin=0.0,pad=0.25)
    default_style.add_style("DDR-Entry",para)

    table = BaseDoc.TableStyle()
    table.set_width(1000)
    table.set_columns(3)
    table.set_column_width(1,"30%")
    #self.default_style.add_style("Images",table)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class DetDescendantReportDialog(Report.TextReportDialog):
    def __init__(self,database,person):
        Report.TextReportDialog.__init__(self,database,person)

    #------------------------------------------------------------------------
    #
    # Customization hooks
    #
    #------------------------------------------------------------------------
    def get_title(self):
        """The window title for this dialog"""
        return _("Gramps - Ahnentafel Report")

    def get_header(self, name):
        """The header line at the top of the dialog contents"""
        return _("Detailed Descendant Report for %s") % name

    def get_target_browser_title(self):
        """The title of the window created when the 'browse' button is
        clicked in the 'Save As' frame."""
        return _("Save Descendant Report")

    def get_stylesheet_savefile(self):
        """Where to save styles for this report."""
        return "det_descendant_report.xml"

    #------------------------------------------------------------------------
    #
    # Create output styles appropriate to this report.
    #
    #------------------------------------------------------------------------
    def make_default_style(self):
        _make_default_style(self.default_style)

    #------------------------------------------------------------------------
    #
    # Create the contents of the report.
    #
    #------------------------------------------------------------------------
    def make_report(self):
        """Create the object that will produce the Detailed Descendant
        Report.  All user dialog has already been handled and the
        output file opened."""

        try:
            MyReport = DetDescendantReport(self.db, self.person, 
                self.max_gen, self.pg_brk, self.rptOpt, self.doc, self.target_path )
            MyReport.write_report()
        except Errors.ReportError, msg:
            (m1,m2) = msg.messages()
            ErrorDialog(m1,m2)
        except Errors.FilterError, msg:
            (m1,m2) = msg.messages()
            ErrorDialog(m1,m2)
        except:
            import DisplayTrace
            DisplayTrace.DisplayTrace()

#*** Begin change
    def add_user_options(self):
        # Create a GTK Checkbox widgets

        # Pronoun instead of first name
        self.first_name_option = gtk.CheckButton(_("Use first names instead of pronouns"))
        self.first_name_option.set_active(0)

        # Full date usage
        self.full_date_option = gtk.CheckButton(_("Use full dates instead of only the year"))
        self.full_date_option.set_active(1)

        # Children List
        self.list_children_option = gtk.CheckButton(_("List children"))
        self.list_children_option.set_active(1)

        # Print notes
        self.include_notes_option = gtk.CheckButton(_("Include notes"))
        self.include_notes_option.set_active(1)

        # Replace missing Place with ___________
        self.place_option = gtk.CheckButton(_("Replace Place with ______"))
        self.place_option.set_active(0)

        # Replace missing dates with __________
        self.date_option = gtk.CheckButton(_("Replace Dates with ______"))
        self.date_option.set_active(0)

        # Add "Died at the age of NN" in text
        self.age_option = gtk.CheckButton(_("Compute age"))
        self.age_option.set_active(1)

        # Omit duplicate persons, occurs when distant cousins marry
        self.dupPersons_option = gtk.CheckButton(_("Omit duplicate people"))
        self.dupPersons_option.set_active(1)

        #Add descendant reference in child list
        self.childRef_option = gtk.CheckButton(_("Add descendant reference in child list"))
        self.childRef_option.set_active(1)

        #Add photo/image reference
        self.image_option = gtk.CheckButton(_("Include Photo/Images from Gallery"))
        self.image_option.set_active(0)

        # Add new options. The first argument is the tab name for grouping options.
        # if you want to put everyting in the generic "Options" category, use
        # self.add_option(text,widget) instead of self.add_frame_option(category,text,widget)

        self.add_frame_option('Content','',self.first_name_option)
        self.add_frame_option('Content','',self.full_date_option)
        self.add_frame_option('Content','',self.list_children_option)
        self.add_frame_option('Content','',self.include_notes_option)
        self.add_frame_option('Content','',self.place_option)
        self.add_frame_option('Content','',self.date_option)
        self.add_frame_option('Content','',self.age_option)
        self.add_frame_option('Content','',self.dupPersons_option)
        self.add_frame_option('Content','',self.childRef_option)
        self.add_frame_option('Content','',self.image_option)


    def parse_report_options_frame(self):
        """Parse the report options frame of the dialog.  Save the user selected choices for later use."""

        # call the parent task to handle normal options
        Report.ReportDialog.parse_report_options_frame(self)

        # get values from the widgets
        if self.first_name_option.get_active():
            self.firstName = reportOptions.Yes
        else:
            self.firstName = reportOptions.No

        if self.full_date_option.get_active():
            self.fullDate = reportOptions.Yes
        else:
            self.fullDate = reportOptions.No

        if self.list_children_option.get_active():
            self.listChildren = reportOptions.Yes
        else:
            self.listChildren = reportOptions.No

        if self.include_notes_option.get_active():
            self.includeNotes = reportOptions.Yes
        else:
            self.includeNotes = reportOptions.No

        if self.place_option.get_active():
            self.blankPlace = reportOptions.Yes
        else:
            self.blankPlace = reportOptions.No

        if self.date_option.get_active():
            self.blankDate = reportOptions.Yes
        else:
            self.blankDate = reportOptions.No

        if self.age_option.get_active():
            self.calcAgeFlag = reportOptions.Yes
        else:
            self.calcAgeFlag = reportOptions.No

        if self.dupPersons_option.get_active():
            self.dupPersons = reportOptions.Yes
        else:
            self.dupPersons = reportOptions.No

        if self.childRef_option.get_active():
            self.childRef = reportOptions.Yes
        else:
            self.childRef = reportOptions.No

        if self.image_option.get_active():
            self.addImages = reportOptions.Yes
        else:
            self.addImages = reportOptions.No

        rptOpt = reportOptions()
        rptOpt.firstName= self.firstName
        rptOpt.fullDate= self.fullDate
        rptOpt.listChildren= self.listChildren
        rptOpt.includeNotes= self.includeNotes
        rptOpt.blankPlace= self.blankPlace
        rptOpt.blankDate= self.blankDate
        rptOpt.calcAgeFlag= self.calcAgeFlag
        rptOpt.dupPersons= self.dupPersons
        rptOpt.childRef= self.childRef
        rptOpt.addImages= self.addImages
        self.rptOpt = rptOpt

#*** End of change


#------------------------------------------------------------------------
#
# Standalone report function
#
#------------------------------------------------------------------------
def report(database,person):
    DetDescendantReportDialog(database,person)

#------------------------------------------------------------------------
#
# Set up sane defaults for the book_item
#
#------------------------------------------------------------------------
_style_file = "det_descendant_report.xml"
_style_name = "default" 

_person_id = ""
_max_gen = 10
_pg_brk = 0
_first_name = 0
_full_date = 1
_list_children = 1
_include_notes = 1
_place = 0
_date = 1
_age = 1
_dup_persons = 1
_child_ref = 1
_images = 0

_options = ( _person_id, _max_gen, _pg_brk, 
   _first_name, _full_date, _list_children, _include_notes, 
   _place, _date, _age, _dup_persons, _child_ref, _images )

#------------------------------------------------------------------------
#
# Book Item Options dialog
#
#------------------------------------------------------------------------
class DetDescendantBareReportDialog(Report.BareReportDialog):
    def __init__(self,database,person,opt,stl):
        self.options = opt
        self.db = database
        if self.options[0]:
            self.person = self.db.getPerson(self.options[0])
        else:
            self.person = person

        self.max_gen = int(self.options[1]) 
        self.pg_brk = int(self.options[2])
        self.first_name = int(self.options[3]) 
        self.full_date = int(self.options[4])
        self.list_children = int(self.options[5]) 
        self.include_notes = int(self.options[6])
        self.place = int(self.options[7]) 
        self.date = int(self.options[8]) 
        self.age = int(self.options[9])
        self.dup_persons = int(self.options[10]) 
        self.child_ref = int(self.options[11])
        self.images = int(self.options[12])

        self.style_name = stl

        Report.BareReportDialog.__init__(self,database,self.person)

        self.new_person = None

        self.window.run()

    #------------------------------------------------------------------------
    #
    # Customization hooks
    #
    #------------------------------------------------------------------------
    def make_default_style(self):
        _make_default_style(self.default_style)

    def get_title(self):
        """The window title for this dialog"""
        return "%s - GRAMPS Book" % (_("Detailed Descendant Report"))

    def get_header(self, name):
        """The header line at the top of the dialog contents"""
        return _("Detailed Descendant Report for GRAMPS Book") 

    def get_stylesheet_savefile(self):
        """Where to save styles for this report."""
        return _style_file

    def add_user_options(self):
        # Create a GTK Checkbox widgets

        # Pronoun instead of first name
        self.first_name_option = gtk.CheckButton(_("Use first names instead of pronouns"))
        self.first_name_option.set_active(self.first_name)

        # Full date usage
        self.full_date_option = gtk.CheckButton(_("Use full dates instead of only the year"))
        self.full_date_option.set_active(self.full_date)

        # Children List
        self.list_children_option = gtk.CheckButton(_("List children"))
        self.list_children_option.set_active(self.list_children)

        # Print notes
        self.include_notes_option = gtk.CheckButton(_("Include notes"))
        self.include_notes_option.set_active(self.include_notes)

        # Replace missing Place with ___________
        self.place_option = gtk.CheckButton(_("Replace Place with ______"))
        self.place_option.set_active(self.place)

        # Replace missing dates with __________
        self.date_option = gtk.CheckButton(_("Replace Dates with ______"))
        self.date_option.set_active(self.date)

        # Add "Died at the age of NN" in text
        self.age_option = gtk.CheckButton(_("Compute age"))
        self.age_option.set_active(self.age)

        # Omit duplicate persons, occurs when distant cousins marry
        self.dupPersons_option = gtk.CheckButton(_("Omit duplicate ancestors"))
        self.dupPersons_option.set_active(self.dup_persons)

        #Add descendant reference in child list
        self.childRef_option = gtk.CheckButton(_("Add descendant reference in child list"))
        self.childRef_option.set_active(self.child_ref)

        #Add photo/image reference
        self.image_option = gtk.CheckButton(_("Include Photo/Images from Gallery"))
        self.image_option.set_active(self.images)

        # Add new options. The first argument is the tab name for grouping options.
        # if you want to put everyting in the generic "Options" category, use
        # self.add_option(text,widget) instead of self.add_frame_option(category,text,widget)

        self.add_frame_option('Content','',self.first_name_option)
        self.add_frame_option('Content','',self.full_date_option)
        self.add_frame_option('Content','',self.list_children_option)
        self.add_frame_option('Content','',self.include_notes_option)
        self.add_frame_option('Content','',self.place_option)
        self.add_frame_option('Content','',self.date_option)
        self.add_frame_option('Content','',self.age_option)
        self.add_frame_option('Content','',self.dupPersons_option)
        self.add_frame_option('Content','',self.childRef_option)
        self.add_frame_option('Content','',self.image_option)

    def parse_report_options_frame(self):
        """Parse the report options frame of the dialog.  Save the user selected choices for later use."""

        # call the parent task to handle normal options
        Report.BareReportDialog.parse_report_options_frame(self)

        # get values from the widgets
        if self.first_name_option.get_active():
            self.first_name = reportOptions.Yes
        else:
            self.first_name = reportOptions.No

        if self.full_date_option.get_active():
            self.full_date = reportOptions.Yes
        else:
            self.full_date = reportOptions.No

        if self.list_children_option.get_active():
            self.list_children = reportOptions.Yes
        else:
            self.list_children = reportOptions.No

        if self.include_notes_option.get_active():
            self.include_notes = reportOptions.Yes
        else:
            self.include_notes = reportOptions.No

        if self.place_option.get_active():
            self.place = reportOptions.Yes
        else:
            self.place = reportOptions.No

        if self.date_option.get_active():
            self.date = reportOptions.Yes
        else:
            self.date = reportOptions.No

        if self.age_option.get_active():
            self.age = reportOptions.Yes
        else:
            self.age = reportOptions.No

        if self.dupPersons_option.get_active():
            self.dup_persons = reportOptions.Yes
        else:
            self.dup_persons = reportOptions.No

        if self.childRef_option.get_active():
            self.child_ref = reportOptions.Yes
        else:
            self.child_ref = reportOptions.No

        if self.image_option.get_active():
            self.images = reportOptions.Yes
        else:
            self.images = reportOptions.No

    def on_cancel(self, obj):
        pass

    def on_ok_clicked(self, obj):
        """The user is satisfied with the dialog choices. Parse all options
        and close the window."""

        # Preparation
        self.parse_style_frame()
        self.parse_report_options_frame()
        
        if self.new_person:
            self.person = self.new_person
        self.options = ( self.person.getId(), self.max_gen, self.pg_brk, 
            self.first_name, self.full_date, self.list_children, 
            self.include_notes, self.place, self.date, self.age, 
            self.dup_persons, self.child_ref, self.images )
        self.style_name = self.selected_style.get_name() 

#------------------------------------------------------------------------
#
# Function to write Book Item 
#
#------------------------------------------------------------------------
def write_book_item(database,person,doc,options,newpage=0):
    """Write the Detailed Descendant Report using options set.
    All user dialog has already been handled and the output file opened."""
    try:
        if options[0]:
            person = database.getPerson(options[0])
        max_gen = int(options[1])
        pg_brk = int(options[2])
        rptOpt = reportOptions()
        rptOpt.firstName = int(options[3]) 
        rptOpt.fullDate = int(options[4])
        rptOpt.listChildren = int(options[5]) 
        rptOpt.includeNotes = int(options[6])
        rptOpt.blankPlace = int(options[7]) 
        rptOpt.blankDate = int(options[8]) 
        rptOpt.calcAgeFlag = int(options[9])
        rptOpt.dupPersons = int(options[10]) 
        rptOpt.childRef = int(options[11])
        rptOpt.addImages = int(options[12])
        return DetDescendantReport(database, person,
            max_gen, pg_brk, rptOpt, doc, None, newpage)
    except Errors.ReportError, msg:
        (m1,m2) = msg.messages()
        ErrorDialog(m1,m2)
    except Errors.FilterError, msg:
        (m1,m2) = msg.messages()
        ErrorDialog(m1,m2)
    except:
        import DisplayTrace
        DisplayTrace.DisplayTrace()

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
from Plugins import register_report, register_book_item

register_report(
    report,
    _("Detailed Descendant Report"),
    status=(_("Beta")),
    category=_("Text Reports"),
    description= _("Produces a detailed descendant report"),
    xpm= get_xpm_image(),
    author_name="Bruce DeGrasse",
    author_email="bdegrasse1@attbi.com"
    )

# (name,category,options_dialog,write_book_item,options,style_name,style_file,make_default_style)
register_book_item( 
    _("Detailed Descendant Report"), 
    _("Text"),
    DetDescendantBareReportDialog,
    write_book_item,
    _options,
    _style_name,
    _style_file,
    _make_default_style
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
        self.includeNotes= reportOptions.No

        #Selectively print notes (omit private information)
        #self.omitPrivInfo= reportOptions.No

        #generate header for each page, specify text
        #self.noHeader= reportOptions.Yes

        #Inculde reference notes
        self.noRefNotes= reportOptions.No

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
        self.addImages= reportOptions.No
        self.imageAttrTag= "DetDescendantReport"

        #Omit sensitive information such as birth, christening, marriage
        #   for living after XXXXX date.

        #Omit duplicate persons, occurs when distant cousins marry
        self.dupPersons= reportOptions.Yes

        #Add descendant reference in child list
        self.childRef= reportOptions.Yes

    def calcAge(self, ind):
        """ Calulate age
        APHRASE=
            at the age of NUMBER UNIT(S)
        UNIT= year | month | day
        UNITS= years | months | days
        null
        """

        birth= ind.getBirth().getDateObj().get_start_date()
        death= ind.getDeath().getDateObj().get_start_date()
        #print "birth=", birth.__dict__
        #print "death=", death.__dict__
        self.t= ""
        if birth.getYearValid() and death.getYearValid():
            self.age= death.getYear() - birth.getYear()
            self.units= 3                          # year
            if birth.getMonthValid() and death.getMonthValid():
                if birth.getMonth() > death.getMonth():
                    self.age= self.age -1
                if birth.getDayValid() and death.getDayValid():
                    if birth.getMonth() == death.getMonth() and birth.getDay() > death.getDay():
                        self.age= self.age -1
                    if self.age == 0:
                        self.age= death.getMonth() - birth.getMonth()   # calc age in months
                        if birth.getDay() > death.getDay():
                            self.age= self.age - 1
			    self.units= 2                        # month
                        if self.age == 0:
                            self.age= death.getDay() + 31 - birth.getDay() # calc age in days
                            self.units= 1            # day
            if self.age > 1:
                if self.units == 1:
                    self.t= _(" at the age of %d days") % self.age
                elif self.units == 2:
                    self.t= _(" at the age of %d months") % self.age
                else:
                    self.t= _(" at the age of %d years") % self.age
            else:
                if self.units == 1:
                    self.t= _(" at the age of %d day") % self.age
                elif self.units == 2:
                    self.t= _(" at the age of %d month") % self.age
                else:
                    self.t= _(" at the age of %d year") % self.age
        return self.t
