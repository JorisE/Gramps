#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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

"""The core library of the GRAMPS database"""

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _

import os
import os.path
import time
import re

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import Date
import DateHandler

#-------------------------------------------------------------------------
#
# Confidence levels
#
#-------------------------------------------------------------------------

CONF_VERY_HIGH = 4
CONF_HIGH      = 3
CONF_NORMAL    = 2
CONF_LOW       = 1
CONF_VERY_LOW  = 0

#-------------------------------------------------------------------------
#
# Class definitions
#
#-------------------------------------------------------------------------
class BaseObject:
    """
    The BaseObject is the base class for all data objects in GRAMPS,
    whether primary or not. Its main goal is to provide common capabilites
    to all objects, such as searching through all available information.
    """
    
    def __init__(self):
        """
        Initialize a BaseObject.
        """
        pass
    
    def matches_string(self,pattern,case_sensitive=False):
        """
        Returns True if any text data in the object or any of it's child
        objects matches a given pattern.

        @param pattern: The pattern to match.
        @type pattern: str
        @param case_sensitive: Whether the match is case-sensitive.
        @type case_sensitive: bool
        @return: Returns whether any text data in the object or any of it's child objects matches a given pattern.
        @rtype: bool
        """
        # Run through its own items
        patern_upper = pattern.upper()
        for item in self.get_text_data_list():
            if case_sensitive:
                if item.find(pattern) != -1:
                    return True
            else:
                if item.upper().find(patern_upper) != -1:
                    return True

        # Run through child objects
        for obj in self.get_text_data_child_list():
            if obj.matches_string(pattern,case_sensitive):
                return True

        return False

    def matches_regexp(self,pattern,case_sensitive=False):
        """
        Returns True if any text data in the object or any of it's child
        objects matches a given regular expression.

        @param pattern: The pattern to match.
        @type pattern: str
        @return: Returns whether any text data in the object or any of it's child objects matches a given regexp.
        @rtype: bool
        """

        # Run through its own items
        if case_sensitive:
            pattern_obj = re.compile(pattern)
        else:
            pattern_obj = re.compile(pattern,re.IGNORECASE)
        for item in self.get_text_data_list():
            if pattern_obj.match(item):
                return True

        # Run through child objects
        for obj in self.get_text_data_child_list():
            if obj.matches_regexp(pattern,case_sensitive):
                return True

        return False

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return []

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        return []

class PrimaryObject(BaseObject):
    """
    The PrimaryObject is the base class for all primary objects in the
    database. Primary objects are the core objects in the database.
    Each object has a database handle and a GRAMPS ID value. The database
    handle is used as the record number for the database, and the GRAMPS
    ID is the user visible version.
    """

    def __init__(self,source=None):
        """
        Initialize a PrimaryObject. If source is None, both the ID and handle
        are assigned as empty strings. If source is not None, then object
        is initialized from values of the source object.

        @param source: Object used to initialize the new object
        @type source: PrimaryObject
        """
        if source:
            self.gramps_id = source.gramps_id
            self.handle = source.handle
            self.change = source.change
        else:
            self.gramps_id = None
            self.handle = None
            self.change = 0

    def get_change_time(self):
        """
        Returns the time that the data was last changed. The value
        in the format returned by the time.time() command.
           
        @returns: Time that the data was last changed. The value
           in the format returned by the time.time() command.
        @rtype: int
        """
        return self.change

    def get_change_display(self):
        """
        Returns the string representation of the last change time.

        @returns: string representation of the last change time.
        @rtype: str
        
        """
        if self.change:
            return time.asctime(time.localtime(self.change))
        else:
            return ''

    def set_handle(self,handle):
        """
        Sets the database handle for the primary object

        @param handle: object database handle
        @type handle: str
        """
        self.handle = handle

    def get_handle(self):
        """
        Returns the database handle for the primary object

        @returns: database handle associated with the object
        @rtype: str
        """
        return self.handle

    def set_gramps_id(self,gramps_id):
        """
        Sets the GRAMPS ID for the primary object
        
        @param gramps_id: GRAMPS ID
        @type gramps_id: str
        """
        self.gramps_id = gramps_id

    def get_gramps_id(self):
        """
        Returns the GRAMPS ID for the primary object

        @returns: GRAMPS ID associated with the object
        @rtype: str
        """
        return self.gramps_id

class SourceNote(BaseObject):
    """
    Base class for storing source references and notes
    """
    
    def __init__(self,source=None):
        """
        Create a new SourceNote, copying from source if not None
        
        @param source: Object used to initialize the new object
        @type source: SourceNote
        """
        
        self.source_list = []
        self.note = None

        if source:
            for sref in source.source_list:
                self.source_list.append(SourceRef(sref))
            if source.note:
                self.note = Note(source.note.get())

    def add_source_reference(self,src_ref) :
        """
        Adds a source reference to this object.

        @param src_ref: The source reference to be added to the
            SourceNote's list of source references.
        @type src_ref: L{SourceRef}
        """
        self.source_list.append(src_ref)

    def get_source_references(self) :
        """
        Returns the list of source references associated with the object.

        @return: Returns the list of L{SourceRef} objects assocated with
            the object.
        @rtype: list
        """
        return self.source_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        return []

    def has_source_reference(self,src_handle) :
        """
        Returns True if the object or any of it's child objects has reference
        to this source handle.

        @param src_handle: The source handle to be checked.
        @type src_ref: str
        @return: Returns whether the object or any of it's child objects has reference to this source handle.
        @rtype: bool
        """
        for src_ref in self.source_list:
            # Using direct access here, not the getter method -- efficiency!
            if src_ref.ref == src_handle:
                return True

        for item in self.get_sourcref_child_list():
            if item.has_source_reference(src_handle):
                return True

        return False

    def remove_source_references(self,src_handle_list):
        """
        Removes references to all source handles in the list
        in this object and all child objects.

        @param src_handle_list: The list of source handles to be removed.
        @type src_handle_list: list
        """
        new_source_list = [ src_ref for src_ref in self.source_list \
                                    if src_ref.ref not in src_handle_list ]
        self.source_list = new_source_list

        for item in self.get_sourcref_child_list():
            item.remove_source_references(src_handle_list)

    def set_source_reference_list(self,src_ref_list) :
        """
        Assigns the passed list to the object's list of source references.

        @param src_ref_list: List of source references to ba associated
            with the object
        @type src_ref_list: list of L{SourceRef} instances
        """
        self.source_list = src_ref_list

    def set_note(self,text):
        """
        Assigns the specified text to the associated note.

        @param text: Text of the note
        @type text: str
        """
        if self.note == None:
            self.note = Note()
        self.note.set(text)

    def get_note(self):
        """
        Returns the text of the current note.

        @returns: the text of the current note
        @rtype: str
        """
        if self.note == None:
            return ""
        else:
            return self.note.get() 

    def set_note_format(self,val):
        """
        Sets the note's format to the given value. The format indicates
        whether the text is flowed (wrapped) or preformatted.

        @param val: True indicates the text is flowed
        @type val: bool
        """
        if self.note:
            self.note.set_format(val)

    def get_note_format(self):
        """
        Returns the current note's format

        @returns: True indicates that the note should be flowed (wrapped)
        @rtype: bool
        """
        if self.note == None:
            return False
        else:
            return self.note.get_format()

    def set_note_object(self,note_obj):
        """
        Replaces the current L{Note} object associated with the object

        @param note_obj: New L{Note} object to be assigned
        @type note_obj: L{Note}
        """
        self.note = note_obj

    def get_note_object(self):
        """
        Returns the L{Note} instance associated with the object.

        @returns: L{Note} object assocated with the object
        @rtype: L{Note}
        """
        return self.note

    def unique_note(self):
        """Creates a unique instance of the current note"""
        self.note = Note(self.note.get())

class DataObj(SourceNote):
    """
    Base class for data elements, providing source, note, and privacy data
    """

    def __init__(self,source=None):
        """
        Initialize a DataObj. If the source is not None, then object
        is initialized from values of the source object.

        @param source: Object used to initialize the new object
        @type source: DateObj
        """
        SourceNote.__init__(self,source)
        
        if source:
            self.private = source.private
        else:
            self.private = False

    def set_privacy(self,val):
        """
        Sets or clears the privacy flag of the data

        @param val: value to assign to the privacy flag. True indicates that the
           record is private, False indicates that it is public.
        @type val: bool
        """
        self.private = val

    def get_privacy(self):
        """
        Returns the privacy level of the data. 

        @returns: True indicates that the record is private
        @rtype: bool
        """
        return self.private

class Person(PrimaryObject,DataObj):
    """
    Introduction
    ============
    The Person record is the GRAMPS in-memory representation of an
    individual person. It contains all the information related to
    an individual.
    
    Usage
    =====
    Person objects are usually created in one of two ways.

      1. Creating a new person object, which is then initialized and
         added to the database.
      2. Retrieving an object from the database using the records
         handle.

    Once a Person object has been modified, it must be committed
    to the database using the database object's commit_person function,
    or the changes will be lost.

    @sort: serialize, unserialize, get_*, set_*, add_*, remove_*
    """
    
    UNKNOWN = 2
    MALE = 1
    FEMALE = 0

    CHILD_REL_NONE  = 0
    CHILD_REL_BIRTH = 1
    CHILD_REL_ADOPT = 2
    CHILD_REL_STEP  = 3
    CHILD_REL_SPONS = 4
    CHILD_REL_FOST  = 5
    CHILD_REL_UNKWN = 6
    CHILD_REL_OTHER = 7

    def __init__(self):
        """
        Creates a new Person instance. After initialization, most
        data items have empty or null values, including the database
        handle.
        """
        PrimaryObject.__init__(self)
        DataObj.__init__(self)
        SourceNote.__init__(self)
        self.primary_name = Name()
        self.event_list = []
        self.family_list = []
        self.parent_family_list = []
        self.media_list = []
        self.nickname = ""
        self.alternate_names = []
        self.gender = Person.UNKNOWN
        self.death_handle = None
        self.birth_handle = None
        self.address_list = []
        self.attribute_list = []
        self.urls = []
        self.lds_bapt = None
        self.lds_endow = None
        self.lds_seal = None
        self.complete = False
        self.private = False
        
        # We hold a reference to the GrampsDB so that we can maintain
        # its genderStats.  It doesn't get set here, but from
        # GenderStats.count_person.
        self.db = None
        
    def serialize(self):
        """
        Converts the data held in the Person to a Python tuple that
        represents all the data elements. This method is used to convert
        the object into a form that can easily be saved to a database.

        These elements may be primative Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objectes or
        lists), the database is responsible for converting the data into
        a form that it can use.

        @returns: Returns a python tuple containing the data that should
            be considered persistent.
        @rtype: tuple
        """
        return (self.handle, self.gramps_id, self.gender, 
                self.primary_name, self.alternate_names,
                unicode(self.nickname), self.death_handle, self.birth_handle,
                self.event_list, self.family_list, self.parent_family_list,
                self.media_list, self.address_list, self.attribute_list,
                self.urls, self.lds_bapt, self.lds_endow, self.lds_seal,
                self.complete, self.source_list, self.note, self.change,
                self.private)

    def unserialize(self,data):
        """
        Converts the data held in a tuple created by the serialize method
        back into the data in a Person object.

        @param data: tuple containing the persistent data associated the
            Person object
        @type data: tuple
        """
        (self.handle, self.gramps_id, self.gender, self.primary_name,
         self.alternate_names, self.nickname, self.death_handle,
         self.birth_handle, self.event_list, self.family_list,
         self.parent_family_list, self.media_list, self.address_list,
         self.attribute_list, self.urls, self.lds_bapt, self.lds_endow,
         self.lds_seal, self.complete, self.source_list, self.note,
         self.change,self.private) = (data + (False,))[0:23]
            
    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.nickname]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = [self.lds_bapt,self.lds_endow,self.lds_seal,self.note]
        add_list = [item for item in check_list if item]
        return [self.primary_name] + self.media_list + \
                    self.alternate_names + self.address_list + \
                    self.attribute_list + self.urls + \
                    self.source_list + add_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        lds_list = [self.lds_bapt,self.lds_endow,self.lds_seal]
        lds_check_list = [item for item in lds_list if item]
        return [self.primary_name] + self.media_list + \
                    self.alternate_names + self.address_list + \
                    self.attribute_list + lds_check_list

    def set_complete_flag(self,val):
        """
        Sets or clears the complete flag, which is used to indicate that the
        Person's data is considered to be complete.

        @param val: True indicates the Person object is considered to be
            complete
        @type val: bool
        """
        self.complete = val

    def get_complete_flag(self):
        """
        Returns the complete flag, which is used to indicate that the
        Person's data is considered to be complete.

        @return: True indicates that the Person's record is considered to
            be complete.
        @rtype: bool
        """
        return self.complete

    def set_primary_name(self,name):
        """
        Sets the primary name of the Person to the specified
        L{Name} instance

        @param name: L{Name} to be assigned to the person
        @type name: L{Name}
        """
        db = self.db
        if db:
            db.genderStats.uncount_person (self)
        self.primary_name = name
        if db:
            db.genderStats.count_person (self, db)

    def get_primary_name(self):
        """
        Returns the L{Name} instance marked as the Person's primary name

        @return: Returns the primary name
        @rtype: L{Name}
        """
        return self.primary_name

    def get_alternate_names(self):
        """
        Returns the list of alternate L{Name} instances

        @return: List of L{Name} instances
        @rtype: list
        """
        return self.alternate_names

    def set_alternate_names(self,alt_name_list):
        """
        Changes the list of alternate names to the passed list. 
        @param alt_name_list: List of L{Name} instances
        @type alt_name_list: list
        """
        self.alternate_names = alt_name_list

    def add_alternate_name(self,name):
        """
        Adds a L{Name} instance to the list of alternative names

        @param name: L{Name} to add to the list
        @type name: L{Name}
        """
        self.alternate_names.append(name)

    def get_url_list(self):
        """
        Returns the list of L{Url} instances associated with the Person

        @returns: List of L{Url} instances
        @rtype: list
        """
        return self.urls

    def set_url_list(self,url_list):
        """
        Sets the list of L{Url} instances to passed the list.

        @param url_list: List of L{Url} instances
        @type url_list: list
        """
        self.urls = url_list

    def add_url(self,url):
        """
        Adds a L{Url} instance to the Person's list of L{Url} instances

        @param url: L{Url} instance to be added to the Person's list of
            related web sites.
        @type url: L{Url}
        """
        self.urls.append(url)
    
    def set_nick_name(self,name):
        """
        Sets the nickname field for the Person

        @param name: Nickname to be assigned
        @type name: str
        """
        self.nickname = name

    def get_nick_name(self) :
        """
        Returns the nickname for the Person

        @returns: Returns the nickname associated with the Person
        @rtype str
        """
        return self.nickname

    def set_gender(self,gender) :
        """
        Sets the gender of the Person.

        @param gender: Assigns the Person's gender to one of the
            following constants::
                Person.MALE
                Person.FEMALE
                Person.UNKNOWN
        @type gender: int
        """
        # if the db object has been assigned, update the
        # genderStats of the database
        if self.db:
            self.db.genderStats.uncount_person (self)
        self.gender = gender
        if self.db:
            self.db.genderStats.count_person (self, self.db)

    def get_gender(self) :
        """
        Returns the gender of the Person

        @returns: Returns one of the following constants::
            Person.MALE
            Person.FEMALE
            Person.UNKNOWN
        @rtype: int
        """
        return self.gender

    def set_birth_handle(self,event_handle):
        """
        Assigns the birth event to the Person object. This is accomplished
        by assigning the handle of a valid L{Event} in the current database.

        @param event_handle: handle of the L{Event} to be associated with
            the Person's birth.
        @type event_handle: str
        """
        self.birth_handle = event_handle

    def set_death_handle(self,event_handle):
        """
        Assigns the death event to the Person object. This is accomplished
        by assigning the handle of a valid L{Event} in the current database.

        @param event_handle: handle of the L{Event} to be associated with
            the Person's death.
        @type event_handle: str
        """
        self.death_handle = event_handle

    def get_birth_handle(self):
        """
        Returns the database handle for the Person's birth event. This
        should correspond to an L{Event} in the database's L{Event} list.

        @returns: Returns the birth L{Event} handle or None if no birth
            L{Event} has been assigned.
        @rtype: str
        """
        return self.birth_handle

    def get_death_handle(self):
        """
        Returns the database handle for the Person's death event. This
        should correspond to an L{Event} in the database's L{Event} list.

        @returns: Returns the death L{Event} handle or None if no death
            L{Event} has been assigned.
        @rtype: str
        """
        return self.death_handle

    def add_media_reference(self,media_ref):
        """
        Adds a L{MediaRef} instance to the Person's media list.

        @param media_ref: L{MediaRef} instance to be added to the Person's
            media list.
        @type media_ref: L{MediaRef}
        """
        self.media_list.append(media_ref)

    def get_media_list(self):
        """
        Returns the list of L{MediaRef} instances associated with the Person

        @returns: list of L{MediaRef} instances associated with the Person
        @rtype: list
        """
        return self.media_list

    def set_media_list(self,media_ref_list):
        """
        Sets the list of L{MediaRef} instances associated with the Person.
        It replaces the previous list.

        @param media_ref_list: list of L{MediaRef} instances to be assigned
            to the Person.
        @type media_ref_list: list
        """
        self.media_list = media_ref_list

    def add_event_handle(self,event_handle):
        """
        Adds the L{Event} to the Person instance's L{Event} list. This is
        accomplished by assigning the handle of a valid L{Event} in the
        current database.
        
        @param event_handle: handle of the L{Event} to be added to the
            Person's L{Event} list.
        @type event_handle: str
        """
        self.event_list.append(event_handle)

    def get_event_list(self):
        """
        Returns the list of handles associated with L{Event} instances.

        @returns: Returns the list of L{Event} handles associated with
            the Person instance.
        @rtype: list
        """
        return self.event_list

    def set_event_list(self,event_list):
        """
        Sets the Person instance's L{Event} list to the passed list.

        @param event_list: List of valid L{Event} handles
        @type event_list: list
        """
        self.event_list = event_list

    def add_family_handle(self,family_handle):
        """
        Adds the L{Family} handle to the Person instance's L{Family} list.
        This is accomplished by assigning the handle of a valid L{Family}
        in the current database.

        Adding a L{Family} handle to a Person does not automatically update
        the corresponding L{Family}. The developer is responsible to make
        sure that when a L{Family} is added to Person, that the Person is
        assigned to either the father or mother role in the L{Family}.
        
        @param family_handle: handle of the L{Family} to be added to the
            Person's L{Family} list.
        @type family_handle: str
        """
        self.family_list.append(family_handle)

    def set_preferred_family_handle(self,family_handle):
        """
        Sets the family_handle specified to be the preferred L{Family}.
        The preferred L{Family} is determined by the first L{Family} in the
        L{Family} list, and is typically used to indicate the preferred
        L{Family} for navigation or reporting.
        
        The family_handle must already be in the list, or the function
        call has no effect.

        @param family_handle: Handle of the L{Family} to make the preferred
            L{Family}.
        @type family_handle: str
        @returns: True if the call succeeded, False if the family_handle
            was not already in the L{Family} list
        @rtype: bool
        """
        if family_handle in self.family_list:
            self.family_list.remove(family_handle)
            self.family_list = [family_handle] + self.family_list
            return True
        else:
            return False

    def get_family_handle_list(self) :
        """
        Returns the list of L{Family} handles in which the person is a
        parent or spouse.

        @return: Returns the list of handles corresponding to the
        L{Family} records with which the person is associated.
        @rtype: list
        """
        return self.family_list

    def set_family_handle_list(self,family_list) :
        """
        Assigns the passed list to the Person's list of families in
        which it is a parent or spouse.

        @param family_list: List of L{Family} handles to ba associated
            with the Person
        @type family_list: list 
        """
        self.family_list = family_list

    def clear_family_handle_list(self):
        """
        Removes all L{Family} handles from the L{Family} list.
        """
        self.family_list = []

    def remove_family_handle(self,family_handle):
        """
        Removes the specified L{Family} handle from the list
        of marriages/partnerships. If the handle does not
        exist in the list, the operation has no effect.

        @param family_handle: L{Family} handle to remove from the list
        @type family_handle: str

        @return: True if the handle was removed, False if it was not
            in the list.
        @rtype: bool
        """
        if family_handle in self.family_list:
            self.family_list.remove(family_handle)
            return True
        else:
            return False

    def add_address(self,address):
        """
        Adds the L{Address} instance to the Person's list of addresses

        @param address: L{Address} instance to add to the Person's address
            list
        @type address: list
        """
        self.address_list.append(address)

    def remove_address(self,address):
        """
        Removes the specified L{Address} instance from the address list
        If the instance does not exist in the list, the operation has
        no effect.

        @param address: L{Address} instance to remove from the list
        @type address: L{Address}

        @return: True if the address was removed, False if it was not
            in the list.
        @rtype: bool
        """
        if address in self.address_list:
            self.address_list.remove(address)
            return True
        else:
            return False

    def get_address_list(self):
        """
        Returns the list of L{Address} instances associated with the
        Person
        @return: Returns the list of L{Address} instances
        @rtype: list
        """
        return self.address_list

    def set_address_list(self,address_list):
        """
        Assigns the passed list to the Person's list of L{Address} instances.
        @param address_list: List of L{Address} instances to ba associated
            with the Person
        @type address_list: list
        """
        self.address_list = address_list

    def add_attribute(self,attribute):
        """
        Adds the L{Attribute} instance to the Person's list of attributes

        @param attribute: L{Attribute} instance to add to the Person's address
            list
        @type attribute: list
        """
        self.attribute_list.append(attribute)

    def remove_attribute(self,attribute):
        """
        Removes the specified L{Attribute} instance from the attribute list
        If the instance does not exist in the list, the operation has
        no effect.

        @param attribute: L{Attribute} instance to remove from the list
        @type attribute: L{Attribute}

        @return: True if the attribute was removed, False if it was not
            in the list.
        @rtype: bool
        """
        if attribute in self.attribute_list:
            self.attribute_list.remove(attribute)
            return True
        else:
            return False

    def get_attribute_list(self):
        """
        Returns the list of L{Attribute} instances associated with the
        Person
        @return: Returns the list of L{Attribute} instances
        @rtype: list
        """
        return self.attribute_list

    def set_attribute_list(self,attribute_list):
        """
        Assigns the passed list to the Person's list of L{Attribute} instances.

        @param attribute_list: List of L{Attribute} instances to ba associated
            with the Person
        @type attribute_list: list
        """
        self.attribute_list = attribute_list

    def get_parent_family_handle_list(self):
        """
        Returns the list of L{Family} handles in which the person is a
        child.

        @return: Returns the list of handles corresponding to the
        L{Family} records with which the person is a child.
        @rtype: list
        """
        return self.parent_family_list

    def add_parent_family_handle(self,family_handle,mrel,frel):
        """
        Adds the L{Family} handle to the Person instance's list of
        families in which it is a child. This is accomplished by
        assigning the handle of a valid L{Family} in the current database.

        Adding a L{Family} handle to a Person does not automatically update
        the corresponding L{Family}. The developer is responsible to make
        sure that when a L{Family} is added to Person, that the Person is
        added to the L{Family} instance's child list.
        
        @param family_handle: handle of the L{Family} to be added to the
            Person's L{Family} list.
        @type family_handle: str
        @param mrel: relationship between the Person and its mother
        @type mrel: str
        @param frel: relationship between the Person and its father
        @type frel: str
        """
        self.parent_family_list.append((family_handle,mrel,frel))

    def clear_parent_family_handle_list(self):
        """
        Removes all L{Family} handles from the parent L{Family} list.
        """
        self.parent_family_list = []

    def remove_parent_family_handle(self,family_handle):
        """
        Removes the specified L{Family} handle from the list of parent
        families (families in which the parent is a child). If the
        handle does not exist in the list, the operation has no effect.

        @param family_handle: L{Family} handle to remove from the list
        @type family_handle: str

        @return: Returns a tuple of three strings, consisting of the
            removed handle, relationship to mother, and relationship
            to father. None is returned if the handle is not in the
            list.
        @rtype: tuple
        """
        for f in self.parent_family_list[:]:
            if f[0] == family_handle:
                self.parent_family_list.remove(f)
                return f
        else:
            return None

    def change_parent_family_handle(self,family_handle,mrel,frel):
        """
        Changes the relationships of the L{Family} handle in the Person
        instance's list of families in which it is a child. The handle
        is assumed to already be in the list.
        
        @param family_handle: handle of the L{Family} to be added to the
            Person's L{Family} list.
        @type family_handle: str
        @param mrel: relationship between the Person and its mother
        @type mrel: str
        @param frel: relationship between the Person and its father
        @type frel: str
        """
        index=0
        for f in self.parent_family_list[:]:
            if f[0] == family_handle:
                self.parent_family_list[index] = (family_handle,mrel,frel)
                return True
            index += 1
        return False
    
    def get_parent_family(self,family_handle):
        """
        Finds the L{Family} and relationships associated with passed
        family_handle.

        @param family_handle: L{Family} handle used to search the parent
            family list.
        @type family_handle: str
        @return: Returns a tuple consisting of the L{Family} handle, the
            mother relationship, and father relationship
        @rtype: tuple
        """
        for f in self.parent_family_list:
            if f[0] == family_handle:
                return f
        else:
            return None

    def set_main_parent_family_handle(self,family_handle):
        """
        Sets the main L{Family} in which the Person is a child. The
        main L{Family} is the L{Family} typically used for reports and
        navigation. This is accomplished by moving the L{Family} to
        the beginning of the list. The family_handle must be in
        the list for this to have any effect.

        @param family_handle: handle of the L{Family} to be marked
            as the main L{Family}
        @type family_handle: str
        @return: Returns True if the assignment has successful
        @rtype: bool
        """
        f = self.remove_parent_family_handle(family_handle)
        if f:
            self.parent_family_list = [f] + self.parent_family_list
            return True
        else:
            return False
        
    def get_main_parents_family_handle(self):
        """
        Returns the handle of the L{Family} considered to be the main
        L{Family} in which the Person is a child.

        @return: Returns the family_handle if a family_handle exists,
            If no L{Family} is assigned, None is returned
        @rtype: str
        """
        if len(self.parent_family_list) == 0:
            return None
        else:
            return self.parent_family_list[0][0]

    def set_lds_baptism(self,lds_ord):
        """
        Sets the LDS Baptism ordinance. An ordinance can be removed
        by assigning to None.

        @param lds_ord: L{LdsOrd} to assign as the LDS Baptism ordinance.
        @type lds_ord: L{LdsOrd}
        """
        self.lds_bapt = lds_ord

    def get_lds_baptism(self):
        """
        Returns the LDS Baptism ordinance.

        @returns: returns the L{LdsOrd} instance assigned as the LDS
        Baptism ordinance, or None if no ordinance has been assigned.
        @rtype: L{LdsOrd}
        """
        return self.lds_bapt

    def set_lds_endowment(self,lds_ord):
        """
        Sets the LDS Endowment ordinance. An ordinance can be removed
        by assigning to None.

        @param lds_ord: L{LdsOrd} to assign as the LDS Endowment ordinance.
        @type lds_ord: L{LdsOrd}
        """
        self.lds_endow = lds_ord

    def get_lds_endowment(self):
        """
        Returns the LDS Endowment ordinance.

        @returns: returns the L{LdsOrd} instance assigned as the LDS
        Endowment ordinance, or None if no ordinance has been assigned.
        @rtype: L{LdsOrd}
        """
        return self.lds_endow

    def set_lds_sealing(self,lds_ord):
        """
        Sets the LDS Sealing ordinance. An ordinance can be removed
        by assigning to None.

        @param lds_ord: L{LdsOrd} to assign as the LDS Sealing ordinance.
        @type lds_ord: L{LdsOrd}
        """
        self.lds_seal = lds_ord

    def get_lds_sealing(self):
        """
        Returns the LDS Sealing ordinance.

        @returns: returns the L{LdsOrd} instance assigned as the LDS
        Sealing ordinance, or None if no ordinance has been assigned.
        @rtype: L{LdsOrd}
        """
        return self.lds_seal

class Family(PrimaryObject,SourceNote):
    """
    Introduction
    ============
    The Family record is the GRAMPS in-memory representation of the
    relationships between people. It contains all the information
    related to the relationship.
    
    Usage
    =====
    Family objects are usually created in one of two ways.

      1. Creating a new Family object, which is then initialized and
         added to the database.
      2. Retrieving an object from the database using the records
         handle.

    Once a Family object has been modified, it must be committed
    to the database using the database object's commit_family function,
    or the changes will be lost.
    """

    MARRIED     = 0
    UNMARRIED   = 1
    CIVIL_UNION = 2
    UNKNOWN     = 3
    OTHER       = 4
    
    def __init__(self):
        """
        Creates a new Family instance. After initialization, most
        data items have empty or null values, including the database
        handle.
        """
        PrimaryObject.__init__(self)
        SourceNote.__init__(self)
        self.father_handle = None
        self.mother_handle = None
        self.child_list = []
        self.type = Family.MARRIED
        self.event_list = []
        self.media_list = []
        self.attribute_list = []
        self.lds_seal = None
        self.complete = 0

    def serialize(self):
        """
        Converts the data held in the event to a Python tuple that
        represents all the data elements. This method is used to convert
        the object into a form that can easily be saved to a database.

        These elements may be primative Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objectes or
        lists), the database is responsible for converting the data into
        a form that it can use.

        @returns: Returns a python tuple containing the data that should
            be considered persistent.
        @rtype: tuple
        """
        return (self.handle, self.gramps_id, self.father_handle, self.mother_handle,
                self.child_list, self.type, self.event_list,
                self.media_list, self.attribute_list, self.lds_seal,
                self.complete, self.source_list, self.note,
                self.change)

    def unserialize(self, data):
        """
        Converts the data held in a tuple created by the serialize method
        back into the data in a Family structure.
        """
        (self.handle, self.gramps_id, self.father_handle, self.mother_handle,
         self.child_list, self.type, self.event_list,
         self.media_list, self.attribute_list, self.lds_seal,
         self.complete, self.source_list, self.note, self.change) = data

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = [self.lds_seal,self.note]
        add_list = [item for item in check_list if item]
        return self.media_list + self.attribute_list + \
	    	self.source_list + add_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        check_list = self.media_list + self.attribute_list
        if self.lds_seal:
            check_list.append(self.lds_seal)
        return check_list

    def set_complete_flag(self,val):
        """
        Sets or clears the complete flag, which is used to indicate that the
        Family's data is considered to be complete.

        @param val: True indicates the Family object is considered to be
            complete
        @type val: bool
        """
        self.complete = val

    def get_complete_flag(self):
        """
        Returns the complete flag, which is used to indicate that the
        Family's data is considered to be complete.

        @return: True indicates that the Family's record is considered to
            be complete.
        @rtype: bool
        """
        return self.complete

    def set_lds_sealing(self,lds_ord):
        """
        Sets the LDS Sealing ordinance. An ordinance can be removed
        by assigning to None.

        @param lds_ord: L{LdsOrd} to assign as the LDS Sealing ordinance.
        @type lds_ord: L{LdsOrd}
        """
        self.lds_seal = lds_ord

    def get_lds_sealing(self):
        """
        Returns the LDS Sealing ordinance.

        @returns: returns the L{LdsOrd} instance assigned as the LDS
        Sealing ordinance, or None if no ordinance has been assigned.
        @rtype: L{LdsOrd}
        """
        return self.lds_seal

    def add_attribute(self,attribute) :
        """
        Adds the L{Attribute} instance to the Family's list of attributes

        @param attribute: L{Attribute} instance to add to the Family's
            address list
        @type attribute: list
        """
        self.attribute_list.append(attribute)

    def remove_attribute(self,attribute):
        """
        Removes the specified L{Attribute} instance from the attribute list
        If the instance does not exist in the list, the operation has
        no effect.

        @param attribute: L{Attribute} instance to remove from the list
        @type attribute: L{Attribute}

        @return: True if the attribute was removed, False if it was not
            in the list.
        @rtype: bool
        """
        if attribute in self.attribute_list:
            self.attribute_list.remove(attribute)

    def get_attribute_list(self) :
        """
        Returns the list of L{Attribute} instances associated with the
        Famliy
        @return: Returns the list of L{Attribute} instances
        @rtype: list
        """
        return self.attribute_list

    def set_attribute_list(self,attribute_list) :
        """
        Assigns the passed list to the Family's list of L{Attribute} instances.

        @param attribute_list: List of L{Attribute} instances to ba associated
            with the Person
        @type attribute_list: list
        """
        self.attribute_list = attribute_list

    def set_relationship(self,relationship_type):
        """
        Sets the relationship type between the people identified as the
        father and mother in the relationship. The valid values are:

            - C{Family.MARRIED} : indicates a legally recognized married
                relationship between two individuals. This may be either
                an opposite or a same sex relationship.
            - C{Family.UNMARRIED} : indicates a relationship between two
                individuals that is not a legally recognized relationship.
            - C{Family.CIVIL_UNION} : indicates a legally recongnized,
                non-married relationship between two individuals of the
                same sex.
            - C{Family.UNKNOWN} : indicates that the type of relationship
                between the two individuals is not know.
            - C{Family.OTHER} : indicates that the type of relationship
                between the two individuals does not match any of the
                other types.

        @param relationship_type: Relationship type between the father
            and mother of the relationship.
        @type relationship_type: int
        """
        self.type = relationship_type

    def get_relationship(self):
        """
        Returns the relationship type between the people identified as the
        father and mother in the relationship.
        """
        return self.type
    
    def set_father_handle(self,person_handle):
        """
        Sets the database handle for L{Person} that corresponds to
        male of the relationship. For a same sex relationship, this
        can represent either of people involved in the relationship.

        @param person_handle: L{Person} database handle
        @type person_handle: str
        """
        self.father_handle = person_handle

    def get_father_handle(self):
        """
        Returns the database handle of the L{Person} identified as
        the father of the Family.

        @returns: L{Person} database handle
        @rtype: str
        """
        return self.father_handle

    def set_mother_handle(self,person_handle):
        """
        Sets the database handle for L{Person} that corresponds to
        male of the relationship. For a same sex relationship, this
        can represent either of people involved in the relationship.

        @param person_handle: L{Person} database handle
        @type person_handle: str
        """
        self.mother_handle = person_handle

    def get_mother_handle(self):
        """
        Returns the database handle of the L{Person} identified as
        the mother of the Family.

        @returns: L{Person} database handle
        @rtype: str
        """
        return self.mother_handle

    def add_child_handle(self,person_handle):
        """
        Adds the database handle for L{Person} to the Family's list
        of children.

        @param person_handle: L{Person} database handle
        @type person_handle: str
        """
        if person_handle not in self.child_list:
            self.child_list.append(person_handle)
            
    def remove_child_handle(self,person_handle):
        """
        Removes the database handle for L{Person} to the Family's list
        of children if the L{Person} is already in the list.

        @param person_handle: L{Person} database handle
        @type person_handle: str
        @return: True if the handle was removed, False if it was not
            in the list.
        @rtype: bool
        """
        if person_handle in self.child_list:
            self.child_list.remove(person_handle)
            return True
        else:
            return False

    def get_child_handle_list(self):
        """
        Returns the list of L{Person} handles identifying the children
        of the Family.

        @return: Returns the list of L{Person} handles assocated with
            the Family.
        @rtype: list
        """
        return self.child_list

    def set_child_handle_list(self, child_list):
        """
        Assigns the passed list to the Family's list children.

        @param child_list: List of L{Person} handles to ba associated
            as the Family's list of children.
        @type child_list: list of L{Person} handles
        """
        self.child_list = child_list

    def add_event_handle(self,event_handle):
        """
        Adds the L{Event} to the Family instance's L{Event} list. This is
        accomplished by assigning the handle of a valid L{Event} in the
        current database.
        
        @param event_handle: handle of the L{Event} to be added to the
            Person's L{Event} list.
        @type event_handle: str
        """
        self.event_list.append(event_handle)

    def get_event_list(self) :
        """
        Returns the list of handles associated with L{Event} instances.

        @returns: Returns the list of L{Event} handles associated with
            the Family instance.
        @rtype: list
        """
        return self.event_list

    def set_event_list(self,event_list) :
        """
        Sets the Family instance's L{Event} list to the passed list.

        @param event_list: List of valid L{Event} handles
        @type event_list: list
        """
        self.event_list = event_list

    def add_media_reference(self,media_ref):
        """
        Adds a L{MediaRef} instance to the Family's media list.

        @param media_ref: L{MediaRef} instance to be added to the Family's
            media list.
        @type media_ref: L{MediaRef}
        """
        self.media_list.append(media_ref)

    def get_media_list(self):
        """
        Returns the list of L{MediaRef} instances associated with the Family

        @returns: list of L{MediaRef} instances associated with the Family
        @rtype: list
        """
        return self.media_list

    def set_media_list(self,media_ref_list):
        """
        Sets the list of L{MediaRef} instances associated with the Person.
        It replaces the previous list.

        @param media_ref_list: list of L{MediaRef} instances to be assigned
            to the Person.
        @type media_ref_list: list
        """
        self.media_list = media_ref_list

class Event(PrimaryObject,DataObj):
    """
    Introduction
    ============
    The Event record is used to store information about some type of
    action that occurred at a particular place at a particular time,
    such as a birth, death, or marriage.
    """

    NAME = 0
    ID = 1
    
    def __init__(self,source=None):
        """
        Creates a new Event instance, copying from the source if present

        @param source: An event used to initialize the new event
        @type source: Event
        """

        PrimaryObject.__init__(self,source)
        DataObj.__init__(self,source)

        if source:
            self.place = source.place
            self.date = Date.Date(source.date)
            self.description = source.description
            self.name = source.name
            self.cause = source.cause
            self.media_list = [MediaRef(media_id) for media_id in source.media_list]
            if source.witness != None:
                self.witness = source.witness[:]
            else:
                self.witness = None
        else:
            self.place = u''
            self.date = None
            self.description = ""
            self.name = ""
            self.cause = ""
            self.witness = None
            self.media_list = []

    def serialize(self):
        """
        Converts the data held in the event to a Python tuple that
        represents all the data elements. This method is used to convert
        the object into a form that can easily be saved to a database.

        These elements may be primative Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objectes or
        lists), the database is responsible for converting the data into
        a form that it can use.

        @returns: Returns a python tuple containing the data that should
            be considered persistent.
        @rtype: tuple
        """
        return (self.handle, self.gramps_id, self.name, self.date,
                self.description, self.place, self.cause, self.private,
                self.source_list, self.note, self.witness, self.media_list,
                self.change)

    def unserialize(self,data):
        """
        Converts the data held in a tuple created by the serialize method
        back into the data in an Event structure.

        @param data: tuple containing the persistent data associated the
            Person object
        @type data: tuple
        """
        (self.handle, self.gramps_id, self.name, self.date, self.description,
         self.place, self.cause, self.private, self.source_list,
         self.note, self.witness, self.media_list, self.change) = data

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.description,self.name,self.cause]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.media_list + self.source_list
        if self.witness:
            check_list = check_list + self.witness
        if self.note:
            check_list.append(self.note)
        return check_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        return self.media_list

    def add_media_reference(self,media_ref):
        """
        Adds a L{MediaRef} instance to the object's media list.

        @param media_ref: L{MediaRef} instance to be added to the object's
            media list.
        @type media_ref: L{MediaRef}
        """
        self.media_list.append(media_ref)

    def get_media_list(self):
        """
        Returns the list of media references associated with the object.

        @return: Returns the list of L{MediaRef} objects assocated with
            the object.
        @rtype: list
        """
        return self.media_list

    def set_media_list(self,media_list):
        """
        Assigns the passed list to the Event's list of media references.

        @param media_list: List of media references to ba associated
            with the Event
        @type media_list: list of L{MediaRef} instances
        """
        self.media_list = media_list

    def get_witness_list(self):
        """
        Returns the list of L{Witness} instances associated with the Event.

        @return: Returns the list of L{Witness} objects assocated with
            the object.
        @rtype: list
        """
        return self.witness

    def set_witness_list(self,witness_list):
        """
        Assigns the passed list to the object's list of L{Witness}
        instances. To clear the list, None should be passed.

        @param witness_list: List of L{Witness} instances to ba associated
            with the Event.
        @type witness_list: list
        """
        if witness_list:
            self.witness = witness_list
        else:
            self.witness = None

    def add_witness(self,witness):
        """
        Adds the L{Witness} instance to the Event's witness list.

        @param witness: The L{Witness} instance to be added to the
            Event's list of L{Witness} instances.
        @type witness: L{Witness}
        """
        if self.witness:
            self.witness.append(witness)
        else:
            self.witness = [witness]
        
    def is_empty(self):
        """
        Returns True if the Event is an empty object (no values set).

        @returns: True if the Event is empty
        @rtype: bool
        """
        date = self.get_date_object()
        place = self.get_place_handle()
        description = self.description
        cause = self.cause
        name = self.name
        return ((not name or name == "Birth" or name == "Death") and 
                date.is_empty() and not place and not description and not cause)

    def are_equal(self,other):
        """
        Returns True if the passed Event is equivalent to the current Event.

        @param other: Event to compare against
        @type other: Event
        @returns: True if the Events are equal
        @rtype: bool
        """
        if other == None:
            other = Event (None)
        if (self.name != other.name or 
            ((self.place or other.place) and (self.place != other.place)) or
            self.description != other.description or self.cause != other.cause or
            self.private != other.private or
            (not self.get_date_object().is_equal(other.get_date_object())) or
            len(self.get_source_references()) != len(other.get_source_references())):
            return False

        index = 0
        olist = other.get_source_references()
        for a in self.get_source_references():
            if not a.are_equal(olist[index]):
                return False
            index += 1

        witness_list = self.get_witness_list()
        other_list = other.get_witness_list()
        if (not witness_list) and (not other_list):
            return True
        elif not (witness_list and other_list):
            return False
        for a in witness_list:
            if a in other_list:
                other_list.remove(a)
            else:
                return False
        if other_list:
            return False
        return True
        
    def set_name(self,name):
        """
        Sets the name of the Event to the passed string.

        @param name: Name to assign to the Event
        @type name: str
        """
        self.name = name

    def get_name(self):
        """
        Returns the name of the Event.

        @return: Name of the Event
        @rtype: str
        """
        return self.name

    def set_place_handle(self,place_handle):
        """
        Sets the database handle for L{Place} associated with the
        Event.

        @param place_handle: L{Place} database handle
        @type place_handle: str
        """
        self.place = place_handle

    def get_place_handle(self):
        """
        Returns the database handle of the L{Place} assocated with
        the Event.

        @returns: L{Place} database handle
        @rtype: str
        """
        return self.place 

    def set_cause(self,cause):
        """
        Sets the cause of the Event to the passed string. The string
        may contain any information.

        @param cause: Cause to assign to the Event
        @type cause: str
        """
        self.cause = cause

    def get_cause(self):
        """
        Returns the cause of the Event.

        @return: Returns the cause of the Event
        @rtype: str
        """
        return self.cause 

    def set_description(self,description):
        """
        Sets the description of the Event to the passed string. The string
        may contain any information.

        @param description: Description to assign to the Event
        @type description: str
        """
        self.description = description

    def get_description(self) :
        """
        Returns the description of the Event.

        @return: Returns the description of the Event
        @rtype: str
        """
        return self.description 

    def set_date(self, date) :
        """
        Sets the date of the Event instance. The date is parsed into
        a L{Date} instance.

        @param date: String representation of a date. The locale specific
            L{DateParser} is used to parse the string into a GRAMPS L{Date}
            object.
        @type date: str
        """
        self.date = DateHandler.parser.parse(date)

    def get_date(self) :
        """
        Returns a string representation of the date of the Event instance
        based off the default date display format determined by the
        locale's L{DateDisplay} instance.

        @return: Returns a string representing the Event's date
        @rtype: str
        """
        if self.date:
            return DateHandler.displayer.display(self.date)
        return u""

    def get_quote_date(self) :
        """
        Returns a string representation of the date of the Event instance
        based off the default date display format determined by the
        locale's L{DateDisplay} instance. The date is enclosed in
        quotes if the L{Date} is not a valid date.

        @return: Returns a string representing the Event's date
        @rtype: str
        """
        if self.date:
            return DateHandler.displayer.quote_display(self.date)
        return u""

    def get_date_object(self):
        """
        Returns the L{Date} object associated with the Event.

        @return: Returns a Event's L{Date} instance.
        @rtype: L{Date}
        """
        if not self.date:
            self.date = Date.Date()
        return self.date

    def set_date_object(self,date):
        """
        Sets the L{Date} object associated with the Event.

        @param date: L{Date} instance to be assigned to the Event
        @type date: L{Date}
        """
        self.date = date

class Place(PrimaryObject,SourceNote):
    """
    Contains information related to a place, including multiple address
    information (since place names can change with time), longitude, latitude,
    a collection of images and URLs, a note and a source
    """
    
    def __init__(self,source=None):
        """
        Creates a new Place object, copying from the source if present.

        @param source: A Place object used to initialize the new Place
        @type source: Place
        """
        PrimaryObject.__init__(self,source)
        SourceNote.__init__(self,source)
        if source:
            self.long = source.long
            self.lat = source.lat
            self.title = source.title
            self.main_loc = Location(source.main_loc)
            self.alt_loc = []
            for loc in source.alt_loc:
                self.alt_loc = Location(loc)
            self.urls = []
            for u in source.urls:
                self.urls.append(Url(u))
            self.media_list = []
            for media_id in source.media_list:
                self.media_list.append(MediaRef(media_id))
        else:
            self.long = ""
            self.lat = ""
            self.title = ""
            self.main_loc = None
            self.alt_loc = []
            self.urls = []
            self.media_list = []

    def serialize(self):
        """
        Converts the data held in the Place to a Python tuple that
        represents all the data elements. This method is used to convert
        the object into a form that can easily be saved to a database.

        These elements may be primative Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objectes or
        lists), the database is responsible for converting the data into
        a form that it can use.

        @returns: Returns a python tuple containing the data that should
            be considered persistent.
        @rtype: tuple
        """
        return (self.handle, self.gramps_id, self.title, self.long, self.lat,
                self.main_loc, self.alt_loc, self.urls, self.media_list,
                self.source_list, self.note, self.change)

    def unserialize(self,data):
        """
        Converts the data held in a tuple created by the serialize method
        back into the data in a Place object.

        @param data: tuple containing the persistent data associated the
            Person object
        @type data: tuple
        """
        (self.handle, self.gramps_id, self.title, self.long, self.lat,
         self.main_loc, self.alt_loc, self.urls, self.media_list,
         self.source_list, self.note, self.change) = data
            
    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.long,self.lat,self.title]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """

        check_list = [self.main_loc,self.note]
        add_list = [item for item in check_list if item]
        return self.media_list + self.source_list + self.alt_loc \
                + self.urls + add_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        return self.media_list

    def get_url_list(self):
        """
        Returns the list of L{Url} instances associated with the Place

        @returns: List of L{Url} instances
        @rtype: list
        """
        return self.urls

    def set_url_list(self,url_list):
        """
        Sets the list of L{Url} instances to passed the list.

        @param url_list: List of L{Url} instances
        @type url_list: list
        """
        self.urls = url_list

    def add_url(self,url):
        """
        Adds a L{Url} instance to the Place's list of L{Url} instances

        @param url: L{Url} instance to be added to the Place's list of
            related web sites.
        @type url: L{Url}
        """
        self.urls.append(url)
    
    def set_title(self,title):
        """
        Sets the descriptive title of the Place object

        @param title: descriptive title to assign to the Place
        @type title: str
        """
        self.title = title

    def get_title(self):
        """
        Returns the descriptive title of the Place object

        @returns: Returns the descriptive title of the Place
        @rtype: str
        """
        return self.title

    def set_longitude(self,longitude):
        """
        Sets the longitude of the Place object

        @param longitude: longitude to assign to the Place
        @type longitude: str
        """
        self.long = longitude

    def get_longitude(self):
        """
        Returns the longitude of the Place object

        @returns: Returns the longitude of the Place
        @rtype: str
        """
        return self.long

    def set_latitude(self,latitude):
        """
        Sets the latitude of the Place object

        @param latitude: latitude to assign to the Place
        @type latitude: str
        """
        self.lat = latitude

    def get_latitude(self):
        """
        Returns the latitude of the Place object

        @returns: Returns the latitude of the Place
        @rtype: str
        """
        return self.lat

    def get_main_location(self):
        """
        Returns the L{Location} object representing the primary information for the
        Place instance. If a L{Location} hasn't been assigned yet, an empty one is
        created.

        @returns: Returns the L{Location} instance representing the primary location
            information about the Place
        @rtype: L{Location}
        """
        if not self.main_loc:
            self.main_loc = Location()
        return self.main_loc

    def set_main_location(self,location):
        """
        Assigns the main location information about the Place to the L{Location}
        object passed

        @param location: L{Location} instance to assign to as the main information for
            the Place
        @type location: L{Location}
        """
        self.main_loc = location

    def get_alternate_locations(self):
        """
        Returns a list of alternate L{Location} objects the present alternate information
        about the current Place. A Place can have more than one L{Location}, since names
        and jurisdictions can change over time for the same place.

        @returns: Returns the alternate L{Location}s for the Place
        @rtype: list of L{Location} objects
        """
        return self.alt_loc

    def set_alternate_locations(self,location_list):
        """
        Replaces the current alternate L{Location} object list with the new one.

        @param location_list: The list of L{Location} objects to assign to the Place's
            internal list
        @type location_list: list of L{Location} objects
        """
        self.alt_loc = location_list

    def add_alternate_locations(self,location):
        """
        Adds a L{Location} object to the alternate location list

        @param location: L{Location} instance to add
        @type location: L{Location}
        """
        if location not in self.alt_loc:
            self.alt_loc.append(location)

    def add_media_reference(self,media_ref):
        """
        Adds a L{MediaRef} instance to the object's media list.

        @param media_ref: L{MediaRef} instance to be added to the objects's
            media list.
        @type media_ref: L{MediaRef}
        """
        self.media_list.append(media_ref)

    def get_media_list(self):
        """
        Returns the list of L{MediaRef} instances associated with the object

        @returns: list of L{MediaRef} instances associated with the object
        @rtype: list
        """
        return self.media_list

    def set_media_list(self,media_ref_list):
        """
        Sets the list of L{MediaRef} instances associated with the object.
        It replaces the previous list.

        @param media_ref_list: list of L{MediaRef} instances to be assigned
            to the object.
        @type media_ref_list: list
        """
        self.media_list = media_ref_list

    def get_display_info(self):
        """Gets the display information associated with the object. This includes
        the information that is used for display and for sorting. Returns a list
        consisting of 13 strings. These are: Place Title, Place ID, Main Location
        Parish, Main Location County, Main Location City, Main Location State/Province,
        Main Location Country, upper case Place Title, upper case Parish, upper
        case city, upper case county, upper case state, upper case country"""
        
        if self.main_loc:
            return [self.title,self.gramps_id,self.main_loc.parish,self.main_loc.city,
                    self.main_loc.county,self.main_loc.state,self.main_loc.country,
                    self.title.upper(), self.main_loc.parish.upper(),
                    self.main_loc.city.upper(), self.main_loc.county.upper(),
                    self.main_loc.state.upper(), self.main_loc.country.upper()]
        else:
            return [self.title,self.gramps_id,'','','','','',
                    self.title.upper(), '','','','','']
        
class MediaObject(PrimaryObject,SourceNote):
    """
    Containter for information about an image file, including location,
    description and privacy
    """
    
    def __init__(self,source=None):
        """
        Initialize a MediaObject. If source is not None, then object
        is initialized from values of the source object.

        @param source: Object used to initialize the new object
        @type source: MediaObject
        """
        PrimaryObject.__init__(self,source)
        SourceNote.__init__(self,source)

        self.attrlist = []
        if source:
            self.path = source.path
            self.mime = source.mime
            self.desc = source.desc
            self.thumb = source.thumb
            self.date = Date.Date(source.date)
            self.place = source.place
            for attr in source.attrlist:
                self.attrlist.append(Attribute(attr))
        else:
            self.path = ""
            self.mime = ""
            self.desc = ""
            self.date = None
            self.place = u""
            self.thumb = None

    def serialize(self):
        """
        Converts the data held in the event to a Python tuple that
        represents all the data elements. This method is used to convert
        the object into a form that can easily be saved to a database.

        These elements may be primative Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objectes or
        lists), the database is responsible for converting the data into
        a form that it can use.

        @returns: Returns a python tuple containing the data that should
            be considered persistent.
        @rtype: tuple
        """
        return (self.handle, self.gramps_id, self.path, self.mime,
                self.desc, self.attrlist, self.source_list, self.note,
                self.change, self.date, self.place)

    def unserialize(self,data):
        """
        Converts the data held in a tuple created by the serialize method
        back into the data in an Event structure.

        @param data: tuple containing the persistent data associated the object
        @type data: tuple
        """
        (self.handle, self.gramps_id, self.path, self.mime, self.desc,
         self.attrlist, self.source_list, self.note, self.change,
         self.date, self.place) = data
    

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.path,self.mime,self.desc]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.attrlist + self.source_list
        if self.note:
            check_list.append(self.note)
        return check_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        return self.attrlist

    def set_place_handle(self,place_handle):
        """
        Sets the handle of the L{Place} instance associated with the MediaRef

        @param place_handle: L{Place} database handle
        @type place_handle: str
        """
        self.place = place_handle

    def get_place_handle(self):
        """
        Returns the database handle of the L{Place} assocated with
        the object.

        @returns: L{Place} database handle
        @rtype: str
        """
        return self.place 

    def get_date(self) :
        """
        Returns a string representation of the date of the instance
        based off the default date display format determined by the
        locale's L{DateDisplay} instance.

        @return: Returns a string representing the object's date
        @rtype: str
        """
        if self.date:
            return DateHandler.displayer.display(self.date)
        return u""

    def get_date_object(self):
        """
        Returns the L{Date} instance associated with the object.

        @return: Returns the object's L{Date} instance.
        @rtype: L{Date}
        """
        if not self.date:
            self.date = Date.Date()
        return self.date

    def set_date(self, date) :
        """
        Sets the date of the object. The date is parsed into a L{Date} instance.

        @param date: String representation of a date. The locale specific
            L{DateParser} is used to parse the string into a GRAMPS L{Date}
            object.
        @type date: str
        """
        self.date = DateHandler.parser.parse(date)

    def set_date_object(self,date):
        """
        Sets the L{Date} instance associated with the object.

        @param date: L{Date} instance to be assigned to the object
        @type date: L{Date}
        """
        self.date = date

    def set_mime_type(self,type):
        """
        Sets the MIME type associated with the MediaObject

        @param type: MIME type to be assigned to the object
        @type type: str
        """
        self.mime = type

    def get_mime_type(self):
        """
        Returns the MIME type associated with the MediaObject

        @returns: Returns the associated MIME type
        @rtype: str
        """
        return self.mime
    
    def set_path(self,path):
        """set the file path to the passed path"""
        self.path = os.path.normpath(path)

    def get_path(self):
        """return the file path"""
        return self.path

    def set_description(self,text):
        """sets the description of the image"""
        self.desc = text

    def get_description(self):
        """returns the description of the image"""
        return self.desc

    def add_attribute(self,attr):
        """Adds a propery to the MediaObject object. This is not used by gramps,
        but provides a means for XML users to attach other properties to
        the image"""
        self.attrlist.append(attr)

    def get_attribute_list(self):
        """returns the property list associated with the image"""
        return self.attrlist

    def set_attribute_list(self,list):
        self.attrlist = list

class Source(PrimaryObject):
    """A record of a source of information"""
    
    def __init__(self):
        """creates a new Source instance"""
        PrimaryObject.__init__(self)
        self.title = ""
        self.author = ""
        self.pubinfo = ""
        self.note = Note()
        self.media_list = []
        self.datamap = {}
        self.abbrev = ""

    def serialize(self):
        return (self.handle, self.gramps_id, unicode(self.title),
                unicode(self.author), unicode(self.pubinfo),
                self.note, self.media_list, unicode(self.abbrev),
                self.change,self.datamap)

    def unserialize(self,data):
        """
        Converts the data held in a tuple created by the serialize method
        back into the data in an Event structure.
        """
        (self.handle, self.gramps_id, self.title, self.author,
         self.pubinfo, self.note, self.media_list,
         self.abbrev, self.change, self.datamap) = data
        
    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.title,self.author,self.pubinfo,self.abbrev]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.media_list
        if self.note:
            check_list.append(self.note)
        return check_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        return self.media_list

    def has_source_reference(self,src_handle) :
        """
        Returns True if any of the child objects has reference
        to this source handle.

        @param src_handle: The source handle to be checked.
        @type src_ref: str
        @return: Returns whether any of it's child objects has reference to this source handle.
        @rtype: bool
        """
        for item in self.get_sourcref_child_list():
            if item.has_source_reference(src_handle):
                return True

        return False

    def remove_source_references(self,src_handle_list):
        """
        Removes references to all source handles in the list
        in all child objects.

        @param src_handle_list: The list of source handles to be removed.
        @type src_handle_list: list
        """
        for item in self.get_sourcref_child_list():
            item.remove_source_references(src_handle_list)

    def add_media_reference(self,media_ref):
        """
        Adds a L{MediaRef} instance to the object's media list.

        @param media_ref: L{MediaRef} instance to be added to the objects's
            media list.
        @type media_ref: L{MediaRef}
        """
        self.media_list.append(media_ref)

    def get_media_list(self):
        """
        Returns the list of L{MediaRef} instances associated with the object

        @returns: list of L{MediaRef} instances associated with the object
        @rtype: list
        """
        return self.media_list

    def set_media_list(self,media_ref_list):
        """
        Sets the list of L{MediaRef} instances associated with the object.
        It replaces the previous list.

        @param media_ref_list: list of L{MediaRef} instances to be assigned
            to the object.
        @type media_ref_list: list
        """
        self.media_list = media_ref_list

    def get_data_map(self):
        """Returns the data map of attributes for the source"""
        return self.datamap

    def set_data_map(self,datamap):
        """Sets the data map of attributes for the source"""
        self.datamap = datamap

    def set_data_item(self,key,value):
        """Sets the particular data item in the attribute data map"""
        self.datamap[key] = value

    def set_title(self,title):
        """
        Sets the descriptive title of the Source object

        @param title: descriptive title to assign to the Source
        @type title: str
        """
        self.title = title

    def get_title(self):
        """
        Returns the descriptive title of the Place object

        @returns: Returns the descriptive title of the Place
        @rtype: str
        """
        return self.title

    def set_note(self,text):
        """sets the text of the note attached to the Source"""
        self.note.set(text)

    def get_note(self):
        """returns the text of the note attached to the Source"""
        return self.note.get()

    def set_note_format(self,val):
        """Set the note's format to the given value"""
        self.note.set_format(val)

    def get_note_format(self):
        """Return the current note's format"""
        return self.note.get_format()

    def set_note_object(self,obj):
        """sets the Note instance attached to the Source"""
        self.note = obj

    def get_note_object(self):
        """returns the Note instance attached to the Source"""
        return self.note

    def unique_note(self):
        """Creates a unique instance of the current note"""
        self.note = Note(self.note.get())

    def set_author(self,author):
        """sets the author of the Source"""
        self.author = author

    def get_author(self):
        """returns the author of the Source"""
        return self.author

    def set_publication_info(self,text):
        """sets the publication information of the Source"""
        self.pubinfo = text

    def get_publication_info(self):
        """returns the publication information of the Source"""
        return self.pubinfo

    def set_abbreviation(self,abbrev):
        """sets the title abbreviation of the Source"""
        self.abbrev = abbrev

    def get_abbreviation(self):
        """returns the title abbreviation of the Source"""
        return self.abbrev

class LdsOrd(SourceNote):
    """
    Class that contains information about LDS Ordinances. LDS
    ordinances are similar to events, but have very specific additional
    information related to data collected by the Church of Jesus Christ
    of Latter Day Saints (Morman church). The LDS church is the largest
    source of genealogical information in the United States.
    """
    def __init__(self,source=None):
        """Creates a LDS Ordinance instance"""
        SourceNote.__init__(self,source)
        
        if source:
            self.famc = source.famc
            self.date = Date.Date(source.date)
            self.temple = source.temple
            self.status = source.status
            self.place = source.place
        else:
            self.famc = None
            self.date = None
            self.temple = ""
            self.status = 0
            self.place = None

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.temple]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.source_list
        if self.note:
            check_list.append(self.note)
        return check_list

    def set_place_handle(self,place):
        """sets the Place database handle of the ordinance"""
        self.place = place

    def get_place_handle(self):
        """returns the Place handle of the ordinance"""
        return self.place 

    def set_family_handle(self,family):
        """Sets the Family database handle associated with the LDS ordinance"""
        self.famc = family

    def get_family_handle(self):
        """Gets the Family database handle associated with the LDS ordinance"""
        return self.famc

    def set_status(self,val):
        """
        Sets the status of the LDS ordinance. The status is a text string
        that matches a predefined set of strings."""
        self.status = val

    def get_status(self):
        """Gets the status of the LDS ordinance"""
        return self.status

    def set_date(self, date) :
        """
        Sets the date of the object. The date is parsed into a L{Date} instance.

        @param date: String representation of a date. The locale specific
            L{DateParser} is used to parse the string into a GRAMPS L{Date}
            object.
        @type date: str
        """
        if not self.date:
            self.date = Date.Date()
        DateHandler.parser.set_date(self.date,date)

    def get_date(self) :
        """
        Returns a string representation of the date of the instance
        based off the default date display format determined by the
        locale's L{DateDisplay} instance.

        @return: Returns a string representing the object's date
        @rtype: str
        """
        if self.date:
            return DateHandler.displayer.display(self.date)
        return u""

    def get_date_object(self):
        """
        Returns the L{Date} instance associated with the object.

        @return: Returns the object's L{Date} instance.
        @rtype: L{Date}
        """
        if not self.date:
            self.date = Date.Date()
        return self.date

    def set_date_object(self,date):
        """
        Sets the L{Date} instance associated with the object.

        @param date: L{Date} instance to be assigned to the object
        @type date: L{Date}
        """
        self.date = date

    def set_temple(self,temple):
        """Sets the temple assocated with the ordinance"""
        self.temple = temple

    def get_temple(self):
        """Gets the temple assocated with the ordinance"""
        return self.temple

    def is_empty(self):
        """Returns 1 if the ordidance is actually empty"""
        if (self.famc or 
                (self.date and not self.date.is_empty()) or 
                self.temple or 
                self.status or 
                self.place):
            return False
        else:
            return True
        
    def are_equal(self,other):
        """returns 1 if the specified ordinance is the same as the instance"""
        if other == None:
            return self.is_empty()
        if (self.famc != other.famc or
            self.place != other.place or
            self.status != other.status or
            self.temple != other.temple or
            not self.get_date_object().is_equal(other.get_date_object()) or
            len(self.get_source_references()) != len(other.get_source_references())):
            return False

        index = 0
        olist = other.get_source_references()
        for a in self.get_source_references():
            if not a.are_equal(olist[index]):
                return False
            index += 1
        return True

class Researcher:
    """Contains the information about the owner of the database"""
    
    def __init__(self):
        """Initializes the Researcher object"""
        self.name = ""
        self.addr = ""
        self.city = ""
        self.state = ""
        self.country = ""
        self.postal = ""
        self.phone = ""
        self.email = ""

    def get_name(self):
        """returns the database owner's name"""
        return self.name

    def get_address(self):
        """returns the database owner's address"""
        return self.addr

    def get_city(self):
        """returns the database owner's city"""
        return self.city

    def get_state(self):
        """returns the database owner's state"""
        return self.state

    def get_country(self):
        """returns the database owner's country"""
        return self.country

    def get_postal_code(self):
        """returns the database owner's postal code"""
        return self.postal

    def get_phone(self):
        """returns the database owner's phone number"""
        return self.phone

    def get_email(self):
        """returns the database owner's email"""
        return self.email

    def set(self,name,addr,city,state,country,postal,phone,email):
        """sets the information about the database owner"""
        if name:
            self.name = name.strip()
        if addr:
            self.addr = addr.strip()
        if city:
            self.city = city.strip()
        if state:
            self.state = state.strip()
        if country:
            self.country = country.strip()
        if postal:
            self.postal = postal.strip()
        if phone:
            self.phone = phone.strip()
        if email:
            self.email = email.strip()

class Location(BaseObject):
    """Provides information about a place, including city, county, state,
    and country. Multiple Location objects can represent the same place,
    since names of citys, countys, states, and even countries can change
    with time"""
    
    def __init__(self,source=None):
        """creates a Location object, copying from the source object if it exists"""
        if source:
            self.city = source.city
            self.parish = source.parish
            self.county = source.county
            self.state = source.state
            self.country = source.country
            self.postal = source.postal
            self.phone = source.phone
        else:
            self.city = ""
            self.parish = ""
            self.county = ""
            self.state = ""
            self.country = ""
            self.postal = ""
            self.phone = ""

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.city,self.parish,self.county,self.state,
                self.country,self.postal,self.phone]

    def is_empty(self):
        return not self.city and not self.county and not self.state and \
               not self.country and not self.postal and not self.phone
        
    def set_city(self,data):
        """sets the city name of the Location object"""
        self.city = data

    def get_postal_code(self):
        """returns the postal code of the Location object"""
        return self.postal

    def set_postal_code(self,data):
        """sets the postal code of the Location object"""
        self.postal = data

    def get_phone(self):
        """returns the phone number of the Location object"""
        return self.phone

    def set_phone(self,data):
        """sets the phone number of the Location object"""
        self.phone = data

    def get_city(self):
        """returns the city name of the Location object"""
        return self.city

    def set_parish(self,data):
        """sets the religious parish name"""
        self.parish = data

    def get_parish(self):
        """gets the religious parish name"""
        return self.parish

    def set_county(self,data):
        """sets the county name of the Location object"""
        self.county = data

    def get_county(self):
        """returns the county name of the Location object"""
        return self.county

    def set_state(self,data):
        """sets the state name of the Location object"""
        self.state = data

    def get_state(self):
        """returns the state name of the Location object"""
        return self.state

    def set_country(self,data):
        """sets the country name of the Location object"""
        self.country = data

    def get_country(self):
        """returns the country name of the Location object"""
        return self.country

class Note(BaseObject):
    """
    Introduction
    ============
    The Note class defines a text note. The note may be preformatted
    or 'flowed', which indicates that it text string is considered
    to be in paragraphs, separated by newlines.
    """
    
    def __init__(self,text = ""):
        """
        Creates a new Note object, initializing from the passed string.
        """
        self.text = text
        self.format = 0

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.text]

    def set(self,text):
        """
        Sets the text associated with the note to the passed string.

        @param text: Text string defining the note contents.
        @type text: str
        """
        self.text = text

    def get(self):
        """
        Return the text string associated with the note.
        @returns: Returns the text string defining the note contents.
        @rtype: str
        """
        return self.text

    def append(self,text):
        """
        Appends the specified text to the text associated with the note.

        @param text: Text string to be appended to the note.
        @type text: str
        """
        self.text = self.text + text

    def set_format(self,format):
        """
        Sets the format of the note to the passed value. The value can
        either indicate Flowed or Preformatted.

        @param format: 0 indicates Flowed, 1 indicates Preformated
        @type format: int
        """
        self.format = format

    def get_format(self):
        """
        Returns the format of the note. The value can either indicate
        Flowed or Preformatted.

        @returns: 0 indicates Flowed, 1 indicates Preformated
        @rtype: int
        """
        return self.format

class MediaRef(SourceNote):
    """Media reference class"""
    def __init__(self,source=None):

        SourceNote.__init__(self,source)

        self.attrlist = []
        if source:
            self.private = source.private
            self.ref = source.ref
            self.note = Note(source.note)
            for attr in source.attrlist:
                self.attrlist.append(Attribute(attr))
            self.rect = source.rect
        else:
            self.private = False
            self.ref = None
            self.note = None
            self.rect = None

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.attrlist + self.source_list
        if self.note:
            check_list.append(self.note)
        return check_list

    def get_sourcref_child_list(self):
        """
        Returns the list of child secondary objects that may refer sources.

        @return: Returns the list of child secondary child objects that may refer sources.
        @rtype: list
        """
        return self.attrlist

    def set_privacy(self,val):
        """
        Sets or clears the privacy flag of the data

        @param val: value to assign to the privacy flag. True indicates that the
           record is private, False indicates that it is public.
        @type val: bool
        """
        self.private = val

    def get_privacy(self):
        """
        Returns the privacy level of the data. 

        @returns: True indicates that the record is private
        @rtype: bool
        """
        return self.private

    def set_rectangle(self,coord):
        """Sets subection of an image"""
        self.rect = coord

    def get_rectangle(self):
        """Returns the subsection of an image"""
        return self.rect

    def set_reference_handle(self,obj_id):
        self.ref = obj_id

    def get_reference_handle(self):
        return self.ref

    def add_attribute(self,attr):
        """Adds a propery to the MediaObject object. This is not used by gramps,
        but provides a means for XML users to attach other properties to
        the image"""
        self.attrlist.append(attr)

    def get_attribute_list(self):
        """returns the property list associated with the image"""
        return self.attrlist

    def set_attribute_list(self,list):
        """sets the property list associated with the image"""
        self.attrlist = list

class Attribute(DataObj):
    """Provides a simple key/value pair for describing properties. Used
    by the Person and Family objects to store descriptive information."""
    
    def __init__(self,source=None):
        """creates a new Attribute object, copying from the source if provided"""
        DataObj.__init__(self,source)
        
        if source:
            self.type = source.type
            self.value = source.value
        else:
            self.type = ""
            self.value = ""

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.type,self.value]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.source_list
        if self.note:
            check_list.append(self.note)
        return check_list

    def set_type(self,val):
        """sets the type (or key) of the Attribute instance"""
        self.type = val

    def get_type(self):
        """returns the type (or key) or the Attribute instance"""
        return self.type

    def set_value(self,val):
        """sets the value of the Attribute instance"""
        self.value = val

    def get_value(self):
        """returns the value of the Attribute instance"""
        return self.value

class Address(DataObj):
    """Provides address information for a person"""

    def __init__(self,source=None):
        """Creates a new Address instance, copying from the source
        if provided"""
        DataObj.__init__(self,source)
        
        if source:
            self.street = source.street
            self.city = source.city
            self.state = source.state
            self.country = source.country
            self.postal = source.postal
            self.date = Date.Date(source.date)
            self.phone = source.phone
        else:
            self.street = ""
            self.city = ""
            self.state = ""
            self.country = ""
            self.postal = ""
            self.date = Date.Date()
            self.phone = ""

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.street,self.city,self.state,self.country,
                self.postal,self.phone]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.source_list
        if self.note:
            check_list.append(self.note)
        return check_list

    def set_date(self,date):
        """
        Sets the date of the object. The date is parsed into a L{Date} instance.

        @param date: String representation of a date. The locale specific
            L{DateParser} is used to parse the string into a GRAMPS L{Date}
            object.
        @type date: str
        """
        self.date = DateHandler.parser.parse(date)

    def get_date(self):
        """
        Returns a string representation of the date of the instance
        based off the default date display format determined by the
        locale's L{DateDisplay} instance.

        @return: Returns a string representing the object's date
        @rtype: str
        """
        if self.date:
            return DateHandler.displayer.display(self.date)
        return u""

    def get_date_object(self):
        """
        Returns the L{Date} instance associated with the object.

        @return: Returns the object's L{Date} instance.
        @rtype: L{Date}
        """
        return self.date

    def set_date_object(self,date):
        """
        Sets the L{Date} instance associated with the object.

        @param date: L{Date} instance to be assigned to the object
        @type date: L{Date}
        """
        self.date = date

    def set_street(self,val):
        """sets the street portion of the Address"""
        self.street = val

    def get_street(self):
        """returns the street portion of the Address"""
        return self.street

    def set_phone(self,val):
        """sets the phone number portion of the Address"""
        self.phone = val

    def get_phone(self):
        """returns the phone number portion of the Address"""
        return self.phone

    def set_city(self,val):
        """sets the city portion of the Address"""
        self.city = val

    def get_city(self):
        """returns the city portion of the Address"""
        return self.city

    def set_state(self,val):
        """sets the state portion of the Address"""
        self.state = val

    def get_state(self):
        """returns the state portion of the Address"""
        return self.state

    def set_country(self,val):
        """sets the country portion of the Address"""
        self.country = val

    def get_country(self):
        """returns the country portion of the Address"""
        return self.country

    def set_postal_code(self,val):
        """sets the postal code of the Address"""
        self.postal = val

    def get_postal_code(self):
        """returns the postal code of the Address"""
        return self.postal

class Name(DataObj):
    """Provides name information about a person. A person may have more
    that one name throughout his or her life."""

    DEF  = 0  # locale default
    LNFN = 1  # last name, first name
    FNLN = 2  # first name, last name
    
    def __init__(self,source=None):
        """creates a new Name instance, copying from the source if provided"""
        DataObj.__init__(self,source)
        
        if source:
            self.first_name = source.first_name
            self.surname = source.surname
            self.suffix = source.suffix
            self.title = source.title
            self.type = source.type
            self.prefix = source.prefix
            self.patronymic = source.patronymic
            self.sname = source.sname
            self.group_as = source.group_as
            self.sort_as = source.sort_as
            self.display_as = source.display_as
            if source.date:
                self.date = Date.Date(source.date)
            else:
                self.date = None
        else:
            self.first_name = ""
            self.surname = ""
            self.suffix = ""
            self.title = ""
            self.type = "Birth Name"
            self.prefix = ""
            self.patronymic = ""
            self.sname = '@'
            self.group_as = ""
            self.sort_as = self.DEF
            self.display_as = self.DEF
            self.date = None

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.first_name,self.surname,self.suffix,self.title,
                self.type,self.prefix,self.patronymic]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        check_list = self.source_list
        if self.note:
            check_list.append(self.note)
        return check_list

    def set_group_as(self,name):
        """
        Sets the grouping name for a person. Normally, this is the person's
        surname. However, some locales group equivalent names (e.g. Ivanova
        and Ivanov in Russian are usually considered equivalent.
        """
        if name == self.surname:
            self.group_as = ""
        else:
            self.group_as = name

    def get_group_as(self):
        """
        Returns the grouping name, which is used to group equivalent surnames.
        """
        return self.group_as

    def get_group_name(self):
        """
        Returns the grouping name, which is used to group equivalent surnames.
        """
        if self.group_as:
            return self.group_as
        else:
            return self.surname

    def set_sort_as(self,value):
        """
        Specifies the sorting method for the specified name. Typically the
        locale's default should be used. However, there may be names where
        a specific sorting structure is desired for a name. 
        """
        self.sort_as = value

    def get_sort_as(self):
        """
        Returns the selected sorting method for the name. The options are
        DEF (default for the current locale), LNFN (last name, first name),
        or FNLN (first name, last name).
        """
        return self.sort_as 

    def set_display_as(self,value):
        """
        Specifies the display format for the specified name. Typically the
        locale's default should be used. However, there may be names where
        a specific display format is desired for a name. 
        """
        self.display_as = value

    def get_display_as(self):
        """
        Returns the selected display format for the name. The options are
        DEF (default for the current locale), LNFN (last name, first name),
        or FNLN (first name, last name).
        """
        return self.display_as

    def get_surname_prefix(self):
        """
        Returns the prefix (or article) of a surname. The prefix is not
        used for sorting or grouping.
        """
        return self.prefix

    def set_surname_prefix(self,val):
        """
        Sets the prefix (or article) of a surname. Examples of articles
        would be 'de' or 'van'.
        """
        self.prefix = val

    def set_type(self,type):
        """sets the type of the Name instance"""
        self.type = type

    def get_type(self):
        """returns the type of the Name instance"""
        return self.type

    def build_sort_name(self):
        if self.surname:
            self.sname = "%-25s%-30s%s" % (self.surname,self.first_name,self.suffix)
        else:
            self.sname = "@"

    def set_first_name(self,name):
        """sets the given name for the Name instance"""
        self.first_name = name
        self.build_sort_name()

    def set_patronymic(self,name):
        """sets the patronymic name for the Name instance"""
        self.patronymic = name
        self.build_sort_name()

    def set_surname(self,name):
        """sets the surname (or last name) for the Name instance"""
        self.surname = name
        self.build_sort_name()

    def set_suffix(self,name):
        """sets the suffix (such as Jr., III, etc.) for the Name instance"""
        self.suffix = name
        self.build_sort_name()

    def get_sort_name(self):
        return self.sname
    
    def get_first_name(self):
        """returns the given name for the Name instance"""
        return self.first_name

    def get_patronymic(self):
        """returns the patronymic name for the Name instance"""
        return self.patronymic

    def get_surname(self):
        """returns the surname (or last name) for the Name instance"""
        return self.surname

    def get_upper_surname(self):
        """returns the surname (or last name) for the Name instance"""
        return self.surname.upper()

    def get_suffix(self):
        """returns the suffix for the Name instance"""
        return self.suffix

    def set_title(self,title):
        """sets the title (Dr., Reverand, Captain) for the Name instance"""
        self.title = title

    def get_title(self):
        """returns the title for the Name instance"""
        return self.title

    def get_name(self):
        """returns a name string built from the components of the Name
        instance, in the form of surname, Firstname"""

        if self.patronymic:
            first = "%s %s" % (self.first_name, self.patronymic)
        else:
            first = self.first_name
        if self.suffix:
            if self.prefix:
                return "%s %s, %s %s" % (self.prefix, self.surname, first, self.suffix)
            else:
                return "%s, %s %s" % (self.surname, first, self.suffix)
        else:
            if self.prefix:
                return "%s %s, %s" % (self.prefix,self.surname, first)
            else:
                return "%s, %s" % (self.surname, first)

    def get_upper_name(self):
        """returns a name string built from the components of the Name
        instance, in the form of surname, Firstname"""
        
        if self.patronymic:
            first = "%s %s" % (self.first_name, self.patronymic)
        else:
            first = self.first_name
        if self.suffix:
            if self.prefix:
                return "%s %s, %s %s" % (self.prefix.upper(), self.surname.upper(), first, self.suffix)
            else:
                return "%s, %s %s" % (self.surname.upper(), first, self.suffix)
        else:
            if self.prefix:
                return "%s %s, %s" % (self.prefix.upper(), self.surname.upper(), first)
            else:
                return "%s, %s" % (self.surname.upper(), first)

    def get_regular_name(self):
        """returns a name string built from the components of the Name
        instance, in the form of Firstname surname"""
        if self.patronymic:
            first = "%s %s" % (self.first_name, self.patronymic)
        else:
            first = self.first_name
        if (self.suffix == ""):
            if self.prefix:
                return "%s %s %s" % (first, self.prefix, self.surname)
            else:
                return "%s %s" % (first, self.surname)
        else:
            if self.prefix:
                return "%s %s %s, %s" % (first, self.prefix, self.surname, self.suffix)
            else:
                return "%s %s, %s" % (first, self.surname, self.suffix)

    def get_regular_upper_name(self):
        """returns a name string built from the components of the Name
        instance, in the form of Firstname surname"""
        if self.patronymic:
            first = "%s %s" % (self.first_name, self.patronymic)
        else:
            first = self.first_name
        if (self.suffix == ""):
            if self.prefix:
                return "%s %s %s" % (first, self.prefix.upper(), self.surname.upper())
            else:
                return "%s %s" % (first, self.surname.upper())
        else:
            if self.prefix:
                return "%s %s %s, %s" % (first, self.prefix.upper(), self.surname.upper(), self.suffix)
            else:
                return "%s %s, %s" % (first, self.surname.upper(), self.suffix)

    def is_equal(self,other):
        """
        compares to names to see if they are equal, return 0 if they
        are not
        """
        if self.first_name != other.first_name:
            return False
        if self.surname != other.surname:
            return False
        if self.patronymic != other.patronymic:
            return False
        if self.prefix != other.prefix:
            return False
        if self.suffix != other.suffix:
            return False
        if self.title != other.title:
            return False
        if self.type != other.type:
            return False
        if self.private != other.private:
            return False
        if self.get_note() != other.get_note():
            return False
        if len(self.get_source_references()) != len(other.get_source_references()):
            return False
        index = 0
        olist = other.get_source_references()
        for a in self.get_source_references():
            if not a.are_equal(olist[index]):
                return True
            index += 1
        return True

    def set_date(self, date) :
        """
        Sets the date of the L{Name} instance. The date is parsed into
        a L{Date} instance.

        @param date: String representation of a date. The locale specific
            L{DateParser} is used to parse the string into a GRAMPS L{Date}
            object.
        @type date: str
        """
        self.date = DateHandler.parser.parse(date)

    def get_date(self) :
        """
        Returns a string representation of the date of the L{Name} instance
        based off the default date display format determined by the
        locale's L{DateDisplay} instance.

        @return: Returns a string representing the L{Name}'s date
        @rtype: str
        """
        if self.date:
            return DateHandler.displayer.display(self.date)
        return u""

    def get_quote_date(self) :
        """
        Returns a string representation of the date of the L{Name} instance
        based off the default date display format determined by the
        locale's L{DateDisplay} instance. The date is enclosed in
        quotes if the L{Date} is not a valid date.

        @return: Returns a string representing the L{Name}'s date
        @rtype: str
        """
        if self.date:
            return DateHandler.displayer.quote_display(self.date)
        return u""

    def get_date_object(self):
        """
        Returns the L{Date} object associated with the L{Name}.

        @return: Returns a L{Name}'s L{Date} instance.
        @rtype: L{Date}
        """
        if not self.date:
            self.date = Date.Date()
        return self.date

    def set_date_object(self,date):
        """
        Sets the L{Date} object associated with the L{Name}.

        @param date: L{Date} instance to be assigned to the L{Name}
        @type date: L{Date}
        """
        self.date = date


class Url(BaseObject):
    """Contains information related to internet Uniform Resource Locators,
    allowing gramps to store information about internet resources"""

    def __init__(self,source=None):
        """creates a new URL instance, copying from the source if present"""
        if source:
            self.path = source.path
            self.desc = source.desc
            self.private = source.private
        else:
            self.path = ""
            self.desc = ""
            self.private = 0

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.path,self.desc]

    def set_privacy(self,val):
        """
        Sets or clears the privacy flag of the data

        @param val: value to assign to the privacy flag. True indicates that the
           record is private, False indicates that it is public.
        @type val: bool
        """
        self.private = val

    def get_privacy(self):
        """
        Returns the privacy level of the data. 

        @returns: True indicates that the record is private
        @rtype: bool
        """
        return self.private

    def set_path(self,path):
        """sets the URL path"""
        self.path = path

    def get_path(self):
        """returns the URL path"""
        return self.path

    def set_description(self,description):
        """sets the description of the URL"""
        self.desc = description

    def get_description(self):
        """returns the description of the URL"""
        return self.desc

    def are_equal(self,other):
        """returns 1 if the specified URL is the same as the instance"""
        if other == None:
            return 0
        if self.path != other.path:
            return 0
        if self.desc != other.desc:
            return 0
        return 1

class Witness(BaseObject):
    """
    The Witness class is used to represent a person who may or may
    not be in the database. If the person is in the database, the
    type will be Event.ID, and the value with be the database handle
    for the person. If the person is not in the database, the type
    will be Event.NAME, and the value will be a string representing
    the person's name.
    """
    def __init__(self,type=Event.NAME,val="",comment=""):
        self.set_type(type)
        self.set_value(val)
        self.set_comment(comment)
        self.private = False

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.val,self.comment]

    def set_privacy(self,val):
        """
        Sets or clears the privacy flag of the data

        @param val: value to assign to the privacy flag. True indicates that the
           record is private, False indicates that it is public.
        @type val: bool
        """
        self.private = val

    def get_privacy(self):
        """
        Returns the privacy level of the data. 

        @returns: True indicates that the record is private
        @rtype: bool
        """
        return self.private

    def set_type(self,type):
        self.type = type

    def get_type(self):
        return self.type

    def set_value(self,val):
        self.val = val

    def get_value(self):
        return self.val

    def set_comment(self,comment):
        self.comment = comment

    def get_comment(self):
        return self.comment

class SourceRef(BaseObject):
    """Source reference, containing detailed information about how a
    referenced source relates to it"""
    
    def __init__(self,source=None):
        """creates a new SourceRef, copying from the source if present"""
        if source:
            self.confidence = source.confidence
            self.ref = source.ref
            self.page = source.page
            self.date = Date.Date(source.date)
            self.comments = Note(source.comments.get())
            self.text = source.text
            self.private = source.private
        else:
            self.confidence = CONF_NORMAL
            self.ref = None
            self.page = ""
            self.date = Date.Date()
            self.comments = Note()
            self.text = ""
            self.private = False

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.page,self.text]

    def get_text_data_child_list(self):
        """
        Returns the list of child objects that may carry textual data.

        @return: Returns the list of child objects that may carry textual data.
        @rtype: list
        """
        return [self.comments]

    def set_privacy(self,val):
        """
        Sets or clears the privacy flag of the data

        @param val: value to assign to the privacy flag. True indicates that the
           record is private, False indicates that it is public.
        @type val: bool
        """
        self.private = val

    def get_privacy(self):
        """
        Returns the privacy level of the data. 

        @returns: True indicates that the record is private
        @rtype: bool
        """
        return self.private

    def set_confidence_level(self,val):
        """Sets the confidence level"""
        self.confidence = val

    def get_confidence_level(self):
        """Returns the confidence level"""
        return self.confidence
        
    def set_base_handle(self,ref):
        """sets the Source instance to which the SourceRef refers"""
        self.ref = ref

    def get_base_handle(self):
        """returns the Source instance to which the SourceRef refers"""
        return self.ref
    
    def set_date(self,date):
        """sets the Date instance of the SourceRef"""
        self.date = date

    def get_date(self):
        """returns the Date instance of the SourceRef"""
        return self.date

    def set_page(self,page):
        """sets the page indicator of the SourceRef"""
        self.page = page

    def get_page(self):
        """gets the page indicator of the SourceRef"""
        return self.page

    def set_text(self,text):
        """sets the text related to the SourceRef"""
        self.text = text

    def get_text(self):
        """returns the text related to the SourceRef"""
        return self.text

    def set_note_object(self,note):
        """Change the Note instance to obj"""
        self.comments = note

    def set_comments(self,comments):
        """sets the comments about the SourceRef"""
        self.comments.set(comments)

    def get_comments(self):
        """returns the comments about the SourceRef"""
        return self.comments.get()

    def are_equal(self,other):
        """returns True if the passed SourceRef is equal to the current"""
        if self.ref and other.ref:
            if self.page != other.page:
                return False
            if self.date != other.date:
                return False
            if self.get_text() != other.get_text():
                return False
            if self.get_comments() != other.get_comments():
                return False
            if self.confidence != other.confidence:
                return False
            return True
        elif not self.ref and not other.ref:
            return True
        else:
            return False
        
    def unique_note(self):
        """Creates a unique instance of the current note"""
        self.comments = Note(self.comments.get())

class GenderStats:
    """
    Class for keeping track of statistics related to Given Name vs.
    Gender. This allows the tracking of the liklihood of a person's
    given name indicating the gender of the person.
    """
    def __init__ (self,stats={}):
        if stats == None:
            self.stats = {}
        else:
            self.stats = stats

    def save_stats(self):
        return self.stats

    def _get_key (self, person):
        name = person.get_primary_name().get_first_name()
        return self._get_key_from_name (name)

    def _get_key_from_name (self, name):
        return name.split (' ')[0].replace ('?', '')

    def name_stats (self, name):
        if self.stats.has_key (name):
            return self.stats[name]
        return (0, 0, 0)

    def count_person (self, person, db, undo = 0):
        # Let the Person do their own counting later
        person.db = db

        name = self._get_key (person)
        if not name:
            return

        gender = person.get_gender()
        (male, female, unknown) = self.name_stats (name)
        if not undo:
            increment = 1
        else:
            increment = -1

        if gender == Person.MALE:
            male += increment
        elif gender == Person.FEMALE:
            female += increment
        elif gender == Person.UNKNOWN:
            unknown += increment

        self.stats[name] = (male, female, unknown)
        return

    def uncount_person (self, person):
        return self.count_person (person, None, undo = 1)

    def guess_gender (self, name):
        name = self._get_key_from_name (name)
        if not name or not self.stats.has_key (name):
            return Person.UNKNOWN

        (male, female, unknown) = self.stats[name]
        if unknown == 0:
            if male and not female:
                return Person.MALE
            if female and not male:
                return Person.FEMALE

        if male > (2 * female):
            return Person.MALE

        if female > (2 * male):
            return Person.FEMALE

        return Person.UNKNOWN
