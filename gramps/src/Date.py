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

"Support for the dates"

from re import IGNORECASE, compile
import string

from Calendar import *
from intl import gettext
_ = gettext

#-------------------------------------------------------------------------
#
# Calendar Mappings
#
#-------------------------------------------------------------------------
GREGORIAN = 0
JULIAN = 1
HEBREW = 2
FRENCH = 3

#-------------------------------------------------------------------------
#
# Month mappings
#
#-------------------------------------------------------------------------
_fmonth = [
    "Vend�miaire", "Brumaire", "Frimaire", "Niv�se", "Pluvi�se",
    "Vent�se", "Germinal", "Flor�al", "Prairial", "Messidor", "Thermidor",
    "Fructidor", "Extra", ]

_fmonth2num = {
    "vend" : 0, "brum" : 1, "frim" : 2, "nivo" : 3, "pluv" : 4,
    "vent" : 5, "germ" : 6, "flor" : 7, "prai" : 8, "mess" : 9,
    "ther" :10, "fruc" :11, "extr" : 12,"niv�" : 3 }

_hmonth = [
    "Tishri", "Heshvan", "Kislev", "Tevet",  "Shevat", "AdarI",
    "AdarII", "Nisan",  "Iyyar",   "Sivan",  "Tammuz", "Av",     "Elul"
]

_hmonth2num = {
    "tishri" : 0, "heshvan" : 1, "kislev" : 2, "tevet" : 3,
    "shevat" : 4, "adari"   : 5, "adarii" : 6, "nisan" : 7,
    "iyyar"  : 8, "sivan"   : 9, "tammuz" :10, "av"    : 11,
    "elul"   : 12,"tsh"     : 0, "csh"    : 1, "ksl"   : 2,
    "tvt"    : 3, "shv"     : 4, "adr"    : 5, "ads"   : 6,
    "nsn"    : 7, "iyr"     : 8, "svn"    : 9, "tmz"   : 10,
    "aav"    :11, "ell"     :12,
    }

_mname = [ _("January"),   _("February"),  _("March"),    _("April"),
           _("May"),       _("June"),      _("July"),     _("August"),
           _("September"), _("October"),   _("November"), _("December") ]

_m2num = { string.lower(_mname[0][0:3]) : 0,
           string.lower(_mname[1][0:3]) : 1,
           string.lower(_mname[2][0:3]) : 2,
           string.lower(_mname[3][0:3]) : 3,
           string.lower(_mname[4][0:3]) : 4,
           string.lower(_mname[5][0:3]) : 5,
           string.lower(_mname[6][0:3]) : 6,
           string.lower(_mname[7][0:3]) : 7,
           string.lower(_mname[8][0:3]) : 8,
           string.lower(_mname[9][0:3]) : 9,
           string.lower(_mname[10][0:3]) : 10,
           string.lower(_mname[11][0:3]) : 11 }


UNDEF = -999999

#-------------------------------------------------------------------------
#
# Date class
#
#-------------------------------------------------------------------------
class Date:
    formatCode = 0
    entryCode = 0
    
    Error = "Illegal Date"

    range = 1
    normal = 0

    from_str = _("(from|between|bet|bet.)")
    to_str = _("(and|to|-)")
    
    fmt = compile(r"\s*" + from_str + r"\s+(.+)\s+" + to_str + r"\s+(.+)\s*$",
                     IGNORECASE)

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
            self.calendar = GREGORIAN

    def get_calendar(self):
        return self.calendar

    def set_calendar(self,val):
        self.calendar = val
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

    def getYear(self):
        return self.start.year

    def getHighYear(self):
        if self.stop == None:
            return self.start.year
        else:
            return self.stop.year

    def getLowYear(self):
        return self.start.getYear()

    def getMonth(self):
        if self.start.month == UNDEF:
            return UNDEF
        return self.start.month+1

    def getDay(self):
        return self.start.day

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
        match = Date.fmt.match(text)
        try:
            if match:
                matches = match.groups()
                self.start.set(matches[1])
                if self.stop == None:
                    self.stop = SingleDate()
                self.stop.calendar = self.calendar
                self.stop.set(matches[3])
                self.range = 1
            else:
                self.start.set(text)
                self.range = 0
        except Date.Error:
            self.range = -1
            self.text = text

    def set_range(self,val):
        self.range = val

    def get_fmt(self,func):
	if self.range == 0:
	    return func(self.start)
        elif self.range == -1:
            return self.text
	else:
            d1 = func(self.start)
            d2 = func(self.stop)
	    return "%s %s %s %s" % ( _("from"),d1,_("to"),d2 )
    
    def getDate(self):
        return self.get_fmt(SingleDate.getDate)

    def getQuoteDate(self):
        if self.calendar == GREGORIAN:
            return self.getGregorianQuoteDate()
        elif self.calendar == JULIAN:
            return self.get_quote_date(_mname,_("Julian"))
        elif self.calendar == HEBREW:
            return self.get_quote_date(_hmonth,_("Hebrew"))
        else:
            return self.get_quote_date(_fmonth,_("French"))

    def getGregorianQuoteDate(self):
        if self.range == 0:
            return _func(self.start)
        elif self.range == -1:
            if self.text:
                return '"%s"' % self.text
            else:
                return ''
        else:
            d1 = _func(self.start)
            d2 = _func(self.stop)
            return "%s %s %s %s" % ( _("from"),d1,_("to"), d2)

    def get_quote_date(self,month_map,cal_str):
        if self.range == 0:
            return "%s (%s)" % (self.start.display_calendar(month_map),cal_str)
        elif self.range == -1:
            if self.text:
                return '"%s (%s)"' % (self.text,cal_str)
            else:
                return ''
        else:
            d1 = self.start.display_calendar(month_map)
            d2 = self.stop.display_calendar(month_map)
            return "%s %s %s %s (%s)" % ( _("from"),d1,_("to"), d2,cal_str)

    def getSaveDate(self):
	if self.range == 1:
            d1 = self.start.getSaveDate()
            d2 = self.stop.getSaveDate()
	    return "FROM %s TO %s" % (d1,d2)
        elif self.range == -1:
            return self.text
	else:
            return self.start.getSaveDate()

    def isEmpty(self):
        s = self.start
        return s.year==UNDEF and s.month==UNDEF and s.day==UNDEF

    def isValid(self):
        return self.range != -1 

    def isRange(self):
        return self.range == 1
        
#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def set_format_code(code):
    global _func
    Date.formatCode = code
    _func = SingleDate.fmtFunc[code]

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def get_format_code():
    return Date.formatCode

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
class SingleDate:
    "Date handling"
    
    exact = 0
    about = 1
    before = 2
    after = 3
    
    emname =[ 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ]

    em2num ={ "jan" : 0, "feb" : 1, "mar" : 2, "apr" : 3,
              "may" : 4, "jun" : 5, "jul" : 6, "aug" : 7,
              "sep" : 8, "oct" : 9, "nov" : 10,"dec" : 11 }

    m2v = { _("abt")    : about ,
            _("about")  : about,
            _("abt.")   : about,
            _("est")    : about ,
            _("est.")   : about ,
            _("circa")  : about,
            _("around") : about,
            _("before") : before,
            _("bef")    : before,
            _("bef.")   : before,
            _("after")  : after,
            _("aft.")   : after,
            _("aft")    : after }

    modifiers = "(" + \
                _("abt\.?") + '|' + \
                _("about") + '|' + \
                _("est\.?") + '|' + \
                _("circa") + '|' + \
                _("around") + '|' + \
                _("before") + '|' + \
                _("after") + '|' + \
                _("aft\.?") + '|' + \
                _("bef\.?") + '|' + \
                "abt" + '|' + \
                "aft" + '|' + \
                "bef" + ')'
    
    start = "^\s*" + modifiers + "?\s*"
    
    fmt1 = compile(start + "(\S+)(\s+\d+\s*,)?\s*(\d+)?\s*$", IGNORECASE)
    fmt2 = compile(start + "(\d+)\.?\s+(\S+)(\s+\d+)?\s*$", IGNORECASE)
    quick= compile(start + "(\d+)?\s(\S\S\S)?\s(\d+)?", IGNORECASE)
    fmt3 = compile(start + r"([?\d]+)\s*[./-]\s*([?\d]+)\s*[./-]\s*([?\d]+)\s*$",
                      IGNORECASE)
    fmt7 = compile(start + r"([?\d]+)\s*[./-]\s*([?\d]+)\s*$", IGNORECASE)
    fmt4 = compile(start + "(\S+)\s+(\d+)\s*$", IGNORECASE)
    fmt5 = compile(start + "(\d+)\s*$", IGNORECASE)
    fmt6 = compile(start + "(\S+)\s*$", IGNORECASE)

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
            self.mode = SingleDate.exact
            self.calendar = GREGORIAN

    def setMode(self,val):
        if val == None:
            self.mode = SingleDate.exact
        else:
            val = string.lower(val)
            self.mode = SingleDate.m2v[val]

    def setMonth(self,val):
        if val > 12 or val < 0:
            self.month = UNDEF
        else:
            self.month = val - 1

    def setMonthVal(self,s):
        try:
            val = int(s)
            self.month = val - 1
        except ValueError:
            self.month = UNDEF

    def setDayVal(self,s):
        try:
            val = int(s)
            self.day = val
        except ValueError:
            self.day = UNDEF

    def setYearVal(self,s):
        try:
            val = int(s)
            self.year = val
        except ValueError:
            self.year = UNDEF

    def getMonth(self):
        if self.month == UNDEF:
            return UNDEF
        return self.month + 1

    def setDay(self,val):
        self.day = val

    def getDay(self):
	return self.day

    def setYear(self,val):
        self.year = val

    def getYear(self):
        return self.year

    def setMonthStr(self,text):
        try:
            self.month = _m2num[string.lower(text[0:3])]
        except KeyError:
            self.setMonthStrEng(text)

    def setMonthStrEng(self,text):
        try:
            self.month = SingleDate.em2num[string.lower(text[0:3])]
        except KeyError:
            self.month = UNDEF

    def getMonthStr(self):
	return _mname[self.month]

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
            m = "-%02d" % (self.month+1)
        if self.day == UNDEF:
            d = ''
        else:
            d = "-%02d" % self.day
        return "%s%s%s" % (y,m,d)
        
    def getSaveDate(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = SingleDate.emname[self.month]
            else:	
                retval = "%s %d" % (SingleDate.emname[self.month],self.year)
        elif self.month == UNDEF:
            retval = str(self.year)
        else:
            month = SingleDate.emname[self.month]
            if self.year == UNDEF:
                retval = "%d %s ????" % (self.day,month)
            else:
                retval = "%d %s %d" % (self.day,month,self.year)

        if self.mode == SingleDate.about:
            retval = "ABT %s"  % retval
        elif self.mode == SingleDate.before:
            retval = "BEFORE" + " " + retval
        elif self.mode == SingleDate.after:
            retval = "AFTER" + " " + retval
        return retval

    def get_fmt1(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = _mname[self.month]
            else:	
                retval = "%s %d" % (_mname[self.month],self.year)
        elif self.month == UNDEF:
            retval = str(self.year)
        else:
            month = _mname[self.month]
            if self.year == UNDEF:
                retval = "%s %d, ????" % (month,self.day)
            else:
                retval = "%s %d, %d" % (month,self.day,self.year)

        if self.mode == SingleDate.about:
	    retval = _("about") + ' ' + retval
        elif self.mode == SingleDate.before:
            retval = _("before") + ' ' + retval
        elif self.mode == SingleDate.after:
            retval = _("after") + ' ' + retval
        return retval

    def get_fmt2(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.month != UNDEF and self.month != UNDEF:
            month = _mname[self.month]
            if self.year == UNDEF:
                retval = "%s %d, ????" % (string.upper(month[0:3]),self.day)
            else:
                retval = "%s %d, %d" % (string.upper(month[0:3]),self.day,self.year)
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                month = _mname[self.month]
                retval = string.upper(month[0:3])
            else:	
                month = _mname[self.month]
                retval = "%s %d" % (string.upper(month[0:3]),self.year)
        else:
            retval =  str(self.year)

        if self.mode == SingleDate.about:
            retval = "%s %s" % (_("abt"),retval)
        elif self.mode == SingleDate.before:
            retval = "%s %s" % (_("before"),retval)
        elif self.mode == SingleDate.after:
            retval = "%s %s" % (_("after"),retval)

        return retval

    def get_fmt3(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                month = _mname[self.month]
                retval = string.upper(month[0:3])
            else:
                month = _mname[self.month]
                retval = "%s %d" % (string.upper(month[0:3]),self.year)
        elif self.month == UNDEF:
            retval = str(self.year)
        else:
            month = _mname[self.month]
            if self.year == UNDEF:
                retval = "%d %s ????" % (self.day,string.upper(month[0:3]))
            else:
                retval = "%d %s %d" % (self.day,string.upper(month[0:3]),self.year)

        if self.mode == SingleDate.about:
            retval = "%s %s" % (_("ABT"),retval)
        elif self.mode == SingleDate.before:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == SingleDate.after:
            retval = "%s %s" % (_("AFTER"),retval)
        return retval

    def get_fmt10(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = _mname[self.month]
            else:
                month = _mname[self.month]
                retval = "%s %d" % (month,self.year)
        elif self.month == UNDEF:
            retval = str(self.year)
        else:
            month = _mname[self.month]
            if self.year == UNDEF:
                retval = "%d. %s ????" % (self.day,month)
            else:
                retval = "%d. %s %d" % (self.day,month,self.year)

        if self.mode == SingleDate.about:
            retval = "%s %s" % (_("ABT"),retval)
        elif self.mode == SingleDate.before:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == SingleDate.after:
            retval = "%s %s" % (_("AFTER"),retval)

        return retval

    def get_mmddyyyy(self,sep):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = "%02d%s??%s??" % (self.month+1,sep,sep)
            else:
                retval = "%02d%s??%s%04d" % (self.month+1,sep,sep,self.year)
        elif self.month == UNDEF:
            retval = "??%s%02d%s%04d" % (sep,self.day,sep,self.year)
        else:
            if self.year == UNDEF:
                retval = "%02d%s%02d%s????" % (self.month+1,sep,self.day,sep)
            else:
                retval = "%02d%s%02d%s%04d" % (self.month+1,sep,self.day,sep,self.year)

        if self.mode == SingleDate.about:
            retval = "%s %s" % (_("ABT"),retval)
        elif self.mode == SingleDate.before:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == SingleDate.after:
            retval = "%s %s" % (_("AFTER"),retval)

        return retval

    def get_yyyymmdd(self,sep):
        retval = ""
        
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            pass
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = "????%s%02d%s??" % (sep,self.month+1,sep)
            else:
                retval = "%04d%s%02d" % (self.year,sep,self.month+1)
        elif self.month == UNDEF:
            retval = "%04d%s??%s%02d" % (self.year,sep,sep,self.day)
        else:
            if self.year == UNDEF:
                retval = "????%02d%s%02d%s" % (self.month+1,sep,self.day,sep)
            else:
                retval = "%02d%s%02d%s%02d" % (self.year,sep,self.month+1,sep,self.day)

        if self.mode == SingleDate.about:
            retval = "%s %s" % (_("ABT"),retval)

        if self.mode == SingleDate.before:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == SingleDate.after:
            retval = "%s %s" % (_("AFTER"),retval)

        return retval

    def get_fmt4(self):
        return self.get_mmddyyyy("/")

    def get_fmt5(self):
        return self.get_mmddyyyy("-")

    def get_fmt8(self):
        return self.get_mmddyyyy(".")

    def get_ddmmyyyy(self,sep):
        retval = ""
        
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            pass
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = "??%s%02d%s??" % (sep,self.month+1,sep)
            else:
                retval = "??%s%02d%s%04d" % (sep,self.month+1,sep,self.year)
        elif self.month == UNDEF:
            retval = "%02d%s??%s%04d" % (self.day,sep,sep,self.year)
        else:
            if self.year == UNDEF:
                retval = "%02d%s%02d%s????" % (self.day,sep,self.month+1,sep)
            else:
                retval = "%02d%s%02d%s%04d" % (self.day,sep,self.month+1,sep,self.year)

        if self.mode == SingleDate.about:
            retval = "%s %s" % (_("ABT"),retval)
        if self.mode == SingleDate.before:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == SingleDate.after:
            retval = "%s %s" % (_("AFTER"),retval)

        return retval

    def get_fmt6(self):
        return self.get_ddmmyyyy("/")

    def get_fmt7(self):
        return self.get_ddmmyyyy("-")

    def get_fmt9(self):
        return self.get_ddmmyyyy(".")

    def get_fmt11(self):
        return self.get_yyyymmdd("/")

    def get_fmt12(self):
        return self.get_yyyymmdd("-")

    def get_fmt13(self):
        return self.get_yyyymmdd(".")

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    fmtFunc = [ get_fmt1, get_fmt2, get_fmt3, get_fmt4, get_fmt5, get_fmt6,
                get_fmt7, get_fmt8, get_fmt9, get_fmt10, get_fmt11, get_fmt12,
                get_fmt13]

    def display_calendar(self,month_map):
        if self.year==UNDEF:
            if self.month == UNDEF:
                return ""
            elif self.day == UNDEF:
                return month_map[self.month]
            else:
                return "%02d %s" % (self.day,month_map[self.month])
        elif self.month == UNDEF:
            return str(self.year)
        elif self.day == UNDEF:
            return "%s %d" % (month_map[self.month],self.year)
        else:
            return "%02d %s %d" % (self.day,month_map[self.month],self.year)

    def getDate(self):
        if self.calendar == GREGORIAN:
            return _func(self)
        elif self.calendar == JULIAN:
            return self.display_calendar(_mname)
        elif self.calendar == HEBREW:
            return self.display_calendar(_hmonth)
        else:
            return self.display_calendar(_fmonth)

    def setIsoDate(self,v):
        data = string.split(v)
        if len(data) > 1:
            self.setMode(data[0])
            v = data[1]
        
        vals = string.split(v,'-')
        self.setYearVal(vals[0])
        if len(vals) > 1:
            self.setMonthVal(vals[1])
        if len(vals) > 2:
            self.setDayVal(vals[2])
        
    def getModeVal(self):
        return self.mode

    def setModeVal(self,val):
        self.mode = val
    
    def set(self,text):
        if self.calendar == GREGORIAN:
            self.set_gregorian(text)
        elif self.calendar == JULIAN:
            self.set_calendar(text,_m2num,3)
        elif self.calendar == HEBREW:
            self.set_calendar(text,_hmonth2num,0)
        else:
            self.set_calendar(text,_fmonth2num,4)

    def set_calendar(self,text,month_map,l):
        match = SingleDate.fmt2.match(text)
        if match:
            matches = match.groups()
            self.setMode(matches[0])
            if l == 0:
                mon = string.lower(matches[2])
            else:
                mon = string.lower(matches[2])[0:l]
            if month_map.has_key(mon):
                self.setYear(int(matches[3]))
                self.setMonth(month_map[mon]+1)
                self.setDay(int(matches[1]))
                return
            else:
                self.setYear(int(matches[3]))
                self.setMonth(UNDEF)
                self.setDay(UNDEF)
                return
        match = SingleDate.fmt3.match(text)
        if match:
            matches = match.groups()
            self.setMode(matches[0])
            self.setYearVal(matches[3])
            self.setMonthVal(matches[2])
            self.setDayVal(matches[1])
            return

        match = SingleDate.fmt4.match(text)
        if match:
            matches = match.groups()
            self.setMode(matches[0])
            if l == 0:
                mon = string.lower(matches[1])
            else:
                mon = string.lower(matches[1])[0:l]
            self.setYearVal(matches[2])
            self.setMonth(month_map[mon]+1)
            self.day = UNDEF
            return

        match = SingleDate.fmt5.match(text)
        if match:
            matches = match.groups()
            self.setMode(matches[0])
            self.setYearVal(matches[1])
            self.month = UNDEF
            self.day = UNDEF
            return

        self.year = UNDEF
        self.month = UNDEF
        self.day = UNDEF

    def set_gregorian(self,text):
        match = SingleDate.fmt2.match(text)
        if match != None:
            matches = match.groups()
            self.setMode(matches[0])
            self.setMonthStr(matches[2])
            if self.month == UNDEF:
                raise Date.Error,text
            self.day = int(matches[1])
            if len(matches) == 4:
                self.setYearVal(matches[3])
            else:
                self.year = UNDEF
            return 1
        
        match = SingleDate.fmt5.match(text)
        if match != None:
            matches = match.groups()
            self.setMode(matches[0])
            self.month = UNDEF
            self.day = UNDEF
            self.year = int(matches[1])
            return 1

        match = SingleDate.fmt7.match(text)
        if match != None:
            matches = match.groups()
            self.setMode(matches[0])
            if Date.entryCode == 2:
                self.setMonthVal(matches[2])
                self.setYearVal(matches[1])
            else:
                self.setMonthVal(matches[1])
                self.setYearVal(matches[2])
            return 1

        match = SingleDate.fmt3.match(text)
        if match != None:
            matches = match.groups()
            self.setMode(matches[0])
            if Date.entryCode == 0:
                self.setMonthVal(matches[1])
                self.setDayVal(matches[2])
                self.setYearVal(matches[3])
            elif Date.entryCode == 1:
                self.setMonthVal(matches[2])
                self.setDayVal(matches[1])
                self.setYearVal(matches[3])
            else:
                self.setMonthVal(matches[2])
                self.setDayVal(matches[3])
                self.setYearVal(matches[1])
            return 1

        match = SingleDate.fmt1.match(text)
        if match != None:
            matches = match.groups()
            self.setMode(matches[0])
            self.setMonthStr(matches[1])
            if self.month == UNDEF:
                raise Date.Error,text
            val = matches[2]
            if val:
                self.day = int(string.replace(val,',',''))
            else:
                self.day = UNDEF
            self.setYearVal(matches[3])
            return 1

        match = SingleDate.fmt4.match(text)
        if match != None:
            matches = match.groups()
            self.setMode(matches[0])
            self.setMonthStr(matches[1])
            if self.month == UNDEF:
                raise Date.Error,text
            self.day = UNDEF
            if len(matches) == 4:
                self.setYearVal(matches[3])
            return 1

        match = SingleDate.fmt6.match(text)
        if match != None:
            matches = match.groups()
            self.setMode(matches[0])
            self.setMonthVal(matches[1])
            self.day = UNDEF
            self.year = UNDEF
            return 1

        raise Date.Error,text

    def get_sdn(self):
        if self.year == UNDEF:
            return 0
        if self.month == UNDEF:
            month = 1
        else:
            month = self.month + 1
        if self.day == UNDEF:
            day = 1
        else:
            day = self.day
            
        if self.calendar == GREGORIAN:
            sdn = gregorian_to_sdn(self.year,month,day)
        elif self.calendar == FRENCH:
            sdn = french_to_sdn(self.year,month,day)
        if self.calendar == HEBREW:
            sdn = jewish_to_sdn(self.year,month,day)
        if self.calendar == JULIAN:
            sdn = julian_to_sdn(self.year,month,day)
        return sdn

    def convert_to(self,val):
        if val == GREGORIAN:
            self.convert_calendar(sdn_to_gregorian,val)
        elif val == JULIAN:
            self.convert_calendar(sdn_to_julian,val)
        elif val == HEBREW:
            self.convert_calendar(sdn_to_jewish,val)
        else:
            self.convert_calendar(sdn_to_french,val)

    def convert_calendar(self,func,mode):
        sdn = self.get_sdn()
        (y,m,d) = func(sdn)
        self.calendar = mode
        if y == 0 and m == 0 and d == 0:
            self.year = UNDEF
            self.month = UNDEF
            self.day = UNDEF
        else:
            self.year = y
            self.month = m-1
            self.day = d

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def compare_dates(f,s):
    if f.calendar != s.calendar:
        return 1
    if f.range == -1 and s.range == -1:
        return cmp(f.text,s.text)
    if f.range == -1 or s.range == -1:
        return -1
    
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

            
_func = SingleDate.fmtFunc[0]

if __name__ == "__main__":

    def checkit(s):
        d = Date()
        d.set(s)
        print s, ':', d.getDate(), ':', d.getQuoteDate()

    for code in range(0,7):
        Date.formatCode = code
        Date.entryCode = 0
        print "\nFormat Code = %d\n" % code
        checkit("June 11")
        checkit("1923")
        checkit("11/12/1293")
        checkit("11 JAN 1923")
        checkit("11-1-1929")
        checkit("4/3/1203")
        checkit("3/1203")
        checkit("?/3/1203")
        checkit("January 4, 1923")
        checkit("before 3/3/1239")
        checkit("est 2-3-1023")
        checkit("between January 4, 1234 and NOV 4, 1245")
        checkit("from 3-2-1234 to 5-4-2345")
        Date.entryCode = 1
        checkit("1/12/1999")
        checkit("12/11/1999")
        checkit("summer")

    print "----------"
    checkit("BET. 1994 - 1999")
