#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2013  Benny Malengier
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

"""
This module parses the evidence csv file and generates the code we need in
Gramps to use the evidence style.
"""

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
import csv


#-------------------------------------------------------------------------
#
# Code
#
#-------------------------------------------------------------------------
csvfilename = "evidence_style.csv"
NRCOL = 0
CATCOL = 1
CATTYPECOL = 2
TYPECOL = 3
DESCRCOL= 4
CITETYPECOL = 5
IDENTCOL = 6
LDELCOL = 7  # left delimiter
FIELDCOL = 8
RDELCOL = 9 # right delimiter
STYLECOL = 10
PRIVACYCOL = 11
OPTCOL = 12

nr = -1
cat = ''
cattype = ''
type = ''
descr = ''
cite_type = ''
ident = ''

TYPE2CITEMAP = {}
FIELDTYPEMAP = {}
index = 100
indexval = 10
first = True

with open(csvfilename, 'rb') as csvfile:
   reader = csv.reader(csvfile, delimiter=',')
   for row in reader:
        if first:
            #skip first row with headers
            first=False
            continue

        if row[CATCOL]:
            cat = row[CATCOL].strip()
            cattype = row[CATTYPECOL].strip()
            types = row[TYPECOL].strip()
            descr = row[DESCRCOL].strip()
            source_type = row[IDENTCOL].strip()
            if descr:
                source_descr = '%s - %s - %s (%s)' % (cat, cattype, types, descr)
                source_descr_code = "_('%(first)s - %(sec)s - %(third)s (%(fourth)s)') % { "\
                        " 'first': _('" + cat + "'),"\
                        " 'sec': _('" + cattype + "'),"\
                        " 'third': _('" + types + "'),"\
                        " 'fourth': _('" + descr + "')}"
            else:
                source_descr = '%s - %s - %s' % (cat, cattype, types)
                source_descr_code = "_('%(first)s - %(sec)s - %(third)s') % { "\
                        " 'first': _('" + cat + "'),"\
                        " 'sec': _('" + cattype + "'),"\
                        " 'third': _('" + types + "')}"
            if source_type in TYPE2CITEMAP:
                assert TYPE2CITEMAP[source_type] ['descr'] == source_descr, source_type + ' ' + TYPE2CITEMAP[source_type] ['descr'] + ' NOT ' + source_descr
            else:
                TYPE2CITEMAP[source_type] = {'L': [], 'F': [], 'S': [], 
                            'i': indexval, 'descr': source_descr,
                            'descrcode': source_descr_code}
                indexval += 1
            
            
        if row[CITETYPECOL]:
            #new citation type, 
            cite_type = row[CITETYPECOL].strip()
        #add field for template to evidence style
        field = row[FIELDCOL].strip()
        field_type = field.replace(' ', '_').replace("'","")\
                     .replace('&','AND').replace('(', '6').replace(')','9')\
                     .replace('[', '').replace(']','').replace('/', '_OR_')\
                     .replace(',', '').replace('.', '').replace(':', '')\
                     .replace('-', '_')
        field_descr =  field.replace('[', '').replace(']','').lower().capitalize()
        if field_type in FIELDTYPEMAP:
            assert field_descr == FIELDTYPEMAP[field_type][1], 'Problem %s %s %s' % (field_type, field_descr, FIELDTYPEMAP[field_type][1])
        else:
            FIELDTYPEMAP[field_type] = (index, field_descr)
            index += 1
        fielddata = []
        private = 'False'
        if  row[PRIVACYCOL].strip():
            private = 'True'
        optional = 'False'
        if  row[OPTCOL].strip():
            optional = 'True'
        TYPE2CITEMAP[source_type][cite_type] += [(row[LDELCOL], field_type, 
                        row[RDELCOL], row[STYLECOL], private, optional)]

#now generate the python code we need in source attr types
code = "    #following fields are generated with evidencefieldgenerator.py\n" \
       "    #the index starts at 100!\n"
datamap = "\n    _DATAMAP += [\n"
allkeys = sorted(FIELDTYPEMAP.keys())
for field_type in allkeys:
    code += "    " + field_type + ' = %d\n' % FIELDTYPEMAP[field_type][0]
    datamap += '        (' + field_type + ', _("' + FIELDTYPEMAP[field_type][1] \
            +'"), "' + FIELDTYPEMAP[field_type][1] + '"),\n'

code += '\n' + datamap + '        ]\n'

with open('srcattrtype_extra.py', 'wb') as srcattrfile:
    srcattrfile.write(code)

#now generate the python code we need in evidencestyle
# we have predefined sourcetypes, and these have a template for formatting
# 

#first an English to internationalized map
code = "    #SRCTEMPLATE has some predefined values which map to citation styles\n"

datamap = "    _SRCTEMPLATEVAL_MAP = [\n"
allkeys = sorted(TYPE2CITEMAP.keys())
for source_type in allkeys:
    code += "    " + source_type + ' = %d\n' % TYPE2CITEMAP[source_type]['i']
    # we use descrcode in to translate string to reduce work for translators
    datamap += '        (' + source_type + ', ' + TYPE2CITEMAP[source_type]['descrcode'] \
            +', "' + TYPE2CITEMAP[source_type]['descr'] + '"),\n'

code += '\n    # Localization of the different source types\n'\
            + datamap + '        ]\n'

code += "\n    #templates for the source types defined\n"\
        "    # F: Full reference\n"\
        "    # S: Short reference (if F used once, use S afterwards)\n" \
        "    # L: List reference (for in bibliography list)\n"
code += '    EVIDENCETEMPLATES = {\n'
for source_type in allkeys:
    code += "        " + source_type + ": {\n"
    for val in ['F', 'L', 'S']:
        code += "            '" + val + "': [\n"
        for field in TYPE2CITEMAP[source_type][val]:
            # field is tuple (row[LDELCOL], field_type, row[RDELCOL], row[STYLECOL]
            #    , private, optional)
            code += "                ('"+ field[0] + "', " + field[1]  + ", '" + field[2] + \
                    "', '" + field[3] + "', " + field[4] + ", " + field[5] + "),\n"
        code += "                ],\n"
    code += "        },\n"
code += "    }\n"

with open('srcattrtype_extraevidence.py', 'wb') as srcattrfile:
    srcattrfile.write(code)