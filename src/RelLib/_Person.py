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

# $Id$

"""
Person object for GRAMPS
"""

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
from warnings import warn

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from _PrimaryObject import PrimaryObject
from _SourceNote import SourceNote
from _MediaBase import MediaBase
from _AttributeBase import AttributeBase
from _AddressBase import AddressBase
from _UrlBase import UrlBase
from _Name import Name
from _EventRef import EventRef
from _LdsOrd import LdsOrd

#-------------------------------------------------------------------------
#
# Person class
#
#-------------------------------------------------------------------------
class Person(PrimaryObject,SourceNote,
             MediaBase,AttributeBase,AddressBase,UrlBase):
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
    MALE    = 1
    FEMALE  = 0
    
    CHILD_NONE      = 0
    CHILD_BIRTH     = 1
    CHILD_ADOPTED   = 2
    CHILD_STEPCHILD = 3
    CHILD_SPONSORED = 4
    CHILD_FOSTER    = 5
    CHILD_UNKNOWN   = 6
    CHILD_CUSTOM    = 7

    def __init__(self,data=None):
        """
        Creates a new Person instance. After initialization, most
        data items have empty or null values, including the database
        handle.
        """
        PrimaryObject.__init__(self)
        SourceNote.__init__(self)
        MediaBase.__init__(self)
        AttributeBase.__init__(self)
        AddressBase.__init__(self)
        UrlBase.__init__(self)
        self.primary_name = Name()
        self.event_ref_list = []
        self.family_list = []
        self.parent_family_list = []
        self.nickname = ""
        self.alternate_names = []
        self.gender = Person.UNKNOWN
        self.death_ref = None
        self.birth_ref = None
        self.lds_bapt = None
        self.lds_endow = None
        self.lds_seal = None

        if data:
            self.unserialize(data)
        
        # We hold a reference to the GrampsDB so that we can maintain
        # its genderStats.  It doesn't get set here, but from
        # GenderStats.count_person.
        
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
        if self.birth_ref == None:
            birth_ref = None
        else:
            birth_ref = self.birth_ref.serialize()
        if self.death_ref == None:
            death_ref = None
        else:
            death_ref = self.death_ref.serialize()
        if self.lds_bapt == None:
            lds_bapt = None
        else:
            lds_bapt = self.lds_bapt.serialize()
        if self.lds_endow == None:
            lds_endow = None
        else:
            lds_endow = self.lds_endow.serialize()
        if self.lds_seal == None:
            lds_seal = None
        else:
            lds_seal = self.lds_seal.serialize()

        return (self.handle, self.gramps_id, self.gender, 
                self.primary_name.serialize(),
                [name.serialize() for name in self.alternate_names],
                unicode(self.nickname), death_ref, birth_ref,
                [er.serialize() for er in self.event_ref_list],
                self.family_list,self.parent_family_list,
                MediaBase.serialize(self),
                AddressBase.serialize(self),
                AttributeBase.serialize(self),
                UrlBase.serialize(self),
                lds_bapt, lds_endow, lds_seal,
                SourceNote.serialize(self),
                self.change, self.marker,
                self.private)

    def unserialize(self,data):
        """
        Converts the data held in a tuple created by the serialize method
        back into the data in a Person object.

        @param data: tuple containing the persistent data associated the
            Person object
        @type data: tuple
        """
        (self.handle, self.gramps_id, self.gender, primary_name,
         alternate_names, self.nickname, death_ref,
         birth_ref, event_ref_list, self.family_list,
         self.parent_family_list, media_list, address_list,
         attribute_list, urls, lds_bapt, lds_endow,
         lds_seal, sn, self.change,
         self.marker, self.private) = (data + (False,))[0:22]

        self.primary_name.unserialize(primary_name)
        if death_ref:
            self.death_ref = EventRef().unserialize(death_ref)
        if birth_ref:
            self.birth_ref = EventRef().unserialize(birth_ref)
        if lds_bapt:
            self.lds_bapt = LdsOrd().unserialize(lds_bapt)
        if lds_endow:
            self.lds_endow = LdsOrd().unserialize(lds_endow)
        if lds_seal:
            self.lds_seal = LdsOrd().unserialize(lds_seal)
        self.alternate_names = [Name().unserialize(name)
                                for name in alternate_names]
        self.event_ref_list = [EventRef().unserialize(er)
                               for er in event_ref_list]
        MediaBase.unserialize(self,media_list)
        AddressBase.unserialize(self,address_list)
        AttributeBase.unserialize(self,attribute_list)
        UrlBase.unserialize(self,urls)
        SourceNote.unserialize(self,sn)
            
    def _has_handle_reference(self,classname,handle):
        if classname == 'Event':
            return handle in [ref.ref for ref in
                              self.event_ref_list + [self.birth_ref,
                                                     self.death_ref]
                              if ref]
        elif classname == 'Family':
            return handle in self.family_list + \
                        [item[0] for item in self.parent_family_list ]
        elif classname == 'Place':
            return handle in [ordinance.place 
                for ordinance in [self.lds_bapt,self.lds_endow,self.lds_seal]
                if ordinance]
        return False

    def _remove_handle_references(self,classname,handle_list):
        if classname == 'Event':
            new_list = [ ref for ref in self.event_ref_list \
                                        if ref and ref.ref not in handle_list ]
            self.event_ref_list = new_list
            if self.death_ref and self.death_ref.ref in handle_list:
                self.death_ref = None
            if self.birth_ref and self.birth_ref.ref in handle_list:
                self.birth_ref = None
        elif classname == 'Family':
            new_list = [ handle for handle in self.family_list \
                                        if handle not in handle_list ]
            self.family_list = new_list
            new_list = [ item for item in self.parent_family_list \
                                        if item[0] not in handle_list ]
            self.parent_family_list = new_list
        elif classname == 'Place':
            for ordinance in [self.lds_bapt,self.lds_endow,self.lds_seal]:
                if ordinance.place in handle_list:
                    ordinance.place == None

    def _replace_handle_reference(self,classname,old_handle,new_handle):
        if classname == 'Event':
            handle_list = [ref.ref for ref in self.event_ref_list]
            while old_handle in handle_list:
                ix = handle_list.index(old_handle)
                self.event_ref_list[ix].ref = new_handle
                handle_list[ix] = ''
            if self.death_ref and self.death_ref.ref == old_handle:
                self.death_ref.ref = new_handle
            if self.birth_ref and self.birth_ref.ref == old_handle:
                self.birth_ref.ref = new_handle
        elif classname == 'Family':
            while old_handle in self.family_list:
                ix = self.family_list.index(old_handle)
                self.family_list[ix] = new_handle

            new_list = []
            for item in self.parent_family_list:
                if item[0] == old_handle:
                    new_list.append((new_handle,item[1],item[2]))
                else:
                    new_list.append(item)
            self.parent_family_list = new_list
        elif classname == 'Place':
            for ordinance in [self.lds_bapt,self.lds_endow,self.lds_seal]:
                if ordinance.place == old_handle:
                    ordinance.place == new_handle

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.nickname,self.gramps_id]

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
                    self.source_list + self.event_ref_list + add_list

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

    def get_referenced_handles(self):
        """
        Returns the list of (classname,handle) tuples for all directly
        referenced primary objects.
        
        @return: Returns the list of (classname,handle) tuples for referenced objects.
        @rtype: list
        """
        return [('Family',handle) for handle in self.family_list 
                        + [item[0] for item in self.parent_family_list]]

    def get_handle_referents(self):
        """
        Returns the list of child objects which may, directly or through
        their children, reference primary objects..
        
        @return: Returns the list of objects refereincing primary objects.
        @rtype: list
        """
        birth_death = [item for item in [birth_ref,death_ref] if item]
        return self.get_sourcref_child_list() + self.source_list \
               + self.event_ref_list + birth_death

    def set_complete_flag(self,val):
        warn( "Use set_marker instead of set_complete_flag", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        if val:
            self.marker = (PrimaryObject.MARKER_COMPLETE, "")
        else:
            self.marker = (PrimaryObject.MARKER_NONE, "")

    def get_complete_flag(self):
        warn( "Use get_marker instead of get_complete_flag", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        return self.marker[0] == PrimaryObject.MARKER_COMPLETE

    def set_primary_name(self,name):
        """
        Sets the primary name of the Person to the specified
        L{Name} instance

        @param name: L{Name} to be assigned to the person
        @type name: L{Name}
        """
        self.primary_name = name

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
        self.gender = gender

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
        warn( "Use set_birth_ref instead of set_birth_handle", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        event_ref = EventRef()
        event_ref.set_reference_handle(event_handle)
        event_ref.set_role((EventRef.PRIMARY,''))
        self.set_birth_ref( event_ref)

    def set_birth_ref(self,event_ref):
        """
        Assigns the birth event to the Person object. This is accomplished
        by assigning the L{EventRef} of the birth event in the current
        database.

        @param event_ref: the L{EventRef} object associated with
            the Person's birth.
        @type event_handle: EventRef
        """
        if event_ref is not None and not isinstance(event_ref,EventRef):
            raise ValueError("Expecting EventRef instance")
        self.birth_ref = event_ref

    def set_death_handle(self,event_handle):
        warn( "Use set_death_ref instead of set_death_handle", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        event_ref = EventRef()
        event_ref.set_reference_handle(event_handle)
        event_ref.set_role((EventRef.PRIMARY,''))
        self.set_death_ref( event_ref)

    def set_death_ref(self,event_ref):
        """
        Assigns the death event to the Person object. This is accomplished
        by assigning the L{EventRef} of the death event in the current
        database.

        @param event_ref: the L{EventRef} object associated with
            the Person's death.
        @type event_handle: EventRef
        """
        if event_ref is not None and not isinstance(event_ref,EventRef):
            raise ValueError("Expecting EventRef instance")
        self.death_ref = event_ref

    def get_birth_handle(self):
        warn( "Use get_birth_ref instead of get_birth_handle", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        event_ref = self.get_birth_ref()
        if event_ref:
            return event_ref.get_reference_handle()
        return ""

    def get_birth_ref(self):
        """
        Returns the L{EventRef} for Person's birth event. This
        should correspond to an L{Event} in the database's L{Event} list.

        @returns: Returns the birth L{EventRef} or None if no birth
            L{Event} has been assigned.
        @rtype: EventRef
        """
        return self.birth_ref

    def get_death_handle(self):
        warn( "Use get_death_ref instead of get_death_handle", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        event_ref = self.get_death_ref()
        if event_ref:
            return event_ref.get_reference_handle()
        return ""

    def get_death_ref(self):
        """
        Returns the L{EventRef} for the Person's death event. This
        should correspond to an L{Event} in the database's L{Event} list.

        @returns: Returns the death L{EventRef} or None if no death
            L{Event} has been assigned.
        @rtype: event_ref
        """
        return self.death_ref

    def add_event_handle(self,event_handle):
        warn( "Use add_event_ref instead of add_event_handle", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        event_ref = EventRef()
        event_ref.set_reference_handle(event_handle)
        event_ref.set_role((EventRef.PRIMARY,''))
        self.add_event_ref( event_ref)

    def add_event_ref(self,event_ref):
        """
        Adds the L{EventRef} to the Person instance's L{EventRef} list.
        This is accomplished by assigning the L{EventRef} of a valid
        L{Event} in the current database.
        
        @param event_ref: the L{EventRef} to be added to the
            Person's L{EventRef} list.
        @type event_ref: EventRef
        """
        if event_ref is not None and not isinstance(event_ref,EventRef):
            raise ValueError("Expecting EventRef instance")
        self.event_ref_list.append(event_ref)

    def get_event_list(self):
        warn( "Use get_event_ref_list instead of get_event_list", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        event_handle_list = []
        for event_ref in self.get_event_ref_list():
            event_handle_list.append( event_ref.get_reference_handle())
        return event_handle_list

    def get_event_ref_list(self):
        """
        Returns the list of L{EventRef} objects associated with L{Event}
        instances.

        @returns: Returns the list of L{EventRef} objects associated with
            the Person instance.
        @rtype: list
        """
        return self.event_ref_list

    def set_event_list(self,event_list):
        warn( "Use set_event_ref_list instead of set_event_list", DeprecationWarning, 2)
        # Wrapper for old API
        # remove when transitition done.
        event_ref_list = []
        for event_handle in event_list:
            event_ref = EventRef()
            event_ref.set_reference_handle(event_handle)
            event_ref.set_role((EventRef.PRIMARY,''))
            event_ref_list.append( event_ref)
        self.set_event_ref_list(event_ref_list)

    def set_event_ref_list(self,event_ref_list):
        """
        Sets the Person instance's L{EventRef} list to the passed list.

        @param event_ref_list: List of valid L{EventRef} objects
        @type event_ref_list: list
        """
        self.event_ref_list = event_ref_list

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
        @type mrel: tuple
        @param frel: relationship between the Person and its father
        @type frel: tuple
        """
        if not type(mrel) == tuple:
            if mrel in range(0,8):
                warn( "add_parent_family_handle now takes a tuple", DeprecationWarning, 2)
                # Wrapper for old API
                # remove when transitition done.
                mrel = (mrel,'')
            else:
                assert type(mrel) == tuple
        if not type(frel) == tuple:
            if frel in range(0,8):
                warn( "add_parent_family_handle now takes a tuple", DeprecationWarning, 2)
                # Wrapper for old API
                # remove when transitition done.
                frel = (frel,'')
            else:
                assert type(frel) == tuple
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
        @type mrel: tuple
        @param frel: relationship between the Person and its father
        @type frel: tuple
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
