#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2005  Donald N. Allingham
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
# Statistics plugin (w) 2004-2005 by Eero Tamminen.
# Partially based on code from the Timeline graph plugin.
#
# $Id$

"""
Statistics Chart report
"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import time
from gettext import gettext as _

#------------------------------------------------------------------------
#
# GNOME/gtk
#
#------------------------------------------------------------------------
import gtk

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import const                # gender and report type names
from RelLib import Person   # need Person internals for getting gender / gender name
import BaseDoc
import Report
import ReportUtils
import ReportOptions
import GenericFilter
from DateHandler import displayer as _dd

#------------------------------------------------------------------------
#
# Module globals
#
#------------------------------------------------------------------------

# needs to be global for the lookup_value_compare()
_lookup_items = {}

# needs to be global for python sort
def lookup_value_compare(a, b):
    "compare given keys according to corresponding _lookup_items values"
    return cmp(_lookup_items[a],_lookup_items[b])

class _options:
    # sort type identifiers
    SORT_VALUE = 0
    SORT_KEY = 1

    sorts = [
        (SORT_VALUE, "Item count", _("Item count")),
        (SORT_KEY, "Item name", _("Item name"))
    ]
    genders = [
        (Person.unknown, "Both", _("Both")),
        (Person.male, "Men", _("Men")),
        (Person.female, "Women", _("Women"))
    ]


#------------------------------------------------------------------------
#
# Data extraction methods from the database
#
#------------------------------------------------------------------------
class Extract:

    def __init__(self):
        """Methods for extracting statistical data from the database"""
	# key, non-localized name, localized name, type method, data method
        self.extractors = {
            'data_title':  ("Titles", _("Titles"),
			    self.get_person, self.get_title),
            'data_fname':  ("Forenames", _("Forenames"),
			    self.get_person, self.get_forename),
            'data_gender': ("Genders", _("Genders"),
			    self.get_person, self.get_gender),
            'data_byear':  ("Birth years", _("Birth years"),
			     self.get_birth, self.get_year),
            'data_dyear':  ("Death years", _("Death years"),
			     self.get_death, self.get_year),
            'data_bmonth': ("Birth months", _("Birth months"),
			    self.get_birth, self.get_month),
            'data_dmonth': ("Death months", _("Death months"),
			    self.get_death, self.get_month),
            'data_dcause': ("Causes of death", _("Causes of death"),
			     self.get_death, self.get_cause),
            'data_bplace': ("Birth places", _("Birth places"),
			    self.get_birth, self.get_place),
            'data_dplace': ("Death places", _("Death places"),
			     self.get_death, self.get_place),
            #'data_mplace': (self.marriage_place, "Marriage place", _("Marriage place")),
            #'data_fchild': (self.first_child_age, "Estimated ages for bearing the first child", _("Estimated ages for bearing the first child")),
            #'data_lchild': (self.last_child_age, "Estimated Ages for bearing the last child", _("Estimated Ages for bearing the last child")),
            #'data_ccount': (self.child_count, "Number of children", _("Number of children")),
            #'data_mage':  (self.marriage_age, "Estimated (first) marriage ages", _("Estimated (first) marriage ages")),
            'data_dage':   ("Estimated ages at death", _("Estimated ages at death"),
			    self.get_person, self.get_death_age),
            'data_age':   ("Estimated ages", _("Estimated ages"),
			    self.get_person, self.get_person_age)
        }

    # ----------------- data extraction methods --------------------
    # take an object and return a list of strings

    def get_title(self, person):
	"return title for given person"
        title = person.get_primary_name().get_title()
        if title:
            return [title]
        else:
            return [_("(Preferred) title missing")]
    
    def get_forename(self, person):
	"return forenames for given person"
        # because this returns list, other methods return list too
        firstnames = person.get_primary_name().get_first_name().strip()
        if firstnames:
            return [name.capitalize() for name in firstnames.split()]
        else:
            return [_("(Preferred) forename missing")]
        
    def get_gender(self, person):
	"return gender for given person"
        # TODO: why there's no Person.getGenderName?
        # It could be used by getDisplayInfo & this...
        if person.gender == Person.male:
            gender = const.male
        elif person.gender == Person.female:
            gender = const.female
        else:
            gender = const.unknown
        return [gender]

    def get_year(self, event):
	"return year for given event"
	date = event.get_date_object()
	if date:
            year = date.get_year()
            if year:
                return [str(year)]
        return [_("Date missing/inaccurate")]
        
    def get_month(self, event):
	"return month for given event"
	date = event.get_date_object()
	if date:
            month = date.get_month()
            if month:
                return [_dd._months[month]]
        return [_("Date missing/inaccurate")]

    def get_cause(self, event):
	"return cause for given event"
	cause = event.get_cause()
	if cause:
	    return [cause]
        return [_("Cause missing")]

    def get_place(self, event):
	"return place for given event"
	place_handle = event.get_place_handle()
	if place_handle:
            place = self.db.get_place_from_handle(place_handle).get_title()
	    if place:
		return [place]
        return [_("Place missing")]
    
    def get_person_age(self, person):
	"return age for given person, if alive"
	death = self.get_death(person)
	if not death:
            return self.estimate_age(person)
        return [_("Dead")]

    def get_death_age(self, person):
	"return age at death for given person, if dead"
	death = self.get_death(person)
	if death:
            return self.estimate_age(person)
        return [_("Alive")]

    def marriage_age(self, person):
        return "TODO: Marriage age stat unimplemented"

    def marriage_place(self, person):
        return "TODO: Marriage place stat unimplemented"

    def first_child_age(self, person):
        return "TODO: First child bearing age stat unimplemented"

    def last_child_age(self, person):
        return "TODO: Last child bearing age stat unimplemented"

    def child_count(self, person):
        return "TODO: Child count stat unimplemented"

    # ------------------- utility methods -------------------------

    def estimate_age(self, person):
        "return estimated age (range) for given person or error message"
        age = ReportUtils.estimate_age(self.db, person)
        if age[0] < 0 or age[1] < 0:
            # inadequate information
            return [_("Missing information")]
        if age[0] == age[1]:
            # exact year
            return [str(age[0])]
        else:
            # minimum and maximum
            return [str(age[0]) + "-" + str(age[1])]

    # ------------------- type methods -------------------------
    # take db and person and return suitable gramps object(s)

    def get_person(self, person):
	"return person"
	return person

    def get_birth(self, person):
	"return birth event for given person or None"
        birth_handle = person.get_birth_handle()
        if birth_handle:
            return self.db.get_event_from_handle(birth_handle)
	return None
    
    def get_death(self, person):
	"return death event for given person or None"
	death_handle = person.get_death_handle()
        if death_handle:
            return self.db.get_event_from_handle(death_handle)
	return None

    # ----------------- data collection methods --------------------

    def get_person_data(self, person, collect):
        """Adds data from the database to 'collect' for the given person,
           using methods rom the 'collect' data dict tuple
        """
        for chart in collect:
            # get the information
            type_func = chart[2]
	    data_func = chart[3]
            obj = type_func(person)	# e.g. get_date()
	    if obj:
		value = data_func(obj)	# e.g. get_year()
	    else:
		value = [_("Information missing")]
            # list of information found
            for key in value:
                if key in chart[1].keys():
                    chart[1][key] += 1
                else:
                    chart[1][key] = 1

    
    def collect_data(self, db, filter_func, options, genders,
                     year_from, year_to, no_years):
        """goes through the database and collects the selected personal
        data persons fitting the filter and birth year criteria. The
        arguments are:
        db          - the GRAMPS database
        filter_func - filtering function selected by the StatisticsDialog
        options     - report options_dict which sets which methods are used
        genders     - which gender(s) to include into statistics
        year_from   - use only persons who've born this year of after
        year_to     - use only persons who've born this year or before
        no_years    - use also people without any birth year
	
	Returns an array of tuple of:
	- Extraction method title
	- Dict of values with their counts
	(- Method)
        """
	self.db = db	# store for methods

        data = []
        ext = self.extractors
        # initialize data
        for key in options:
            if options[key] and key in self.extractors:
                # localized data title, value dict and method
                data.append((ext[key][1], {}, ext[key][2], ext[key][3]))
        
        # go through the people and collect data
        for person_handle in filter_func.apply(db, db.get_person_handles(sort_handles=False)):

            person = db.get_person_from_handle(person_handle)
            # check whether person has suitable gender
            if person.gender != genders and genders != Person.unknown:
                continue
        
            # check whether birth year is within required range
	    birth = self.get_birth(person).get_date_object()
	    if birth:
                if birth.get_year_valid():
                    year = birth.get_year()
                    if not (year >= year_from and year <= year_to):
                        continue
                else:
                    # if death before range, person's out of range too...
		    death = self.get_death(person).get_date_object()
		    if death:
                        if death.get_year_valid() and death.get_year() < year_from:
                            continue
                        if not no_years:
                            # do not accept people who are not known to be in range
                            continue

            self.get_person_data(person, data)
        return data

# GLOBAL: required so that we get access to _Extract.extractors[]
# Unfortunately class variables cannot reference instance methods :-/
_Extract = Extract()

#------------------------------------------------------------------------
#
# Statistics report
#
#------------------------------------------------------------------------
class StatisticsChart(Report.Report):

    def __init__(self, database, person, options_class):
        """
        Creates the Statistics object that produces the report.
        Uses the Extractor class to extract the data from the database.

        The arguments are:

        database        - the GRAMPS database instance
        person          - currently selected person
        options_class   - instance of the Options class for this report

        To see what the options are, check the options help in the options class.
        """
        Report.Report.__init__(self,database,person,options_class)
    
        filter_num = options_class.get_filter_number()
        filters = options_class.get_report_filters(person)
        filters.extend(GenericFilter.CustomFilters.get_filters())
        filterfun = filters[filter_num]

        options = options_class.handler.options_dict
        year_from = options['year_from']
        year_to = options['year_to']
        gender = options['gender']

        # title needs both data extraction method name + gender name
        if gender == Person.male:
            genders = _("men")
        elif gender == Person.female:
            genders = _("women")
        else:
            genders = None

        # needed for keyword based localization
        mapping = {
            'genders': genders,
            'year_from': year_from,
            'year_to': year_to
	}

        # extract requested items from the database and count them
        tables = _Extract.collect_data(database, filterfun, options,
                        gender, year_from, year_to, options['no_years'])

        self.data = []
        sortby = options['sortby']
        reverse = options['reverse']
        for table in tables:
            # generate sorted item lookup index index
            lookup = self.index_items(table[1], sortby, reverse)
            # document heading
            mapping['title'] = table[0]
            if genders:
                heading = "%(genders)s born %(year_from)04d-%(year_to)04d: %(title)s" % mapping
            else:
                heading = "Persons born %(year_from)04d-%(year_to)04d: %(title)s" % mapping
            self.data.append((heading, table[1], lookup))
	    # DEBUG
	    print heading
	    print table[1]
	
        
    def index_items(self, data, sort, reverse):
        """creates & stores a sorted index for the items"""
        global _lookup_items

        # sort by item keys
        index = data.keys()
        index.sort()
        if reverse:
            index.reverse()

        if sort == _options.SORT_VALUE:
            # set for the sorting function
            _lookup_items = data
        
            # then sort by value
            index.sort(lookup_value_compare)
            if reverse:
                index.reverse()

        return index

    
    def define_graphics_styles(self):
        """
        Define the graphics styles used by the report. Paragraph definitions
        have already been defined in the document. The styles used are:

        SC-bar - A red bar with 0.5pt black line.
        SC-text  - Contains the SC-Name paragraph style used for
                the individual's name
        SC-title - Contains the SC-Title paragraph style used for
                the title of the document
        """
        g = BaseDoc.GraphicsStyle()
        g.set_line_width(0.8)
        g.set_color((0,0,0))
        g.set_fill_color((255,0,0))
        self.doc.add_draw_style("SC-bar",g)

        g = BaseDoc.GraphicsStyle()
        g.set_paragraph_style("SC-Text")
        g.set_color((0,0,0))
        g.set_fill_color((255,255,255))
        g.set_line_width(0)
        self.doc.add_draw_style("SC-text",g)

        g = BaseDoc.GraphicsStyle()
        g.set_paragraph_style("SC-Title")
        g.set_color((0,0,0))
        g.set_fill_color((255,255,255))
        g.set_line_width(0)
        g.set_width(self.doc.get_usable_width())
        self.doc.add_draw_style("SC-title",g)


    def write_report(self):
        "output the selected statistics..."

        self.doc.start_page()
        
        for data in self.data:
            self.output_chart(data[0], data[1], data[2])
            
        self.doc.end_page()    


    def output_chart(self, title, data, lookup):

        pt2cm = ReportUtils.pt2cm
        font = self.doc.style_list['SC-Text'].get_font()

        # set layout variables
        width = self.doc.get_usable_width()
        row_h = pt2cm(font.get_size())
        max_y = self.doc.get_usable_height() - row_h
        pad =  row_h * 0.5
        
        # calculate maximum key string size
        max_size = 0
        max_value = 0
        for key in lookup:
            max_size = max(self.doc.string_width(font, key), max_size)
            max_value = max(data[key], max_value)
        # horizontal area for the gfx bars
        start = pt2cm(max_size) + 1.0
        size = width - 1.5 - start

        # start output
        self.doc.center_text('SC-title', title, width/2, 0)
        print title

        yoffset = pt2cm(self.doc.style_list['SC-Title'].get_font().get_size())
        for key in lookup:
            yoffset += (row_h + pad)
            if yoffset > max_y:
            # for graphical report, page_break() doesn't seem to work
                self.doc.end_page()
                self.doc.start_page()
                yoffset = 0

            # right align the text to the value
            x = start - pt2cm(self.doc.string_width(font, key)) - 1.0
            self.doc.draw_text('SC-text', key, x, yoffset)
            print key + ":",
        
            value = data[key]
            stop = start + (size * value / max_value)
            path = ((start, yoffset),
                    (stop, yoffset),
                    (stop, yoffset + row_h),
                    (start, yoffset + row_h))
            self.doc.draw_path('SC-bar', path)
            self.doc.draw_text('SC-text', str(value), stop + 0.5, yoffset)
            print "%d/%d" % (value, max_value)

        return

#------------------------------------------------------------------------
#
# Statistics report options
#
#------------------------------------------------------------------------
class StatisticsChartOptions(ReportOptions.ReportOptions):
    """
    Defines options and provides their handling interface.
    """
    def __init__(self,name, person_id=None):
        ReportOptions.ReportOptions.__init__(self, name, person_id)

    def set_new_options(self):
    # Options specific for this report
        self.options_dict = {
            'gender'    : Person.unknown,
            'sortby'    : _options.SORT_VALUE,
            'reverse'   : 0,
            'year_from' : 1700,
            'year_to'   : time.localtime()[0],
            'no_years'  : 0
        }
        for key in _Extract.extractors:
            self.options_dict[key] = 0
        self.options_dict['data_gender'] = 1

        self.options_help = {
            'gender'    : ("=num", "Genders included",
                               ["%d\t%s" % (item[0], item[1]) for item in _options.genders],
                               False),
            'sortby'    : ("=num", "Sort chart items by",
                                ["%d\t%s" % (item[0], item[1]) for item in _options.sorts],
                                False),
            'reverse'   : ("=0/1", "Whether to sort in reverse order",
                                ["Do not sort in reverse", "Sort in reverse"],
                                True),
            'year_from' : ("=num", "Birth year from which to include people",
                                "earlier than 'year_to' value"),
            'year_to'   : ("=num", "Birth year until which to include people",
                                "smaller than %d" % self.options_dict['year_to']),
            'no_years'  : ("=0/1", "Whether to include people without birth years",
                                ["Do not include", "Include"], True)
        }
        for key in _Extract.extractors:
            self.options_help[key] = ("=0/1", _Extract.extractors[key][0],
                                ["Leave char with this data out", "Include chart with this data"],
                                True)

				
    def enable_options(self):
        # Semi-common options that should be enabled for this report
        self.enable_dict = {
            'filter'    : 0,
        }
    
	
    def make_default_style(self, default_style):
        """Make the default output style for the Statistics report."""
        f = BaseDoc.FontStyle()
        f.set_size(10)
        f.set_type_face(BaseDoc.FONT_SERIF)
        p = BaseDoc.ParagraphStyle()
        p.set_font(f)
        p.set_alignment(BaseDoc.PARA_ALIGN_RIGHT)
        p.set_description(_("The style used for the items and values."))
        default_style.add_style("SC-Text",p)

        f = BaseDoc.FontStyle()
        f.set_size(14)
        f.set_type_face(BaseDoc.FONT_SANS_SERIF)
        p = BaseDoc.ParagraphStyle()
        p.set_font(f)
        p.set_alignment(BaseDoc.PARA_ALIGN_CENTER)
        p.set_description(_("The style used for the title of the page."))
        default_style.add_style("SC-Title",p)

	
    def get_report_filters(self, person):
        """Set up the list of possible content filters."""
    
        if person:
            name = person.get_primary_name().get_name()
            handle = person.get_handle()
        else:
            name = 'PERSON'
            handle = ''
    
        all = GenericFilter.GenericFilter()
        all.set_name(_("Entire Database"))
        all.add_rule(GenericFilter.Everyone([]))

        des = GenericFilter.GenericFilter()
        des.set_name(_("Descendants of %s") % name)
        des.add_rule(GenericFilter.IsDescendantOf([handle, 1]))

        ans = GenericFilter.GenericFilter()
        ans.set_name(_("Ancestors of %s") % name)
        ans.add_rule(GenericFilter.IsAncestorOf([handle, 1]))

        com = GenericFilter.GenericFilter()
        com.set_name(_("People with common ancestor with %s") % name)
        com.add_rule(GenericFilter.HasCommonAncestorWith([handle]))

        return [all, des, ans, com]

    
    def add_user_options(self, dialog):
        """
        Override the base class add_user_options task to add
        report specific options
        """
        # how to sort the data
        self.sort_menu = gtk.combo_box_new_text()
        for item_idx in range(len(_options.sorts)):
            item = _options.sorts[item_idx]
            self.sort_menu.append_text(item[2])
            if item[0] == self.options_dict['sortby']:
                self.sort_menu.set_active(item_idx)
        tip = _("Select how the statistical data is sorted.")
        dialog.add_option(_("Sort chart items by"), self.sort_menu, tip)

        # sorting order
        tip = _("Check to reverse the sorting order.")
        self.reverse = gtk.CheckButton(_("Sort in reverse order"))
        self.reverse.set_active(self.options_dict['reverse'])
        dialog.add_option(None, self.reverse, tip)
        self.reverse.show()

        # year range
        self.from_box = gtk.Entry(4)
        self.from_box.set_text(str(self.options_dict['year_from']))
        self.to_box = gtk.Entry(4)
        self.to_box.set_text(str(self.options_dict['year_to']))

        box = gtk.HBox()
        box.add(self.from_box)
        box.add(gtk.Label("-"))
        box.add(self.to_box)
        tip = _("Select year range within which people need to be born to be selected for statistics.")
        dialog.add_option(_('People born between'), box, tip)
        box.show_all()

        # include people without birth year?
        tip = _("Check this if you want people who have no birth date or year to be accounted also in the statistics.")
        self.no_years = gtk.CheckButton(_("Include people without birth years"))
        self.no_years.set_active(self.options_dict['no_years'])
        dialog.add_option(None, self.no_years, tip)
        self.no_years.show()

        # gender selection
        self.gender_menu = gtk.combo_box_new_text()
        for item_idx in range(len(_options.genders)):
            item = _options.genders[item_idx]
            self.gender_menu.append_text(item[2])
            if item[0] == self.options_dict['gender']:
                self.gender_menu.set_active(item_idx)
        tip = _("Select which genders are included into statistics.")
        dialog.add_option(_("Genders included"), self.gender_menu, tip)

        # List of available charts on a separate option tab
	idx = 0
	half = (len(_Extract.extractors)+1)/2
        hbox = gtk.HBox()
        vbox = gtk.VBox()
        self.charts = {}
        for key in _Extract.extractors:
            check = gtk.CheckButton(_Extract.extractors[key][1])
            check.set_active(self.options_dict[key])
            self.charts[key] = check
	    vbox.add(check)
	    idx += 1
	    if idx == half:
		hbox.add(vbox)
		vbox = gtk.VBox()
        hbox.add(vbox)
	tip = _("Mark checkboxes to add charts with indicated data")
	dialog.add_frame_option("Chart Selection", "", hbox, tip)
        hbox.show_all()

	
    def parse_user_options(self, dialog):
        """
        Parses the custom options that we have added.
        """
        self.options_dict['sortby'] = _options.sorts[self.sort_menu.get_active()][0]
        self.options_dict['reverse'] = int(self.reverse.get_active())
        self.options_dict['year_to'] = int(self.to_box.get_text())
        self.options_dict['year_from'] = int(self.from_box.get_text())
        self.options_dict['no_years'] = int(self.no_years.get_active())
        self.options_dict['gender'] = _options.genders[self.gender_menu.get_active()][0]
        for key in _Extract.extractors:
            self.options_dict[key] = int(self.charts[key].get_active())

#------------------------------------------------------------------------
#
# Register report/options
#
#------------------------------------------------------------------------
from PluginMgr import register_report

register_report(
    name = 'statisticschart',
    category = const.CATEGORY_DRAW,
    report_class = StatisticsChart,
    options_class = StatisticsChartOptions,
    modes = Report.MODE_GUI | Report.MODE_BKI | Report.MODE_CLI,
    translated_name = _("Statistics Chart"),
    status = (_("Alpha")),
    author_name="Eero Tamminen",
    author_email="",
    description= _("Generates statistical bar graphs.")
    )
