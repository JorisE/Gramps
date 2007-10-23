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

# $Id$

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------

import gen.lib
import types
from TransUtils import sgettext as _

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------

_level_name = [ "", "first", "second", "third", "fourth", "fifth", "sixth",
                "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
                "thirteenth", "fourteenth", "fifteenth", "sixteenth",
                "seventeenth", "eighteenth", "nineteenth", "twentieth" ]

_removed_level = [ "", " once removed", " twice removed", 
                   " three times removed",
                   " four times removed", " five times removed", 
                    " six times removed",
                   " sevent times removed", " eight times removed", 
                   " nine times removed",
                   " ten times removed", " eleven times removed", 
                   " twelve times removed",
                   " thirteen times removed", " fourteen times removed", 
                   " fifteen times removed",
                   " sixteen times removed", " seventeen times removed", 
                   " eighteen times removed",
                   " nineteen times removed", " twenty times removed" ]

_parents_level = [ "", "parents", "grandparents", "great grandparents", "second great grandparents",
                  "third great grandparents",  "fourth great grandparents",
                  "fifth great grandparents",  "sixth great grandparents",
                  "seventh great grandparents", "eighth great grandparents",
                  "ninth great grandparents", "tenth great grandparents",
                  "eleventh great grandparents",  "twelfth great grandparents",
                  "thirteenth great grandparents", "fourteenth great grandparents",
                  "fifteenth great grandparents", "sixteenth great grandparents",
                  "seventeenth great grandparents", "eighteenth great grandparents",
                  "nineteenth great grandparents", "twentieth great grandparents", ]

_father_level = [ "", "father", "grandfather", "great grandfather", "second great grandfather",
                  "third great grandfather",  "fourth great grandfather",
                  "fifth great grandfather",  "sixth great grandfather",
                  "seventh great grandfather", "eighth great grandfather",
                  "ninth great grandfather", "tenth great grandfather",
                  "eleventh great grandfather",  "twelfth great grandfather",
                  "thirteenth great grandfather", "fourteenth great grandfather",
                  "fifteenth great grandfather", "sixteenth great grandfather",
                  "seventeenth great grandfather", "eighteenth great grandfather",
                  "nineteenth great grandfather", "twentieth great grandfather", ]

_mother_level = [ "", "mother", "grandmother", "great grandmother", "second great grandmother",
                  "third great grandmother",  "fourth great grandmother",
                  "fifth great grandmother",  "sixth great grandmother",
                  "seventh great grandmother", "eighth great grandmother",
                  "ninth great grandmother", "tenth great grandmother",
                  "eleventh great grandmother",  "twelfth great grandmother",
                  "thirteenth great grandmother", "fourteenth great grandmother",
                  "fifteenth great grandmother", "sixteenth great grandmother",
                  "seventeenth great grandmother", "eighteenth great grandmother",
                  "nineteenth great grandmother", "twentieth great grandmother", ]

_son_level = [ "", "son", "grandson", "great grandson", "second great grandson",
               "third great grandson",  "fourth great grandson",
               "fifth great grandson",  "sixth great grandson",
               "seventh great grandson", "eighth great grandson",
               "ninth great grandson", "tenth great grandson",
               "eleventh great grandson",  "twelfth great grandson",
               "thirteenth great grandson", "fourteenth great grandson",
               "fifteenth great grandson", "sixteenth great grandson",
               "seventeenth great grandson", "eighteenth great grandson",
               "nineteenth great grandson", "twentieth great grandson", ]

_daughter_level = [ "", "daughter", "granddaughter", "great granddaughter",
                    "second great granddaughter",
                    "third great granddaughter",  "fourth great granddaughter",
                    "fifth great granddaughter",  "sixth great granddaughter",
                    "seventh great granddaughter", "eighth great granddaughter",
                    "ninth great granddaughter", "tenth great granddaughter",
                    "eleventh great granddaughter",  "twelfth great granddaughter",
                    "thirteenth great granddaughter", "fourteenth great granddaughter",
                    "fifteenth great granddaughter", "sixteenth great granddaughter",
                    "seventeenth great granddaughter", "eighteenth great granddaughter",
                    "nineteenth great granddaughter", "twentieth great granddaughter", ]

_sister_level = [ "", "sister", "aunt", "grandaunt", "great grandaunt", "second great grandaunt",
                  "third great grandaunt",  "fourth great grandaunt",
                  "fifth great grandaunt",  "sixth great grandaunt",
                  "seventh great grandaunt", "eighth great grandaunt",
                  "ninth great grandaunt", "tenth great grandaunt",
                  "eleventh great grandaunt",  "twelfth great grandaunt",
                  "thirteenth great grandaunt", "fourteenth great grandaunt",
                  "fifteenth great grandaunt", "sixteenth great grandaunt",
                  "seventeenth great grandaunt", "eighteenth great grandaunt",
                  "nineteenth great grandaunt", "twentieth great grandaunt", ]

_brother_level = [ "", "brother", "uncle", "granduncle", "great granduncle", "second great granduncle",
                   "third great granduncle",  "fourth great granduncle",
                   "fifth great granduncle",  "sixth great granduncle",
                   "seventh great granduncle", "eighth great granduncle",
                   "ninth great granduncle", "tenth great granduncle",
                   "eleventh great granduncle",  "twelfth great granduncle",
                   "thirteenth great granduncle", "fourteenth great granduncle",
                   "fifteenth great granduncle", "sixteenth great granduncle",
                   "seventeenth great granduncle", "eighteenth great granduncle",
                   "nineteenth great granduncle", "twentieth great granduncle", ]

_nephew_level = [ "", "nephew", "grandnephew", "great grandnephew", "second great grandnephew",
                  "third great grandnephew",  "fourth great grandnephew",
                  "fifth great grandnephew",  "sixth great grandnephew",
                  "seventh great grandnephew", "eighth great grandnephew",
                  "ninth great grandnephew", "tenth great grandnephew",
                  "eleventh great grandnephew",  "twelfth great grandnephew",
                  "thirteenth great grandnephew", "fourteenth great grandnephew",
                  "fifteenth great grandnephew", "sixteenth great grandnephew",
                  "seventeenth great grandnephew", "eighteenth great grandnephew",
                  "nineteenth great grandnephew", "twentieth great grandnephew", ]

_niece_level = [ "", "niece", "grandniece", "great grandniece", "second great grandniece",
                 "third great grandniece",  "fourth great grandniece",
                 "fifth great grandniece",  "sixth great grandniece",
                 "seventh great grandniece", "eighth great grandniece",
                 "ninth great grandniece", "tenth great grandniece",
                 "eleventh great grandniece",  "twelfth great grandniece",
                 "thirteenth great grandniece", "fourteenth great grandniece",
                 "fifteenth great grandniece", "sixteenth great grandniece",
                 "seventeenth great grandniece", "eighteenth great grandniece",
                 "nineteenth great grandniece", "twentieth great grandniece", ]

_children_level = [ "",
    "children",                        "grandchildren", 
    "great grandchildren",             "second great grandchildren",
    "third great grandchildren",       "fourth great grandchildren",
    "fifth great grandchildren",       "sixth great grandchildren",
    "seventh great grandchildren",     "eighth great grandchildren",
    "ninth great grandchildren",       "tenth great grandchildren",
    "eleventh great grandchildren",    "twelfth great grandchildren",
    "thirteenth great grandchildren",  "fourteenth great grandchildren",
    "fifteenth great grandchildren",   "sixteenth great grandchildren",
    "seventeenth great grandchildren", "eighteenth great grandchildren",
     "nineteenth great grandchildren", "twentieth great grandchildren", ]

_siblings_level = [ "",
    "siblings",                           "uncles/aunts", 
    "granduncles/aunts",                  "great granduncles/aunts", 
    "second great granduncles/aunts",     "third great granduncles/aunts",  
    "fourth great granduncles/aunts",     "fifth great granduncles/aunts",  
    "sixth great granduncles/aunts",      "seventh great granduncles/aunts", 
    "eighth great granduncles/aunts",     "ninth great granduncles/aunts", 
    "tenth great granduncles/aunts",      "eleventh great granduncles/aunts",  
    "twelfth great granduncles/aunts",    "thirteenth great granduncles/aunts", 
    "fourteenth great granduncles/aunts", "fifteenth great granduncles/aunts", 
    "sixteenth great granduncles/aunts",  "seventeenth great granduncles/aunts", 
    "eighteenth great granduncles/aunts", "nineteenth great granduncles/aunts", 
    "twentieth great granduncles/aunts", ]
    
_sibling_level = [ "",
    "sibling",                          "uncle/aunt", 
    "granduncle/aunt",                  "great granduncle/aunt", 
    "second great granduncle/aunt",     "third great granduncle/aunt",  
    "fourth great granduncle/aunt",     "fifth great granduncle/aunt",  
    "sixth great granduncle/aunt",      "seventh great granduncle/aunt", 
    "eighth great granduncle/aunt",     "ninth great granduncle/aunt", 
    "tenth great granduncle/aunt",      "eleventh great granduncle/aunt",  
    "twelfth great granduncle/aunt",    "thirteenth great granduncle/aunt", 
    "fourteenth great granduncle/aunt", "fifteenth great granduncle/aunt", 
    "sixteenth great granduncle/aunt",  "seventeenth great granduncle/aunt", 
    "eighteenth great granduncle/aunt", "nineteenth great granduncle/aunt", 
    "twentieth great granduncle/aunt", ]

_nephews_nieces_level = [   "", 
                            "siblings",
                            "nephews/nieces",
                            "grandnephews/nieces", 
                            "great grandnephews/nieces",
                            "second great grandnephews/nieces",
                            "third great grandnephews/nieces",
                            "fourth great grandnephews/nieces",
                            "fifth great grandnephews/nieces",
                            "sixth great grandnephews/nieces",
                            "seventh great grandnephews/nieces",
                            "eighth great grandnephews/nieces",
                            "ninth great grandnephews/nieces",
                            "tenth great grandnephews/nieces",
                            "eleventh great grandnephews/nieces",
                            "twelfth great grandnephews/nieces",
                            "thirteenth great grandnephews/nieces",
                            "fourteenth great grandnephews/nieces",
                            "fifteenth great grandnephews/nieces",
                            "sixteenth great grandnephews/nieces",
                            "seventeenth great grandnephews/nieces",
                            "eighteenth great grandnephews/nieces",
                            "nineteenth great grandnephews/nieces",
                            "twentieth great grandnephews/nieces",    ]


#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------

MAX_DEPTH = 15

class RelationshipCalculator:
    
    REL_MOTHER           = 'm'
    REL_FATHER           = 'f'
    REL_MOTHER_NOTBIRTH  = 'M'
    REL_FATHER_NOTBIRTH  = 'F'
    REL_SIBLING          = 's'

    def __init__(self):
        pass

    def get_cousin(self, level, removed):
        if removed > len(_removed_level)-1 or level>len(_level_name)-1:
            return "distant relative"
        else:
            return "%s cousin%s" % (_level_name[level], 
                                    _removed_level[removed])

    def get_parents(self, level):
        if level>len(_parents_level)-1:
            return "distant ancestors"
        else:
            return _parents_level[level]

    def get_father(self, level):
        if level>len(_father_level)-1:
            return "distant ancestor"
        else:
            return _father_level[level]

    def get_son(self, level):
        if level>len(_son_level)-1:
            return "distant descendant"
        else:
            return _son_level[level]

    def get_mother(self, level):
        if level>len(_mother_level)-1:
            return "distant ancestor"
        else:
            return _mother_level[level]

    def get_daughter(self, level):
        if level>len(_daughter_level)-1:
            return "distant descendant"
        else:
            return _daughter_level[level]

    def get_aunt(self, level):
        if level>len(_sister_level)-1:
            return "distant ancestor"
        else:
            return _sister_level[level]

    def get_uncle(self, level):
        if level>len(_brother_level)-1:
            return "distant ancestor"
        else:
            return _brother_level[level]

    def get_nephew(self, level):
        if level>len(_nephew_level)-1:
            return "distant descendant"
        else:
            return _nephew_level[level]

    def get_niece(self, level):
        if level>len(_niece_level)-1:
            return "distant descendant"
        else:
            return _niece_level[level]
        
    def is_spouse(self, db, orig, other):
        for f in orig.get_family_handle_list():
            family = db.get_family_from_handle(f)
            if family and other.get_handle() in [family.get_father_handle(),
                                                 family.get_mother_handle()]:
                family_rel = family.get_relationship()
                # Determine person's gender
                if other.get_gender() == gen.lib.Person.MALE:
                    gender = gen.lib.Person.MALE
                elif other.get_gender() == gen.lib.Person.FEMALE:
                    gender = gen.lib.Person.FEMALE
                # Person's gender is unknown, try guessing from spouse's
                elif orig.get_gender() == gen.lib.Person.MALE:
                    if family_rel == gen.lib.FamilyRelType.CIVIL_UNION:
                        gender = gen.lib.Person.MALE
                    else:
                        gender = gen.lib.Person.FEMALE
                elif orig.get_gender() == gen.lib.Person.FEMALE:
                    if family_rel == gen.lib.FamilyRelType.CIVIL_UNION:
                        gender = gen.lib.Person.FEMALE
                    else:
                        gender = gen.lib.Person.MALE
                else:
                    gender = gen.lib.Person.UNKNOWN

                if family_rel == gen.lib.FamilyRelType.MARRIED:
                    if gender == gen.lib.Person.MALE:
                        return _("husband")
                    elif gender == gen.lib.Person.FEMALE:
                        return _("wife")
                    else:
                        return _("gender unknown|spouse")
                elif family_rel == gen.lib.FamilyRelType.UNMARRIED:
                    if gender == gen.lib.Person.MALE:
                        return _("unmarried|husband")
                    elif gender == gen.lib.Person.FEMALE:
                        return _("unmarried|wife")
                    else:
                        return _("gender unknown,unmarried|spouse")
                elif family_rel == gen.lib.FamilyRelType.CIVIL_UNION:
                    if gender == gen.lib.Person.MALE:
                        return _("male,civil union|partner")
                    elif gender == gen.lib.Person.FEMALE:
                        return _("female,civil union|partner")
                    else:
                        return _("gender unknown,civil union|partner")
                else:
                    if gender == gen.lib.Person.MALE:
                        return _("male,unknown relation|partner")
                    elif gender == gen.lib.Person.FEMALE:
                        return _("female,unknown relation|partner")
                    else:
                        return _("gender unknown,unknown relation|partner")
            else:
                return None
        return None

    def get_relationship_distance_old(self, db, orig_person, other_person):
        """
           ** DEPRECATED  -- USE NEW **
        
        NOTE: CHANGED ORDER OF RETURN, now first is rel to orig, second to other
                (as it should, but wasn't !! )

        Returns a tuple (firstRel, secondRel, common):
        
        firstRel    Number of generations from the orig_person to their
                    closest common ancestors, as eg 'ffmm'
        secondRel   Number of generations from the other_person to that
                    firstRel closest common ancestors, as eg 'ffmm'
        common      list of all these common ancestors (so same generation
                    difference with firstRel), no specific order !!
                    
        in the Rel, f is father, m is mother
        """
        print "get_relationship_distance_old is deprecated, use new instead!"
        
        firstRel = -1
        secondRel = -1
        common = []

        firstMap = {}
        firstList = []
        secondMap = {}
        secondList = []
        rank = 9999999

        try:
            self.__apply_filter(db, orig_person, '', firstList, firstMap)
            self.__apply_filter(db, other_person, '', secondList, secondMap)
        except RuntimeError:
            return (firstRel, secondRel, _("Relationship loop detected"))

        for person_handle in firstList:
            if person_handle in secondList:
                new_rank = len(firstMap[person_handle])
                if new_rank < rank:
                    rank = new_rank
                    common = [ person_handle ]
                elif new_rank == rank:
                    common.append(person_handle)

        if common:
            person_handle = common[0]
            firstRel = firstMap[person_handle]
            secondRel = secondMap[person_handle]

        return (firstRel,secondRel,common)

    def __apply_filter(self, db, person, rel_str, plist, pmap, depth=1):
        if person == None or depth > MAX_DEPTH:
            return
        depth += 1
        plist.append(person.handle)
        pmap[person.handle] = rel_str  # ?? this overwrites if person is double!

        family_handle = person.get_main_parents_family_handle()
        try:
            if family_handle:
                family = db.get_family_from_handle(family_handle)
                fhandle = family.father_handle
                if fhandle:
                    father = db.get_person_from_handle(fhandle)
                    self.__apply_filter(db, father, rel_str+'f', plist, pmap,
                                        depth)
                mhandle = family.mother_handle
                if mhandle:
                    mother = db.get_person_from_handle(mhandle)
                    self.__apply_filter(db, mother, rel_str+'m', plist, pmap,
                                        depth)
        except:
            return
        
    def get_relationship_distance(self, db, orig_person, other_person):
        """
        wrapper around get_relationship_distance_new to return a value like
        the old method (note, firstRel is now to orig person, not to other as
            it was in 2.2.x series !!!)
            
            *** DO NOT USE, IS INCORRECT IN SOME CASES, eg person common 
                ancestor along two paths, only one returned,
                however this should not matter for number of generation or 
                last gender, eg firstRel is 'ffffm' or 'mmfmm', only one 
                returned ***
        
        Returns a tuple (firstRel, secondRel, common):
        
        firstRel    Number of generations from the orig_person to their
                    closest common ancestors, as eg 'ffmm'
        secondRel   Number of generations from the other_person to that 
                    firstRel closest common ancestors, as eg 'ffmm'
        common      list of all these common ancestors (so same generation
                    difference with firstRel), no specific order !!
                    
        in the Rel, f is father, m is mother
        """
        
        firstRel = -1
        secondRel = -1
        common = []
        rank = 9999999
        
        data, msg = self.get_relationship_distance_new(
                                db, orig_person, other_person,
                                all_dist=True,
                                all_families=False, only_birth=True)
        #data is sorted on rank, we need closest to orig instead
        if data[0][0] == -1 :
            return firstRel, secondRel, common
        for common_anc in data :
            # common_anc looks like:
            #(total dist, handle_common, 'ffffff', [0,0,0,0,0,0],'ff',[0, 0])
            #where 2&3 are related to orig_pers, 4&5 other_pers
            new_rank = len(common_anc[2])
            if new_rank < rank:
                    rank = new_rank
                    common = [ common_anc[1] ]
                    firstRel = common_anc[2]
                    secondRel = common_anc[4]
            elif new_rank == rank:
                common.append( common_anc[1] )
            
        return (firstRel, secondRel, common)
        

    def get_relationship_distance_new(self, db, orig_person,
                                      other_person,
                                      all_families=False, 
                                      all_dist=False, 
                                      only_birth=True,
                                      max_depth = MAX_DEPTH):
        """
        Returns if all_dist == First a 'tuple, string':
            (rank, person handle, firstRel_str, firstRel_fam,
             secondRel_str, secondRel_fam), msg 
        or if all_dist == True a 'list of tuple, string': 
            [.....], msg:
        
        The tuple or list of tuples consists of:
         
        *rank           Total number of generations from common ancestor to 
                        the two persons, rank is -1 if no relations found
        *person_handle  The Common ancestor
        *firstRel_str   String with the path to the common ancestor 
                        from orig Person
        *firstRel_fam   Family numbers along the path
        *secondRel_str  String with the path to the common ancestor 
                        from otherPerson
        *secondRel_fam  Family numbers along the path
        *msg            List of messages indicating errors. Empyt list if no
                        errors.
                        
        Example:
                firstRel_str = 'ffm' and firstRel_fam = [2,0,1] means 
                common ancestor is mother of the second family of the 
                father of the first family of the father of the third 
                family.
        Note that the same person might be present twice if the person is
        reached via a different branch too. Path (firstRel_str and 
        secondRel_str) will of course be different
        
        @param db: database to work on
        @param orig_person: first person 
        @type orig_person:  Person Obj
        @param other_person: second person, relation is sought between
                             first and second person
        @type other_person:  Person Obj
        @param all_families: if False only Main family is searched, otherwise
                             all families are used
        @type all_families:  bool
        @param all_dist: if False only the shortest distance is returned, 
                         otherwise all relationships
        @type all_dist:  bool
        @param only_birth: if True only parents with birth relation are 
                           considered
        @type only_birth:  bool
        @param max_depth: how many generations deep do we search?
        @type max_depth: int
        """
        #data storage to communicate with recursive functions
        self.__maxDepthReached = False
        self.__loopDetected = False
        self.__max_depth = max_depth
        self.__all_families = all_families
        self.__all_dist = all_dist
        self.__only_birth = only_birth
        
        firstRel   = -1
        secondRel  = -1
        common_str = []
        common_fam = []
        self.__msg = []
        
        common = []
        firstMap = {}
        firstList = []
        secondMap = {}
        secondList = []
        rank = 9999999

        try:
            self.__apply_filter_new(db, orig_person, '', [], firstMap)
            self.__apply_filter_new(db, other_person, '', [], secondMap,
                                    stoprecursemap = firstMap, 
                                    store_all=False)
##            print firstMap
##            print secondMap
        except RuntimeError:
            return (-1,None,-1,[],-1,[] ) , \
                            [_("Relationship loop detected")] + self.__msg

        for person_handle in secondMap.keys() :
            if firstMap.has_key(person_handle) :
                com = []
                #a common ancestor
                for rel1,fam1 in zip(firstMap[person_handle][0],
                                        firstMap[person_handle][1]):
                    l1 = len(rel1)
                    for rel2,fam2 in zip(secondMap[person_handle][0], 
                                        secondMap[person_handle][1]):
                        l2 = len(rel2)
                        #collect paths to arrive at common ancestor
                        com.append((l1+l2,person_handle,rel1,fam1,
                                                        rel2,fam2))
                #insert common ancestor in correct position,
                #  if shorter links, check if not subset
                #  if longer links, check if not superset
                pos=0
                for ranknew,handlenew,rel1new,fam1new,rel2new,fam2new in com :
                    insert = True
                    for rank, handle, rel1, fam1, rel2, fam2 in common :
                        if ranknew < rank : 
                            break
                        elif ranknew >= rank :
                            #check subset
                            if rel1 == rel1new[:len(rel1)] and \
                                    rel2 == rel2new[:len(rel2)] :
                                #subset relation exists already
                                insert = False
                                break
                        pos += 1
                    if insert :
                        if common :
                            common.insert(pos, (ranknew, handlenew,
                                    rel1new, fam1new,rel2new,fam2new))
                        else:
                            common = [(ranknew, handlenew,
                                    rel1new, fam1new, rel2new, fam2new)]
                        #now check if superset must be deleted from common
                        deletelist=[]
                        index = pos+1
                        for rank,handle,rel1,fam1,rel2,fam2 in common[pos+1:]:
                            if rel1new == rel1[:len(rel1new)] and \
                                    rel2new == rel2[:len(rel2new)] :
                                deletelist.append(index)
                                index += 1
                        deletelist.reverse()
                        for index in deletelist:
                            del common[index]  
        #check for extra messages
        if self.__maxDepthReached :
            self.__msg += [_('Family tree reaches back more than the maximum '
                        '%d generations searched.\nIt is possible that '
                        'relationships have been missed') % (max_depth)]
        
##        print 'common list :', common

        if common and not self.__all_dist :
            rank          = common[0][0]
            person_handle = common[0][1]
            firstRel      = common[0][2]
            firstFam      = common[0][3]
            secondRel     = common[0][4]
            secondFam     = common[0][5]
            return (rank,person_handle,firstRel,firstFam,secondRel,secondFam),\
                        self.__msg
        if common : 
            #list with tuples (rank,handle person,rel_str_orig,rel_fam_orig,
            #       rel_str_other,rel_fam_str) and messages
            return common, self.__msg
        if not self.__all_dist :
            return  (-1,None,'',[],'',[]), self.__msg
        else :
            return [(-1,None,'',[],'',[])], self.__msg
    
    def __apply_filter_new(self, db, person, rel_str, rel_fam, pmap,
                            depth=1, stoprecursemap=None, store_all=True):
        '''We recursively add parents of person in pmap with correct rel_str, 
            if store_all. If store_all false, only store parents if in the
            stoprecursemap.
            Stop recursion if parent is in the stoprecursemap (no need to 
            look parents of otherpers if done so already for origpers)
            store pers
        '''
        if person == None or not person.handle :
            return
        if depth > self.__max_depth:
            self.__maxDepthReached = True
            print 'Max depth reached for ', person.get_primary_name(), depth,\
                        rel_str
            return
        depth += 1
        
        commonancestor = False
        if stoprecursemap and stoprecursemap.has_key(person.handle) :
            commonancestor = True

        #add person to the map, take into account that person can be obtained 
        #from different sides 
        if pmap.has_key(person.handle) :
            #person is already a grandparent in another branch, we already have
            # had lookup of all parents
            pmap[person.handle][0] += [rel_str]
            pmap[person.handle][1] += [rel_fam]
            #check if there is no loop father son of his son, ...
            # loop means person is twice reached, same rel_str in begin
            for rel1 in pmap[person.handle][0]: 
                for rel2 in pmap[person.handle][0] :
                    if len(rel1) < len(rel2) and \
                            rel1 == rel2[:len(rel1)]:
                        #loop, keep one message in storage!
                        self.__loopDetected = True
                        self.__msg += [_("Relationship loop detected:") + \
                            _("Person %s connects to himself via %s") % \
                                (person.get_primary_name().get_name(),
                                 rel2[len(rel1):])]
                        return
        elif store_all or commonancestor:
            pmap[person.handle] = [[rel_str],[rel_fam]]
            
        #having added person to the pmap, we only look up recursively to 
        # parents if this person is not common relative
        if commonancestor :
##            print 'common ancestor found'
            return 

        family_handles = []
        main = person.get_main_parents_family_handle()
##        print 'main',main
        if main :
            family_handles = [main]
        if self.__all_families :
            family_handles = person.get_parent_family_handle_list()    
##            print 'all_families', family_handles
            
        try:
            parentsdone = [] #avoid doing same parent twice in diff families
            fam = 0
##            print 'starting family loop over family_handles', family_handles
            for family_handle in family_handles :
                rel_fam_new = rel_fam +[fam]
                family = db.get_family_from_handle(family_handle)
                #obtain childref for this person
                childrel = [(ref.get_mother_relation(), 
                             ref.get_father_relation()) for ref in 
                                family.get_child_ref_list() 
                                if ref.ref == person.handle]
                fhandle = family.father_handle
##                print 'fhandle', fhandle, parentsdone
                if fhandle and not fhandle in parentsdone:
                    father = db.get_person_from_handle(fhandle)
                    if childrel[0][1] == gen.lib.ChildRefType.BIRTH :
                        addstr = self.REL_FATHER
                    elif not self.only_birth :
                        addstr = self.REL_FATHER_NOTBIRTH
                    else :
                        addstr = ''
##                    print 'for father, add string is =',addstr
                    if addstr :
                        parentsdone.append(fhandle)
                        self.__apply_filter_new(db, father,
                                rel_str + addstr, rel_fam_new,
                                pmap, depth, stoprecursemap, store_all)
                mhandle = family.mother_handle
                if mhandle and not mhandle in parentsdone:
                    mother = db.get_person_from_handle(mhandle)
                    if childrel[0][0] == gen.lib.ChildRefType.BIRTH :
                        addstr = self.REL_MOTHER
                    elif not self.only_birth :
                        addstr = self.REL_MOTHER_NOTBIRTH
                    else :
                        addstr = ''
##                    print 'for mother, add string is =',addstr
                    if addstr:
                        parentsdone.append(mhandle)
                        self.__apply_filter_new(db, mother,
                                rel_str + addstr, rel_fam_new,
                                pmap, depth, stoprecursemap, store_all)
                if not fhandle and not mhandle :
                    #family without parents, add brothers
                    child_list = [ref.ref for ref in family.get_child_ref_list()
                          if ref.ref != person.handle]
                    addstr = self.REL_SIBLING
                    if pmap.has_key(person.handle) :
                        pmap[person.handle][0] += [rel_str + addstr]
                        pmap[person.handle][1] += [rel_fam_new]
                        #person is already a grandparent in another branch
                    elif store_all or commonancestor:
                        pmap[person.handle] = [[rel_str+addstr],[rel_fam_new]]
                fam += 1
        except:
            import traceback
            print traceback.print_exc()
            return
           
    def get_relationship(self,db,orig_person,other_person):
        """
        returns a string representing the relationshp between the two people,
        along with a list of common ancestors (typically father,mother) 
        """

        if orig_person == None:
            return (_("undefined"),[])

        if orig_person.get_handle() == other_person.get_handle():
            return ('', [])

        is_spouse = self.is_spouse(db,orig_person,other_person)

        (firstRel,secondRel,common) = \
                self.get_relationship_distance(db,orig_person,other_person)
        
        if type(common) == types.StringType or \
           type(common) == types.UnicodeType:
            if is_spouse:
                return (is_spouse,[])
            else:
                return (common,[])
        elif common:
            person_handle = common[0]
        else:
            if is_spouse:
                return (is_spouse,[])
            else:
                return ("",[])

        #distance from common ancestor to the people
        dist_orig = len(firstRel)
        dist_other= len(secondRel)
        rel_str = self.get_single_relationship_string(dist_orig,
                                                      dist_other,
                                                      orig_person.get_gender(),
                                                      other_person.get_gender()
                                                     )
        if is_spouse:
            return (_('%(spouse_relation)s and %(other_relation)s') % {
                        'spouse_relation': is_spouse, 
                        'other_relation': rel_str} , common )
        else:
            return (rel_str, common)
##        #original programmer did a sick joke here, switching first with other!
##        firstRel = dist_other
##        secondRel = dist_orig
##
##        if firstRel == 0:        #other is common ancestor, so a father/mother
##            if secondRel == 0:
##                return ('',common)
##            elif other_person.get_gender() == gen.lib.Person.MALE:
##                return (self.get_father(secondRel),common)
##            else:
##                return (self.get_mother(secondRel),common)
##        elif secondRel == 0:    #orig is common ancestor, so other is son/daugh
##            if other_person.get_gender() == gen.lib.Person.MALE:
##                return (self.get_son(firstRel),common)
##            else:
##                return (self.get_daughter(firstRel),common)
##        elif firstRel == 1:
##            if other_person.get_gender() == gen.lib.Person.MALE:
##                return (self.get_uncle(secondRel),common)
##            else:
##                return (self.get_aunt(secondRel),common)
##        elif secondRel == 1:
##            if other_person.get_gender() == gen.lib.Person.MALE:
##                return (self.get_nephew(firstRel-1),common)
##            else:
##                return (self.get_niece(firstRel-1),common)
##        else:
##            if secondRel > firstRel:
##                return (self.get_cousin(firstRel-1,secondRel-firstRel),common)
##            else:
##                return (self.get_cousin(secondRel-1,firstRel-secondRel),common)


    def get_grandparents_string(self,db,orig_person,other_person):
        """
        returns a string representing the relationshp between the two people,
        along with a list of common ancestors (typically father,mother) 
        """
        if orig_person == None:
            return ("undefined",[])

        if orig_person == other_person:
            return ('', [])
        
        (firstRel,secondRel,common) = \
                     self.get_relationship_distance(db,orig_person,other_person)
        
        if type(common) == types.StringType or \
           type(common) == types.UnicodeType:
            return (common,[])
        elif common:
            person_handle = common[0]
        else:
            return ("",[])

        if len(firstRel) == 0:
            if len(secondRel) == 0:
                return ('',common)
            else:
                return (self.get_parents(len(secondRel)),common)
        else:
            return None
        
    def get_plural_relationship_string(self, Ga, Gb):
        """
        Provides a string that describes the relationsip between a person, and
        a group of people with the same relationship. E.g. "grandparents" or
        "children".
        
        Ga and Gb can be used to mathematically calculate the relationship.
        See the Wikipedia entry for more information:
            http://en.wikipedia.org/wiki/Cousin#Mathematical_definitions
        
        @param Ga: The number of generations between the main person and the 
        common ancestor.
        @type Ga: int
        @param Gb: The number of generations between the group of people and the
        common ancestor
        @type Gb: int
        @returns: A string describing the relationship between the person and
        the group.
        @rtype: str
        """
        rel_str = "distant relatives"
        if Ga == 0:
            # These are descendants
            if Gb < len(_children_level):
                rel_str = _children_level[Gb]
            else:
                rel_str = "distant descendants"
        elif Gb == 0:
            # These are parents/grand parents
            if Ga < len(_parents_level):
                rel_str = _parents_level[Ga]
            else:
                rel_str = "distant ancestors"
        elif Gb == 1:
            # These are siblings/aunts/uncles
            if Ga < len(_siblings_level):
                rel_str = _siblings_level[Ga]
            else:
                rel_str = "distant uncles/aunts"
        elif Ga == 1:
            # These are nieces/nephews
            if Gb < len(_nephews_nieces_level):
                rel_str = _nephews_nieces_level[Gb]
            else:
                rel_str = "distant nephews/nieces"
        elif Ga > 1 and Ga == Gb:
            # These are cousins in the same generation
            if Ga <= len(_level_name):
                rel_str = "%s cousins" % _level_name[Ga-1]
            else:
                rel_str = "distant cousins"
        elif Ga > 1 and Ga > Gb:
            # These are cousins in different generations with the second person 
            # being in a higher generation from the common ancestor than the 
            # first person.
            if Gb <= len(_level_name) and (Ga-Gb) < len(_removed_level):
                rel_str = "%s cousins%s (up)" % ( _level_name[Gb-1], 
                                                  _removed_level[Ga-Gb] )
            else:
                rel_str =  "distant cousins"
        elif Gb > 1 and Gb > Ga:
            # These are cousins in different generations with the second person 
            # being in a lower generation from the common ancestor than the 
            # first person.
            if Ga <= len(_level_name) and (Gb-Ga) < len(_removed_level):
                rel_str = "%s cousins%s (down)" % ( _level_name[Ga-1], 
                                                    _removed_level[Gb-Ga] )
            else:
                rel_str =  "distant cousins"
        return rel_str
    
    def get_single_relationship_string(self, Ga, Gb, gender_a, gender_b,
                                       only_birth=True):
        """
        Provides a string that describes the relationsip between a person, and
        another person. E.g. "grandparent" or "child".
        To be used as: 'person a is the grandparent of b', this will 
            be in translation string :
                            'person a is the %(relation)s of b'
            Note that languages with gender should add 'the' inside the 
            translation, so eg in french:
                            'person a est %(relation)s de b'
            where relation will be here: le grandparent
        
        Ga and Gb can be used to mathematically calculate the relationship.
        See the Wikipedia entry for more information:
            http://en.wikipedia.org/wiki/Cousin#Mathematical_definitions
            
        @param Ga: The number of generations between the main person and the 
                   common ancestor.
        @type Ga: int
        @param Gb: The number of generations between the other person and the
                   common ancestor
        @type Gb: int
        @param gender_a : gender of person a
        @type gender_a: int gender
        @param gender_b : gender of person b
        @type gender_b: int gender
        @param only_birth : True if relation between a and b is by birth only
                            False otherwise
        @type only_birth: bool
        @returns: A string describing the relationship between the two people
        @rtype: str
        """
##        print 'Ga, Gb :', Ga, Gb
        rel_str = "distant relatives"
        if Ga == 0:
            # b is descendant of a
            if Gb == 0 :
                rel_str = 'same person'
            elif gender_b == gen.lib.Person.MALE and Gb < len(_son_level):
                rel_str = _son_level[Gb]
            elif gender_b == gen.lib.Person.FEMALE and Gb < len(_daughter_level):
                rel_str = _daughter_level[Gb]
            elif Gb < len(_level_name):
                rel_str = _level_name[Gb] + ' ' + 'descendant'
            else:
                rel_str = "distant descendant (%d generations)" % Gb
        elif Gb == 0:
            # b is parents/grand parent of a
            if gender_b == gen.lib.Person.MALE and Ga < len(_father_level):
                rel_str = _father_level[Ga]
            elif gender_b == gen.lib.Person.FEMALE and Gb < len(_mother_level):
                rel_str = _mother_level[Ga]
            elif Ga < len(_level_name):
                rel_str = _level_name[Ga] + ' ' + 'ancestor'
            else:
                rel_str = "distant ancestor (%d generations)" % Ga
        elif Gb == 1:
            # b is sibling/aunt/uncle of a
            if gender_b == gen.lib.Person.MALE and Ga < len(_brother_level):
                rel_str = _brother_level[Ga]
            elif gender_b == gen.lib.Person.FEMALE and Ga < len(_sister_level):
                rel_str = _sister_level[Ga]
            elif Ga < len(_sibling_level):
                rel_str = _sibling_level[Ga]
            else:
                rel_str = "distant uncle/aunt"
        elif Ga == 1:
            # b is niece/nephew of a
            if gender_b == gen.lib.Person.MALE and Gb < len(_nephew_level):
                rel_str = _nephew_level[Gb]
            elif gender_b == gen.lib.Person.FEMALE and Gb < len(_niece_level):
                rel_str = _niece_level[Gb]
            elif Gb < len(_niece_level) and Gb < len(_nephew_level):
                rel_str = "%s or %s" %(_nephew_level[Gb], _niece_level[Gb])
            else:
                rel_str = "distant nephews/nieces"
        elif Ga > 1 and Ga == Gb:
            # a and b cousins in the same generation
            if Ga <= len(_level_name):
                rel_str = "%s cousin" % _level_name[Ga-1]
            else:
                rel_str = "distant cousin"
        elif Ga > 1 and Ga > Gb:
            # These are cousins in different generations with the second person 
            # being in a higher generation from the common ancestor than the 
            # first person.
            if Gb <= len(_level_name) and (Ga-Gb) < len(_removed_level):
                rel_str = "%s cousin%s (up)" % ( _level_name[Gb-1], 
                                                  _removed_level[Ga-Gb] )
            else:
                rel_str =  "distant cousin"
        elif Gb > 1 and Gb > Ga:
            # These are cousins in different generations with the second person 
            # being in a lower generation from the common ancestor than the 
            # first person.
            if Ga <= len(_level_name) and (Gb-Ga) < len(_removed_level):
                rel_str = "%s cousin%s (down)" % ( _level_name[Ga-1], 
                                                    _removed_level[Gb-Ga] )
            else:
                rel_str =  "distant cousin"
        return rel_str
