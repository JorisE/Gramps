#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003  Donald N. Allingham
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

#
# Written by Alex Roitman, largely based on Relationship.py by Don Allingham.
#

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------

import RelLib
import GrampsCfg

#-------------------------------------------------------------------------
#
# Russian-specific definitions of relationships
#
#-------------------------------------------------------------------------

_male_cousin_level = [ 
  "", "двоюродный", "троюродный", "четвероюродный",
  "пятиюродный", "шестиюродный", "семиюродный", "восьмиюродный",
  "девятиюродный", "десятиюродный", "одиннацатиюродный", "двенадцатиюродный", 
  "тринадцатиюродный", "четырнадцатиюродный", "пятнадцатиюродный", "шестнадцатиюродный", 
  "семнадцатиюродный", "восемнадцатиюродный", "девятнадцатиюродный","двадцатиюродный" ]

_female_cousin_level = [ 
  "", "двоюродная", "троюродная", "четвероюродная",
  "пятиюродная", "шестиюродная", "семиюродная", "восьмиюродная",
  "девятиюродная", "десятиюродная", "одиннацатиюродная", "двенадцатиюродная", 
  "тринадцатиюродная", "четырнадцатиюродная", "пятнадцатиюродная", "шестнадцатиюродная", 
  "семнадцатиюродная", "восемнадцатиюродная", "девятнадцатиюродная","двадцатиюродная" ]

_junior_male_removed_level = [ 
  "брат", "племянник", "внучатый племянник", "правнучатый племянник", 
  "праправнучатый племянник", "прапраправнучатый племянник", 
  "прапрапраправнучатый племянник" ]

_junior_female_removed_level = [ 
  "сестра", "племянница", "внучатая племянница", "правнучатая племянница", 
  "праправнучатая племянница", "прапраправнучатая племянница", 
  "прапрапраправнучатая племянница" ]

_senior_male_removed_level = [ 
  "", "дядя", "дед", "прадед", "прапрадед", "прапрапрадед","прапрапрапрадед" ]

_senior_female_removed_level = [ 
  "", "тетка", "бабка", "прабабка", "прапрабабка", "прапрапрабабка","прапрапрапрабабка" ]

_father_level = [ 
  "", "отец", "дед", "прадед", "прапрадед", "прапрапрадед", "прапрапрапрадед" ]

_mother_level = [ 
   "", "мать", "бабка", "прабабка", "прапрабабка", "прапрапрабабка", "прапрапрапрабабка" ]

_son_level = [ 
  "", "сын", "внук", "правнук", "праправнук", "прапраправнук", "прапрапраправнук" ]

_daughter_level = [ 
  "", "дочь", "внучка", "правнучка", "праправнучка", "прапраправнучка",
  "прапрапраправнучка" ]

_sister_level = [ 
  "", "сестра", "тетка", "двоюродная бабка", "двоюродная прабабка", 
  "двоюродная прапрабабка", "двоюродная прапрапрабабка", "двоюродная прапрапрапрабабка" ]

_brother_level = [ 
  "", "брат", "дядя", "двоюродный дед", "двоюродный прадед", 
  "двоюродный прапрадед", "двоюродный прапрапрадед", "двоюродный прапрапрапрадед" ]

_nephew_level = [ 
  "", "племянник", "внучатый племянник", "правнучатый племянник", 
  "праправнучатый племянник", "прапраправнучатый племянник", 
  "прапрапраправнучатый племянник" ]

_niece_level = [ 
  "", "племянница", "внучатая племянница", "правнучатая племянница", 
  "праправнучатая племянница", "прапраправнучатая племянница", 
  "прапрапраправнучатая племянница" ]

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def getallancestors(person,index,ancestorlist,ancestormap):
    if person == None:
        return
    ancestorlist.append(person)
    ancestormap[person.getId()] = index
    
    family = person.getMainParents()
    if family != None:
        getallancestors(family.getFather(),index+1,ancestorlist,ancestormap)
        getallancestors(family.getMother(),index+1,ancestorlist,ancestormap)

def get_junior_male_cousin(level,removed):
    if removed > len(_junior_male_removed_level)-1 or level>len(_male_cousin_level)-1:
        return "дальний родственник"
    else:
        return "%s %s" % (_male_cousin_level[level],_junior_male_removed_level[removed])

def get_senior_male_cousin(level,removed):
    if removed > len(_senior_male_removed_level)-1 or level>len(_male_cousin_level)-1:
        return "дальний родственник"
    else:
        return "%s %s" % (_male_cousin_level[level],_senior_male_removed_level[removed])

def get_junior_female_cousin(level,removed):
    if removed > len(_junior_female_removed_level)-1 or level>len(_male_cousin_level)-1:
        return "дальняя родственница"
    else:
        return "%s %s" % (_female_cousin_level[level],_junior_female_removed_level[removed])

def get_senior_female_cousin(level,removed):
    if removed > len(_senior_female_removed_level)-1 or level>len(_male_cousin_level)-1:
        return "дальняя родственница"
    else:
        return "%s %s" % (_female_cousin_level[level],_senior_female_removed_level[removed])

def get_father(level):
    if level>len(_father_level)-1:
        return "дальний предок"
    else:
        return _father_level[level]

def get_son(level):
    if level>len(_son_level)-1:
        return "дальний потомок"
    else:
        return _son_level[level]

def get_mother(level):
    if level>len(_mother_level)-1:
        return "дальний предок"
    else:
        return _mother_level[level]

def get_daughter(level):
    if level>len(_daughter_level)-1:
        return "дальний потомок"
    else:
        return _daughter_level[level]

def get_aunt(level):
    if level>len(_sister_level)-1:
        return "дальний предок"
    else:
        return _sister_level[level]

def get_uncle(level):
    if level>len(_brother_level)-1:
        return "дальний предок"
    else:
        return _brother_level[level]

def get_nephew(level):
    if level>len(_nephew_level)-1:
        return "дальний потомок"
    else:
        return _nephew_level[level]

def get_niece(level):
    if level>len(_niece_level)-1:
        return "дальний потомок"
    else:
        return _niece_level[level]

def is_spouse(orig,other):
    for f in orig.getFamilyList():
        if other == f.getFather() or other == f.getMother():
            return 1
    return 0

def get_relationship(orig_person,other_person):
    """
    Returns a string representing the relationshp between the two people,
    along with a list of common ancestors (typically father,mother) 
    
    Special cases: relation strings "", "undefined" and "spouse".
    """

    firstMap = {}
    firstList = []
    secondMap = {}
    secondList = []
    common = []
    rank = 9999999
    
    if orig_person == None:
        return ("undefined",[])
    
    firstName = orig_person.getPrimaryName().getRegularName()
    secondName = other_person.getPrimaryName().getRegularName()
    
    if orig_person == other_person:
        return ('', [])
    if is_spouse(orig_person,other_person):
        return ("spouse",[])

    getallancestors(orig_person,0,firstList,firstMap)
    getallancestors(other_person,0,secondList,secondMap)
    
    for person in firstList:
        if person in secondList:
            new_rank = firstMap[person.getId()]
            if new_rank < rank:
                rank = new_rank
                common = [ person ]
            elif new_rank == rank:
                common.append(person)

    firstRel = -1
    secondRel = -1

    length = len(common)
    
    if length == 1:
        person = common[0]
        secondRel = firstMap[person.getId()]
        firstRel = secondMap[person.getId()]
    elif length == 2:
        p1 = common[0]
        secondRel = firstMap[p1.getId()]
        firstRel = secondMap[p1.getId()]
    elif length > 2:
        person = common[0]
        secondRel = firstMap[person.getId()]
        firstRel = secondMap[person.getId()]
    
    if firstRel == -1:
        return ("",[])
    elif firstRel == 0:
        if secondRel == 0:
            return ('',common)
        elif other_person.getGender() == RelLib.Person.male:
            return (get_father(secondRel),common)
        else:
            return (get_mother(secondRel),common)
    elif secondRel == 0:
        if other_person.getGender() == RelLib.Person.male:
            return (get_son(firstRel),common)
        else:
            return (get_daughter(firstRel),common)
    elif firstRel == 1:
        if other_person.getGender() == RelLib.Person.male:
            return (get_uncle(secondRel),common)
        else:
            return (get_aunt(secondRel),common)
    elif secondRel == 1:
        if other_person.getGender() == RelLib.Person.male:
            return (get_nephew(firstRel-1),common)
        else:
            return (get_niece(firstRel-1),common)
    elif secondRel > firstRel:
        if other_person.getGender() == RelLib.Person.male:
            return (get_senior_male_cousin(firstRel-1,secondRel-firstRel),common)
        else:
            return (get_senior_female_cousin(firstRel-1,secondRel-firstRel),common)
    else:
        if other_person.getGender() == RelLib.Person.male:
            return (get_junior_male_cousin(secondRel-1,firstRel-secondRel),common)
        else:
            return (get_junior_female_cousin(secondRel-1,firstRel-secondRel),common)
    

#-------------------------------------------------------------------------
#
# Register this function with the Plugins system 
#
#-------------------------------------------------------------------------
from Plugins import register_relcalc

register_relcalc(get_relationship,
    ["ru","RU","ru_RU","koi8r","ru_koi8r","russian","Russian","ru_RU.koi8r"])
