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

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import os
import string

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import RelLib
import const
import BaseDoc
import StyleEditor
import Report
import GenericFilter
import Errors
from QuestionDialog import ErrorDialog
from gettext import gettext as _

#------------------------------------------------------------------------
#
# Gnome/GTK modules
#
#------------------------------------------------------------------------
import gtk

#------------------------------------------------------------------------
#
# Set up sane defaults for the book_item
#
#------------------------------------------------------------------------
_person_id = ""
_max_gen = 0
_pg_brk = 0
_filter_num = 0
_options = ( _person_id, _max_gen, _pg_brk, _filter_num )

#------------------------------------------------------------------------
#
# IndivComplete
#
#------------------------------------------------------------------------
class IndivComplete(Report.Report):

    def __init__(self,database,person,output,document,filter,use_srcs,newpage=0):
        self.d = document
        self.use_srcs = use_srcs
        self.filter = filter
        c = database.getResearcher().getName()
        self.d.creator(c)
        self.map = {}
        self.database = database
        self.person = person
        self.output = output
        self.setup()
        self.newpage = newpage
        if output:
            self.standalone = 1
            self.d.open(output)
        else:
            self.standalone = 0
        
    def setup(self):
        tbl = BaseDoc.TableStyle()
        tbl.set_width(100)
        tbl.set_columns(2)
        tbl.set_column_width(0,20)
        tbl.set_column_width(1,80)
        self.d.add_table_style("IDS-IndTable",tbl)

        tbl = BaseDoc.TableStyle()
        tbl.set_width(100)
        tbl.set_columns(2)
        tbl.set_column_width(0,50)
        tbl.set_column_width(1,50)
        self.d.add_table_style("IDS-ParentsTable",tbl)

        cell = BaseDoc.TableCellStyle()
        cell.set_top_border(1)
        cell.set_bottom_border(1)
        self.d.add_cell_style("IDS-TableHead",cell)

        cell = BaseDoc.TableCellStyle()
        self.d.add_cell_style("IDS-NormalCell",cell)

        cell = BaseDoc.TableCellStyle()
	cell.set_longlist(1)
        self.d.add_cell_style("IDS-ListCell",cell)

    def end(self):
        if self.standalone:
            self.d.close()

    def write_fact(self,event):
        if event == None:
            return
        name = _(event.getName())
        date = event.getDate()
        place = event.getPlaceName()
        description = event.getDescription()
        if date == "":
            if place == "":
                return
            else:
                text = '%s. %s' % (place,description)
        else:
            if place == "":
                text = '%s. %s' % (date,description)
            else:
                text = _('%(date)s in %(place)s.') % { 'date' : date,
                                                      'place' : place }
                text = '%s %s' % (text,description)

        self.d.start_row()
        self.normal_cell(name)
        if self.use_srcs:
            for s in event.getSourceRefList():
                text = "%s [%s]" % (text,s.getBase().getId())
                self.slist.append(s)
        self.normal_cell(text)
        self.d.end_row()

    def write_p_entry(self,label,parent,rel):
        self.d.start_row()
        self.normal_cell(label)

        if parent:
            self.normal_cell('%(parent)s, relationship: %(relation)s' %
                               { 'parent' : parent, 'relation' : rel })
        else:
            self.normal_cell('')
        self.d.end_row()

    def write_note(self):
        note = self.person.getNote()
        if note == '':
            return
        self.d.start_table('note','IDS-IndTable')
        self.d.start_row()
        self.d.start_cell('IDS-TableHead',2)
        self.d.start_paragraph('IDS-TableTitle')
        self.d.write_text(_('Notes'))
        self.d.end_paragraph()
        self.d.end_cell()
        self.d.end_row()

        self.d.start_row()
        self.d.start_cell('IDS-NormalCell',2)
        for line in string.split(note,'\n'):
            self.d.start_paragraph('IDS-Normal')
            self.d.write_text(line)
            self.d.end_paragraph()
        self.d.end_cell()
        self.d.end_row()

        self.d.end_table()
        self.d.start_paragraph("IDS-Normal")
        self.d.end_paragraph()

    def write_alt_parents(self):

        if len(self.person.getParentList()) < 2:
            return
        
        self.d.start_table("altparents","IDS-IndTable")
        self.d.start_row()
        self.d.start_cell("IDS-TableHead",2)
        self.d.start_paragraph("IDS-TableTitle")
        self.d.write_text(_("Alternate Parents"))
        self.d.end_paragraph()
        self.d.end_cell()
        self.d.end_row()
        
        for (family,mrel,frel) in self.person.getParentList():
            if family == self.person.getMainParents():
                continue
            
            father = family.getFather()
            if father:
                fname = father.getPrimaryName().getRegularName()
                frel = const.childRelations[frel]
                self.write_p_entry(_('Father'),fname,frel)
            else:
                self.write_p_entry(_('Father'),'','')

            mother = family.getMother()
            if mother:
                fname = mother.getPrimaryName().getRegularName()
                frel = const.childRelations[frel]
                self.write_p_entry(_('Mother'),fname,frel)
            else:
                self.write_p_entry(_('Mother'),'','')
                
        self.d.end_table()
        self.d.start_paragraph("IDS-Normal")
        self.d.end_paragraph()

    def write_alt_names(self):

        if len(self.person.getAlternateNames()) < 1:
            return
        
        self.d.start_table("altparents","IDS-IndTable")
        self.d.start_row()
        self.d.start_cell("IDS-TableHead",2)
        self.d.start_paragraph("IDS-TableTitle")
        self.d.write_text(_("Alternate Names"))
        self.d.end_paragraph()
        self.d.end_cell()
        self.d.end_row()
        
        for name in self.person.getAlternateNames():
            type = const.InverseNameTypesMap[name.getType()]
            self.d.start_row()
            self.normal_cell(type)
            text = name.getRegularName()
            if self.use_srcs:
                for s in name.getSourceRefList():
                    text = "%s [%s]" % (text,s.getBase().getId())
                    self.slist.append(s)
            self.normal_cell(text)
            self.d.end_row()
        self.d.end_table()
        self.d.start_paragraph('IDS-Normal')
        self.d.end_paragraph()
        
    def write_families(self):

        if len(self.person.getFamilyList()) == 0:
            return
        
        self.d.start_table("three","IDS-IndTable")
        self.d.start_row()
        self.d.start_cell("IDS-TableHead",2)
        self.d.start_paragraph("IDS-TableTitle")
        self.d.write_text(_("Marriages/Children"))
        self.d.end_paragraph()
        self.d.end_cell()
        self.d.end_row()
        
        for family in self.person.getFamilyList():
            if self.person == family.getFather():
                spouse = family.getMother()
            else:
                spouse = family.getFather()
            self.d.start_row()
            self.d.start_cell("IDS-NormalCell",2)
            self.d.start_paragraph("IDS-Spouse")
            if spouse:
                text = spouse.getPrimaryName().getRegularName()
            else:
                text = _("unknown")
            self.d.write_text(text)
            self.d.end_paragraph()
            self.d.end_cell()
            self.d.end_row()
            
            for event in family.getEventList():
                self.write_fact(event)

            child_list = family.getChildList()
            if len(child_list) > 0:
                self.d.start_row()
                self.normal_cell(_("Children"))

                self.d.start_cell("IDS-ListCell")
                self.d.start_paragraph("IDS-Normal")
                
                first = 1
                for child in family.getChildList():
                    if first == 1:
                        first = 0
                    else:
                        self.d.write_text('\n')
                    self.d.write_text(child.getPrimaryName().getRegularName())
                self.d.end_paragraph()
                self.d.end_cell()
                self.d.end_row()
        self.d.end_table()
        self.d.start_paragraph('IDS-Normal')
        self.d.end_paragraph()

    def write_sources(self):

        if len(self.slist) == 0:
            return
        
        self.d.start_table("three","IDS-IndTable")
        self.d.start_row()
        self.d.start_cell("IDS-TableHead",2)
        self.d.start_paragraph("IDS-TableTitle")
        self.d.write_text(_("Sources"))
        self.d.end_paragraph()
        self.d.end_cell()
        self.d.end_row()
        
        for source in self.slist:
            self.d.start_row()
            sname = source.getBase()
            self.normal_cell(sname.getId())
            self.normal_cell(sname.getTitle())
            self.d.end_row()
        self.d.end_table()

    def write_facts(self):
        self.d.start_table("two","IDS-IndTable")
        self.d.start_row()
        self.d.start_cell("IDS-TableHead",2)
        self.d.start_paragraph("IDS-TableTitle")
        self.d.write_text(_("Individual Facts"))
        self.d.end_paragraph()
        self.d.end_cell()
        self.d.end_row()

        event_list = [ self.person.getBirth(), self.person.getDeath() ]
        event_list = event_list + self.person.getEventList()
        for event in event_list:
            self.write_fact(event)
        self.d.end_table()
        self.d.start_paragraph("IDS-Normal")
        self.d.end_paragraph()

    def normal_cell(self,text):
        self.d.start_cell('IDS-NormalCell')
        self.d.start_paragraph('IDS-Normal')
        self.d.write_text(text)
        self.d.end_paragraph()
        self.d.end_cell()

    def write_report(self):
        if self.newpage:
            self.d.page_break()

        plist = self.database.getPersonMap().values()
        if self.filter:
            ind_list = self.filter.apply(self.database,plist)
        else:
            ind_list = plist
            
        count = 0
        for self.person in ind_list:
            self.write_person(count)
            count = count + 1
        self.end()

    def write_person(self,count):
        if count != 0:
            self.d.page_break()
        self.slist = []
        
        photo_list = self.person.getPhotoList()
        name = self.person.getPrimaryName().getRegularName()
        self.d.start_paragraph("IDS-Title")
        self.d.write_text(_("Summary of %s") % name)
        self.d.end_paragraph()

        self.d.start_paragraph("IDS-Normal")
        self.d.end_paragraph()

        if len(photo_list) > 0:
            object = photo_list[0].getReference()
            if object.getMimeType()[0:5] == "image":
                file = object.getPath()
                self.d.start_paragraph("IDS-Normal")
                self.d.add_photo(file,"row",4.0,4.0)
                self.d.end_paragraph()

        self.d.start_table("one","IDS-IndTable")

        self.d.start_row()
        self.normal_cell("%s:" % _("Name"))
        name = self.person.getPrimaryName()
        text = name.getRegularName()
        if self.use_srcs:
            for s in name.getSourceRefList():
                self.slist.append(s)
                text = "%s [%s]" % (text,s.getBase().getId())
        self.normal_cell(text)
        self.d.end_row()

        self.d.start_row()
        self.normal_cell("%s:" % _("Gender"))
        if self.person.getGender() == RelLib.Person.male:
            self.normal_cell(_("Male"))
        else:
            self.normal_cell(_("Female"))
        self.d.end_row()

        family = self.person.getMainParents()
        if family:
            father_inst = family.getFather()
            if father_inst:
                father = father_inst.getPrimaryName().getRegularName()
            else:
                father = ""
            mother_inst = family.getMother()
            if mother_inst:
                mother = mother_inst.getPrimaryName().getRegularName()
            else:
                mother = ""
        else:
            father = ""
            mother = ""

        self.d.start_row()
        self.normal_cell("%s:" % _("Father"))
        self.normal_cell(father)
        self.d.end_row()

        self.d.start_row()
        self.normal_cell("%s:" % _("Mother"))
        self.normal_cell(mother)
        self.d.end_row()
        self.d.end_table()

        self.d.start_paragraph("IDS-Normal")
        self.d.end_paragraph()

        self.write_alt_names()
        self.write_facts()
        self.write_alt_parents()
        self.write_families()
        self.write_note()
        self.write_sources()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class IndivCompleteDialog(Report.TextReportDialog):

    report_options = {}

    def __init__(self,database,person):
        Report.TextReportDialog.__init__(self,database,person,self.report_options)

    def add_user_options(self):
        self.use_srcs = gtk.CheckButton(_('Include Source Information'))
        self.use_srcs.show()
        self.add_option('',self.use_srcs)

    #------------------------------------------------------------------------
    #
    # Customization hooks
    #
    #------------------------------------------------------------------------
    def get_title(self):
        """The window title for this dialog"""
        return "%s - %s - GRAMPS" %(_("Complete Individual Report"),_("Text Reports"))

    def get_header(self, name):
        """The header line at the top of the dialog contents"""
        return _("Complete Individual Report")

    def get_target_browser_title(self):
        """The title of the window created when the 'browse' button is
        clicked in the 'Save As' frame."""
        return _("Save Complete Individual Report")
    
    def get_stylesheet_savefile(self):
        """Where to save styles for this report."""
        return "indiv_complete.xml"
    
    def doc_uses_tables(self):
        """This report requires table support."""
        return 1

    def get_report_filters(self):
        """Set up the list of possible content filters."""
        return _get_report_filters(self.person)

    #------------------------------------------------------------------------
    #
    # Create output styles appropriate to this report.
    #
    #------------------------------------------------------------------------
    def make_default_style(self):
        """Make the default output style for the Individual Complete Report."""
        _make_default_style(self.default_style)
    
    def setup_report_options(self):
        """The 'Report Options' frame is not used in this dialog."""
        pass

    def make_report(self):
        """Create the object that will produce the Ancestor Chart.
        All user dialog has already been handled and the output file
        opened."""

        act = self.use_srcs.get_active()
        
        try:
            MyReport = IndivComplete(self.db, self.person, self.target_path,
                                     self.doc, self.filter, act)
            MyReport.setup()
            MyReport.write_report()
        except Errors.FilterError, msg:
            (m1,m2) = msg.messages()
            ErrorDialog(m1,m2)
        except Errors.ReportError, msg:
            (m1,m2) = msg.messages()
            ErrorDialog(m1,m2)
        except:
            import DisplayTrace
            DisplayTrace.DisplayTrace()
        

    def get_report_generations(self):
        """Return the default number of generations to start the
        spinbox (zero to disable) and whether or not to include the
        'page break between generations' check box"""
        return (0, 0)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
def report(database,person):
    IndivCompleteDialog(database,person)

#------------------------------------------------------------------------
#
# Book Item Options dialog
#
#------------------------------------------------------------------------
class IndivCompleteBareReportDialog(Report.BareReportDialog):

    def __init__(self,database,person,opt,stl):

        self.options = opt
        self.db = database
        if self.options[0]:
            self.person = self.db.getPerson(self.options[0])
        else:
            self.person = person
        self.style_name = stl

        Report.BareReportDialog.__init__(self,database,self.person)

        self.max_gen = int(self.options[1])
        self.pg_brk = int(self.options[2])
        self.filter_num = int(self.options[3])
        self.new_person = None

        self.generations_spinbox.set_value(self.max_gen)
        self.pagebreak_checkbox.set_active(self.pg_brk)
        self.filter_combo.set_history(self.filter_num)

        self.window.run()

    def make_default_style(self):
        _make_default_style(self.default_style)

    def get_report_filters(self):
        return _get_report_filters(self.person)

    #------------------------------------------------------------------------
    #
    # Customization hooks
    #
    #------------------------------------------------------------------------
    def get_title(self):
        """The window title for this dialog"""
        return "%s - GRAMPS Book" % (_("Individual Complete"))

    def get_header(self, name):
        """The header line at the top of the dialog contents"""
        return _("Individual Complete Report for GRAMPS Book") 

    def get_stylesheet_savefile(self):
        """Where to save styles for this report."""
        return "individual_summary.xml"
    
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
        self.filter_num = self.filter_combo.get_history()
        self.options = ( self.person.getId(), self.max_gen, self.pg_brk, self.filter_num )
        self.style_name = self.selected_style.get_name()


#------------------------------------------------------------------------
#
# Function to write Book Item 
#
#------------------------------------------------------------------------
def write_book_item(database,person,doc,options,newpage=0):
    """Write the Individual Copmlete Report using the options set.
    All user dialog has already been handled and the output file opened."""
    try:
        if options[0]:
            person = database.getPerson(options[0])
        max_gen = int(options[1])
        pg_brk = int(options[2])
        filter_num = int(options[3])
        filters = _get_report_filters(person)
        filter = filters[filter_num]
#        act = self.use_srcs.get_active()
        
        return IndivComplete(database, person, None, doc, filter, 0, newpage)
#        return IndivComplete(database, person, None, doc, filter, act, newpage)
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
# Makes the default styles
#
#------------------------------------------------------------------------
def _make_default_style(default_style):
    """Make the default output style for the Individual Complete Report."""
    font = BaseDoc.FontStyle()
    font.set_bold(1)
    font.set_type_face(BaseDoc.FONT_SANS_SERIF)
    font.set_size(16)
    p = BaseDoc.ParagraphStyle()
    p.set_alignment(BaseDoc.PARA_ALIGN_CENTER)
    p.set_font(font)
    p.set_description(_("The style used for the title of the page."))
    default_style.add_style("IDS-Title",p)
    
    font = BaseDoc.FontStyle()
    font.set_bold(1)
    font.set_type_face(BaseDoc.FONT_SANS_SERIF)
    font.set_size(12)
    font.set_italic(1)
    p = BaseDoc.ParagraphStyle()
    p.set_font(font)
    p.set_description(_("The style used for category labels."))
    default_style.add_style("IDS-TableTitle",p)
    
    font = BaseDoc.FontStyle()
    font.set_bold(1)
    font.set_type_face(BaseDoc.FONT_SANS_SERIF)
    font.set_size(12)
    p = BaseDoc.ParagraphStyle()
    p.set_font(font)
    p.set_description(_("The style used for the spouse's name."))
    default_style.add_style("IDS-Spouse",p)
    
    font = BaseDoc.FontStyle()
    font.set_size(12)
    p = BaseDoc.ParagraphStyle()
    p.set_font(font)
    p.set_description(_('The basic style used for the text display.'))
    default_style.add_style("IDS-Normal",p)
    

#------------------------------------------------------------------------
#
# Builds filter list for this report
#
#------------------------------------------------------------------------
def _get_report_filters(person):
    """Set up the list of possible content filters."""

    name = person.getPrimaryName().getName()
        
    filt_id = GenericFilter.GenericFilter()
    filt_id.set_name(name)
    filt_id.add_rule(GenericFilter.HasIdOf([person.getId()]))

    des = GenericFilter.GenericFilter()
    des.set_name(_("Descendants of %s") % name)
    des.add_rule(GenericFilter.IsDescendantOf([person.getId()]))
        
    ans = GenericFilter.GenericFilter()
    ans.set_name(_("Ancestors of %s") % name)
    ans.add_rule(GenericFilter.IsAncestorOf([person.getId()]))

    all = GenericFilter.GenericFilter()
    all.set_name(_("Entire Database"))
    all.add_rule(GenericFilter.Everyone([]))

    return [filt_id,des,ans,all]

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
def get_xpm_image():
    return [
        "48 48 33 1",
        " 	c None",
        ".	c #312D2A",
        "+	c #4773AA",
        "@	c #A8A7A5",
        "#	c #BABAB6",
        "$	c #CECECE",
        "%	c #ECDECB",
        "&	c #5C5C60",
        "*	c #7C7262",
        "=	c #F2EADE",
        "-	c #867A6F",
        ";	c #8E887E",
        ">	c #E2CAA2",
        ",	c #565354",
        "'	c #4C4E51",
        ")	c #6D655E",
        "!	c #B69970",
        "~	c #F6F2EE",
        "{	c #9E9286",
        "]	c #416CA3",
        "^	c #3D4557",
        "/	c #A29E96",
        "(	c #FAFAFA",
        "_	c #BA7458",
        ":	c #C67C5E",
        "<	c #BDA37E",
        "[	c #CECABE",
        "}	c #A26E62",
        "|	c #E6E2E2",
        "1	c #423E43",
        "2	c #966A60",
        "3	c #D2D2D2",
        "4	c #E5D2B8",
        "                                                ",
        "                                                ",
        "             ;-;-----***)*))))&,&)*             ",
        "             -##############@#@/;&,*            ",
        "             -#((((((((((((((=|$#;;{,           ",
        "             ;#(((((((((((((((~|3/*[{1          ",
        "             -#((((((((((((((((~|3,|[;.         ",
        "             -#((((((((@/@@@@@@/@/'(|[;.        ",
        "             -#((((((((((((((((((~'((|[;.       ",
        "             -#(((((((((((]+]+]]+('=((|[;1      ",
        "             -#(((((((((((]+]}2&+('|=((|[{,     ",
        "             *#(((((((((((]+}<:-+('[|~((|#{)    ",
        "             *#(((((((((((+]2_:)+('...1'&*-)*   ",
        "             -#(((((((((((]&1(_&+(3@#//--)&1)   ",
        "             *#~((((((((((+]1}/^]((|$##/;--'1   ",
        "             *#(((((((((((]]^)11,(((|$[#@/;)1   ",
        "             *#(((((((((((]^.^^&&((~=|$[#@/*.   ",
        "             *#(((((((((((((~(((((((|$[$[#/-.   ",
        "             *#~(((((((((((((((((~~~~||$[[@;.   ",
        "             )#((((@@@@@@/@@/@/@@@@///{;[[[;.   ",
        "             )#(((((((((((((((((~~~~==|$$[#;.   ",
        "             )#((((@/@@/@@@@@@@@@//////{4>3{.   ",
        "             )#(((((((((((((((~~~~==|=||%$[{.   ",
        "             )#((((@@@@@/@@@///////////{43>/.   ",
        "             )#((((((((((((((~~~~~==|||%>4[!.   ",
        "             )#((((@/@@@@@//~~~~======%%%43{.   ",
        "             )#((((((((((((~~~~=|==||=%%%44!.   ",
        "             ,#((((@@/@@/@/@////////{/{{%4$!.   ",
        "             )#~((((((((~~~~~~==||%=%=%%44>/.   ",
        "             ,#((((/@@//@///////////{{{{%4>!.   ",
        "             )#((((((((~~~=~||=|%%%%%4%%%44{.   ",
        "             ,#((((@@@/@/////////{{{{{{{444!.   ",
        "             &#(((((~~~~~|~|||%%|%%%%44444%!.   ",
        "             ,#(((~/@//////////{{{{{{;{;4>4!.   ",
        "             ,#(((~~~~=~|==|%|=%%%4%%44444>!.   ",
        "             &#(((~//////////{{{{{{{;{;{4>><.   ",
        "             ,#(~~~~~~==||%|%%%%%%44444>4>>!.   ",
        "             '#~~~~///////{{{{{{{;!;{;;;>>>!.   ",
        "             ,#~~~~||=||%|%=%%4%444>44>>>>>!.   ",
        "             '#~~~~====%=%=%4%%444444>>>>>>!.   ",
        "             '@~~====|%=%%%%%4%444>>4>>>>>>!.   ",
        "             ,@~======%%%%%%>%%4444>>>>>>>>!.   ",
        "             '#====||=%%%%4%44444>4>>>>>>>>!.   ",
        "             ,@##@<#<<#@<<<<<<<<<<!<!!:!!!!!.   ",
        "             ................................   ",
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
    _("Complete Individual Report"),
    status=(_("Beta")),
    category=_("Text Reports"),
    description=_("Produces a complete report on the selected people."),
    xpm=get_xpm_image()
    )

register_book_item( 
    _("Individual Complete"), 
    _("Text"),
    IndivCompleteBareReportDialog,
    write_book_item,
    _options,
    "default" ,
    "individual_complete.xml",
    _make_default_style
    )
