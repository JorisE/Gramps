#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2004  Donald N. Allingham
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

"""Generic Filtering Routines"""

__author__ = "Don Allingham"

#-------------------------------------------------------------------------
#
# Try to abstract SAX1 from SAX2
#
#-------------------------------------------------------------------------
from xml.sax import make_parser,handler,SAXParseException

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
import os
import string
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import const
import RelLib
import Date
import Calendar
from TransTable import TransTable
from gettext import gettext as _
from Utils import for_each_ancestor

#-------------------------------------------------------------------------
#
# date_cmp
#
#-------------------------------------------------------------------------
def date_cmp(rule,value):
    sd = rule.get_start_date()
    s = sd.mode
    if s == Calendar.BEFORE:
        return Date.compare_dates(rule,value) == 1
    elif s == Calendar.AFTER:
        return Date.compare_dates(rule,value) == -1
    elif sd.month == Date.UNDEF and sd.year != Date.UNDEF:
        return sd.year == value.get_start_date().year
    else:
        return Date.compare_dates(rule,value) == 0

#-------------------------------------------------------------------------
#
# Rule
#
#-------------------------------------------------------------------------
class Rule:
    """Base rule class"""

    labels = []
    
    def __init__(self,list):
        self.set_list(list)

    def set_list(self,list):
        assert type(list) == type([]) or list == None, "Argument is not a list"
        self.list = list

    def values(self):
        return self.list

    def trans_name(self):
        return _(self.name())
    
    def name(self): 
        return 'None'

    def category(self): 
        return _('Miscellaneous filters')
    
    def description(self):
        return _('No description')

    def check(self):
        return len(self.list) == len(self.labels)

    def apply(self,db,p):
        return 1

    def display_values(self):
        v = []
        for i in range(0,len(self.list)):
            if self.list[i]:
                v.append('%s="%s"' % (_(self.labels[i]),_(self.list[i])))
        return string.join(v,'; ')

#-------------------------------------------------------------------------
#
# Everyone
#
#-------------------------------------------------------------------------
class Everyone(Rule):
    """Matches Everyone"""

    labels = []
    
    def name(self):
        return 'Everyone'

    def category(self): 
        return _('General filters')
    
    def description(self):
        return _('Matches everyone in the database')

    def apply(self,db,p_id):
        return 1

#-------------------------------------------------------------------------
#
# RelationshipPathBetween
#
#-------------------------------------------------------------------------
class RelationshipPathBetween(Rule):
    """Rule that checks for a person that is a descendant of a specified person
    not more than N generations away"""

    labels = [ _('ID:'), _('ID:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}

    def name(self):
        return "Relationship path between two people"

    def category(self): 
        return _('Relationship filters')

    def description(self):
        return _("Matches the ancestors of two people back to a common ancestor, producing "
                 "the relationship path between two people.")

    def desc_list(self, p_id, map, first):
        if not first:
            map[p_id] = 1
        
        p = self.db.find_person_from_id(p_id)
        for fam_id in p.get_family_id_list():
            if fam_id:
                fam = self.db.find_family_from_id(fam_id)
                for child_id in fam.get_child_id_list():
                    if child_id:
                        self.desc_list(child_id,map,0)
    
    def apply_filter(self,rank,person,plist,pmap):
        if person == None:
            return
        plist.append(person)
        pmap[person.get_id()] = rank
        
        family = person.get_main_parents_family_id()
        if family != None:
            self.apply_filter(rank+1,family.get_father_id(),plist,pmap)
            self.apply_filter(rank+1,family.get_mother_id(),plist,pmap)

    def apply(self,db,p_id):
        self.db = db
        if not self.init:
            self.init = 1
            root1 = self.list[0]
            root2 = self.list[1]
            self.init_list(root1,root2)
        return self.map.has_key(p_id)

    def init_list(self,p1_id,p2_id):

        firstMap = {}
        firstList = []
        secondMap = {}
        secondList = []
        common = []
        rank = 9999999

        self.apply_filter(0,p1_id,firstList,firstMap)
        self.apply_filter(0,p2_id,secondList,secondMap)
        
        for person_id in firstList:
            if person_id in secondList:
                new_rank = firstMap[person_id]
                if new_rank < rank:
                    rank = new_rank
                    common = [ person_id ]
                elif new_rank == rank:
                    common.append(person_id)

        path1 = { p1_id : 1}
        path2 = { p2_id : 1}

        for person_id in common:
            new_map = {}
            self.desc_list(person_id,new_map,1)
            self.get_intersection(path1,firstMap,new_map)
            self.get_intersection(path2,secondMap,new_map)

        for e in path1:
            self.map[e] = 1
        for e in path2:
            self.map[e] = 1
        for e in common:
            self.map[e] = 1

    def get_intersection(self,target, map1, map2):
        for e in map1.keys():
            if map2.has_key(e):
                target[e] = map2[e]
        
#-------------------------------------------------------------------------
#
# HasIdOf
#
#-------------------------------------------------------------------------
class HasIdOf(Rule):
    """Rule that checks for a person with a specific GRAMPS ID"""

    labels = [ _('ID:') ]
    
    def name(self):
        return 'Has the Id'

    def description(self):
        return _("Matches the person with a specified GRAMPS ID")

    def category(self):
        return _('General filters')

    def apply(self,db,p_id):
        return p_id == self.list[0]

#-------------------------------------------------------------------------
#
# HasCompleteRecord
#
#-------------------------------------------------------------------------
class HasCompleteRecord(Rule):
    """Rule that checks for a person whose record is complete"""

    labels = []
    
    def name(self):
        return 'Has complete record'

    def category(self): 
        return _('General filters')
    
    def description(self):
        return _('Matches all people whose records are complete')

    def apply(self,db,p_id):
        return db.find_person_from_id(p_id).get_complete() == 1

#-------------------------------------------------------------------------
#
# IsFemale
#
#-------------------------------------------------------------------------
class IsFemale(Rule):
    """Rule that checks for a person that is a female"""

    labels = []
    
    def name(self):
        return 'Is a female'

    def category(self): 
        return _('General filters')
    
    def description(self):
        return _('Matches all females')

    def apply(self,db,p_id):
        return db.find_person_from_id(p_id).get_gender() == RelLib.Person.female

#-------------------------------------------------------------------------
#
# IsDescendantOf
#
#-------------------------------------------------------------------------
class IsDescendantOf(Rule):
    """Rule that checks for a person that is a descendant
    of a specified person"""

    labels = [ _('ID:'), _('Inclusive:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}

    def name(self):
        return 'Is a descendant of'

    def category(self): 
        return _('Descendant filters')
    
    def description(self):
        return _('Matches all descendants for the specified person')

    def apply(self,db,p_id):
        self.orig_id = p_id
        self.db = db
        try:
            if int(self.list[1]):
                first = 0
            else:
                first = 1
        except IndexError:
            first = 1

        if not self.init:
            self.init = 1
            root_id = self.list[0]
            self.init_list(root_id,first)
        return self.map.has_key(p_id)

    def init_list(self,p_id,first):
        if not first:
            self.map[p_id] = 1
        
        p = self.db.find_person_from_id(p_id)
        for fam_id in p.get_family_id_list():
            if fam_id:
                fam = self.db.find_family_from_id(fam_id)
                for child_id in fam.get_child_id_list():
                    self.init_list(child_id,0)

#-------------------------------------------------------------------------
#
# IsDescendantOfFilterMatch
#
#-------------------------------------------------------------------------
class IsDescendantOfFilterMatch(IsDescendantOf):
    """Rule that checks for a person that is a descendant
    of someone matched by a filter"""

    labels = [ _('Filter name:'), _('Inclusive:') ]

    def __init__(self,list):
        IsDescendantOf.__init__(self,list)

    def name(self):
        return 'Is a descendant of filter match'

    def category(self): 
        return _('Descendant filters')

    def description(self):
        return _("Matches people that are descendants of someone matched by a filter")
    
    def apply(self,db,p_id):
        self.orig_id = p_id
        self.db = db
        try:
            if int(self.list[1]):
                first = 0
            else:
                first = 1
        except IndexError:
            first = 1

        if not self.init:
            self.init = 1
            filter = MatchesFilter(self.list)
            for person_id in db.get_person_keys():
                if filter.apply (db, person_id):
                    self.init_list (person_id, first)
        return self.map.has_key(p_id)

#-------------------------------------------------------------------------
#
# IsLessThanNthGenerationDescendantOf
#
#-------------------------------------------------------------------------
class IsLessThanNthGenerationDescendantOf(Rule):
    """Rule that checks for a person that is a descendant of a specified person
    not more than N generations away"""

    labels = [ _('ID:'), _('Number of generations:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}

    def name(self):
        return 'Is a descendant of person not more than N generations away'

    def category(self): 
        return _('Descendant filters')

    def description(self):
        return _("Matches people that are descendants of a specified person "
                 "not more than N generations away")
    
    def apply(self,db,p_id):
        self.orig_id = p_id
        self.db = db

        if not self.init:
            self.init = 1
            root_id = self.list[0]
            self.init_list(root_id,0)
        return self.map.has_key(p_id)

    def init_list(self,p_id,gen):
        if gen:
            self.map[p_id] = 1
            if gen >= int(self.list[1]):
                return

        p = self.db.find_person_from_id(p_id)
        for fam_id in p.get_family_id_list():
            fam = self.db.find_family_from_id(fam_id)
            for child_id in fam.get_child_id_list():
                self.init_list(child_id,gen+1)

#-------------------------------------------------------------------------
#
# IsMoreThanNthGenerationDescendantOf
#
#-------------------------------------------------------------------------
class IsMoreThanNthGenerationDescendantOf(Rule):
    """Rule that checks for a person that is a descendant of a specified person
    at least N generations away"""

    labels = [ _('ID:'), _('Number of generations:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}

    def name(self):
        return 'Is a descendant of person at least N generations away'

    def description(self):
        return _("Matches people that are descendants of a specified "
                 "person at least N generations away")
    
    def category(self):
        return _("Descendant filters")

    def apply(self,db,p_id):
        self.orig_id = p_id
        self.db = db

        if not self.init:
            self.init = 1
            root_id = self.list[0]
            self.init_list(root_id,0)
        return self.map.has_key(p_id)

    def init_list(self,p_id,gen):
        if gen >= int(self.list[1]):
            self.map[p_id] = 1

        p = self.db.find_person_from_id(p_id)
        for fam_id in p.get_family_id_list():
            fam = self.db.find_family_from_id(fam_id)
            for child_id in fam.get_child_id_list():
                self.init_list(child_id,gen+1)

#-------------------------------------------------------------------------
#
# IsChildOfFilterMatch
#
#-------------------------------------------------------------------------
class IsChildOfFilterMatch(Rule):
    """Rule that checks for a person that is a child
    of someone matched by a filter"""

    labels = [ _('Filter name:') ]

    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}

    def name(self):
        return 'Is a child of filter match'

    def description(self):
        return _("Matches the person that is a child of someone matched by a filter")

    def category(self):
        return _('Family filters')

    def apply(self,db,p_id):
        self.orig_id = p_id
        self.db = db

        if not self.init:
            self.init = 1
            filter = MatchesFilter(self.list)
            for person_id in db.get_person_keys():
                if filter.apply (db, person_id):
                    self.init_list (person_id)
        return self.map.has_key(p_id)

    def init_list(self,p_id):
        p = self.db.find_person_from_id(p_id)
        for fam_id in p.get_family_id_list():
            fam = self.db.find_family_from_id(fam_id)
            for child_id in fam.get_child_id_list():
                self.map[child_id] = 1

#-------------------------------------------------------------------------
#
# IsDescendantFamilyOf
#
#-------------------------------------------------------------------------
class IsDescendantFamilyOf(Rule):
    """Rule that checks for a person that is a descendant or the spouse
    of a descendant of a specified person"""

    labels = [ _('ID:') ]
    
    def name(self):
        return "Is a descendant family member of"

    def category(self): 
        return _('Descendant filters')

    def description(self):
        return _("Matches people that are descendants or the spouse "
                 "of a descendant of a specified person")
    
    def apply(self,db,p_id):
        self.map = {}
        self.orig_id = p_id
        self.db = db
        return self.search(p_id,1)

    def search(self,p_id,val):
        if p_id == self.list[0]:
            self.map[p_id] = 1
            return 1
        
        p = self.db.find_person_from_id(p_id)
        for (f,r1,r2) in p.get_parent_family_id_list():
            family = self.db.find_family_from_id(f)
            for person_id in [family.get_mother_id(),family.get_father_id()]:
                if person_id:
                    if self.search(person_id,0):
                        return 1
        if val:
            for family_id in p.get_family_id_list():
                family = self.db.find_family_from_id(family_id)
                if p_id == family.get_father_id():
                    spouse_id = family.get_mother_id()
                else:
                    spouse_id = family.get_father_id()
                if spouse_id:
                    if self.search(spouse_id,0):
                        return 1
        return 0

#-------------------------------------------------------------------------
#
# IsAncestorOf
#
#-------------------------------------------------------------------------
class IsAncestorOf(Rule):
    """Rule that checks for a person that is an ancestor of a specified person"""

    labels = [ _('ID:'), _('Inclusive:') ]

    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}
    
    def name(self):
        return 'Is an ancestor of'

    def description(self):
        return _("Matches people that are ancestors of a specified person")
    
    def category(self):
        return _("Ancestral filters")

    def apply(self,db,p_id):
        """Assume that if 'Inclusive' not defined, assume inclusive"""
        self.orig_id = p_id
        self.db = db
        try:
            if int(self.list[1]):
                first = 0
            else:
                first = 1
        except IndexError:
            first = 1
            
        if not self.init:
            self.init = 1
            root_id = self.list[0]
            self.init_ancestor_list(root_id,first)
        return self.map.has_key(p_id)

    def init_ancestor_list(self,p_id,first):
        if not first:
            self.map[p_id] = 1
        
        p = self.db.find_person_from_id(p_id)
        fam_id = p.get_main_parents_family_id()
        if fam_id:
            fam = self.db.find_family_from_id(fam_id)
            f_id = fam.get_father_id()
            m_id = fam.get_mother_id()
        
            if f_id:
                self.init_ancestor_list(f_id,0)
            if m_id:
                self.init_ancestor_list(m_id,0)

#-------------------------------------------------------------------------
#
# IsAncestorOfFilterMatch
#
#-------------------------------------------------------------------------
class IsAncestorOfFilterMatch(IsAncestorOf):
    """Rule that checks for a person that is an ancestor of
    someone matched by a filter"""

    labels = [ _('Filter name:'), _('Inclusive:') ]

    def __init__(self,list):
        IsAncestorOf.__init__(self,list)
    
    def name(self):
        return 'Is an ancestor of filter match'

    def description(self):
        return _("Matches people that are ancestors "
            "of someone matched by a filter")
    
    def category(self):
        return _("Ancestral filters")

    def apply(self,db,p_id):
        self.orig_id = p_id
        try:
            if int(self.list[1]):
                first = 0
            else:
                first = 1
        except IndexError:
            first = 1
            
        if not self.init:
            self.init = 1
            filter = MatchesFilter(self.list[0])
            for person_id in db.get_person_keys():
                if filter.apply (db, person_id):
                    self.init_ancestor_list (person_id,first)
        return self.map.has_key(p_id)

#-------------------------------------------------------------------------
#
# IsLessThanNthGenerationAncestorOf
#
#-------------------------------------------------------------------------
class IsLessThanNthGenerationAncestorOf(Rule):
    """Rule that checks for a person that is an ancestor of a specified person
    not more than N generations away"""

    labels = [ _('ID:'), _('Number of generations:') ]

    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}
    
    def name(self):
        return 'Is an ancestor of person not more than N generations away'

    def description(self):
        return _("Matches people that are ancestors "
            "of a specified person not more than N generations away")
    
    def category(self):
        return _("Ancestral filters")

    def apply(self,db,p_id):
        self.orig_id = p_id
        self.db = db
        if not self.init:
            self.init = 1
            root_id = self.list[0]
            self.init_ancestor_list(root_id,0)
        return self.map.has_key(p_id)

    def init_ancestor_list(self,p_id,gen):
#        if self.map.has_key(p.get_id()) == 1:
#            loop_error(self.orig,p)
        if gen:
            self.map[p_id] = 1
            if gen >= int(self.list[1]):
                return
        
        p = self.db.find_person_from_id(p_id)
        fam_id = p.get_main_parents_family_id()
        if fam_id:
            fam = self.db.find_family_from_id(fam_id)
            f_id = fam.get_father_id()
            m_id = fam.get_mother_id()
        
            if f_id:
                self.init_ancestor_list(f_id,gen+1)
            if m_id:
                self.init_ancestor_list(m_id,gen+1)

#-------------------------------------------------------------------------
#
# IsMoreThanNthGenerationAncestorOf
#
#-------------------------------------------------------------------------
class IsMoreThanNthGenerationAncestorOf(Rule):
    """Rule that checks for a person that is an ancestor of a specified person
    at least N generations away"""

    labels = [ _('ID:'), _('Number of generations:') ]

    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}
    
    def name(self):
        return 'Is an ancestor of person at least N generations away'

    def description(self):
        return _("Matches people that are ancestors "
            "of a specified person at least N generations away")
    
    def category(self):
        return _("Ancestral filters")

    def apply(self,db,p_id):
        self.orig_id = p_id
        self.db = db
        if not self.init:
            self.init = 1
            root_id = self.list[0]
            self.init_ancestor_list(root_id,0)
        return self.map.has_key(p_id)

    def init_ancestor_list(self,p_id,gen):
#        if self.map.has_key(p.get_id()) == 1:
#            loop_error(self.orig,p)
        if gen >= int(self.list[1]):
            self.map[p_id] = 1
        
        p = self.db.find_person_from_id(p_id)
        fam_id = p.get_main_parents_family_id()
        if fam_id:
            fam = self.db.find_family_from_id(fam_id)
            f_id = fam.get_father_id()
            m_id = fam.get_mother_id()
        
            if f_id:
                self.init_ancestor_list(f_id,gen+1)
            if m_id:
                self.init_ancestor_list(m_id,gen+1)

#-------------------------------------------------------------------------
#
# IsParentOfFilterMatch
#
#-------------------------------------------------------------------------
class IsParentOfFilterMatch(Rule):
    """Rule that checks for a person that is a parent
    of someone matched by a filter"""

    labels = [ _('Filter name:') ]

    def __init__(self,list):
        Rule.__init__(self,list)
        self.init = 0
        self.map = {}

    def name(self):
        return 'Is a parent of filter match'

    def description(self):
        return _("Matches the person that is a parent of someone matched by a filter")

    def category(self):
        return _('Family filters')

    def apply(self,db,p):
        self.orig_id = p_id
        self.db = db

        if not self.init:
            self.init = 1
            filter = MatchesFilter(self.list)
            for person_id in db.get_person_keys():
                if filter.apply (db, person_id):
                    self.init_list (person_id)
        return self.map.has_key(p_id)

    def init_list(self,p_id):
        p = self.db.find_person_from_id(p_id)
        for fam_id in p.get_main_parents_family_id():
            fam = self.db.find_family_from_id(fam_id)
            for parent_id in [fam.get_father_id (), fam.get_mother_id ()]:
                if parent_id:
                    self.map[parent_id] = 1

#-------------------------------------------------------------------------
#
# HasCommonAncestorWith
#
#-------------------------------------------------------------------------
class HasCommonAncestorWith(Rule):
    """Rule that checks for a person that has a common ancestor with a specified person"""

    labels = [ _('ID:') ]

    def name(self):
        return 'Has a common ancestor with'

    def description(self):
        return _("Matches people that have a common ancestor "
            "with a specified person")
    
    def category(self):
        return _("Ancestral filters")

    def __init__(self,list):
        Rule.__init__(self,list)
        # Keys in `ancestor_cache' are ancestors of list[0].
        # We delay the computation of ancestor_cache until the
        # first use, because it's not uncommon to instantiate
        # this class and not use it.
        self.ancestor_cache = {}

    def init_ancestor_cache(self,db):
        # list[0] is an Id, but we need to pass a Person to for_each_ancestor.
        p_id = self.list[0]
        if p_id:
            def init(self,pid): self.ancestor_cache[pid] = 1
            for_each_ancestor([p_id],init,self)

    def apply(self,db,p_id):
        # On the first call, we build the ancestor cache for the
        # reference person.   Then, for each person to test,
        # we browse his ancestors until we found one in the cache.
        if len(self.ancestor_cache) == 0:
            self.init_ancestor_cache(db)
        return for_each_ancestor([p_id],
                                 lambda self,p_id: self.ancestor_cache.has_key(p_id),
                                 self);

#-------------------------------------------------------------------------
#
# HasCommonAncestorWithFilterMatch
#
#-------------------------------------------------------------------------
class HasCommonAncestorWithFilterMatch(HasCommonAncestorWith):
    """Rule that checks for a person that has a common ancestor with
    someone matching a filter"""

    labels = [ _('Filter name:') ]

    def name(self):
        return 'Has a common ancestor with filter match'

    def description(self):
        return _("Matches people that have a common ancestor "
            "with someone matched by a filter")
    
    def category(self):
        return _("Ancestral filters")

    def __init__(self,list):
        HasCommonAncestorWith.__init__(self,list)

    def init_ancestor_cache(self,db):
        filter = MatchesFilter(self.list)
        def init(self,pid): self.ancestor_cache[pid] = 1
        for p_id in db.get_person_keys():
            if (not self.ancestor_cache.has_key (p_id)
                and filter.apply (db, p_id)):
                for_each_ancestor([p_id],init,self)

#-------------------------------------------------------------------------
#
# IsMale
#
#-------------------------------------------------------------------------
class IsMale(Rule):
    """Rule that checks for a person that is a male"""

    labels = []
    
    def name(self):
        return 'Is a male'

    def category(self): 
        return _('General filters')
    
    def description(self):
        return _('Matches all males')

    def apply(self,db,p_id):
        return db.find_person_from_id(p_id).get_gender() == RelLib.Person.male

#-------------------------------------------------------------------------
#
# HasEvent
#
#-------------------------------------------------------------------------
class HasEvent(Rule):
    """Rule that checks for a person with a particular value"""

    labels = [ _('Personal event:'), _('Date:'), _('Place:'), _('Description:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        if self.list and self.list[0]:
            self.date = Date.Date()
            self.date.set(self.list[0])
        else:
            self.date = None

    def name(self):
        return 'Has the personal event'

    def description(self):
        return _("Matches the person with a personal event of a particular value")

    def category(self):
        return _('Event filters')

    def apply(self,db,p_id):
        p = db.find_person_from_id(p_id)
        for event_id in p.get_event_list():
            if not event_id:
                continue
            event = db.find_event_from_id(event_id)
            val = 1
            if self.list[0] and event.get_name() != self.list[0]:
                val = 0
            if self.list[3] and string.find(event.get_description().upper(),
                                            self.list[3].upper())==-1:
                val = 0
            if self.date:
                if date_cmp(self.date,event.get_date_object()):
                    val = 0
            if self.list[2]:
                pl_id = event.get_place_id()
                if pl_id:
                    pl = db.find_place_from_id(pl_id)
                    pn = pl.get_title()
                    if string.find(pn.upper(),self.list[2].upper()) == -1:
                        val = 0
                if val == 1:
                    return 1
        return 0

#-------------------------------------------------------------------------
#
# HasFamilyEvent
#
#-------------------------------------------------------------------------
class HasFamilyEvent(Rule):
    """Rule that checks for a person who has a relationship event
    with a particular value"""

    labels = [ _('Family event:'), _('Date:'), _('Place:'), _('Description:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        if self.list and self.list[0]:
            self.date = Date.Date()
            self.date.set(self.list[0])
        else:
            self.date = None

    def name(self):
        return 'Has the family event'

    def description(self):
        return _("Matches the person with a family event of a particular value")

    def category(self):
        return _('Event filters')

    def apply(self,db,p_id):
        p = db.find_person_from_id(p_id)
        for f_id in p.get_family_id_list():
            f = db.find_family_from_id(f_id)
            for event_id in f.get_event_list():
                if not event_id:
                    continue
                event = db.find_event_from_id(event_id)
                val = 1
                if self.list[0] and event.get_name() != self.list[0]:
                    val = 0
                v = self.list[3]
                if v and string.find(event.get_description().upper(),v.upper())==-1:
                    val = 0
                if self.date:
                    if date_cmp(self.date,event.get_date_object()):
                        val = 0
                pl_id = event.get_place_id()
                if pl_id:
                    pl = db.find_place_from_id(pl_id)
                    pn = pl.get_title()
                    if self.list[2] and string.find(pn,self.list[2].upper()) == -1:
                        val = 0
                    if val == 1:
                        return 1
        return 0

#-------------------------------------------------------------------------
#
# HasRelationship
#
#-------------------------------------------------------------------------
class HasRelationship(Rule):
    """Rule that checks for a person who has a particular relationship"""

    labels = [ _('Number of relationships:'),
               _('Relationship type:'),
               _('Number of children:') ]

    def name(self):
        return 'Has the relationships'

    def description(self):
        return _("Matches the person who has a particular relationship")

    def category(self):
        return _('Family filters')

    def apply(self,db,p_id):
        rel_type = 0
        cnt = 0
        p = db.find_person_from_id(p_id)
        num_rel = len(p.get_family_id_list())

        # count children and look for a relationship type match
        for f_id in p.get_family_id_list():
            f = db.find_family_from_id(f_id)
            cnt = cnt + len(f.get_child_id_list())
            if self.list[1] and f.get_relationship() == self.list[1]:
                rel_type = 1

        # if number of relations specified
        if self.list[0]:
            try:
                v = int(self.list[0])
            except:
                return 0
            if v != num_rel:
                return 0

        # number of childred
        if self.list[2]:
            try:
                v = int(self.list[2])
            except:
                return 0
            if v != cnt:
                return 0

        # relation
        if self.list[1]:
            return rel_type == 1
        else:
            return 1

#-------------------------------------------------------------------------
#
# HasBirth
#
#-------------------------------------------------------------------------
class HasBirth(Rule):
    """Rule that checks for a person with a birth of a particular value"""

    labels = [ _('Date:'), _('Place:'), _('Description:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        if self.list and self.list[0]:
            self.date = Date.Date()
            self.date.set(self.list[0])
        else:
            self.date = None
        
    def name(self):
        return 'Has the birth'

    def description(self):
        return _("Matches the person with a birth of a particular value")

    def category(self):
        return _('Event filters')

    def apply(self,db,p_id):
        p = db.find_person_from_id(p_id)
        event_id = p.get_birth_id()
        if not event_id:
            return 0
        event = db.find_event_from_id(event_id)
        ed = event.get_description().upper()
        if len(self.list) > 2 and string.find(ed,self.list[2].upper())==-1:
            return 0
        if self.date:
            if date_cmp(self.date,event.get_date_object()) == 0:
                return 0
        pl_id = event.get_place_id()
        if pl_id:
            pl = db.find_place_from_id(pl_id)
            pn = pl.get_title()
            if len(self.list) > 1 and string.find(pn,self.list[1].upper()) == -1:
                return 0
        return 1

#-------------------------------------------------------------------------
#
# HasDeath
#
#-------------------------------------------------------------------------
class HasDeath(Rule):
    """Rule that checks for a person with a death of a particular value"""

    labels = [ _('Date:'), _('Place:'), _('Description:') ]
    
    def __init__(self,list):
        Rule.__init__(self,list)
        if self.list and self.list[0]:
            self.date = Date.Date()
            self.date.set(self.list[0])
        else:
            self.date = None

    def name(self):
        return 'Has the death'

    def description(self):
        return _("Matches the person with a death of a particular value")

    def category(self):
        return _('Event filters')

    def apply(self,db,p_id):
        p = db.find_person_from_id(p_id)
        event_id = p.get_death_id()
        if not event_id:
            return 0
        event = db.find_event_from_id(event_id)
        ed = event.get_description().upper()
        if self.list[2] and string.find(ed,self.list[2].upper())==-1:
            return 0
        if self.date:
            if date_cmp(self.date,event.get_date_object()) == 0:
                return 0
        pl_id = event.get_place_id()
        if pl_id:
            pl = db.find_place_from_id(pl_id)
            pn = pl.get_title()
            if self.list[1] and string.find(pn,self.list[1].upper()) == -1:
                return 0
        return 1

#-------------------------------------------------------------------------
#
# HasAttribute
#
#-------------------------------------------------------------------------
class HasAttribute(Rule):
    """Rule that checks for a person with a particular personal attribute"""

    labels = [ _('Personal attribute:'), _('Value:') ]
    
    def name(self):
        return 'Has the personal attribute'

    def apply(self,db,p_id):
        p = db.find_person_from_id(p_id)
        for event in p.getAttributes():
            if self.list[0] and event.get_type() != self.list[0]:
                return 0
            ev = event.get_value().upper()
            if self.list[1] and string.find(ev,self.list[1].upper())==-1:
                return 0
        return 1

#-------------------------------------------------------------------------
#
# HasFamilyAttribute
#
#-------------------------------------------------------------------------
class HasFamilyAttribute(Rule):
    """Rule that checks for a person with a particular family attribute"""

    labels = [ _('Family attribute:'), _('Value:') ]
    
    def name(self):
        return 'Has the family attribute'

    def apply(self,db,p_id):
        p = db.find_person_from_id(p_id)
        for f_id in p.get_family_id_list():
            f = db.find_family_from_id(f_id)
            for event in f.getAttributes():
                val = 1
                if self.list[0] and event.get_type() != self.list[0]:
                    val = 0
                ev = event.get_value().upper()
                if self.list[1] and string.find(ev,self.list[1].upper())==-1:
                    val = 0
                if val == 1:
                    return 1
        return 0

#-------------------------------------------------------------------------
#
# HasNameOf
#
#-------------------------------------------------------------------------
class HasNameOf(Rule):
    """Rule that checks for full or partial name matches"""

    labels = [_('Given name:'),_('Family name:'),_('Suffix:'),_('Title:')]
    
    def name(self):
        return 'Has a name'
    
    def description(self):
        return _("Matches the person with a specified (partial) name")

    def category(self):
        return _('General filters')

    def apply(self,db,p_id):
        self.f = self.list[0]
        self.l = self.list[1]
        self.s = self.list[2]
        self.t = self.list[3]
        p = db.find_person_from_id(p_id)
        for name in [p.get_primary_name()] + p.get_alternate_names():
            val = 1
            if self.f and string.find(name.get_first_name().upper(),self.f.upper()) == -1:
                val = 0
            if self.l and string.find(name.get_surname().upper(),self.l.upper()) == -1:
                val = 0
            if self.s and string.find(name.get_suffix().upper(),self.s.upper()) == -1:
                val = 0
            if self.t and string.find(name.get_title().upper(),self.t.upper()) == -1:
                val = 0
            if val == 1:
                return 1
        return 0

#-------------------------------------------------------------------------
#
# HasNameOf
#
#-------------------------------------------------------------------------
class SearchName(Rule):
    """Rule that checks for full or partial name matches"""

    labels = [_('Substring:')]
    
    def name(self):
        return 'Matches name'
    
    def description(self):
        return _("Matches the person with a specified (partial) name")

    def category(self):
        return _('General filters')

    def apply(self,db,p_id):
        self.f = self.list[0]
        p = db.find_person_from_id(p_id)
        return self.f and string.find(p.get_primary_name().get_name().upper(),self.f.upper()) != -1
    
#-------------------------------------------------------------------------
#
# MatchesFilter
#
#-------------------------------------------------------------------------
class MatchesFilter(Rule):
    """Rule that checks against another filter"""

    labels = [_('Filter name:')]

    def name(self):
        return 'Matches the filter named'

    def apply(self,db,p_id):
        for filter in SystemFilters.get_filters():
            if filter.get_name() == self.list[0]:
                return filter.check(p_id)
        for filter in CustomFilters.get_filters():
            if filter.get_name() == self.list[0]:
                return filter.check(db,p_id)
        return 0

#-------------------------------------------------------------------------
#
# IsSpouseOfFilterMatch
#
#-------------------------------------------------------------------------
class IsSpouseOfFilterMatch(Rule):
    """Rule that checks for a person married to someone matching
    a filter"""

    labels = [_('Filter name:')]

    def name(self):
        return 'Is spouse of filter match'

    def description(self):
        return _("Matches the person married to someone matching a filter")

    def category(self):
        return _('Family filters')

    def apply(self,db,p_id):
        filter = MatchesFilter (self.list)
        p = db.find_person_from_id(p_id)
        for family_id in p.get_family_id_list ():
            family = db.find_family_from_id(family_id)
            for spouse_id in [family.get_father_id (), family.get_mother_id ()]:
                if not spouse_id:
                    continue
                if spouse_id == p_id:
                    continue
                if filter.apply (db, spouse_id):
                    return 1
        return 0

#-------------------------------------------------------------------------
#
# GenericFilter
#
#-------------------------------------------------------------------------
class GenericFilter:
    """Filter class that consists of several rules"""
    
    def __init__(self,source=None):
        if source:
            self.need_param = source.need_param
            self.flist = source.flist[:]
            self.name = source.name
            self.comment = source.comment
            self.logical_op = source.logical_op
            self.invert = source.invert
        else:
            self.need_param = 0
            self.flist = []
            self.name = ''
            self.comment = ''
            self.logical_op = 'and'
            self.invert = 0

    def set_logical_op(self,val):
        if val in const.logical_functions:
            self.logical_op = val
        else:
            self.logical_op = 'and'

    def get_logical_op(self):
        return self.logical_op

    def set_invert(self, val):
        self.invert = not not val

    def get_invert(self):
        return self.invert
    
    def get_name(self):
        return self.name
    
    def set_name(self,name):
        self.name = name

    def set_comment(self,comment):
        self.comment = comment

    def get_comment(self):
        return self.comment
    
    def add_rule(self,rule):
        self.flist.append(rule)

    def delete_rule(self,rule):
        self.flist.remove(rule)

    def set_rules(self,rules):
        self.flist = rules

    def get_rules(self):
        return self.flist

    def check_or(self,db,p_id):
        test = 0
        for rule in self.flist:
            test = test or rule.apply(db,p_id)
            if test:
                break
        if self.invert:
            return not test
        else:
            return test

    def check_xor(self,db,p_id):
        test = 0
        for rule in self.flist:
            temp = rule.apply(db,p_id)
            test = ((not test) and temp) or (test and (not temp))
        if self.invert:
            return not test
        else:
            return test

    def check_one(self,db,p_id):
        count = 0
        for rule in self.flist:
            if rule.apply(db,p_id):
                count = count + 1
                if count > 1:
                    break
        if self.invert:
            return count != 1
        else:
            return count == 1

    def check_and(self,db,p_id):
        test = 1
        for rule in self.flist:
            test = test and rule.apply(db,p_id)
            if not test:
                break
        if self.invert:
            return not test
        else:
            return test
    
    def get_check_func(self):
        try:
            m = getattr(self, 'check_' + self.logical_op)
        except AttributeError:
            m = self.check_and
        return m

    def check(self,db,p_id):
        return self.get_check_func()(db,p_id)

    def apply(self,db,id_list):
        m = self.get_check_func()
        res = []
        for p_id in id_list:
            if m(db,p_id):
                res.append(p_id)
        return res


#-------------------------------------------------------------------------
#
# Name to class mappings
#
#-------------------------------------------------------------------------
tasks = {
    unicode(_("Everyone"))                             : Everyone,
    unicode(_("Has the Id"))                           : HasIdOf,
    unicode(_("Has a name"))                           : HasNameOf,
    unicode(_("Has the relationships"))                : HasRelationship,
    unicode(_("Has the death"))                        : HasDeath,
    unicode(_("Has the birth"))                        : HasBirth,
    unicode(_("Is a descendant of"))                   : IsDescendantOf,
    unicode(_("Is a descendant family member of"))     : IsDescendantFamilyOf,
    unicode(_("Is a descendant of filter match"))      : IsDescendantOfFilterMatch,
    unicode(_("Is a descendant of person not more than N generations away"))
                                                       : IsLessThanNthGenerationDescendantOf,
    unicode(_("Is a descendant of person at least N generations away"))
                                                       : IsMoreThanNthGenerationDescendantOf,
    unicode(_("Is a child of filter match"))           : IsChildOfFilterMatch,
    unicode(_("Is an ancestor of"))                    : IsAncestorOf,
    unicode(_("Is an ancestor of filter match"))       : IsAncestorOfFilterMatch,
    unicode(_("Is an ancestor of person not more than N generations away"))
                                                       : IsLessThanNthGenerationAncestorOf,
    unicode(_("Is an ancestor of person at least N generations away"))
                                                       : IsMoreThanNthGenerationAncestorOf,
    unicode(_("Is a parent of filter match"))          : IsParentOfFilterMatch,
    unicode(_("Has a common ancestor with"))           : HasCommonAncestorWith,
    unicode(_("Has a common ancestor with filter match"))
                                                       : HasCommonAncestorWithFilterMatch,
    unicode(_("Is a female"))                          : IsFemale,
    unicode(_("Is a male"))                            : IsMale,
    unicode(_("Has complete record"))                  : HasCompleteRecord,
    unicode(_("Has the personal event"))               : HasEvent,
    unicode(_("Has the family event"))                 : HasFamilyEvent,
    unicode(_("Has the personal attribute"))           : HasAttribute,
    unicode(_("Has the family attribute"))             : HasFamilyAttribute,
    unicode(_("Matches the filter named"))             : MatchesFilter,
    unicode(_("Is spouse of filter match"))            : IsSpouseOfFilterMatch,
    unicode(_("Relationship path between two people")) : RelationshipPathBetween,
    }

#-------------------------------------------------------------------------
#
# GenericFilterList
#
#-------------------------------------------------------------------------
class GenericFilterList:
    """Container class for the generic filters. Stores, saves, and
    loads the filters."""
    
    def __init__(self,file):
        self.filter_list = []
        self.file = os.path.expanduser(file)

    def get_filters(self):
        return self.filter_list
    
    def add(self,filter):
        self.filter_list.append(filter)
        
    def load(self):
        try:
            parser = make_parser()
            parser.setContentHandler(FilterParser(self))
            if self.file[0:7] != "file://":
                parser.parse("file://" + self.file)
            else:
                parser.parse(self.file)
        except (IOError,OSError,SAXParseException):
            pass

    def fix(self,line):
        l = line.strip()
        l = l.replace('&','&amp;')
        l = l.replace('>','&gt;')
        l = l.replace('<','&lt;')
        return l.replace('"','&quot;')

    def save(self):
#        try:
#            f = open(self.file,'w')
#        except:
#            return

        f = open(self.file.encode('utf-8'),'w')
        
        f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        f.write('<filters>\n')
        for i in self.filter_list:
            f.write('  <filter name="%s"' % self.fix(i.get_name()))
            if i.get_invert():
                f.write(' invert="1"')
            f.write(' function="%s"' % i.get_logical_op())
            comment = i.get_comment()
            if comment:
                f.write(' comment="%s"' % self.fix(comment))
            f.write('>\n')
            for rule in i.get_rules():
                f.write('    <rule class="%s">\n' % self.fix(rule.name()))
                for v in rule.values():
                    f.write('      <arg value="%s"/>\n' % self.fix(v))
                f.write('    </rule>\n')
            f.write('  </filter>\n')
        f.write('</filters>\n')
        f.close()

#-------------------------------------------------------------------------
#
# FilterParser
#
#-------------------------------------------------------------------------
class FilterParser(handler.ContentHandler):
    """Parses the XML file and builds the list of filters"""
    
    def __init__(self,gfilter_list):
        handler.ContentHandler.__init__(self)
        self.gfilter_list = gfilter_list
        self.f = None
        self.r = None
        self.a = []
        self.cname = None
        
    def setDocumentLocator(self,locator):
        self.locator = locator

    def startElement(self,tag,attrs):
        if tag == "filter":
            self.f = GenericFilter()
            self.f.set_name(attrs['name'])
            if attrs.has_key('function'):
                try:
                    if int(attrs['function']):
                        op = 'or'
                    else:
                        op = 'and'
                except ValueError:
                    op = attrs['function']
                self.f.set_logical_op(op)
            if attrs.has_key('comment'):
                self.f.set_comment(attrs['comment'])
            if attrs.has_key('invert'):
                try:
                    self.f.set_invert(int(attrs['invert']))
                except ValueError:
                    pass
            self.gfilter_list.add(self.f)
        elif tag == "rule":
            cname = attrs['class']
            name = unicode(_(cname))
            self.a = []
            self.cname = tasks[name]
        elif tag == "arg":
            self.a.append(attrs['value'])

    def endElement(self,tag):
        if tag == "rule":
            rule = self.cname(self.a)
            self.f.add_rule(rule)
            
    def characters(self, data):
        pass

class ParamFilter(GenericFilter):

    def __init__(self,source=None):
        GenericFilter.__init__(self,source)
        self.need_param = 1
        self.param_list = []

    def set_parameter(self,param):
        self.param_list = [param]

    def apply(self,db,id_list):
        for rule in self.flist:
            rule.set_list(self.param_list)
        return GenericFilter.apply(self,db,id_list)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
SystemFilters = None
CustomFilters = None

def reload_system_filters():
    global SystemFilters
    SystemFilters = GenericFilterList(const.system_filters)
    SystemFilters.load()
    
def reload_custom_filters():
    global CustomFilters
    CustomFilters = GenericFilterList(const.custom_filters)
    CustomFilters.load()
    
if not SystemFilters:
    reload_system_filters()

if not CustomFilters:
    reload_custom_filters()

def build_filter_menu(local_filters = [], default=""):
    menu = gtk.Menu()

    active = 0
    cnt = 0
    for filter in local_filters:
        menuitem = gtk.MenuItem(filter.get_name())
        menuitem.show()
        menu.append(menuitem)
        menuitem.set_data("filter", filter)
        if default != "" and default == filter.get_name():
            active = cnt
        cnt += 1
        
    for filter in SystemFilters.get_filters():
        menuitem = gtk.MenuItem(_(filter.get_name()))
        menuitem.show()
        menu.append(menuitem)
        menuitem.set_data("filter", filter)
        if default != "" and default == filter.get_name():
            active = cnt
        cnt += 1

    for filter in CustomFilters.get_filters():
        menuitem = gtk.MenuItem(_(filter.get_name()))
        menuitem.show()
        menu.append(menuitem)
        menuitem.set_data("filter", filter)
        if default != "" and default == filter.get_name():
            active = cnt
        cnt += 1

    if active:
        menu.set_active(active)
    elif len(local_filters):
        menu.set_active(2)
    elif len(SystemFilters.get_filters()):
        menu.set_active(4 + len(local_filters))
    elif len(CustomFilters.get_filters()):
        menu.set_active(6 + len(local_filters) + len(SystemFilters.get_filters()))
    else:
        menu.set_active(0)
        
    return menu
