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

"Support for dates"

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
from re import IGNORECASE, compile
import string
import time

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import Calendar
import Gregorian
import Julian
import Hebrew
import FrenchRepublic
import Errors

from intl import gettext as _

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
UNDEF = -999999

_calendar_val = [
    Gregorian.Gregorian,
    Julian.Julian,
    Hebrew.Hebrew,
    FrenchRepublic.FrenchRepublic,
    ]

#-------------------------------------------------------------------------
#
# Date class
#
#-------------------------------------------------------------------------
class Date:
    """
    The core date handling class for GRAMPs. Supports partial dates,
    date ranges, and alternate calendars.
    """
    formatCode = 0
    
    fstr = _("(from|between|bet|bet.)")
    tstr = _("(and|to|-)")
    
    fmt = compile("\s*%s\s+(.+)\s+%s\s+(.+)\s*$" % (fstr,tstr),IGNORECASE)
    fmt1 = compile("\s*([^-]+)\s*-\s*([^-]+)\s*$",IGNORECASE)

    def __init__(self,source=None):
        if source:
            self.start = SingleDate(source.start)
            if source.stop:
                self.stop = SingleDate(source.stop)
            else:
                self.stop = None
            self.range = source.range
            self.text = source.text
            self.calendar = source.calendar
        else:
            self.start = SingleDate()
            self.stop = None
            self.range = 0
            self.text = ""
            self.calendar = Gregorian.Gregorian()

    def get_calendar(self):
        return self.calendar

    def set_calendar(self,val):
        self.calendar = val()
        self.start.convert_to(val)
        if self.stop:
            self.stop.convert_to(val)

    def set_calendar_obj(self,val):
        self.calendar = val
        self.start.convert_to_obj(val)
        if self.stop:
            self.stop.convert_to_obj(val)

    def set_calendar_val(self,integer):
        val = _calendar_val[integer]
        self.calendar = val()
        self.start.convert_to(val)
        if self.stop:
            self.stop.convert_to(val)

    def get_start_date(self):
        return self.start

    def get_stop_date(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop

    def getLowYear(self):
        return self.start.getYear()
        
    def getHighYear(self):
        if self.stop == None:
            return self.start.getYear()
        else:
            return self.stop.getYear()

    def getYear(self):
        return self.start.year

    def getYearValid(self):
        return self.start.year != UNDEF

    def getMonth(self):
        if self.start.month == UNDEF:
            return UNDEF
        return self.start.month

    def getMonthValid(self):
        return self.start.month != UNDEF

    def getDay(self):
        return self.start.day

    def getDayValid(self):
        return self.start.day != UNDEF

    def getValid(self):
        """ Returns true if any part of the date is valid"""
        return self.start.year != UNDEF or self.start.month != UNDEF or self.start.day != UNDEF

    def getIncomplete(self):
        return self.range == 0 and self.start.year == UNDEF or \
               self.start.month == UNDEF or self.start.day == UNDEF

    def getStopYear(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop.year

    def getStopMonth(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop.month+1

    def getStopDay(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop.day

    def getText(self):
        return self.text

    def greater_than(self,other):
        return compare_dates(self,other) > 0

    def less_than(self,other):
        return compare_dates(self,other) < 0

    def equal_to(self,other):
        return compare_dates(self,other) == 0

    def set(self,text):
        try:
            match = Date.fmt.match(text)
            if match:
                matches = match.groups()
                self.start.set(matches[1])
		self.range = 0
                if self.stop == None:
                    self.stop = SingleDate()
                self.stop.calendar = self.calendar
                self.stop.set(matches[3])
                self.range = 1
                return
            
            match = Date.fmt1.match(text)
            if match:
                matches = match.groups()
                self.start.set(matches[0])
		self.range = 0
                if self.stop == None:
                    self.stop = SingleDate()
                self.stop.calendar = self.calendar
                self.stop.set(matches[1])
                self.range = 1
                return

            self.start.set(text)
            self.range = 0
        except Errors.DateError:
            if text != "":
                self.range = -1
            self.text = text

    def set_text(self,text):
        self.range = -1
        self.text = text

    def set_range(self,val):
        self.range = val
    
    def getDate(self):
        if self.range == 0:
            return self.start.getDate()
        elif self.range == -1:
            return self.text
        else:
            return _("from %(start_date)s to %(stop_date)s") % {
                'start_date' : self.start.getDate(),
                'stop_date' : self.stop.getDate() }

    def getQuoteDate(self):
        if self.range == 0:
            return self.start.getQuoteDate()
        elif self.range == -1:
            if self.text:
                return '"%s"' % self.text
            else:
                return ''
        else:
            return _("from %(start_date)s to %(stop_date)s") % {
                'start_date' : self.start.getQuoteDate(),
                'stop_date' : self.stop.getQuoteDate() }

    def isEmpty(self):
        s = self.start
        return s.year==UNDEF and s.month==UNDEF and s.day==UNDEF and not self.text

    def isValid(self):
        if self.range == -1:
            return 0
        elif self.range:
            return self.start.getValid() and self.stop.getValid()
        return self.start.getValid()
    
    def isRange(self):
        return self.range == 1
        
#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
class SingleDate:
    "Date handling"

    def __init__(self,source=None):
        if source:
            self.month = source.month
            self.day = source.day
            self.year = source.year
            self.mode = source.mode
            self.calendar = source.calendar
        else:
            self.month = UNDEF
            self.day = UNDEF
            self.year = UNDEF
            self.mode = Calendar.EXACT
            self.calendar = Gregorian.Gregorian()

    def setMode(self,val):
        self.mode = self.calendar.set_mode_value(val)

    def setMonth(self,val):
        if val > 14 or val < 0:
            self.month = UNDEF
        else:
            self.month = val

    def setMonthVal(self,s):
        self.month = self.calendar.set_value(s)

    def setDayVal(self,s):
        self.day = self.calendar.set_value(s)

    def setYearVal(self,s):
        if s:
            self.year = self.calendar.set_value(s)
        else:
            self.year = UNDEF

    def getMonth(self):
        return self.month

    def getMonthValid(self):
        return self.month != UNDEF

    def setDay(self,val):
        self.day = val

    def getDay(self):
	return self.day

    def getDayValid(self):
	return self.day != UNDEF

    def setYear(self,val):
        self.year = val

    def getYear(self):
        return self.year

    def getYearValid(self):
        return self.year != UNDEF

    def getValid(self):
        """ Returns true if any part of the date is valid"""
        if self.year == UNDEF and self.month == UNDEF and self.day == UNDEF:
            return 1
        return self.calendar.check(self.year,self.month,self.day)

    def setMonthStr(self,text):
        self.calendar.set_month_string(text)

    def getMonthStr(self):
	return self.calendar.month(self.month)

    def getIsoDate(self):
        if self.year == UNDEF:
            y = "????"
        else:
            y = "%04d" % self.year
        if self.month == UNDEF:
            if self.day == UNDEF:
                m = ""
            else:
                m = "-??"
        else:
            m = "-%02d" % (self.month)
        if self.day == UNDEF:
            d = ''
        else:
            d = "-%02d" % self.day
        return "%s%s%s" % (y,m,d)
        

    def getDate(self):
        return self.calendar.display(self.year, self.month, self.day, self.mode)

    def getQuoteDate(self):
        if self.year == UNDEF and self.month == UNDEF and self.day == UNDEF:
            return ""
        else:
            return self.calendar.quote_display(self.year, self.month, self.day, self.mode)

    def setIsoDate(self,v):
        data = string.split(v)
        if len(data) > 1:
            self.setMode(data[0])
            v = data[1]
        
        vals = string.split(v,'-')
        self.setYearVal(vals[0])
        if len(vals) > 1:
            try:
                self.setMonthVal(int(vals[1]))
            except:
                self.month = UNDEF
        else:
            self.month = UNDEF
        if len(vals) > 2:
            self.setDayVal(vals[2])
        else:
            self.day = UNDEF
        
    def getModeVal(self):
        return self.mode

    def setModeVal(self,val):
        self.mode = val
    
    def set(self,text):
        self.year, self.month, self.day, self.mode = self.calendar.set(text)
        
    def convert_to(self,val):
        sdn = self.calendar.get_sdn(self.year, self.month, self.day)
        self.calendar = val()
        (self.year, self.month, self.day) = self.calendar.get_ymd(sdn)

    def convert_to_obj(self,val):
        sdn = self.calendar.get_sdn(self.year, self.month, self.day)
        self.calendar = val
        (self.year, self.month, self.day) = self.calendar.get_ymd(sdn)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def not_too_old(date):
    time_struct = time.localtime(time.time())
    current_year = time_struct[0]
    if date.year != UNDEF and current_year - date.year > 110:
        return 0
    return 1

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def compare_dates(f,s):
    if f.calendar.NAME != s.calendar.NAME:
        return 1
    if f.range == -1 and s.range == -1:
        return cmp(f.text,s.text)
    if f.range == -1 or s.range == -1:
        return -1
    if f.range != s.range:
        return 1
    
    first = f.get_start_date()
    second = s.get_start_date()
    if first.year != second.year:
        return cmp(first.year,second.year)
    elif first.month != second.month:
        return cmp(first.month,second.month)
    elif f.range != 1:
        return cmp(first.day,second.day)
    else:
        first = f.get_stop_date()
        second = s.get_stop_date()
        if first.year != second.year:
            return cmp(first.year,second.year)
        elif first.month != second.month:
            return cmp(first.month,second.month)
        else:
            return cmp(first.day,second.day)
