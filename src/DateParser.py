#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004  Donald N. Allingham
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

"""
U.S. English date parsing class. Serves as the base class for any localized
date parsing class.
"""

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

import re
import time
import locale

import Date


class DateParser:
    """
    Converts a text string into a Date object. If the date cannot be
    converted, the text string is assigned.
    """

    # determine the code set returned by nl_langinfo
    _codeset = locale.nl_langinfo(locale.CODESET)

    # RFC-2822 only uses capitalized English abbreviated names, no locales.
    _rfc_days = ('Sun','Mon','Tue','Wed','Thu','Fri','Sat')
    _rfc_mons_to_int = {
        'Jan' : 1,
        'Feb' : 2, 
        'Mar' : 3,
        'Apr' : 4,
        'May' : 5,
        'Jun' : 6,
        'Jul' : 7,
        'Aug' : 8,
        'Sep' : 9,
        'Oct' : 10,
        'Nov' : 11,
        'Dec' : 12,
        }

    month_to_int = {
        unicode(locale.nl_langinfo(locale.MON_1),_codeset).lower()   : 1,
        unicode(locale.nl_langinfo(locale.ABMON_1),_codeset).lower() : 1,
        unicode(locale.nl_langinfo(locale.MON_2),_codeset).lower()   : 2,
        unicode(locale.nl_langinfo(locale.ABMON_2),_codeset).lower() : 2,
        unicode(locale.nl_langinfo(locale.MON_3),_codeset).lower()   : 3,
        unicode(locale.nl_langinfo(locale.ABMON_3),_codeset).lower() : 3,
        unicode(locale.nl_langinfo(locale.MON_4),_codeset).lower()   : 4,
        unicode(locale.nl_langinfo(locale.ABMON_4),_codeset).lower() : 4,
        unicode(locale.nl_langinfo(locale.MON_5),_codeset).lower()   : 5,
        unicode(locale.nl_langinfo(locale.ABMON_5),_codeset).lower() : 5,
        unicode(locale.nl_langinfo(locale.MON_6),_codeset).lower()   : 6,
        unicode(locale.nl_langinfo(locale.ABMON_6),_codeset).lower() : 6,
        unicode(locale.nl_langinfo(locale.MON_7),_codeset).lower()   : 7,
        unicode(locale.nl_langinfo(locale.ABMON_7),_codeset).lower() : 7,
        unicode(locale.nl_langinfo(locale.MON_8),_codeset).lower()   : 8,
        unicode(locale.nl_langinfo(locale.ABMON_8),_codeset).lower() : 8,
        unicode(locale.nl_langinfo(locale.MON_9),_codeset).lower()   : 9,
        unicode(locale.nl_langinfo(locale.ABMON_9),_codeset).lower() : 9,
        unicode(locale.nl_langinfo(locale.MON_10),_codeset).lower()  : 10,
        unicode(locale.nl_langinfo(locale.ABMON_10),_codeset).lower(): 10,
        unicode(locale.nl_langinfo(locale.MON_11),_codeset).lower()  : 11,
        unicode(locale.nl_langinfo(locale.ABMON_11),_codeset).lower(): 11,
        unicode(locale.nl_langinfo(locale.MON_12),_codeset).lower()  : 12,
        unicode(locale.nl_langinfo(locale.ABMON_12),_codeset).lower(): 12,
       }

    modifier_to_int = {
        'before' : Date.MOD_BEFORE, 'bef'    : Date.MOD_BEFORE,
        'bef.'   : Date.MOD_BEFORE, 'after'  : Date.MOD_AFTER,
        'aft'    : Date.MOD_AFTER,  'aft.'   : Date.MOD_AFTER,
        'about'  : Date.MOD_ABOUT,  'abt.'   : Date.MOD_ABOUT,
        'abt'    : Date.MOD_ABOUT,  'circa'  : Date.MOD_ABOUT,
        'c.'     : Date.MOD_ABOUT,  'around' : Date.MOD_ABOUT,
        }

    hebrew_to_int = {
        "tishri"  : 1,   "heshvan" : 2,   "kislev"  : 3,
        "tevet"   : 4,   "shevat"  : 5,   "adari"   : 6,
        "adarii"  : 7,   "nisan"   : 8,   "iyyar"   : 9,
        "sivan"   : 10,  "tammuz"  : 11,  "av"      : 12,
        "elul"    : 13,
        }

    french_to_int = {
        u'vend\xe9miaire' : 1,  u'brumaire'   : 2,
        u'frimaire'       : 3,  u'niv\xf4se  ': 4,
        u'pluvi\xf4se'    : 5,  u'vent\xf4se' : 6,
        u'germinal'       : 7,  u'flor\xe9al' : 8,
        u'prairial'       : 9,  u'messidor'   : 10,
        u'thermidor'      : 11, u'fructidor'  : 12,
        u'extra'          : 13
        }

    islamic_to_int = {
        "muharram"           : 1,  "muharram ul haram"  : 1,
        "safar"              : 2,  "rabi`al-awwal"      : 3,
        "rabi'l"             : 3,  "rabi`ul-akhir"      : 4,
        "rabi`ath-thani"     : 4,  "rabi` ath-thani"    : 4,
        "rabi`al-thaany"     : 4,  "rabi` al-thaany"    : 4,
        "rabi' ii"           : 4,  "jumada l-ula"       : 5,
        "jumaada-ul-awwal"   : 5,  "jumaada i"          : 5,
        "jumada t-tania"     : 6,  "jumaada-ul-akhir"   : 6,
        "jumaada al-thaany"  : 6,  "jumaada ii"         : 5,
        "rajab"              : 7,  "sha`ban"            : 8,
        "sha`aban"           : 8,  "ramadan"            : 9,
        "ramadhan"           : 9,  "shawwal"            : 10,
        "dhu l-qa`da"        : 11, "dhu qadah"          : 11,
        "thw al-qi`dah"      : 11, "dhu l-hijja"        : 12,
        "dhu hijja"          : 12, "thw al-hijjah"      : 12,
        }

    persian_to_int = {
        "Farvardin"   : 1,  "Ordibehesht" : 2,
        "Khordad"     : 3,  "Tir"         : 4,
        "Mordad"      : 5,  "Shahrivar"   : 6,
        "Mehr"        : 7,  "Aban"        : 8,
        "Azar"        : 9,  "Dey"         : 10,
        "Bahman"      : 11, "Esfand"      : 12,
        }


    calendar_to_int = {
        'gregorian'        : Date.CAL_GREGORIAN,
        'g'                : Date.CAL_GREGORIAN,
        'julian'           : Date.CAL_JULIAN,
        'j'                : Date.CAL_JULIAN,
        'hebrew'           : Date.CAL_HEBREW,
        'h'                : Date.CAL_HEBREW,
        'islamic'          : Date.CAL_ISLAMIC,
        'i'                : Date.CAL_ISLAMIC,
        'french'           : Date.CAL_FRENCH,
        'french republican': Date.CAL_FRENCH,
        'f'                : Date.CAL_FRENCH,
        'persian'          : Date.CAL_PERSIAN,
        'p'                : Date.CAL_PERSIAN,
        }
    
    quality_to_int = {
        'estimated'  : Date.QUAL_ESTIMATED,
        'est.'       : Date.QUAL_ESTIMATED,
        'est'        : Date.QUAL_ESTIMATED,
        'calc.'      : Date.QUAL_CALCULATED,
        'calc'       : Date.QUAL_CALCULATED,
        'calculated' : Date.QUAL_CALCULATED,
        }
    
    _rfc_mon_str  = '(' + '|'.join(_rfc_mons_to_int.keys()) + ')'
    _rfc_day_str  = '(' + '|'.join(_rfc_days) + ')'
        
    _qual_str = '(' + '|'.join(
        [ key.replace('.','\.') for key in quality_to_int.keys() ]
        ) + ')'
    _mod_str  = '(' + '|'.join(
        [ key.replace('.','\.') for key in modifier_to_int.keys() ]
        ) + ')'
    _mon_str  = '(' + '|'.join(month_to_int.keys()) + ')'
    _jmon_str = '(' + '|'.join(hebrew_to_int.keys()) + ')'
    _fmon_str = '(' + '|'.join(french_to_int.keys()) + ')'
    _pmon_str = '(' + '|'.join(persian_to_int.keys()) + ')'
    _cal_str  = '(' + '|'.join(calendar_to_int.keys()) + ')'
    _imon_str = '(' + '|'.join(islamic_to_int.keys()) + ')'
    
    _cal      = re.compile("(.+)\s\(%s\)" % _cal_str,
                           re.IGNORECASE)
    _qual     = re.compile("%s\s+(.+)" % _qual_str,
                           re.IGNORECASE)
    _span     = re.compile("from\s+(.+)\s+to\s+(.+)",
                           re.IGNORECASE)
    _range    = re.compile("(bet.|between)\s+(.+)\s+and\s+(.+)",
                           re.IGNORECASE)
    _modifier = re.compile('%s\s+(.*)' % _mod_str,
                           re.IGNORECASE)
    _text     = re.compile('%s\s+(\d+)?\s*,?\s*((\d+)(/\d+)?)?' % _mon_str,
                           re.IGNORECASE)
    _text2    = re.compile('(\d+)?\s+?%s\s*((\d+)(/\d+)?)?' % _mon_str,
                           re.IGNORECASE)
    _jtext    = re.compile('%s\s+(\d+)?\s*,?\s*((\d+)(/\d+)?)?' % _jmon_str,
                           re.IGNORECASE)
    _jtext2   = re.compile('(\d+)?\s+?%s\s*((\d+)(/\d+)?)?' % _jmon_str,
                           re.IGNORECASE)
    _ftext    = re.compile('%s\s+(\d+)?\s*,?\s*((\d+)(/\d+)?)?' % _fmon_str,
                           re.IGNORECASE)
    _ftext2   = re.compile('(\d+)?\s+?%s\s*((\d+)(/\d+)?)?' % _fmon_str,
                           re.IGNORECASE)
    _ptext    = re.compile('%s\s+(\d+)?\s*,?\s*((\d+)(/\d+)?)?' % _pmon_str,
                           re.IGNORECASE)
    _ptext2   = re.compile('(\d+)?\s+?%s\s*((\d+)(/\d+)?)?' % _pmon_str,
                           re.IGNORECASE)
    _itext    = re.compile('%s\s+(\d+)?\s*,?\s*((\d+)(/\d+)?)?' % _imon_str,
                           re.IGNORECASE)
    _itext2   = re.compile('(\d+)?\s+?%s\s*((\d+)(/\d+)?)?' % _imon_str,
                           re.IGNORECASE)
    _range2   = re.compile('%s\s+(\d+)-(\d+)\s*,?\s*((\d+)(/\d+)?)?' % _mon_str,
                           re.IGNORECASE)
    _numeric  = re.compile("((\d+)[/\.])?((\d+)[/\.])?(\d+)")
    _iso      = re.compile("(\d+)-(\d+)-(\d+)")
    _rfc      = re.compile("%s,\s+(\d\d)\s+%s\s+(\d+)\s+\d\d:\d\d:\d\d\s+(\+|-)\d\d\d\d" 
                        % (_rfc_day_str,_rfc_mon_str))


    def __init__(self):
        self.parser = {
            Date.CAL_GREGORIAN : self._parse_greg_julian,
            Date.CAL_JULIAN    : self._parse_greg_julian,
            Date.CAL_PERSIAN   : self._parse_persian,
            Date.CAL_HEBREW    : self._parse_hebrew,
            Date.CAL_ISLAMIC   : self._parse_islamic,
            }
        
    def _get_int(self,val):
        """
        Converts the string to an integer if the value is not None. If the
        value is None, a zero is returned
        """
        if val == None:
            return 0
        else:
            return int(val)

    def _parse_hebrew(self,text):
        return self._parse_calendar(text,self._jtext,self._jtext2,
                                    self.hebrew_to_int)

    def _parse_islamic(self,text):
        return self._parse_calendar(text,self._itext,self._itext2,
                                    self.islamic_to_int)

    def _parse_persian(self,text):
        return self._parse_calendar(text,self._ptext,self._ptext2,
                                    self.persian_to_int)

    def _parse_french(self,text):
        return self._parse_calendar(text,self._ftext,self._ftext2,
                                    self.french_to_int)

    def _parse_greg_julian(self,text):
        return self._parse_calendar(text,self._text,self._text2,
                                    self.month_to_int)
                             
    def _parse_calendar(self,text,regex1,regex2,mmap):
        match = regex1.match(text)
        if match:
            groups = match.groups()
            if groups[0] == None:
                m = 0
            else:
                m = mmap[groups[0].lower()]

            d = self._get_int(groups[1])

            if groups[2] == None:
                y = 0
                s = None
            else:
                y = int(groups[3])
                s = groups[4] != None
            return (d,m,y,s)

        match = regex2.match(text)
        if match:
            groups = match.groups()
            if groups[1] == None:
                m = 0
            else:
                m = mmap[groups[1].lower()]

            d = self._get_int(groups[0])

            if groups[2] == None:
                y = 0
                s = None
            else:
                y = int(groups[3])
                s = groups[4] != None
            return (d,m,y,s)
        return Date.EMPTY
    
    def _parse_subdate(self,text,subparser=None):
        """
        Converts only the date portion of a date.
        """
        if subparser == None:
            subparser = self._parse_greg_julian
            
        try:
            value = time.strptime(text)
            return (value[2],value[1],value[0],False)
        except ValueError:
            pass

        value = subparser(text)
        if value != Date.EMPTY:
            return value
        
        match = self._iso.match(text)
        if match:
            groups = match.groups()
            y = self._get_int(groups[0])
            m = self._get_int(groups[1])
            d = self._get_int(groups[2])
            return (d,m,y,False)

        match = self._rfc.match(text)
        if match:
            groups = match.groups()
            d = self._get_int(groups[1])
            m = self._rfc_mons_to_int[groups[2]]
            y = self._get_int(groups[3])
            return (d,m,y,False)

        match = self._numeric.match(text)
        if match:
            groups = match.groups()
            m = self._get_int(groups[1])
            d = self._get_int(groups[3])
            y = self._get_int(groups[4])
            return (d,m,y,False)

        return Date.EMPTY

    def set_date(self,date,text):
        """
        Parses the text and sets the date according to the parsing.
        """
        date.set_text_value(text)
        qual = Date.QUAL_NONE
        cal  = Date.CAL_GREGORIAN
        
        match = self._cal.match(text)
        if match:
            grps = match.groups()
            cal = self.calendar_to_int[grps[1].lower()]
            text = grps[0]

        text_parser = self.parser[cal]

        match = self._qual.match(text)
        if match:
            grps = match.groups()
            qual = self.quality_to_int[grps[0].lower()]
            text = grps[1]

        match = self._span.match(text)
        if match:
            grps = match.groups()
            start = self._parse_subdate(grps[0],text_parser)
            stop = self._parse_subdate(grps[1],text_parser)
            date.set(qual,Date.MOD_SPAN,cal,start + stop)
            return
    
        match = self._range.match(text)
        if match:
            grps = match.groups()
            start = self._parse_subdate(grps[1],text_parser)
            stop = self._parse_subdate(grps[2],text_parser)
            date.set(qual,Date.MOD_RANGE,cal,start + stop)
            return

        match = self._range2.match(text)
        if match:
            grps = match.groups()
            m = self.month_to_int[grps[0].lower()]

            d0 = self._get_int(grps[1])
            d1 = self._get_int(grps[2])

            if grps[3] == None:
                y = 0
                s = None
            else:
                y = int(grps[3])
                s = grps[4] != None
            date.set(qual,Date.MOD_RANGE,Date.CAL_GREGORIAN,
                     (d0,m,y,s,d1,m,y,s))
            return
    
        match = self._modifier.match(text)
        if match:
            grps = match.groups()
            start = self._parse_subdate(grps[1])
            mod = self.modifier_to_int.get(grps[0].lower(),Date.MOD_NONE)
            date.set(qual,mod,cal,start)
            return

        subdate = self._parse_subdate(text)
        if subdate == Date.EMPTY:
            subdate = self._parse_hebrew(text)
            if subdate == Date.EMPTY:
                subdate = self._parse_persian(text)
                if subdate == Date.EMPTY:
                    subdate = self._parse_islamic(text)
                    if subdate == Date.EMPTY:
                        subdate = self._parse_french(text)
                        if subdate == Date.EMPTY:
                            date.set_as_text(text)
                            return
                        else:
                            cal = Date.CAL_FRENCH
                    else:
                        cal = Date.CAL_ISLAMIC
                else:
                    cal = Date.CAL_PERSIAN
            else:
                cal = Date.CAL_HEBREW
            
        date.set(qual,Date.MOD_NONE,cal,subdate)

    def parse(self,text):
        """
        Parses the text, returning a Date object.
        """
        new_date = Date.Date()
        self.set_date(new_date,text)
        return new_date
