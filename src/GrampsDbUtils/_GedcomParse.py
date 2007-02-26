#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

# $Id: _ReadGedcom.py 8032 2007-02-03 17:11:05Z hippy $

"""
Import from GEDCOM

The GEDCOM file format is defined by the GEDCOM 5.5 Specfication, found
at http://www.familysearch.org/GEDCOM/GEDCOM55.EXE

The basic structure is a line with three attributes:

<LEVEL> <TOKEN> <DATA>

Because of this structure, it does not lend itself to more traditional
parsing techniques, such as LALR. The LEVEL token implies too much to be
useful in this context. While this makes parsing more difficult, it
does provide one very beneficial feature for GEDCOM: Error recoverability.
GEDCOM is a poorly implemented standard, primarily because it is a poor
standard to begin with. 

Most commercial applications that implement GEDCOM output add custom 
extensions, and feel free to violate the existing structure. If one were
cynical, one might believe that the commercial programs were trying to
make it difficult to transfer your data to another application.

This parser takes a different approach to parsing a GEDCOM file. The first
state, GedcomLex, reads lines from the file, and does some basic lexical
analysis on each line (actually several lines, since it automatically
combines CONT and CONC tagged lines). Each logical line returned to this
parser contains:

  Level, Token, Token text, Data, and line number.

The Data field is typically text, but in some cases, it may be a integer 
value representing an enumerated type or a GRAMPS object (in the case of
dates).

The parser works on the current level. Each context and level has a an 
associated table (dictionary) of functions indexed by the corresponding
TOKEN. When a token is found, we index into the table to find the function
associated with the token. If no token is found, a function that skips the
line and all subordinate (lines with a higher number). If a function is 
found, then we call that function, which in turn processes the line, and
all tokens at the lower level. 

For example:

1 BIRT
  2 DATE 1 JAN 2000
  2 UKNOWN TAG
    3 NOTE DATA

The function parsing the individual at level 1, would encounter the BIRT tag.
It would look up the BIRT token in the table to see if a function as defined 
for this TOKEN, and pass control to this function. This function would then
start parsing level 2. It would encounter the DATE tag, look up the 
corresponding function the in level 2 table, and pass control to its 
associated function. This function would terminate, and return control back to
the level 2 parser, which would then encounter the "UKNOWN" tag. Since this is
not a valid token, it would not be in the table, and a function that would skip
all lines until the next level 2 token is found (in this case, skipping the 
"3 NOTE DATA" line.
"""

__revision__ = "$Revision: $"
__author__   = "Don Allingham"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import os
import re
import time
from gettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".GedcomImport")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import Errors
import RelLib
from BasicUtils import NameDisplay, UpdateCallback
import Utils
import Mime
import LdsUtils

from _GedcomInfo import *
from _GedcomTokens import *
from _GedcomLex import Reader
from _GedcomChar import *

import _GedcomUtils as GedcomUtils 

from GrampsDb._GrampsDbConst  import EVENT_KEY

try:
    import Config
    DEFAULT_SOURCE = Config.get(Config.DEFAULT_SOURCE)
except:
    LOG.warn("No Config module available using defaults.")
    DEFAULT_SOURCE = False
    
#-------------------------------------------------------------------------
#
# Address/Place constants
#
#-------------------------------------------------------------------------
ADDR_RE  = re.compile('(.+)([\n\r]+)(.+)\s*,(.+)\s+(\d+)\s*(.*)')
ADDR2_RE = re.compile('(.+)([\n\r]+)(.+)\s*,(.+)\s+(\d+)')
ADDR3_RE = re.compile('(.+)([\n\r]+)(.+)\s*,(.+)')

TRUNC_MSG = _("Your GEDCOM file is corrupted. "
              "It appears to have been truncated.")

#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
TYPE_BIRTH  = RelLib.ChildRefType()
TYPE_ADOPT  = RelLib.ChildRefType(RelLib.ChildRefType.ADOPTED)
TYPE_FOSTER = RelLib.ChildRefType(RelLib.ChildRefType.FOSTER)

RELATION_TYPES = (
    RelLib.ChildRefType.BIRTH,
    RelLib.ChildRefType.UNKNOWN,
    RelLib.ChildRefType.NONE,
    )

PEDIGREE_TYPES = {
    'birth'  : RelLib.ChildRefType(),
    'natural': RelLib.ChildRefType(),
    'step'   : TYPE_ADOPT,
    'adopted': TYPE_ADOPT,
    'foster' : TYPE_FOSTER,
    }

MIME_MAP = {
    'jpeg' : 'image/jpeg',   'jpg'  : 'image/jpeg',
    'rtf'  : 'text/rtf',     'pdf'  : 'application/pdf',
    'mpeg' : 'video/mpeg',   'mpg'  : 'video/mpeg',
    'gif'  : 'image/gif',    'bmp'  : 'image/x-ms-bmp',
    'tiff' : 'image/tiff',   'aif'  : 'audio/x-aiff',
    'text' : 'text/plain',   'w8bn' : 'application/msword',
    'wav'  : 'audio/x-wav',  'mov'  : 'video/quicktime',
    }
    

EVENT_FAMILY_STR = _("%(event_name)s of %(family)s")
EVENT_PERSON_STR = _("%(event_name)s of %(person)s")

FTW_BAD_PLACE = [
    RelLib.EventType.OCCUPATION, 
    RelLib.EventType.RELIGION,
    RelLib.EventType.DEGREE
    ]

#-------------------------------------------------------------------------
#
# GEDCOM events to GRAMPS events conversion
#
#-------------------------------------------------------------------------
GED_2_GRAMPS = {}
for _val in personalConstantEvents.keys():
    _key = personalConstantEvents[_val]
    if _key != "":
        GED_2_GRAMPS[_key] = _val

GED_2_FAMILY = {}
for _val in familyConstantEvents.keys():
    _key = familyConstantEvents[_val]
    if _key != "":
        GED_2_FAMILY[_key] = _val

GED_2_FAMILY_CUSTOM = {}

#-------------------------------------------------------------------------
#
# regular expressions
#
#-------------------------------------------------------------------------
INT_RE     = re.compile(r"\s*(\d+)\s*$")
NOTE_RE    = re.compile(r"\s*\d+\s+\@(\S+)\@\s+NOTE(.*)$")
CONT_RE    = re.compile(r"\s*\d+\s+CONT\s?(.*)$")
CONC_RE    = re.compile(r"\s*\d+\s+CONC\s?(.*)$")
PERSON_RE  = re.compile(r"\s*\d+\s+\@(\S+)\@\s+INDI(.*)$")

class StageOne:

    def __init__(self, ifile):
	self.ifile = ifile
	self.famc = {}
	self.fams = {}
	self.enc = ""
	self.pcnt = 0
	self.lcnt = 0

    def parse(self):
	current = ""

        line = self.ifile.read(3)
        if line == "\xef\xbb":
            self.ifile.read(1)
            self.enc = "UTF8"
        else:
            self.ifile.seek(0)

	for line in self.ifile:
	    self.lcnt +=1

            data = line.split(None,2) + ['']
            try:
                (level, key, value) = data[:3]
                try:
                    level = int(level)
                except:
                    level = 0
                key = key.strip()
            except:
                raise Errors.GedcomError("Corrupted file at line %d" % self.lcnt)

	    if level == 0 and key[0] == '@':
                if value == ("FAM", "FAMILY") :
                    current = key.strip()
                    current = current[1:-1]
                elif value == ("INDI", "INDIVIDUAL"):
                    self.pcnt += 1
	    elif key in ("HUSB", "HUSBAND", "WIFE") and value and value[0] == '@':
		value = value[1:-1]
		if self.fams.has_key(value):
		    self.fams[value].append(current)
		else:
		    self.fams[value] = [current]
	    elif key in ("CHIL", "CHILD") and value and value[0] == '@':
		value = value[1:-1]
		if self.famc.has_key(value):
		    self.famc[value].append(current)
		else:
		    self.famc[value] = [current]
	    elif key == 'CHAR' and not self.enc:
		self.enc = value

    def get_famc_map(self):
	return self.famc

    def get_fams_map(self):
	return self.fams

    def get_encoding(self):
	return self.enc.upper()

    def set_encoding(self, enc):
	self.enc = enc

    def get_person_count(self):
	return self.pcnt

    def get_line_count(self):
	return self.lcnt

#-------------------------------------------------------------------------
#
# GedcomParser
#
#-------------------------------------------------------------------------
class GedcomParser(UpdateCallback):
    """
    Performs the second pass of the GEDCOM parser, which does all the heavy
    lifting.
    """

    SyntaxError = "Syntax Error"
    BadFile = "Not a GEDCOM file"

    def __init__(self, dbase, ifile, filename, callback, stage_one):
        UpdateCallback.__init__(self, callback)

        self.set_total(stage_one.get_line_count())

        self.repo2id = {}
        self.maxpeople = stage_one.get_person_count()
        self.dbase = dbase
        self.emapper = GedcomUtils.IdFinder(dbase.get_gramps_ids(EVENT_KEY),
                                            dbase.eprefix)

	self.famc_map = stage_one.get_famc_map()
	self.fams_map = stage_one.get_fams_map()

        self.place_parser = GedcomUtils.PlaceParser()
        self.debug = False
        self.inline_srcs = {}
        self.media_map = {}
        self.refn = {}
        self.added = set()
        self.gedmap = GedcomInfoDB()
        self.gedsource = self.gedmap.get_from_source_tag('GEDCOM 5.5')
        self.use_def_src = DEFAULT_SOURCE
        if self.use_def_src:
            self.def_src = RelLib.Source()
            fname = os.path.basename(filename).split('\\')[-1]
            self.def_src.set_title(_("Import from GEDCOM (%s)") % 
                                   unicode(fname,
                                           encoding=sys.getfilesystemencoding(),
                                           errors='replace'))
        self.dir_path = os.path.dirname(filename)
        self.is_ftw = False
	self.is_ancestry_com = False

        self.pid_map = GedcomUtils.IdMapper(
            self.dbase.id_trans, 
            self.dbase.find_next_person_gramps_id,
            self.dbase.get_number_of_people())
        self.fid_map = GedcomUtils.IdMapper(
            self.dbase.fid_trans, 
            self.dbase.find_next_family_gramps_id,
            self.dbase.get_number_of_families())
        self.sid_map = GedcomUtils.IdMapper(
            self.dbase.sid_trans, 
            self.dbase.find_next_source_gramps_id,
            self.dbase.get_number_of_sources())
        self.oid_map = GedcomUtils.IdMapper(
            self.dbase.oid_trans, 
            self.dbase.find_next_object_gramps_id,
            self.dbase.get_number_of_media_objects())
        self.rid_map = GedcomUtils.IdMapper(
            self.dbase.rid_trans, 
            self.dbase.find_next_repository_gramps_id,
            self.dbase.get_number_of_repositories())

        self.gid2id = {}
        self.oid2id = {}
        self.sid2id = {}
        self.lid2id = {}
        self.fid2id = {}
        self.rid2id = {}

	#
	# Parse table for INDI tag
	#
        self.indi_parse_tbl = {
            # +1 RESN <RESTRICTION_NOTICE> {0:1}
            TOKEN_RESN  : self.func_person_resn,
            # +1 <<PERSONAL_NAME_STRUCTURE>> {0:M}
            TOKEN_NAME  : self.func_person_name,
            # +1 SEX <SEX_VALUE> {0:1}
            TOKEN_SEX   : self.func_person_sex,
            # +1 <<INDIVIDUAL_EVENT_STRUCTURE>> {0:M}
            TOKEN_EVEN  : self.func_person_even,
            TOKEN_GEVENT: self.func_person_std_event,
            TOKEN_BIRT  : self.func_person_birt,
            TOKEN_RELI  : self.func_person_reli,
            TOKEN_ADOP  : self.func_person_adop,
            TOKEN_DEAT  : self.func_person_deat,
            TOKEN_RESI  : self.func_person_resi,
            # +1 <<INDIVIDUAL_ATTRIBUTE_STRUCTURE>> {0:M}
            # +1 AFN <ANCESTRAL_FILE_NUMBER> {0:1}
            TOKEN_ATTR  : self.func_person_std_attr,
            #+1 <<LDS_INDIVIDUAL_ORDINANCE>> {0:M}
            TOKEN_BAPL  : self.func_person_bapl,
            TOKEN_CONL  : self.func_person_conl,
            TOKEN_ENDL  : self.func_person_endl,
            TOKEN_SLGC  : self.func_person_slgc,
            #+1 <<CHILD_TO_FAMILY_LINK>> {0:M}
            TOKEN_FAMC  : self.func_person_famc,
            # +1 <<SPOUSE_TO_FAMILY_LINK>> {0:M}
            TOKEN_FAMS  : self.func_person_fams,
            # +1 SUBM @<XREF:SUBM>@ {0:M}
            TOKEN_SUBM  : self.skip_record,
            # +1 <<ASSOCIATION_STRUCTURE>> {0:M}
            TOKEN_ASSO  : self.func_person_asso,
            # +1 ALIA @<XREF:INDI>@ {0:M}
            TOKEN_ALIA  : self.func_person_alt_name,
            # +1 ANCI @<XREF:SUBM>@ {0:M}
            TOKEN_ANCI  : self.skip_record,
            # +1 DESI @<XREF:SUBM>@ {0:M}
            TOKEN_DESI  : self.skip_record,
            # +1 <<SOURCE_CITATION>> {0:M}
            TOKEN_SOUR  : self.func_person_sour,
            # +1 <<MULTIMEDIA_LINK>> {0:M}
            TOKEN_OBJE  : self.func_person_object,
            # +1 <<NOTE_STRUCTURE>> {0:M} 
            TOKEN_NOTE  : self.func_person_note,
            TOKEN_RNOTE : self.func_person_rnote,
            TOKEN__COMM : self.func_person_note,
            # +1 RFN <PERMANENT_RECORD_FILE_NUMBER> {0:1}
            TOKEN_RFN   : self.func_person_attr,
            # +1 REFN <USER_REFERENCE_NUMBER> {0:M}
            # +2 TYPE <USER_REFERENCE_TYPE> {0:1}
            TOKEN_REFN  : self.func_person_refn,
            # +1 RIN <AUTOMATED_RECORD_ID> {0:1}
            TOKEN_RIN   : self.skip_record,
            # +1 <<CHANGE_DATE>> {0:1}
            TOKEN_CHAN  : self.func_person_chan,

            TOKEN_ADDR  : self.func_person_addr,
            TOKEN_PHON  : self.func_person_phon,
            TOKEN__TODO : self.skip_record,
            TOKEN_TITL  : self.func_person_titl,
            }

	#
	# Parse table for INDI.NAME
	# 
        self.name_parse_tbl = {
            # +1 NPFX <NAME_PIECE_PREFIX> {0:1}
            TOKEN_NPFX   : self.func_name_npfx,
            # +1 GIVN <NAME_PIECE_GIVEN> {0:1}
            TOKEN_GIVN   : self.func_name_givn,
            # NICK <NAME_PIECE_NICKNAME> {0:1}
            TOKEN_NICK   : self.func_name_nick,
            # +1 SPFX <NAME_PIECE_SURNAME_PREFIX {0:1}
            TOKEN_SPFX   : self.func_name_spfx,
            # +1 SURN <NAME_PIECE_SURNAME> {0:1}
            TOKEN_SURN   : self.func_name_surn,
            # +1 NSFX <NAME_PIECE_SUFFIX> {0:1}
            TOKEN_NSFX   : self.func_name_nsfx,
            # +1 <<SOURCE_CITATION>> {0:M}
            TOKEN_SOUR   : self.func_name_sour,
            # +1 <<NOTE_STRUCTURE>> {0:M}
            TOKEN_NOTE   : self.func_name_note,
            TOKEN_RNOTE  : self.func_name_note,
            # Extensions
            TOKEN_ALIA   : self.func_name_alia,
            TOKEN__MARNM : self.func_name_marnm,
            TOKEN__AKA   : self.func_name_aka,
            TOKEN_TYPE   : self.func_name_type,
            TOKEN_BIRT   : self.func_ignore,
            }

        self.repo_parse_tbl = {
            TOKEN_NAME   : self.func_repo_name,
            TOKEN_ADDR   : self.func_repo_addr,
            TOKEN_RIN    : self.func_ignore,
            }

        self.event_parse_tbl = {
            # n TYPE <EVENT_DESCRIPTOR> {0:1}
            TOKEN_TYPE   : self.func_event_type,
            # n DATE <DATE_VALUE> {0:1} p.*/*
            TOKEN_DATE   : self.func_event_date,
            # n <<PLACE_STRUCTURE>> {0:1} p.*
            TOKEN_PLAC   : self.func_event_place,
            # n <<ADDRESS_STRUCTURE>> {0:1} p.*
            TOKEN_ADDR   : self.func_event_addr,
            # n AGE <AGE_AT_EVENT> {0:1} p.*
            TOKEN_AGE    : self.func_event_age,
            # n AGNC <RESPONSIBLE_AGENCY> {0:1} p.*
            TOKEN_AGNC   : self.func_event_agnc,
            # n CAUS <CAUSE_OF_EVENT> {0:1} p.*
            TOKEN_CAUS   : self.func_event_cause,
            # n <<SOURCE_CITATION>> {0:M} p.*
            TOKEN_SOUR   : self.func_event_source,
            # n <<MULTIMEDIA_LINK>> {0:M} p.*,*
            TOKEN_OBJE   : self.func_event_object,
            # n <<NOTE_STRUCTURE>> {0:M} p.
            TOKEN_NOTE   : self.func_event_note,
            TOKEN_RNOTE  : self.func_event_note,
            # Other
            TOKEN__PRIV  : self.func_event_privacy,
            TOKEN_OFFI   : self.func_event_note,
            TOKEN_PHON   : self.func_ignore,
            TOKEN__GODP  : self.func_ignore,
            TOKEN__WITN  : self.func_ignore,
            TOKEN__WTN   : self.func_ignore,
            TOKEN_RELI   : self.func_ignore,
            TOKEN_TIME   : self.func_ignore,
            TOKEN_ASSO   : self.func_ignore,
            TOKEN_IGNORE : self.func_ignore,
            TOKEN_STAT   : self.func_ignore,
            TOKEN_TEMP   : self.func_ignore,
            TOKEN_HUSB   : self.func_event_husb,
            TOKEN_WIFE   : self.func_event_wife,
            TOKEN_FAMC   : self.func_person_birth_famc,
            }

        self.adopt_parse_tbl = {
            TOKEN_TYPE   : self.func_event_type,
            TOKEN__PRIV  : self.func_event_privacy,
            TOKEN_DATE   : self.func_event_date,
            TOKEN_SOUR   : self.func_event_source,
            TOKEN_PLAC   : self.func_event_place,
            TOKEN_ADDR   : self.func_event_addr,
            TOKEN_CAUS   : self.func_event_cause,
            TOKEN_AGNC   : self.func_event_agnc,
            TOKEN_AGE    : self.func_event_age,
            TOKEN_NOTE   : self.func_event_note,
            TOKEN_RNOTE  : self.func_event_note,
            TOKEN_OFFI   : self.func_event_note,
            TOKEN__GODP  : self.func_ignore,
            TOKEN__WITN  : self.func_ignore,
            TOKEN__WTN   : self.func_ignore,
            TOKEN_RELI   : self.func_ignore,
            TOKEN_TIME   : self.func_ignore,
            TOKEN_ASSO   : self.func_ignore,
            TOKEN_IGNORE : self.func_ignore,
            TOKEN_STAT   : self.func_ignore,
            TOKEN_TEMP   : self.func_ignore,
            TOKEN_OBJE   : self.func_event_object,
            TOKEN_FAMC   : self.func_person_adopt_famc,
            }

        self.famc_parse_tbl = {
            # n FAMC @<XREF:FAM>@ {1:1}
            # +1 PEDI <PEDIGREE_LINKAGE_TYPE> {0:M} p.*
            TOKEN_PEDI   : self.func_person_famc_pedi,
            # +1 <<NOTE_STRUCTURE>> {0:M} p.*
            TOKEN_NOTE   : self.func_person_famc_note,
            TOKEN_RNOTE  : self.func_person_famc_note,
            # Extras
            TOKEN__PRIMARY: self.func_person_famc_primary,
            TOKEN_SOUR   : self.func_person_famc_sour,
            # GEDit
            TOKEN_STAT   : self.func_ignore,
            }

        self.resi_parse_tbl = {
            TOKEN_DATE   : self.func_person_resi_date,
            TOKEN_ADDR   : self.func_person_resi_addr,
            TOKEN_SOUR   : self.func_person_resi_sour,
            TOKEN_PLAC   : self.func_person_resi_plac,
            TOKEN_PHON   : self.func_person_resi_phon,
            TOKEN_NOTE   : self.func_person_resi_note,
            TOKEN_RNOTE  : self.func_person_resi_note,
            TOKEN_IGNORE : self.func_ignore,
            TOKEN_CAUS   : self.func_ignore,
            TOKEN_STAT   : self.func_ignore,
            TOKEN_TEMP   : self.func_ignore,
            TOKEN_OBJE   : self.func_ignore,
            TOKEN_TYPE   : self.func_ignore,
            }

        self.person_attr_parse_tbl = {
            TOKEN_TYPE  : self.func_person_attr_type,
            TOKEN_CAUS  : self.func_ignore,
            TOKEN_DATE  : self.func_ignore,
            TOKEN_TIME  : self.func_ignore,
            TOKEN_ADDR  : self.func_ignore,
            TOKEN_IGNORE: self.func_ignore,
            TOKEN_STAT  : self.func_ignore,
            TOKEN_TEMP  : self.func_ignore,
            TOKEN_OBJE  : self.func_ignore,
            TOKEN_SOUR  : self.func_person_attr_source,
            TOKEN_PLAC  : self.func_person_attr_place,
            TOKEN_NOTE  : self.func_person_attr_note,
            TOKEN_RNOTE : self.func_person_attr_note,
            }

        self.lds_parse_tbl = {
            TOKEN_TEMP  : self.func_lds_temple,
            TOKEN_DATE  : self.func_lds_date,
            TOKEN_FAMC  : self.func_lds_famc,
            TOKEN_FORM  : self.func_lds_form,
            TOKEN_PLAC  : self.func_lds_plac,
            TOKEN_SOUR  : self.func_lds_sour,
            TOKEN_NOTE  : self.func_lds_note,
            TOKEN_RNOTE : self.func_lds_note,
            TOKEN_STAT  : self.func_lds_stat,
            }

        self.asso_parse_tbl = {
            TOKEN_TYPE  : self.func_person_asso_type,
            TOKEN_RELA  : self.func_person_asso_rela,
            TOKEN_SOUR  : self.func_person_asso_sour,
            TOKEN_NOTE  : self.func_person_asso_note,
            TOKEN_RNOTE : self.func_person_asso_note,
            }

        self.srcref_parse_tbl = {
            TOKEN_PAGE   : self.func_srcref_page,
            TOKEN_DATE   : self.func_srcref_date,
            TOKEN_DATA   : self.func_srcref_data,
            TOKEN_OBJE   : self.func_srcref_obje,
            TOKEN_REFN   : self.func_srcref_refn,
            TOKEN_EVEN   : self.func_ignore,
            TOKEN_IGNORE : self.func_ignore,
            TOKEN__LKD   : self.func_ignore,
            TOKEN_QUAY   : self.func_srcref_quay,
            TOKEN_NOTE   : self.func_srcref_note,
            TOKEN_RNOTE  : self.func_srcref_note,
            TOKEN_TEXT   : self.func_srcref_text,
            }

        self.object_parse_tbl = {
            TOKEN_FORM   : self.func_object_ref_form,
            TOKEN_TITL   : self.func_object_ref_titl,
            TOKEN_FILE   : self.func_object_ref_file,
            TOKEN_NOTE   : self.func_object_ref_note,
            TOKEN_RNOTE  : self.func_object_ref_note,
            TOKEN_IGNORE : self.func_ignore,
        }

        self.parse_loc_tbl = {
            TOKEN_ADDR : self.func_location_addr,
            TOKEN_ADR1 : self.func_location_addr,
            TOKEN_ADR2 : self.func_location_addr,
            TOKEN_DATE : self.func_location_date,
            TOKEN_CITY : self.func_location_city,
            TOKEN_STAE : self.func_location_stae,
            TOKEN_POST : self.func_location_post,
            TOKEN_CTRY : self.func_location_ctry,
            TOKEN_NOTE : self.func_location_note,
            TOKEN_RNOTE: self.func_location_note,
            TOKEN__LOC : self.func_ignore,
            TOKEN__NAME: self.func_ignore,
            TOKEN_PHON : self.func_ignore,
            }
        
	#
	# FAM 
	# 
        self.family_func = {
	    # +1 <<FAMILY_EVENT_STRUCTURE>>  {0:M}
            TOKEN_GEVENT: self.func_family_std_event,
            TOKEN_EVEN  : self.func_family_even,
	    # +1 HUSB @<XREF:INDI>@  {0:1}
            TOKEN_HUSB  : self.func_family_husb,
	    # +1 WIFE @<XREF:INDI>@  {0:1}
            TOKEN_WIFE  : self.func_family_wife,
	    # +1 CHIL @<XREF:INDI>@  {0:M}
            TOKEN_CHIL  : self.func_family_chil,
	    # +1 NCHI <COUNT_OF_CHILDREN>  {0:1}
	    # +1 SUBM @<XREF:SUBM>@  {0:M}
	    # +1 <<LDS_SPOUSE_SEALING>>  {0:M}
            TOKEN_SLGS  : self.func_family_slgs,
	    # +1 <<SOURCE_CITATION>>  {0:M}
            TOKEN_SOUR  : self.func_family_source,
	    # +1 <<MULTIMEDIA_LINK>>  {0:M}
            TOKEN_OBJE  : self.func_family_object,
	    # +1 <<NOTE_STRUCTURE>>  {0:M}
            TOKEN__COMM : self.func_family_comm,
            TOKEN_NOTE  : self.func_family_note,
            TOKEN_RNOTE : self.func_family_note,
	    # +1 REFN <USER_REFERENCE_NUMBER>  {0:M}
            TOKEN_REFN  : self.func_ignore,
	    # +1 RIN <AUTOMATED_RECORD_ID>  {0:1}
	    # +1 <<CHANGE_DATE>>  {0:1}
            TOKEN_CHAN  : self.func_family_chan,

            TOKEN_ADDR  : self.func_family_addr,
            TOKEN_RIN   : self.func_family_cust_attr, 
            TOKEN_SUBM  : self.func_ignore,
            TOKEN_ATTR  : self.func_family_attr,
            }

        self.family_rel_tbl = {
            TOKEN__FREL : self.func_family_frel,
            TOKEN__MREL : self.func_family_mrel,
            TOKEN_ADOP  : self.func_family_adopt,
            TOKEN__STAT : self.func_family_stat,
            }

        self.source_func = {
            TOKEN_TITL  : self.func_source_title,
            TOKEN_TAXT  : self.func_source_taxt_peri,
            TOKEN_PERI  : self.func_source_taxt_peri,
            TOKEN_AUTH  : self.func_source_auth,
            TOKEN_PUBL  : self.func_source_publ,
            TOKEN_NOTE  : self.func_source_note,
            TOKEN_RNOTE : self.func_source_note,
            TOKEN_TEXT  : self.func_source_text,
            TOKEN_ABBR  : self.func_source_abbr,
            TOKEN_REFN  : self.func_ignore,
            TOKEN_RIN   : self.func_ignore,
            TOKEN_REPO  : self.func_source_repo,
            TOKEN_OBJE  : self.func_source_object,
            TOKEN_CHAN  : self.func_source_chan,
            TOKEN_MEDI  : self.func_source_attr,
            TOKEN__NAME : self.func_source_attr,
            TOKEN_DATA  : self.func_ignore,
            TOKEN_TYPE  : self.func_source_attr,
            TOKEN_CALN  : self.func_ignore,
            TOKEN_IGNORE: self.func_ignore,
        }

        self.obje_func = {
            TOKEN_FORM  : self.func_obje_form,
            TOKEN_TITL  : self.func_obje_title,
            TOKEN_FILE  : self.func_obje_file,
            TOKEN_NOTE  : self.func_obje_note,
            TOKEN_RNOTE : self.func_obje_note,
            TOKEN_BLOB  : self.func_obje_blob,
            TOKEN_REFN  : self.func_obje_refn,
            TOKEN_TYPE  : self.func_obje_type,
            TOKEN_RIN   : self.func_obje_rin,
            TOKEN_CHAN  : self.func_obje_chan,
            }

        self.parse_addr_tbl = {
            TOKEN_DATE  : self.func_address_date,
            TOKEN_CITY  : self.func_address_city,
            TOKEN_STAE  : self.func_address_state,
            TOKEN_POST  : self.func_address_post,
            TOKEN_CTRY  : self.func_address_country,
            TOKEN_PHON  : self.func_address_phone,
            TOKEN_SOUR  : self.func_address_sour,
            TOKEN_NOTE  : self.func_address_note,
            TOKEN_RNOTE : self.func_address_note,
            TOKEN__LOC  : self.func_ignore,
            TOKEN__NAME : self.func_ignore,
            TOKEN_IGNORE: self.func_ignore,
            TOKEN_TYPE  : self.func_ignore,
            TOKEN_CAUS  : self.func_ignore,
            }

        self.event_cause_tbl = {
            TOKEN_SOUR  : self.func_event_cause_source,
            }

        self.event_place_map = {
            TOKEN_NOTE  : self.func_event_place_note,
            TOKEN_RNOTE : self.func_event_place_note,
            TOKEN_FORM  : self.func_event_place_form,
            TOKEN_OBJE  : self.func_event_place_object,
            TOKEN_SOUR  : self.func_event_place_sour,
            }

        self.repo_ref_tbl = {
            TOKEN_CALN : self.func_repo_ref_call,
            TOKEN_NOTE : self.func_repo_ref_note,
            TOKEN_RNOTE: self.func_repo_ref_note,
            }

        self.parse_person_adopt = {
            TOKEN_ADOP : self.func_person_adopt_famc_adopt,
            }

        # look for existing place titles, build a map 
        self.place_names = {}
        cursor = dbase.get_place_cursor()
        data = cursor.next()
        while data:
            (handle, val) = data
            self.place_names[val[2]] = handle
            data = cursor.next()
        cursor.close()

        enc = stage_one.get_encoding()

        if enc == "ANSEL":
            rdr = AnselReader(ifile)
        elif enc in ("UTF-8", "UTF8"):
            rdr = UTF8Reader(ifile)
        elif enc in ("UTF-16", "UTF16", "UNICODE"):
            rdr = UTF16Reader(ifile)
        else:
            rdr = AnsiReader(ifile)

        self.lexer = Reader(rdr)
        self.filename = filename
        self.backoff = False

        fullpath = os.path.normpath(os.path.abspath(filename))
        self.geddir = os.path.dirname(fullpath)
    
        self.error_count = 0
        amap = personalConstantAttributes
        
        self.attrs = amap.values()
        self.gedattr = {}
        for val in amap.keys():
            self.gedattr[amap[val]] = val
        self.search_paths = []

    #-------------------------------------------------------------------------
    #
    # Create new objects
    #
    #-------------------------------------------------------------------------
    def _find_from_handle(self, gramps_id, table):
        """
        Finds a handle corresponding the the specified GRAMPS ID. The passed
        table contains the mapping. If the value is found, we return it, otherwise
        we create a new handle, store it, and return it.
        """
        intid = table.get(gramps_id)
        if not intid:
            intid = Utils.create_id()
            table[gramps_id] = intid
        return intid

    def find_person_handle(self, gramps_id):
        """
        Returns the database handle associated with the person's GRAMPS ID
        """
        return self._find_from_handle(gramps_id, self.gid2id)

    def find_family_handle(self, gramps_id):
        """
        Returns the database handle associated with the family's GRAMPS ID
        """
        return self._find_from_handle(gramps_id, self.fid2id)
        
    def find_object_handle(self, gramps_id):
        """
        Returns the database handle associated with the media object's GRAMPS ID
        """
        return self._find_from_handle(gramps_id, self.oid2id)

    def find_or_create_person(self, gramps_id):
        """
        Finds or creates a person based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise,
        we create a new person, assign the handle and GRAMPS ID.
        """
        person = RelLib.Person()
        intid = self.gid2id.get(gramps_id)
        if self.dbase.has_person_handle(intid):
            person.unserialize(self.dbase.get_raw_person_data(intid))
        else:
            intid = self._find_from_handle(gramps_id, self.gid2id)
            person.set_handle(intid)
            person.set_gramps_id(gramps_id)
        return person

    def find_or_create_family(self, gramps_id):
        """
        Finds or creates a family based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise,
        we create a new family, assign the handle and GRAMPS ID.
        """
        family = RelLib.Family()
        intid = self.fid2id.get(gramps_id)
        if self.dbase.has_family_handle(intid):
            family.unserialize(self.dbase.get_raw_family_data(intid))
        else:
            intid = self._find_from_handle(gramps_id, self.fid2id)
            family.set_handle(intid)
            family.set_gramps_id(gramps_id)
        return family

    def find_or_create_object(self, gramps_id):
        """
        Finds or creates a media object based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise,
        we create a new media object, assign the handle and GRAMPS ID.
        """
        obj = RelLib.MediaObject()
        intid = self.oid2id.get(gramps_id)
        if self.dbase.has_object_handle(intid):
            obj.unserialize(self.dbase.get_raw_object_data(intid))
        else:
            intid = self._find_from_handle(gramps_id, self.oid2id)
            obj.set_handle(intid)
            obj.set_gramps_id(gramps_id)
        return obj

    def find_or_create_source(self, gramps_id):
        """
        Finds or creates a source based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise,
        we create a new source, assign the handle and GRAMPS ID.
        """
        obj = RelLib.Source()
        intid = self.sid2id.get(gramps_id)
        if self.dbase.has_source_handle(intid):
            obj.unserialize(self.dbase.get_raw_source_data(intid))
        else:
            intid = self._find_from_handle(gramps_id, self.sid2id)
            obj.set_handle(intid)
            obj.set_gramps_id(gramps_id)
        return obj

    def find_or_create_repository(self, gramps_id):
        """
        Finds or creates a repository based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise,
        we create a new repository, assign the handle and GRAMPS ID.

        Some GEDCOM "flavors" destroy the specification, and declare the repository
        inline instead of in a object. 
        """
        repository = RelLib.Repository()
        if not gramps_id:
            need_commit = True
            gramps_id = self.dbase.find_next_repository_gramps_id()
        else:
            need_commit = False

        intid = self.rid2id.get(gramps_id)
        if self.dbase.has_repository_handle(intid):
            repository.unserialize(self.dbase.get_raw_repository_data(intid))
        else:
            intid = self._find_from_handle(gramps_id, self.rid2id)
            repository.set_handle(intid)
            repository.set_gramps_id(gramps_id)
        if need_commit:
            self.dbase.commit_repository(repository, self.trans)
        return repository

    def find_or_create_place(self, title):
        """
        Finds or creates a place based on the GRAMPS ID. If the ID is
        already used (is in the db), we return the item in the db. Otherwise,
        we create a new place, assign the handle and GRAMPS ID.
        """
        place = RelLib.Place()

        # check to see if we've encountered this name before
        # if we haven't we need to get a new GRAMPS ID
        
        intid = self.place_names.get(title)
        if intid == None:
            intid = self.lid2id.get(title)
            if intid == None:
                new_id = self.dbase.find_next_place_gramps_id()
            else:
                new_id = None
        else:
            new_id = None

        # check to see if the name already existed in the database
        # if it does, create a new name by appending the GRAMPS ID.
        # generate a GRAMPS ID if needed
        
        if self.dbase.has_place_handle(intid):
            place.unserialize(self.dbase.get_raw_place_data(intid))
        else:
            intid = Utils.create_id()
            place.set_handle(intid)
            place.set_title(title)
            place.set_gramps_id(new_id)
            self.dbase.add_place(place, self.trans)
            self.lid2id[title] = intid
        return place

    def find_file(self, fullname, altpath):
        tries = []
        fullname = fullname.replace('\\', os.path.sep)
        tries.append(fullname)
        
        try:
            if os.path.isfile(fullname):
                return (1, fullname)
        except UnicodeEncodeError:
            # FIXME: problem possibly caused by umlaut/accented character 
            # in filename
            return (0, tries)
        other = os.path.join(altpath, fullname)
        tries.append(other)
        if os.path.isfile(other):
            return (1, other)
        other = os.path.join(altpath, os.path.basename(fullname))
        tries.append(other)
        if os.path.isfile(other):
            return (1, other)
        if len(fullname) > 3:
            if fullname[1] == ':':
                fullname = fullname[2:]
                for path in self.search_paths:
                    other = os.path.normpath("%s/%s" % (path, fullname))
                    tries.append(other)
                    if os.path.isfile(other):
                        return (1, other)
            return (0, tries)
        else:
            return (0, tries)

    def level_is_finished(self, text, level):
        """
        Check to see if the level has been completed, indicated by finding
        a level indiciated by the passed level value. If the level is finished,
        then make sure to call self.backup to reset the text pointer.
        """
        done = text.level < level
        if done:
            self.backup()
        return done

    def get_next(self):
        """
        Gets the next line for analysis from the lexical analyzer. Return the
        same value if the backup flag is set.
        """
        if not self.backoff:
            self.groups = self.lexer.readline()
            self.update()
            
            # EOF ?
            if not self.groups:
                self.backoff = False
                self.warn(TRUNC_MSG)
                self.error_count += 1
                self.groups = None
                raise Errors.GedcomError(TRUNC_MSG)

        self.backoff = False
        return self.groups
            
    def not_recognized(self, level):
        """
        Prints a message when an undefined token is found. All subordinate items
        to the current item are ignored.

        @param level: Current level in the file
        @type level: int
        """
        text = self.groups.line
        msg = _("Line %d was not understood, so it was ignored.") % text
        self.warn(msg)
        self.error_count += 1
        import sys
        sys.exit(1)
        self.skip_subordinate_levels(level)

    def warn(self, msg):
        """
        Displays a msg using the logging facilities.
        """
        LOG.warning(msg)
        self.error_count += 1

    def backup(self):
        """
        Sets the backup flag so that the current line can be accessed by the next
        level up.
        """
        self.backoff = True

    def parse_gedcom_file(self, use_trans=False):
        """
        Parses the opened GEDCOM file.
        """
        no_magic = self.maxpeople < 1000
        self.trans = self.dbase.transaction_begin("", not use_trans, no_magic)

        self.dbase.disable_signals()
        self.parse_header_head()
        self.parse_header_source()
        self.parse_submitter()
        if self.use_def_src:
            self.dbase.add_source(self.def_src, self.trans)
        self.parse_record()
        self.parse_trailer()
            
        for title in self.inline_srcs.keys():
            handle = self.inline_srcs[title]
            src = RelLib.Source()
            src.set_handle(handle)
            src.set_title(title)
            self.dbase.add_source(src, self.trans)
            
        self.dbase.transaction_commit(self.trans, _("GEDCOM import"))
        self.dbase.enable_signals()
        self.dbase.request_rebuild()
        
    def parse_trailer(self):
        """
        Looks for the expected TRLR token
        """
        try:
            line = self.get_next()
            if line and line.token != TOKEN_TRLR:
                self.not_recognized(0)
        except TypeError:
            return
        
    def parse_submitter(self):
        """
        Parses the submitter data
        """
        line = self.get_next()
        if line.data != "SUBM":
            self.backup()
            return
        else:
            while True:
                line = self.get_next()
                if self.level_is_finished(line, 1):
                    break
                elif line.token == TOKEN_NAME:
                    if self.use_def_src:
                        self.def_src.set_author(line.data)
                elif line.token == TOKEN_ADDR:
                    self.skip_subordinate_levels(2)

    def parse_record(self):
        """
        Parses the top level (0 level) instances.
        """
        while True:
            line = self.get_next()
            key = line.data
            if not line or line.token == TOKEN_TRLR:
                self.backup()
                break
            if line.token == TOKEN_UNKNOWN:
                self.skip_subordinate_levels(1)
            elif key in ("FAM", "FAMILY"):
                self.parse_fam(line)
            elif key in ("INDI", "INDIVIDUAL"):
                self.parse_indi(line)
            elif key in ("OBJE", "OBJECT"):
                self.parse_obje(line)
            elif key in ("REPO", "REPOSITORY"):
                self.parse_repo(line)
            elif key in ("SUBM", "SUBN", "SUBMITTER"):
                print line
                self.skip_subordinate_levels(1)
            elif line.token in (TOKEN_SUBM, TOKEN_SUBN, TOKEN_IGNORE):
                self.skip_subordinate_levels(1)
            elif key in ("SOUR","SOURCE"):
                self.parse_source(line.token_text, 1)
            elif line.data.startswith("SOUR ") or \
                    line.data.startswith("SOURCE "):
                print line
                # A source formatted in a single line, for example:
                # 0 @S62@ SOUR This is the title of the source
                source = self.find_or_create_source(self.sid_map[line[3]])
                source.set_title(line.data[5:])
                self.dbase.commit_source(source, self.trans)
            elif key[0:4] == "NOTE":
                self.skip_subordinate_levels(1)
            else:
                self.not_recognized(1)

    def parse_level(self, state, func_map, default):
        """
        Loops trough the current GEDCOM level level, calling the appropriate functions
        associated with the TOKEN. If no matching function for the token is found, the
        default function is called instead.
        """
        while True:
            line = self.get_next()
            if line.level < state.level:
                self.backoff = True
                return
            else:
                func = func_map.get(line.token, default)
                if self.debug:
                    print line
                func(line, state)

    def func_undefined(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.not_recognized(state.level+1)

    #----------------------------------------------------------------------
    #
    # INDI parsing
    #
    #----------------------------------------------------------------------
    def parse_indi(self, line):
        """
        Handling of the GEDCOM INDI tag and all lines subordinate to the current
        line.

        n  @XREF:INDI@ INDI {1:1}
        +1 RESN <RESTRICTION_NOTICE> {0:1}
        +1 <<PERSONAL_NAME_STRUCTURE>> {0:M}
        +1 SEX <SEX_VALUE> {0:1}
        +1 <<INDIVIDUAL_EVENT_STRUCTURE>> {0:M}
        +1 <<INDIVIDUAL_ATTRIBUTE_STRUCTURE>> {0:M}
        +1 <<LDS_INDIVIDUAL_ORDINANCE>> {0:M}
        +1 <<CHILD_TO_FAMILY_LINK>> {0:M}
        +1 <<SPOUSE_TO_FAMILY_LINK>> {0:M}
        +1 SUBM @<XREF:SUBM>@ {0:M}
        +1 <<ASSOCIATION_STRUCTURE>> {0:M}
        +1 ALIA @<XREF:INDI>@ {0:M}
        +1 ANCI @<XREF:SUBM>@ {0:M}
        +1 DESI @<XREF:SUBM>@ {0:M}
        +1 <<SOURCE_CITATION>> {0:M}
        +1 <<MULTIMEDIA_LINK>> {0:M}
        +1 <<NOTE_STRUCTURE>> {0:M} 
        +1 RFN <PERMANENT_RECORD_FILE_NUMBER> {0:1}
        +1 AFN <ANCESTRAL_FILE_NUMBER> {0:1}
        +1 REFN <USER_REFERENCE_NUMBER> {0:M}
        +2 TYPE <USER_REFERENCE_TYPE> {0:1}
        +1 RIN <AUTOMATED_RECORD_ID> {0:1}
        +1 <<CHANGE_DATE>> {0:1}
        """

        # find the person
        self.person = self.find_or_create_person(self.pid_map[line.token_text])
        self.added.add(self.person.handle)

        # set up the state for the parsing
        state = GedcomUtils.CurrentState(person=self.person, level=1)

	# Ancestry.com GEDCOM files are massively broken, not providing 
	# the FAMC and FAMS values for a person
	if self.is_ancestry_com:
	    self.map_ancestry_com(line.token_text.strip())

        # do the actual parsing
        self.parse_level(state, self.indi_parse_tbl, self.func_person_event)

        # Add the default reference if no source has found
        self.add_default_source(self.person)

        # commit the person to the database
        if self.person.change:
            self.dbase.commit_person(self.person, self.trans,
                                  change_time=state.person.change)
        else:
            self.dbase.commit_person(self.person, self.trans)
        del self.person

    def func_person_sour(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        source_ref = self.handle_source(line, state.level+1)
        state.person.add_source_reference(source_ref)

    def func_person_refn(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if INT_RE.match(line.data):
            try:
                self.refn[state.person.handle] = int(line.data)
            except:
                return

    def func_person_attr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type((RelLib.AttributeType.CUSTOM, line.token_text))
        attr.set_value(line.data)
        state.person.add_attribute(attr)

    def func_person_event(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self._build_event_pair(state, RelLib.EventType.CUSTOM, 
                                           self.event_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def skip_record(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(2)

    def func_person_chan(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_change(line, state.person, state.level+1)
        
    def func_person_resn(self, line, state):
        """
        Parses the RESN tag, adding it as an attribute.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type((RelLib.AttributeType.CUSTOM, 'RESN'))
        state.person.add_attribute(attr)

    def func_person_alt_name(self, line, state):
        """
        Parse a altername name, usually indicated by a AKA or _AKA
        tag. This is not valid GEDCOM, but several programs will add
        this just to make life interesting. Odd, since GEDCOM supports
        multiple NAME indicators, which is the correct way of handling
        multiple names.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        name = GedcomUtils.parse_name_personal(line.data)
        name.set_type(RelLib.NameType.AKA)
        state.person.add_alternate_name(name)

        # Create a new state, and parse the remainder of the NAME level
        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.name = name
        sub_state.level = 2

        self.parse_level(sub_state,  self.name_parse_tbl, self.func_undefined)

    def func_person_object(self, line, state):
        """
        Currently, the embedded form is not supported
        
        Embedded form
        
        >   n OBJE @<XREF:OBJE>@ {1:1}

        Linked form
         
        >   n OBJE {1:1}
        >   +1 FORM <MULTIMEDIA_FORMAT> {1:1}
        >   +1 TITL <DESCRIPTIVE_TITLE> {0:1}
        >   +1 FILE <MULTIMEDIA_FILE_REFERENCE> {1:1}
        >   +1 <<NOTE_STRUCTURE>> {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            ref = RelLib.MediaRef()
            handle = self.find_object_handle(line.data[1:-1])
            ref.set_reference_handle(handle)
            state.person.add_media_reference(ref)
        else:
            (form, filename, title, note) = self.func_obje(state.level+1)
            self.build_media_object(state.person, form, filename, title, note)

    def func_person_name(self, line, state):
        """
        Parsers the NAME token in a GEDCOM file. The text is in the format
        of (according to the GEDCOM Spec):
        >   <TEXT>|/<TEXT>/|<TEXT>/<TEXT>/|/<TEXT>/<TEXT>|<TEXT>/<TEXT>/<TEXT>
        We have encountered some variations that use:
        >   <TEXT>/

        The basic Name structure is:

          n  NAME <NAME_PERSONAL> {1:1}
          +1 NPFX <NAME_PIECE_PREFIX> {0:1}
          +1 GIVN <NAME_PIECE_GIVEN> {0:1}
          +1 NICK <NAME_PIECE_NICKNAME> {0:1}
          +1 SPFX <NAME_PIECE_SURNAME_PREFIX {0:1}
          +1 SURN <NAME_PIECE_SURNAME> {0:1}
          +1 NSFX <NAME_PIECE_SUFFIX> {0:1}
          +1 <<SOURCE_CITATION>> {0:M}
          +1 <<NOTE_STRUCTURE>> {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        # build a RelLib.Name structure from the text
        
        name = GedcomUtils.parse_name_personal(line.data)

        # Add the name as the primary name if this is the first one that
        # we have encountered for this person. Assume that if this is the
        # first name, that it is a birth name. Otherwise, label it as an
        # "Also Known As (AKA)". GEDCOM does not seem to have the concept
        # of different name types
        
        if state.name_cnt == 0:
            name.set_type(RelLib.NameType.BIRTH)
            state.person.set_primary_name(name)
        else:
            name.set_type(RelLib.NameType.AKA)
            state.person.add_alternate_name(name)
        state.name_cnt += 1

        # Create a new state, and parse the remainder of the NAME level
        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.name = name
        sub_state.level = state.level+1

        self.parse_level(sub_state, self.name_parse_tbl, self.func_undefined)

    def func_person_sex(self, line, state):
        """
        Parses the SEX line of a GEDCOM file. It has the format of:

        +1 SEX <SEX_VALUE> {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.person.set_gender(line.data)

    def func_person_even(self, line, state):
        """
        Parses the custom EVEN tag, which has the format of:

           n  <<EVENT_TYPE>> {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self._build_event_pair(state, RelLib.EventType.CUSTOM,
                                           self.event_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def func_person_std_event(self, line, state):
        """
        Parses GEDCOM event types that map to a GRAMPS standard type. Additional
        parsing required is for the event detail:

           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event = RelLib.Event()
        event_ref = RelLib.EventRef()
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(line.data)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.parse_level(sub_state, self.event_parse_tbl, self.func_undefined)

        person_event_name(event, state.person)
        self.dbase.add_event(event, self.trans)
        event_ref.ref = event.handle
        state.person.add_event_ref(event_ref)

    def func_person_reli(self, line, state):
        """
        Parses the RELI tag.

           n  RELI [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self._build_event_pair(state, RelLib.EventType.RELIGION,
                                           self.event_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def func_person_birt(self, line, state):
        """
        Parses GEDCOM BIRT tag into a GRAMPS birth event. Additional work
        must be done, since additional handling must be done by GRAMPS to set this up
        as a birth reference event.

           n  BIRT [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*
           +1 FAMC @<XREF:FAM>@ {0:1} p.*

        I'm not sure what value the FAMC actually offers here, since
        the FAMC record should handle this. Why it is a valid sub value
        is beyond me.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self._build_event_pair(state, RelLib.EventType.BIRTH,
                                           self.event_parse_tbl, line.data)
        if state.person.get_birth_ref():
            state.person.add_event_ref(event_ref)
        else:
            state.person.set_birth_ref(event_ref)

    def func_person_adop(self, line, state):
        """
        Parses GEDCOM ADOP tag, subordinate to the INDI tag. Additinal tags
        are needed by the tag, so we pass a different function map.

           n  ADOP [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*
           +1 FAMC @<XREF:FAM>@ {0:1} p.*
           +2 ADOP <ADOPTED_BY_WHICH_PARENT> {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self._build_event_pair(state, RelLib.EventType.ADOPT,
                                           self.adopt_parse_tbl, line.data)
        state.person.add_event_ref(event_ref)

    def func_person_deat(self, line, state):
        """
        Parses GEDCOM DEAT tag into a GRAMPS birth event. Additional work
        must be done, since additional handling must be done by GRAMPS to set this up
        as a death reference event.

           n  DEAT [Y|<NULL>] {1:1}
           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event_ref = self._build_event_pair(state, RelLib.EventType.DEATH,
                                           self.event_parse_tbl, line.data)
        if state.person.get_death_ref():
            state.person.add_event_ref(event_ref)
        else:
            state.person.set_death_ref(event_ref)

    def func_person_note(self, line, state):
        """
        Parses a note associated with the person

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.person, 1)

    def func_person_rnote(self, line, state):
        """
        Parses a note associated with the person

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.person, 1)

    def func_person_addr(self, line, state):
        """
        Parses the Address structure

        n ADDR <ADDRESS_LINE> {0:1} 
        +1 CONT <ADDRESS_LINE> {0:M}
        +1 ADR1 <ADDRESS_LINE1> {0:1}
        +1 ADR2 <ADDRESS_LINE2> {0:1}
        +1 CITY <ADDRESS_CITY> {0:1}
        +1 STAE <ADDRESS_STATE> {0:1}
        +1 POST <ADDRESS_POSTAL_CODE> {0:1}
        +1 CTRY <ADDRESS_COUNTRY> {0:1}
        n PHON <PHONE_NUMBER> {0:3}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr = RelLib.Address()
        state.addr.set_street(line.data)
        state.person.add_address(state.addr)
        self.parse_level(state, self.parse_addr_tbl, self.func_ignore)

    def func_person_phon(self, line, state):
        """
        n PHON <PHONE_NUMBER> {0:3}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        addr = RelLib.Address()
        addr.set_street("Unknown")
        addr.set_phone(line.data)
        state.person.add_address(addr)

    def func_person_titl(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event = RelLib.Event()
        event_ref = RelLib.EventRef()
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(RelLib.EventType.NOB_TITLE)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.parse_level(sub_state, self.event_parse_tbl, self.func_undefined)

        person_event_name(event, state.person)
        self.dbase.add_event(event, self.trans)

    def func_person_attr_plac(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.attr.get_value() == "":
            state.attr.set_value(line.data)

    def func_name_type(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data == "_OTHN":
            state.name.set_type(RelLib.NameType.AKA)
        else:
            state.name.set_type((RelLib.NameType.CUSTOM,line.data))

    def func_name_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.name, state.level+1)

    def func_name_alia(self, line, state):
        """
        The ALIA tag is supposed to cross reference another person.
        However, we do not support this.

        Some systems use the ALIA tag as an alternate NAME tag, which
        is not legal in GEDCOM, but oddly enough, is easy to support.
        """
        if line.data[0] == '@':
            aka = GedcomUtils.parse_name_personal(line.data)
            state.person.add_alternate_name(aka)

    def func_name_npfx(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_title(line.data.strip())
        self.skip_subordinate_levels(state.level+1)

    def func_name_givn(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_first_name(line.data.strip())
        self.skip_subordinate_levels(state.level+1)

    def func_name_spfx(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_surname_prefix(line.data.strip())
        self.skip_subordinate_levels(state.level+1)

    def func_name_surn(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.name.set_surname(line.data.strip())
        self.skip_subordinate_levels(state.level+1)

    def func_name_marnm(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        text = line.data.strip()
        data = text.split()
        if len(data) == 1:
            name = RelLib.Name(state.person.primary_name)
            name.set_surname(data[0].strip())
            name.set_type(RelLib.NameType.MARRIED)
            state.person.add_alternate_name(name)
        elif len(data) > 1:
            name = GedcomUtils.parse_name_personal(text)
            name.set_type(RelLib.NameType.MARRIED)
            state.person.add_alternate_name(name)

    def func_name_nsfx(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.name.get_suffix() == "":
            state.name.set_suffix(line.data)
        self.skip_subordinate_levels(state.level+1)

    def func_name_nick(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type(RelLib.AttributeType.NICKNAME)
        attr.set_value(line.data)
        state.person.add_attribute(attr)
        self.skip_subordinate_levels(state.level+1)

    def func_name_aka(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """        
        lname = line.data.split()
        name_len = len(lname)
        if name_len == 1:
            attr = RelLib.Attribute()
            attr.set_type(RelLib.AttributeType.NICKNAME)
            attr.set_value(line.data)
            state.person.add_attribute(attr)
        else:
            name = RelLib.Name()
            name.set_surname(lname[-1].strip())
            name.set_first_name(' '.join(lname[0:name_len-1]))
            state.person.add_alternate_name(name)

    def func_name_sour(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sref = self.handle_source(line, state.level+1)
        state.name.add_source_reference(sref)

    def func_person_resi(self, line, state):
        """
        The RESI tag follows the EVENT_DETAIL structure, which is:

          n TYPE <EVENT_DESCRIPTOR> {0:1}
          n DATE <DATE_VALUE> {0:1}
          n <<PLACE_STRUCTURE>> {0:1}
          n <<ADDRESS_STRUCTURE>> {0:1}
          n AGE <AGE_AT_EVENT> {0:1}
          n AGNC <RESPONSIBLE_AGENCY> {0:1}
          n CAUS <CAUSE_OF_EVENT> {0:1}
          n <<SOURCE_CITATION>> {0:M}
          n <<MULTIMEDIA_LINK>> {0:M}
          n <<NOTE_STRUCTURE>> {0:M}

        Currently, the TYPE, AGE, CAUSE, STAT, and other tags which
        do not apply to an address are ignored.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        addr = RelLib.Address()

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.addr = addr
        sub_state.person.add_address(addr)

        self.parse_level(sub_state, self.resi_parse_tbl, self.func_undefined)

    def func_person_resi_date(self, line, state): 
        """
        Sets the date on the address associated with and Address.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_date_object(line.data)
        
    def func_person_resi_addr(self, line, state):
        """
        Parses the ADDR line of a RESI tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_street(line.data)

        sub_state = GedcomUtils.CurrentState()
        sub_state.addr = state.addr
        sub_state.level = state.level + 1
        sub_state.person = state.person
        self.parse_level(sub_state, self.parse_addr_tbl, self.func_ignore)

    def func_person_resi_sour(self, line, state):
        """
        Parses the source connected to a RESI tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.add_source_reference(self.handle_source(line, state.level+1))

    def func_person_resi_plac(self, line, state):
        """
        Parses the PLAC tag connected to a RESI tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_street(line.data)
        self.parse_level(state, self.parse_addr_tbl, self.func_ignore)

    def func_person_resi_phon(self, line, state): 
        """
        Parses the source connected to a PHON tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.addr.get_street() == "":
            state.addr.set_street("Unknown")
        state.addr.set_phone(line.data)

    def func_person_resi_note(self, line, state):
        """
        Parses the NOTE connected to a RESI tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.addr, state.level+1)

    def func_ignore(self, line, state):
        """
        Ignores an unsupported tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(state.level+1)

    def func_person_std_attr(self, line, state):
        """
        Parses an TOKEN that GRAMPS recognizes as an Attribute

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.attr = line.data
        sub_state.level = state.level+1
        state.person.add_attribute(sub_state.attr)
        self.parse_level(sub_state, self.person_attr_parse_tbl, 
			 self.func_ignore)

    def func_person_bapl(self, line, state):
        """
        Parses an BAPL TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, RelLib.LdsOrd.BAPTISM)

    def func_person_conl(self, line, state):
        """
        Parses an CONL TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, RelLib.LdsOrd.CONFIRMATION)

    def func_person_endl(self, line, state):
        """
        Parses an ENDL TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, RelLib.LdsOrd.ENDOWMENT)

    def func_person_slgc(self, line, state):
        """
        Parses an SLGC TOKEN, producing a GRAMPS LdsOrd instance

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.build_lds_ord(state, RelLib.LdsOrd.SEAL_TO_PARENTS)

    def build_lds_ord(self, state, lds_type):
        """
        Parses an LDS ordinance, using the type passed to the routine

        @param state: The current state
        @type state: CurrentState
        @param lds_type: The type of the LDS ordinance
        @type line: LdsOrd type
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level + 1
        sub_state.lds_ord = RelLib.LdsOrd()
        sub_state.lds_ord.set_type(lds_type)
        sub_state.place = None
        sub_state.place_fields = GedcomUtils.PlaceParser()
        sub_state.person = state.person
        state.person.lds_ord_list.append(sub_state.lds_ord)

        self.parse_level(sub_state, self.lds_parse_tbl, self.func_ignore)

        if sub_state.place:
            sub_state.place_fields.load_place(sub_state.place, 
                                              sub_state.place.get_title())

    def func_lds_temple(self, line, state):
        """
        Parses the TEMP tag, looking up the code for a match.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        value = self.extract_temple(line)
        if value:
            state.lds_ord.set_temple(value)

    def func_lds_date(self, line, state): 
        """
        Parses the DATE tag for the LdsOrd

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.lds_ord.set_date_object(line.data)

    def func_lds_famc(self, line, state):
        """
        Parses the FAMC tag attached to the LdsOrd

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        gid = self.fid_map[line.data]
        state.lds_ord.set_family_handle(self.find_family_handle(gid))

    def func_lds_form(self, line, state): 
        """
        Parses the FORM tag thate defines the place structure for a place. This
        tag, if found, will override any global place structure.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.pf = GedcomUtils.PlaceParser(line)

    def func_lds_plac(self, line, state):
        """
        Parses the PLAC tag attached to the LdsOrd. Create a new place if
        needed and set the title.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        try:
            state.place = self.find_or_create_place(line.data)
            state.place.set_title(line.data)
            state.lds_ord.set_place_handle(state.place.handle)
        except NameError:
            return

    def func_lds_sour(self, line, state):
        """
        Parses the SOUR tag attached to the LdsOrd. 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        srcref = self.handle_source(line, state.level+1)
        state.lds_ord.add_source_reference(srcref)

    def func_lds_note(self, line, state):
        """
        Parses the NOTE tag attached to the LdsOrd. 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.lds_ord, state.level+1)

    def func_lds_stat(self, line, state): 
        """
        Parses the STAT (status) tag attached to the LdsOrd. 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        status = lds_status.get(line.data, RelLib.LdsOrd.STATUS_NONE)
        state.lds_ord.set_status(status)

    def func_person_famc(self, line, state):
        """
        Handles the parsing of the FAMC line, which indicates which family the
        person is a child of.

        n FAMC @<XREF:FAM>@ {1:1}
        +1 PEDI <PEDIGREE_LINKAGE_TYPE> {0:M} p.*
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level + 1
        sub_state.ftype = None
        sub_state.primary = False

        gid = self.fid_map[line.data]
        handle = self.find_family_handle(gid)

        self.parse_level(sub_state, self.famc_parse_tbl, self.func_undefined)

        # if the handle is not already in the person's parent family list, we
        # need to add it to thie list.

        flist = [fam[0] for fam in state.person.get_parent_family_handle_list()]
        if not handle in flist:
            if sub_state.ftype and int(sub_state.ftype) in RELATION_TYPES:
                state.person.add_parent_family_handle(handle)
            else:
                if state.person.get_main_parents_family_handle() == handle:
                    state.person.set_main_parent_family_handle(None)
                state.person.add_parent_family_handle(handle)

            # search childrefs
            family = self.dbase.find_family_from_handle(handle, self.trans)
            family.set_gramps_id(gid)
                
            for ref in family.get_child_ref_list():
                if ref.ref == state.person.handle:
                    if sub_state.ftype:
                        ref.set_mother_relation(sub_state.ftype)
                        ref.set_father_relation(sub_state.ftype)
                    break
            else:
                ref = RelLib.ChildRef()
                ref.ref = state.person.handle
                if sub_state.ftype:
                    ref.set_mother_relation(sub_state.ftype)
                    ref.set_father_relation(sub_state.ftype)
                family.add_child_ref(ref)
            self.dbase.commit_family(family, self.trans)

    def func_person_famc_pedi(self, line, state): 
        """
        Parses the PEDI tag attached to a INDI.FAMC record. No values are set
        at this point, because we have to do some post processing. Instead, we
        assign the ftype field of the state variable. We convert the text from
        the line to an index into the PEDIGREE_TYPES dictionary, which will map
        to the correct ChildTypeRef.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.ftype = PEDIGREE_TYPES.get(line.data.lower(), 
                                         RelLib.ChildRefType.UNKNOWN)

    def func_person_famc_note(self, line, state):
        """
        Parses the INDI.FAMC.NOTE tag .

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.person, state.level+1)

    def func_person_famc_primary(self, line, state): 
        """
        Parses the _PRIM tag on an INDI.FAMC tag. This value is stored in 
        the state record to be used later.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.primary = True

    def func_person_famc_sour(self, line, state):
        """
        Parses the SOUR tag on an INDI.FAMC tag. GRAMPS has no corresponding
        record on its family relationship, so we add the source to the Person
        record.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        source_ref = self.handle_source(line, state.level)
        state.person.add_source_reference(source_ref)

    def func_person_fams(self, line, state):
        """
        Parses the INDI.FAMS record, which indicates the family in which the
        person is a spouse.

        n FAMS @<XREF:FAM>@ {1:1} p.*
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        handle = self.find_family_handle(self.fid_map[line.data])
        state.person.add_family_handle(handle)
        self.parse_optional_note(self.person, 2)

    def func_person_asso(self, line, state):
        """
        Parse the ASSO tag, add the the referenced person to the person we
        are currently parsing. The GEDCOM spec indicates that valid ASSO tag
        is:
        
        n ASSO @<XREF:INDI>@ {0:M}
           
        And the the sub tags are:
        
        ASSOCIATION_STRUCTURE:=
         +1 TYPE <RECORD_TYPE> {1:1}
         +1 RELA <RELATION_IS_DESCRIPTOR> {1:1}
         +1 <<NOTE_STRUCTURE>> {0:M}
         +1 <<SOURCE_CITATION>> {0:M}

        GRAMPS only supports ASSO records to people, so if the TYPE is
        something other than INDI, the record is ignored.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        # find the id and person that we are referencing
        handle = self.find_person_handle(self.pid_map[line.data])

        # create a new PersonRef, and assign the handle, add the
        # PersonRef to the active person

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level + 1
        sub_state.ref = RelLib.PersonRef()
        sub_state.ref.ref = handle
        sub_state.ignore = False

        self.parse_level(sub_state, self.asso_parse_tbl, self.func_ignore)
        if not sub_state.ignore:
            state.person.add_person_ref(sub_state.ref)

    def func_person_asso_type(self, line, state): 
        """
        Parses the INDI.ASSO.TYPE tag. GRAMPS only supports the ASSO tag when
        the tag represents an INDI. So if the data is not INDI, we set the ignore
        flag, so that we ignore the record.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data != "INDI":
            state.ignore = True

    def func_person_asso_rela(self, line, state): 
        """
        Parses the INDI.ASSO.RELA tag.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.ref.rel = line.data

    def func_person_asso_sour(self, line, state):
        """
        Parses the INDI.ASSO.SOUR tag.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.ref.add_source_reference(self.handle_source(line, state.level))

    def func_person_asso_note(self, line, state):
        """
        Parses the INDI.ASSO.NOTE tag.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.ref, state.level)

    #-------------------------------------------------------------------
    # 
    # Family parsing
    #
    #-------------------------------------------------------------------
	
    def parse_fam(self, line):
        """
          n @<XREF:FAM>@   FAM   {1:1}
	  +1 <<FAMILY_EVENT_STRUCTURE>>  {0:M}
	  +1 HUSB @<XREF:INDI>@  {0:1}
	  +1 WIFE @<XREF:INDI>@  {0:1}
	  +1 CHIL @<XREF:INDI>@  {0:M}
	  +1 NCHI <COUNT_OF_CHILDREN>  {0:1}
	  +1 SUBM @<XREF:SUBM>@  {0:M}
	  +1 <<LDS_SPOUSE_SEALING>>  {0:M}
	  +1 <<SOURCE_CITATION>>  {0:M}
	  +1 <<MULTIMEDIA_LINK>>  {0:M}
	  +1 <<NOTE_STRUCTURE>>  {0:M}
	  +1 REFN <USER_REFERENCE_NUMBER>  {0:M}
	  +1 RIN <AUTOMATED_RECORD_ID>  {0:1}
	  +1 <<CHANGE_DATE>>  {0:1}
	"""
        # create a family
        
        family = self.find_or_create_family(self.fid_map[line.token_text])

        # parse the family

        state = GedcomUtils.CurrentState()
        state.level = 1
        state.family = family

        while True:
            line = self.get_next()

            if self.level_is_finished(line, 1):
                break
            if line.token not in (TOKEN_ENDL, TOKEN_BAPL, TOKEN_CONL):
                func = self.family_func.get(line.token, self.func_family_even)
                func(line, state)

        # handle addresses attached to families
        if state.addr != None:
            father_handle = family.get_father_handle()
            father = self.dbase.get_person_from_handle(father_handle)
            if father:
                father.add_address(state.addr)
                self.dbase.commit_person(father, self.trans)
            mother_handle = family.get_mother_handle()
            mother = self.dbase.get_person_from_handle(mother_handle)
            if mother:
                mother.add_address(state.addr)
                self.dbase.commit_person(mother, self.trans)

            for child_ref in family.get_child_ref_list():
                child_handle = child_ref.ref
                child = self.dbase.get_person_from_handle(child_handle)
                if child:
                    child.add_address(state.addr)
                    self.dbase.commit_person(child, self.trans)

        # add default reference if no reference exists
        self.add_default_source(family)

        # commit family to database
        if family.change:
            self.dbase.commit_family(family, self.trans,
                                  change_time=family.change)
        else:
            self.dbase.commit_family(family, self.trans)
    
    def func_family_husb(self, line, state):
        """
        Parses the husband line of a family

        n HUSB @<XREF:INDI>@  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
	    """
        handle = self.find_person_handle(self.pid_map[line.data])
        state.family.set_father_handle(handle)

    def func_family_wife(self, line, state):
        """
	    Parses the wife line of a family

	      n WIFE @<XREF:INDI>@  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
	    """
        handle = self.find_person_handle(self.pid_map[line.data])
        state.family.set_mother_handle(handle)

    def func_family_std_event(self, line, state):
        """
        Parses GEDCOM event types that map to a GRAMPS standard type. Additional
        parsing required is for the event detail:

           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event = RelLib.Event()
        event_ref = RelLib.EventRef()
        event_ref.set_role(RelLib.EventRoleType.FAMILY)
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(line.data)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.parse_level(sub_state, self.event_parse_tbl, self.func_undefined)

        family_event_name(event, state.family)
        self.dbase.add_event(event, self.trans)
        event_ref.ref = event.handle
        state.family.add_event_ref(event_ref)

    def func_family_even(self, line, state):
        """
        Parses GEDCOM event types that map to a GRAMPS standard type. Additional
        parsing required is for the event detail:

           +1 <<EVENT_DETAIL>> {0:1} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        event = RelLib.Event()
        event_ref = RelLib.EventRef()
        event_ref.set_role(RelLib.EventRoleType.FAMILY)
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(line.data)

        sub_state = GedcomUtils.CurrentState()
        sub_state.person = state.person
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.parse_level(sub_state, self.event_parse_tbl, self.func_undefined)

        if int(event.get_type()) == RelLib.EventType.MARRIAGE:

            descr = event.get_description()
            if descr == "Civil Union":
                state.family.type.set(RelLib.FamilyRelType.CIVIL_UNION)
                event.set_description('')
            elif descr == "Unmarried":
                state.family.type.set(RelLib.FamilyRelType.UNMARRIED)
                event.set_description('')
            else:
                state.family.type.set(RelLib.FamilyRelType.MARRIED)

        family_event_name(event, state.family)

        self.dbase.add_event(event, self.trans)
        event_ref.ref = event.handle
        state.family.add_event_ref(event_ref)

    def func_family_chil(self, line, state):
        """
        Parses the child line of a family

        n CHIL @<XREF:INDI>@  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.family = state.family
        sub_state.level = state.level + 1
        sub_state.mrel = None
        sub_state.frel = None

        self.parse_level(sub_state, self.family_rel_tbl, self.func_undefined)

        child = self.find_or_create_person(self.pid_map[line.data])

        reflist = [ ref for ref in state.family.get_child_ref_list() \
                    if ref.ref == child.handle ]

        if reflist:
            ref = reflist[0]
            if sub_state.frel:
                ref.set_father_relation(sub_state.frel)
            if sub_state.mrel:
                ref.set_mother_relation(sub_state.mrel)
        else:
            ref = RelLib.ChildRef()
            ref.ref = child.handle
            if sub_state.frel:
                ref.set_father_relation(sub_state.frel)
            if sub_state.mrel:
                ref.set_mother_relation(sub_state.mrel)
            state.family.add_child_ref(ref)

    def func_family_slgs(self, line, state):
        """
        n  SLGS          {1:1}
        +1 STAT <LDS_SPOUSE_SEALING_DATE_STATUS>  {0:1}
        +1 DATE <DATE_LDS_ORD>  {0:1}
        +1 TEMP <TEMPLE_CODE>  {0:1}
        +1 PLAC <PLACE_LIVING_ORDINANCE>  {0:1}
        +1 <<SOURCE_CITATION>>  {0:M}
        +1 <<NOTE_STRUCTURE>>  {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
	    """
        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level + 1
        sub_state.lds_ord = RelLib.LdsOrd()
        sub_state.lds_ord.set_type(RelLib.LdsOrd.SEAL_TO_SPOUSE)
        sub_state.place = None
        sub_state.family = state.family
        sub_state.place_fields = GedcomUtils.PlaceParser()
        state.family.lds_ord_list.append(sub_state.lds_ord)

        self.parse_level(sub_state, self.lds_parse_tbl, self.func_ignore)

        if sub_state.place:
            sub_state.place_fields.load_place(sub_state.place, 
					      sub_state.place.get_title())

    def func_family_source(self, line, state):
        """
        n SOUR @<XREF:SOUR>@ /* pointer to source record */ {1:1} p.*
        +1 PAGE <WHERE_WITHIN_SOURCE> {0:1} p.*
        +1 EVEN <EVENT_TYPE_CITED_FROM> {0:1} p.*
        +1 DATA {0:1}
        +1 QUAY <CERTAINTY_ASSESSMENT> {0:1} p.*
        +1 <<MULTIMEDIA_LINK>> {0:M} p.*,*
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        | /* Systems not using source records */
        n SOUR <SOURCE_DESCRIPTION> {1:1} p.*
        +1 [ CONC | CONT ] <SOURCE_DESCRIPTION> {0:M}
        +1 TEXT <TEXT_FROM_SOURCE> {0:M} p.*
        +1 <<NOTE_STRUCTURE>> {0:M} p.*

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        source_ref = self.handle_source(line, state.level+1)
        state.family.add_source_reference(source_ref)

    def func_family_object(self, line, state):
        """
    	  +1 <<MULTIMEDIA_LINK>>  {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.not_recognized(state.level)
        else:
            (form, filename, title, note) = self.func_obje(state.level)
            self.build_media_object(state.family, form, filename, title, note)

    def func_family_comm(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        note = line.data
        state.family.add_note(note)
        self.skip_subordinate_levels(state.level+1)

    def func_family_note(self, line, state):
        """
        +1 <<NOTE_STRUCTURE>>  {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.family, state.level)

    def func_family_chan(self, line, state):
        """
        +1 <<CHANGE_DATE>>  {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_change(line, state.family, state.level+1)

    def func_family_addr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr = RelLib.Address()
        state.addr.set_street(line.data)
        self.parse_level(state, self.parse_addr_tbl, self.func_ignore)

    def func_family_attr(self, line, state): 
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.family.add_attribute(line.data)

    def func_family_cust_attr(self, line, state): 
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type(line.token_text)
        attr.set_value(line.data)
        state.family.add_attribute(attr)

    def func_obje(self, level):
        """
          n  OBJE {1:1}
          +1 FORM <MULTIMEDIA_FORMAT> {1:1}
          +1 TITL <DESCRIPTIVE_TITLE> {0:1}
          +1 FILE <MULTIMEDIA_FILE_REFERENCE> {1:1}
          +1 <<NOTE_STRUCTURE>> {0:M} 

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState()
        sub_state.form = ""
        sub_state.filename = ""
        sub_state.title = ""
        sub_state.note = ""
        sub_state.level = level

        self.parse_level(sub_state, self.object_parse_tbl, self.func_ignore)
        return (sub_state.form, sub_state.filename, sub_state.title, 
                sub_state.note)

    def func_object_ref_form(self, line, state): 
        """
          +1 FORM <MULTIMEDIA_FORMAT> {1:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.form = line.data

    def func_object_ref_titl(self, line, state): 
        """
          +1 TITL <DESCRIPTIVE_TITLE> {0:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.title = line.data

    def func_object_ref_file(self, line, state): 
        """
          +1 FILE <MULTIMEDIA_FILE_REFERENCE> {1:1}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.filename = line.data

    def func_object_ref_note(self, line, state): 
        """
          +1 <<NOTE_STRUCTURE>> {0:M} 

          TODO: Fix this for full reference

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.note = line.data

    def func_family_adopt(self, line, state):
        """
        n ADOP

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.frel = TYPE_ADOPT
        state.mrel = TYPE_ADOPT

    def func_family_frel(self, line, state):
        """
        The _FREL key is a FTW specific extension to indicate father/child
        relationship.

        n _FREL <type>

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.frel = PEDIGREE_TYPES.get(line.data.strip().lower())

    def func_family_mrel(self, line, state):
        """
        The _MREL key is a FTW specific extension to indicate father/child
        relationship.

        n _MREL <type>

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.mrel = PEDIGREE_TYPES.get(line.data.strip().lower())

    def func_family_stat(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.mrel = TYPE_BIRTH
        state.frel = TYPE_BIRTH

    def func_event_object(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.not_recognized(state.level)
        else:
            (form, filename, title, note) = self.func_obje(state.level)
            self.build_media_object(state.event, form, filename, title, note)

    def func_event_type(self, line, state):
        """
	Parses the TYPE line for an event.

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
	"""
        if state.event.get_type().is_custom():
            if GED_2_GRAMPS.has_key(line.data):
                name = RelLib.EventType(GED_2_GRAMPS[line.data])
            else:
                val = self.gedsource.tag2gramps(line.data)
                if val:
                    name = RelLib.EventType((RelLib.EventType.CUSTOM, val))
                else:
                    name = RelLib.EventType((RelLib.EventType.CUSTOM, line[3]))
            state.event.set_type(name)
        else:
            try:
                if not GED_2_GRAMPS.has_key(line.data) and \
                       not GED_2_FAMILY.has_key(line.data) and \
                       line.data[0] != 'Y':
                    state.event.set_description(line.data)
            except IndexError:
                return

    def func_event_date(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.event.set_date_object(line.data)

    def func_event_place(self, line, state):
        """
        Parse the place portion of a event. A special case has to be made for
        Family Tree Maker, which violates the GEDCOM spec. It uses the PLAC field
        to store the description or value assocated with the event.

         n  PLAC <PLACE_VALUE> {1:1}
         +1 FORM <PLACE_HIERARCHY> {0:1}
         +1 <<SOURCE_CITATION>> {0:M}
         +1 <<NOTE_STRUCTURE>> {0:M}

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """

        if self.is_ftw and int(state.event.get_type()) in FTW_BAD_PLACE:
            state.event.set_description(line.data)
        else:
            place = self.find_or_create_place(line.data)
            place.set_title(line.data)
            state.event.set_place_handle(place.handle)

            sub_state = GedcomUtils.CurrentState()
            sub_state.place = place
            sub_state.level = state.level+1
            sub_state.pf = self.place_parser

            self.parse_level(sub_state, self.event_place_map, 
                             self.func_undefined)

            sub_state.pf.load_place(place, place.get_title())
            self.dbase.commit_place(place, self.trans)

    def func_event_place_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.place, state.level+1)

    def func_event_place_form(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.pf = GedcomUtils.PlaceParser(line)

    def func_event_place_object(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.not_recognized(state.level)
        else:
            (form, filename, title, note) = self.func_obje(state.level)
            self.build_media_object(state.place, form, filename, title, note)

    def func_event_place_sour(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.place.add_source_reference(self.handle_source(line, state.level))

    def func_event_addr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        sub_state.location = RelLib.Location()
        sub_state.location.set_street(line.data)
        sub_state.note = []

        self.parse_level(sub_state, self.parse_loc_tbl, self.func_undefined)

        location = sub_state.location
        note_list = sub_state.note

        place_handle = state.event.get_place_handle()
        if place_handle:
            place = self.dbase.get_place_from_handle(place_handle)
            index = place.get_title() + location.get_street()

            old_title = place.get_title()
            place = self.find_or_create_place(index)
            if place.get_title():
                place.set_title(old_title)
                place_handle = place.handle
                place.set_main_location(location)
        else:
            place = self.find_or_create_place(line.data)
            place.set_title(line.data)
            place_handle = place.handle
            place.set_main_location(location)

        for note in note_list:
            place.add_note(note)

        state.event.set_place_handle(place_handle)
        self.dbase.commit_place(place, self.trans)

    def func_event_privacy(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.event.set_privacy(True)

    def func_event_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.event, state.level+1)
                
    def func_event_source(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.event.add_source_reference(self.handle_source(line, state.level))

    def func_event_cause(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type(RelLib.AttributeType.CAUSE)
        attr.set_value(line.data)
        state.event.add_attribute(attr)

        sub_state = GedcomUtils.CurrentState()
        sub_state.event = state.event
        sub_state.level = state.level + 1

        self.parse_level(sub_state, self.event_cause_tbl, self.func_undefined)

    def func_event_cause_source(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.event.add_source_reference(self.handle_source(line, 
                                                            state.level+1))

    def func_event_age(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type(RelLib.AttributeType.AGE)
        attr.set_value(line.data)
        state.event_ref.add_attribute(attr)

    def func_event_husb(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        while True:
            line = self.get_next()
            if self.level_is_finished(line, state.level):
                break
            elif line.token == TOKEN_AGE:
                attr = RelLib.Attribute()
                attr.set_type(RelLib.AttributeType.FATHER_AGE)
                attr.set_value(line.data)
                state.event_ref.add_attribute(attr)

    def func_event_wife(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        while True:
            line = self.get_next()
            if self.level_is_finished(line, state.level):
                break
            elif line.token == TOKEN_AGE:
                attr = RelLib.Attribute()
                attr.set_type(RelLib.AttributeType.MOTHER_AGE)
                attr.set_value(line.data)
                state.event_ref.add_attribute(attr)

    def func_event_agnc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type(RelLib.AttributeType.AGENCY)
        attr.set_value(line.data)
        state.event.add_attribute(attr)

    def func_person_adopt_famc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        gid = self.fid_map[line.data]
        handle = self.find_family_handle(gid)
        family = self.find_or_create_family(gid)

        sub_state = GedcomUtils.CurrentState(level=state.level+1)
        sub_state.mrel = TYPE_BIRTH
        sub_state.frel = TYPE_BIRTH

        self.parse_level(sub_state, self.parse_person_adopt, 
                         self.func_undefined)

        if (int(sub_state.mrel) == RelLib.ChildRefType.BIRTH  and
            int(sub_state.frel) == RelLib.ChildRefType.BIRTH):
            sub_state.mrel = sub_state.frel = TYPE_ADOPT

        if state.person.get_main_parents_family_handle() == handle:
            state.person.set_main_parent_family_handle(None)
        state.person.add_parent_family_handle(handle)
        
        reflist = [ ref for ref in family.get_child_ref_list() \
                        if ref.ref == state.person.handle ]
        if reflist:
            ref = reflist[0]
            ref.set_father_relation(sub_state.frel)
            ref.set_mother_relation(sub_state.mrel)
        else:
            ref = RelLib.ChildRef()
            ref.ref = state.person.handle
            ref.set_father_relation(sub_state.frel)
            ref.set_mother_relation(sub_state.mrel)
            family.add_child_ref(ref)
            self.dbase.commit_family(family, self.trans)

    def func_person_adopt_famc_adopt(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data.strip() == "HUSB":
            state.frel = TYPE_ADOPT
        elif line.data.strip() == "WIFE":
            state.mrel = TYPE_ADOPT
        else:
            state.mrel = TYPE_ADOPT
            state.frel = TYPE_ADOPT

    def func_person_birth_famc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        handle = self.find_family_handle(line.data.strip()[1:-1])

        if state.person.get_main_parents_family_handle() == handle:
            state.person.set_main_parent_family_handle(None)
        state.person.add_parent_family_handle(handle)
        
        frel = mrel = RelLib.ChildRefType.BIRTH

        family = self.dbase.find_family_from_handle(handle, self.trans)
        reflist = [ ref for ref in family.get_child_ref_list() \
                        if ref.ref == state.person.handle ]
        if reflist:
            ref = reflist[0]
            ref.set_father_relation(frel)
            ref.set_mother_relation(mrel)
        else:
            ref = RelLib.ChildRef()
            ref.ref = state.person.handle
            ref.set_father_relation(frel)
            ref.set_mother_relation(mrel)
            family.add_child_ref(ref)
            self.dbase.commit_family(family, self.trans)

    def func_address_date(self, line, state):
        """
        Parses the DATE line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_date_object(line.data)

    def func_address_city(self, line, state):
        """
        Parses the CITY line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_city(line.data)

    def func_address_state(self, line, state):
        """
        Parses the STAE line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_state(line.data)

    def func_address_post(self, line, state):
        """
        Parses the POST line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_postal_code(line.data)
            
    def func_address_country(self, line, state):
        """
        Parses the country line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_country(line.data)
    
    def func_address_phone(self, line, state):
        """
        Parses the PHON line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.set_phone(line.data)
            
    def func_address_sour(self, line, state):
        """
        Parses the SOUR line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.addr.add_source_reference(self.handle_source(line, state.level+1))
            
    def func_address_note(self, line, state):
        """
        Parses the NOTE line of an ADDR tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.addr, state.level+1)

    def func_srcref_page(self, line, state):
        """
        Parses the PAGE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.src_ref.set_page(line.data)

    def func_srcref_date(self, line, state):
        """
        Parses the DATE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.src_ref.set_date_object(line.data)

    def func_srcref_data(self, line, state): 
        """
        Parses the DATA line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        date, text = self.parse_source_data(state.level+2)
        if date:
            state.src_ref.set_date_object(date)
        state.src_ref.set_text(text)

    def func_srcref_obje(self, line, state): 
        """
        Parses the OBJE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.not_recognized(state.level)
        else:
            src = self.dbase.get_source_from_handle(state.handle)
            (form, filename, title, note) = self.func_obje(state.level)
            self.build_media_object(src, form, filename, title, note)
            self.dbase.commit_source(src, self.trans)

    def func_srcref_refn(self, line, state): 
        """
        Parses the REFN line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(state.level+1)

    def func_srcref_quay(self, line, state): 
        """
        Parses the QUAY line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        try:
            val = int(line.data)
        except ValueError:
            return
        # If value is greater than 3, cap at 3
        val = min(val, 3)
        if val > 1:
            state.src_ref.set_confidence_level(val+1)
        else:
            state.src_ref.set_confidence_level(val)

    def func_srcref_note(self, line, state): 
        """
        Parses the NOTE line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.src_ref, state.level+1)

    def func_srcref_text(self, line, state): 
        """
        Parses the TEXT line of an SOUR instance tag

        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.src_ref.set_text(line.data)
        self.skip_subordinate_levels(state.level+1)

    def parse_source(self, name, level):
        """
          n @<XREF:SOUR>@ SOUR {1:1}
          +1 DATA {0:1}
          +2 EVEN <EVENTS_RECORDED> {0:M}
          +3 DATE <DATE_PERIOD> {0:1} 
          +3 PLAC <SOURCE_JURISDICTION_PLACE> {0:1}
          +2 AGNC <RESPONSIBLE_AGENCY> {0:1}
          +2 <<NOTE_STRUCTURE>> {0:M}
          +1 AUTH <SOURCE_ORIGINATOR> {0:1}
          +1 TITL <SOURCE_DESCRIPTIVE_TITLE> {0:1}
          +1 ABBR <SOURCE_FILED_BY_ENTRY> {0:1}
          +1 PUBL <SOURCE_PUBLICATION_FACTS> {0:1}
          +1 TEXT <TEXT_FROM_SOURCE> {0:1}
          +1 <<SOURCE_REPOSITORY_CITATION>> {0:1} 
          +1 <<MULTIMEDIA_LINK>> {0:M} 
          +1 <<NOTE_STRUCTURE>> {0:M}
          +1 REFN <USER_REFERENCE_NUMBER> {0:M}
          +2 TYPE <USER_REFERENCE_TYPE> {0:1}
          +1 RIN <AUTOMATED_RECORD_ID> {0:1}
          +1 <<CHANGE_DATE>> {0:1}
        """

        state = GedcomUtils.CurrentState()
        state.source = self.find_or_create_source(self.sid_map[name]) 
        state.source.set_title("No title - ID %s" % 
                               state.source.get_gramps_id())
        state.level = level

        self.parse_level(state, self.source_func, self.func_undefined)
        self.dbase.commit_source(state.source, self.trans)

    def func_source_attr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_data_item(line.token_text, line.data)

    def func_source_object(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            self.not_recognized(state.level)
        else:
            (form, filename, title, note) = self.func_obje(state.level+1)
            self.build_media_object(state.source, form, filename, title, note)

    def func_source_chan(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_change(line, state.source, state.level+1)

    def func_source_undef(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.not_recognized(state.level+1)

    def func_source_repo(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if line.data and line.data[0] == '@':
            gid = self.rid_map[line.data]
            repo = self.find_or_create_repository(gid)
        else:
            gid = self.repo2id.get(line.data)
            repo = self.find_or_create_repository(gid)
            self.repo2id[line.data] = repo.get_gramps_id()
            repo.set_name(line.data)
            self.dbase.commit_repository(repo, self.trans)
        repo_ref = RelLib.RepoRef()
        repo_ref.set_reference_handle(repo.handle)

        sub_state = GedcomUtils.CurrentState()
        sub_state.repo_ref = repo_ref
        sub_state.level = state.level + 1

        self.parse_level(sub_state, self.repo_ref_tbl, self.func_undefined)

        state.source.add_repo_reference(repo_ref)

    def func_repo_ref_call(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.repo_ref.set_call_number(line.data)
        self.skip_subordinate_levels(state.level+1)

    def func_repo_ref_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.repo_ref, state.level+1)

    def func_source_abbr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_abbreviation(line.data)

    def func_source_agnc(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        attr = RelLib.Attribute()
        attr.set_type(RelLib.AttributeType.AGENCY)
        attr.set_value(line.data)
        state.source.add_attribute(attr)

    def func_source_text(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.add_note(line.data)

    def func_source_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.source, state.level+1)

    def func_source_auth(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_author(line.data)

    def func_source_publ(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_publication_info(line.data)
        self.skip_subordinate_levels(state.level+1)

    def func_source_title(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.source.set_title(line.data.replace('\n',' '))

    def func_source_taxt_peri(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.source.get_title() == "":
            state.source.set_title(line.data.replace('\n',' '))

    def parse_obje(self, line):
        """
           n  @XREF:OBJE@ OBJE {1:1}
           +1 FORM <MULTIMEDIA_FORMAT> {1:1} p.*
           +1 TITL <DESCRIPTIVE_TITLE> {0:1} p.*
           +1 <<NOTE_STRUCTURE>> {0:M} p.*
           +1 BLOB {1:1}
           +2 CONT <ENCODED_MULTIMEDIA_LINE> {1:M} p.*
           +1 OBJE @<XREF:OBJE>@ /* chain to continued object */ {0:1} p.*
           +1 REFN <USER_REFERENCE_NUMBER> {0:M} p.*
           +2 TYPE <USER_REFERENCE_TYPE> {0:1} p.*
           +1 RIN <AUTOMATED_RECORD_ID> {0:1} p.*
           +1 <<CHANGE_DATE>> {0:1} p.*
        """
        gid = line.token_text.strip()
        media = self.find_or_create_object(self.oid_map[gid])

        state = GedcomUtils.CurrentState()
        state.media = media
        state.level = 1

        self.parse_level(state, self.obje_func, self.func_undefined)

        # Add the default reference if no source has found
        self.add_default_source(media)

        # commit the person to the database
        if media.change:
            self.dbase.commit_media_object(media, self.trans,
                                        change_time=media.change)
        else:
            self.dbase.commit_media_object(media, self.trans)

    def func_obje_form(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        # TODO: FIX THIS!!!
        state.media_form = line.data.strip()
        self.skip_subordinate_levels(state.level+1)

    def func_obje_file(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        (file_ok, filename) = self.find_file(line.data, self.dir_path)
        if media != URL:
            if not file_ok:
                self.warn(_("Could not import %s") % filename[0])
        path = filename[0].replace('\\', os.path.sep)
        state.media.set_path(path)
        state.media.set_mime_type(Mime.get_type(path))
        if not state.media.get_description():
            state.media.set_description(path)

    def func_obje_title(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.media.set_description(line.data)

    def func_obje_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.media, state.level+1)

    def func_obje_blob(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(state.level+1)

    def func_obje_refn(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(state.level+1)

    def func_obje_type(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(state.level+1)

    def func_obje_rin(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(state.level+1)

    def func_obje_chan(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.skip_subordinate_levels(state.level+1)

    def func_person_attr_type(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if state.attr.get_type() == "":
            if GED_2_GRAMPS.has_key(line.data):
                name = GED_2_GRAMPS[line.data]
            else:
                val = self.gedsource.tag2gramps(line.data)
                if val:
                    name = val
                else:
                    name = line.data
            state.attr.set_type(name)

    def func_person_attr_source(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.attr.add_source_reference(self.handle_source(line, state.level))

    def func_person_attr_place(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        val = line.data
        if state.attr.get_value() == "":
            state.attr.set_value(val)
        self.skip_subordinate_levels(state.level)

    def func_person_attr_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        self.parse_note(line, state.attr, state.level+1)

    #----------------------------------------------------------------------
    #
    # REPO parsing
    #
    #----------------------------------------------------------------------
    def parse_repo(self, line):
        """
        REPOSITORY_RECORD:=
          n @<XREF:REPO>@ REPO {1:1}
         +1 NAME <NAME_OF_REPOSITORY> {0:1} p.*
         +1 <<ADDRESS_STRUCTURE>> {0:1} p.*
         +1 <<NOTE_STRUCTURE>> {0:M} p.*
         +1 REFN <USER_REFERENCE_NUMBER> {0:M} p.*
         +1 RIN <AUTOMATED_RECORD_ID> {0:1} p.*
         +1 <<CHANGE_DATE>> {0:1} p.
        """
        repo = self.find_or_create_repository(line.token_text)
        self.added.add(repo.handle)

        state = GedcomUtils.CurrentState()
        state.repo = repo
        state.level = 1
        self.parse_level(state, self.repo_parse_tbl, self.func_ignore)

        self.dbase.commit_repository(repo, self.trans)

    def func_repo_name(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        state.repo.set_name(line.data)

    def func_repo_addr(self, line, state):
        """
        n ADDR <ADDRESS_LINE> {0:1} 
        +1 CONT <ADDRESS_LINE> {0:M}
        +1 ADR1 <ADDRESS_LINE1> {0:1}
        +1 ADR2 <ADDRESS_LINE2> {0:1}
        +1 CITY <ADDRESS_CITY> {0:1}
        +1 STAE <ADDRESS_STATE> {0:1}
        +1 POST <ADDRESS_POSTAL_CODE> {0:1}
        +1 CTRY <ADDRESS_COUNTRY> {0:1}
        n PHON <PHONE_NUMBER> {0:3}

        Some repositories do not try to break up the address,
        instead they put everything on a single line. Try to determine
        if this happened, and try to fix it.
        """

        addr = RelLib.Address()
        addr.set_street(line.data)

        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level+1
        sub_state.addr = addr

        self.parse_level(sub_state, self.parse_addr_tbl, self.func_ignore)

        text = addr.get_street()
        if not addr.get_city() and not addr.get_state() and \
           not addr.get_postal_code() and not addr.get_country():
        
            match = ADDR_RE.match(text)
            if match:
                groups = match.groups()
                addr.set_street(groups[0].strip())
                addr.set_city(groups[2].strip())
                addr.set_state(groups[3].strip())
                addr.set_postal_code(groups[4].strip())
                addr.set_country(groups[5].strip())
            
            match = ADDR2_RE.match(text)
            if match:
                groups = match.groups()
                addr.set_street(groups[0].strip())
                addr.set_city(groups[2].strip())
                addr.set_state(groups[3].strip())
                addr.set_postal_code(groups[4].strip())

            match = ADDR3_RE.match(text)
            if match:
                groups = match.groups()
                addr.set_street(groups[0].strip())
                addr.set_city(groups[2].strip())
                addr.set_state(groups[3].strip())

        state.repo.add_address(addr)

    def func_location_addr(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = RelLib.Location()
        val = state.location.get_street()
        if val:
            val = "%s, %s" % (val, line.data.strip())
        else:
            val = line.data.strip()
        state.location.set_street(val.replace('\n',' '))

    def func_location_date(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = RelLib.Location()
        state.location.set_date_object(line.data)

    def func_location_city(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = RelLib.Location()
        state.location.set_city(line.data)

    def func_location_stae(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = RelLib.Location()
        state.location.set_state(line.data)

    def func_location_post(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = RelLib.Location()
        state.location.set_postal_code(line.data)

    def func_location_ctry(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = RelLib.Location()
        state.location.set_country(line.data)

    def func_location_note(self, line, state):
        """
        @param line: The current line in GedLine format
        @type line: GedLine
        @param state: The current state
        @type state: CurrentState
        """
        if not state.location:
            state.location = RelLib.Location()
        self.parse_note(line, state.event, state.level+1)

    def map_ancestry_com(self, original_gid):
	"""
	GEDCOM files created by Ancestry.com for some reason do not include
	the FAMC and FAMS mappings in the INDI record. If we don't fix this,
	we end up with a bunch of broken family connections. The family 
	references the people, but the people do not reference the family.

	To resolve this, we use the mappings acquired from the first pass
	of the parsing. The StageOne parser will grab the mappins from the
	family to the child on the first pass, and we can use them here.

	We have to make sure we use the original person ID, since the StageOne
	parser does not remap colliding IDs.
	"""
	for fams_id in self.fams_map.get(original_gid,[]):
	    mapped_id = self.fid_map[fams_id]
	    fams_handle = self.find_family_handle(mapped_id)
	    self.person.add_family_handle(fams_handle)

	for famc_id in self.famc_map.get(original_gid,[]):
	    mapped_id = self.fid_map[famc_id]
	    famc_handle = self.find_family_handle(mapped_id)
	    self.person.add_parent_family_handle(famc_handle)

###############################################################################

    def parse_note(self, line, obj, level):
        # reference to a named note defined elsewhere
        if line.token == TOKEN_RNOTE:
            obj.add_note(line.data.strip())
        else:
            new_note = RelLib.Note(line.data)
            self.dbase.commit_note(new_note,self.trans)
            obj.add_note(new_note.handle)
            self.skip_subordinate_levels(level+1)

    def parse_comment(self, line, obj, level, old_note):
        return self.parse_note_base(line, obj, level, old_note, obj.add_note)

    def parse_optional_note(self, obj, level):
        note = ""
        while True:
            line = self.get_next()

            if self.level_is_finished(line, level):
                return note
            elif line.token == TOKEN_NOTE or line.token == TOKEN_RNOTE:
                self.parse_note(line, obj, level)
            else:
                self.not_recognized(level+1)
        return None

    def parse_source_reference(self, src_ref, level, handle):
        """Reads the data associated with a SOUR reference"""
        state = GedcomUtils.CurrentState()
        state.level = level
        state.src_ref = src_ref
        state.handle = handle
        self.parse_level(state, self.srcref_parse_tbl, self.func_ignore)

    def parse_source_data(self, level):
        """Parses the source data"""
        date = ""
        note = ""
        while True:
            line = self.get_next()
            if self.level_is_finished(line, level):
                break
            elif line.token == TOKEN_DATE:
                date = line.data
            elif line.token == TOKEN_TEXT:
                note = line.data
            elif line.token == TOKEN_NOTE:
                continue
            elif line.token == TOKEN_RNOTE:
                continue
            else:
                self.not_recognized(level+1)
        return (date, note)
    
    def parse_header_head(self):
        """validiates that this is a valid GEDCOM file"""
        line = self.lexer.readline()
        if line.token != TOKEN_HEAD:
            raise Errors.GedcomError("%s is not a GEDCOM file" % self.filename)

    def parse_header_source(self):
        genby = ""
        while True:
            line = self.get_next()
            if self.level_is_finished(line, 1):
                return
            elif line.token == TOKEN_SOUR:
                self.gedsource = self.gedmap.get_from_source_tag(line.data)
                self.lexer.set_broken_conc(self.gedsource.get_conc())
                if line.data == "FTW":
                    self.is_ftw = True
		if line.data == "Ancestry.com Family Trees":
		    self.is_ancestry_com = True
                genby = line.data
            elif line.token == TOKEN_NAME:
                pass
            elif line.token == TOKEN_VERS:
                if self.use_def_src:
                    self.def_src.set_data_item('Generated by',"%s %s" %
                                               (genby, line.data))
            elif line.token == TOKEN_FILE:
                if self.use_def_src:
                    filename = os.path.basename(line.data).split('\\')[-1]
                    self.def_src.set_title(_("Import from %s") % filename)
            elif line.token == TOKEN_COPR:
                if self.use_def_src:
                    self.def_src.set_publication_info(line.data)
            elif line.token ==  TOKEN_SUBM:
                self.parse_subm(2)
            elif line.token in (TOKEN_CORP, TOKEN_DATA, TOKEN_SUBN,
                                TOKEN_LANG, TOKEN_TIME):
                self.skip_subordinate_levels(2)
            elif line.token == TOKEN_DEST:
                if genby == "GRAMPS":
                    self.gedsource = self.gedmap.get_from_source_tag(line.data)
                    self.lexer.set_broken_conc(self.gedsource.get_conc())
            elif line.token == TOKEN_CHAR:
                pass
                self.skip_subordinate_levels(2)
            elif line.token == TOKEN_GEDC:
                self.skip_subordinate_levels(2)
            elif line.token == TOKEN__SCHEMA:
                self.parse_ftw_schema(2)
            elif line.token == TOKEN_PLAC:
                self.parse_place_form(2)
            elif line.token == TOKEN_DATE:
                self.parse_date(2)
                if self.use_def_src:
                    self.def_src.set_data_item('Creation date', line.data)
            elif line.token == TOKEN_NOTE:
                if self.use_def_src:
                    self.parse_note(line, self.def_src, 2, '')
            elif line.token == TOKEN_UNKNOWN:
                self.skip_subordinate_levels(2)
            else:
                self.not_recognized(2)

    def parse_subm(self, level):
        while True:
            line = self.get_next()

            if self.level_is_finished(line, level):
                break
            elif line.token == TOKEN_NAME:
                if self.use_def_src:
                    self.def_src.set_author(line.data)
            else:
                self.skip_subordinate_levels(2)

    def parse_ftw_schema(self, level):
        while True:
            line = self.get_next()

            if self.level_is_finished(line, level):
                break
            elif line.token == TOKEN_INDI:
                self.parse_ftw_indi_schema(level+1)
            elif line.token == TOKEN_FAM:
                self.parse_ftw_fam_schema(level+1)
            else:
                self.not_recognized(2)

    def parse_ftw_indi_schema(self, level):
        while True:
            line = self.get_next()

            if self.level_is_finished(line, level):
                break
            else:
                GED_2_GRAMPS[line.token] = self.parse_label(level+1)

    def parse_label(self, level):
        value = None
        
        while True:
            line = self.get_next()

            if self.level_is_finished(line, level):
                break
            elif line.token == TOKEN_LABL:
                value = line.data
            else:
                self.not_recognized(2)
        return value
    
    def parse_ftw_fam_schema(self, level):
        while True:
            line = self.get_next()

            if self.level_is_finished(line, level):
                break
            else:
                GED_2_FAMILY_CUSTOM[line.token_text] = self.parse_label(level+1)
    
    def skip_subordinate_levels(self, level):
        while True:
            line = self.get_next()
            if self.level_is_finished(line, level):
                return
    
    def ignore_change_data(self, level):
        line = self.get_next()
        if line.token == TOKEN_CHAN:
            self.skip_subordinate_levels(level+1)
        else:
            self.backup()

    def parse_place_form(self, level):
        while True:
            line = self.get_next()

            if self.level_is_finished(line, level):
                break
            elif line.token == TOKEN_FORM:
                self.place_parser.parse_form(line)
            else:
                self.not_recognized(level+1)

    def parse_date(self, level):
        while True:
            line = self.get_next()
            if self.level_is_finished(line, level):
                break
            elif line.token == TOKEN_TIME:
                pass
            else:
                self.not_recognized(level+1)

    def handle_source(self, line, level):
        source_ref = RelLib.SourceRef()
        if line.data and line.data[0] != "@":
            title = line.data
            handle = self.inline_srcs.get(title, Utils.create_id())
            src = RelLib.Source()
            src.handle = handle
            src.gramps_id = self.dbase.find_next_source_gramps_id()
            self.inline_srcs[title] = handle
        else:
            src = self.find_or_create_source(self.sid_map[line.data])
        self.dbase.commit_source(src, self.trans)
        self.parse_source_reference(source_ref, level, src.handle)
        source_ref.set_reference_handle(src.handle)
        return source_ref

    def resolve_refns(self):
        return
    
        prefix = self.dbase.iprefix
        index = 0
        new_pmax = self.dbase.pmap_index
        for pid in self.added:
            index += 1
            if self.refn.has_key(pid):
                val = self.refn[pid]
                new_key = prefix % val
                new_pmax = max(new_pmax, val)

                person = self.dbase.get_person_from_handle(pid, self.trans)

                # new ID is not used
                if not self.dbase.has_person_handle(new_key):
                    self.dbase.remove_person(pid, self.trans)
                    person.set_handle(new_key)
                    person.set_gramps_id(new_key)
                    self.dbase.add_person(person, self.trans)
                else:
                    temp = self.dbase.get_person_from_handle(new_key, self.trans)
                    # same person, just change it
                    if person == temp:
                        self.dbase.remove_person(pid, self.trans)
                        person.set_handle(new_key)
                        person.set_gramps_id(new_key)
                        self.dbase.add_person(person, self.trans)
                    # give up trying to use the refn as a key
                    else:
                        pass

        self.dbase.pmap_index = new_pmax

    #--------------------------------------------------------------------
    #
    #
    #
    #--------------------------------------------------------------------

    def parse_change(self, line, obj, level):
        """
        CHANGE_DATE:=

        >  n CHAN {1:1}
        >  +1 DATE <CHANGE_DATE> {1:1}
        >  +2 TIME <TIME_VALUE> {0:1}
        >  +1 <<NOTE_STRUCTURE>> {0:M}

        The Note structure is ignored, since we have nothing
        corresponding in GRAMPS.

        Based on the values calculated, attempt to convert to a valid
        change time using time.strptime. If this fails (and it shouldn't
        unless the value is meaningless and doesn't conform to the GEDCOM
        spec), the value is ignored.
        """
        tstr = None
        dstr = None
        
        while True:
            line = self.get_next()
            if self.level_is_finished(line, level):
                break
            elif line.token == TOKEN_TIME:
                tstr = line.data
            elif line.token == TOKEN_DATE:
                dstr = line.data
            elif line.token == TOKEN_NOTE:
                self.skip_subordinate_levels(level+1)
            else:
                self.not_recognized(level+1)

        # Attempt to convert the values to a valid change time
        if tstr:
            try:
                if dstr:
                    tstruct = time.strptime("%s %s" % (dstr, tstr),
                                            "%d %b %Y %H:%M:%S")
                else:
                    tstruct = time.strptime(tstr, "%d %b %Y")
                val = time.mktime(tstruct)
                obj.change = val
            except ValueError:
                # parse of time structure failed, so ignore
                pass
        
    def build_media_object(self, obj, form, filename, title, note):
        if form == "url":
            url = RelLib.Url()
            url.set_path(filename)
            url.set_description(title)
            obj.add_url(url)
        else:
            (valid, path) = self.find_file(filename, self.dir_path)
            if not valid:
                self.warn(_("Could not import %s") % filename)
                path = filename.replace('\\', os.path.sep)
            photo_handle = self.media_map.get(path)
            if photo_handle == None:
                photo = RelLib.MediaObject()
                photo.set_path(path)
                photo.set_description(title)
                full_path = os.path.abspath(path)
                if os.path.isfile(full_path):
                    photo.set_mime_type(Mime.get_type(full_path))
                else:
                    photo.set_mime_type(MIME_MAP.get(form.lower(),'unknown'))
                self.dbase.add_object(photo, self.trans)
                self.media_map[path] = photo.handle
            else:
                photo = self.dbase.get_object_from_handle(photo_handle)
            oref = RelLib.MediaRef()
            oref.set_reference_handle(photo.handle)
            oref.add_note(note)
            obj.add_media_reference(oref)

    def _build_event_pair(self, state, event_type, event_map, description):
        """
        n TYPE <EVENT_DESCRIPTOR> {0:1} p.*
        n DATE <DATE_VALUE> {0:1} p.*/*
        n <<PLACE_STRUCTURE>> {0:1} p.*
        n <<ADDRESS_STRUCTURE>> {0:1} p.*
        n AGE <AGE_AT_EVENT> {0:1} p.*
        n AGNC <RESPONSIBLE_AGENCY> {0:1} p.*
        n CAUS <CAUSE_OF_EVENT> {0:1} p.*
        n <<SOURCE_CITATION>> {0:M} p.*
        n <<MULTIMEDIA_LINK>> {0:M} p.*,*
        n <<NOTE_STRUCTURE>> {0:M} p.
        """
        event = RelLib.Event()
        event_ref = RelLib.EventRef()
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(event_type)
        if description and description != 'Y':
            event.set_description(description)

        sub_state = GedcomUtils.CurrentState()
        sub_state.level = state.level + 1
        sub_state.event_ref = event_ref
        sub_state.event = event
        sub_state.person = state.person

        self.parse_level(sub_state, event_map, self.func_undefined)
        self.dbase.add_event(event, self.trans)

        event_ref.set_reference_handle(event.handle)
        return event_ref

    def _build_family_event_pair(self, state, event_type, event_map, 
                                 description):
        event = RelLib.Event()
        event_ref = RelLib.EventRef()
        event.set_gramps_id(self.emapper.find_next())
        event.set_type(event_type)
        if description and description != 'Y':
            event.set_description(description)

        sub_state = GedcomUtils.CurrentState()
        sub_state.family = state.family
        sub_state.level = state.level+1
        sub_state.event = event
        sub_state.event_ref = event_ref

        self.parse_level(sub_state, event_map, self.func_undefined)

        family_event_name(event, state.family)
        self.dbase.add_event(event, self.trans)

        event_ref.set_reference_handle(event.handle)
        return event_ref

    def extract_temple(self, line):
        def get_code(code):
            if LdsUtils.temple_to_abrev.has_key(code):
                return code
            elif LdsUtils.temple_codes.has_key(code):
                return LdsUtils.temple_codes[code]
        
        code = get_code(line.data)
        if code: 
            return code
        
        ## Not sure why we do this. Kind of ugly.
        code = get_code(line.data.split()[0])
        if code: 
            return code

        ## Okay we have no clue which temple this is.
        ## We should tell the user and store it anyway.
        self.warn("Invalid temple code '%s'" % (line.data,))
        return line.data

    def add_default_source(self, obj):
        if self.use_def_src and len(obj.get_source_references()) == 0:
            sref = RelLib.SourceRef()
            sref.set_reference_handle(self.def_src.handle)
            obj.add_source_reference(sref)

def person_event_name(event, person):
    if event.get_type().is_custom():
        if not event.get_description():
            text = EVENT_PERSON_STR % {
                'event_name' : str(event.get_type()),
                'person' : NameDisplay.displayer.display(person),
                }
            event.set_description(text)

def family_event_name(event, family):
    if event.get_type().is_custom():
        if not event.get_description():
            text = EVENT_FAMILY_STR % {
                'event_name' : str(event.get_type()),
                'family' : "<TBD>",
                }
            event.set_description(text)

