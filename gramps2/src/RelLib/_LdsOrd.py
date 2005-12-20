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

"""
LDS Ordinance class for GRAMPS
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from _SourceNote import SourceNote
from _DateBase import DateBase
from _PlaceBase import PlaceBase

#-------------------------------------------------------------------------
#
# LDS Ordinance class
#
#-------------------------------------------------------------------------
class LdsOrd(SourceNote,DateBase,PlaceBase):
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
        DateBase.__init__(self,source)
        PlaceBase.__init__(self,source)
        
        if source:
            self.famc = source.famc
            self.temple = source.temple
            self.status = source.status
        else:
            self.famc = None
            self.temple = ""
            self.status = 0

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.temple]
        #return [self.temple,self.get_date()]

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

    def get_referenced_handles(self):
        """
        Returns the list of (classname,handle) tuples for all directly
        referenced primary objects.
        
        @return: Returns the list of (classname,handle) tuples for referenced objects.
        @rtype: list
        """
        if self.place:
            return [('Place',self.place)]
        else:
            return []

    def get_handle_referents(self):
        """
        Returns the list of child objects which may, directly or through
        their children, reference primary objects..
        
        @return: Returns the list of objects refereincing primary objects.
        @rtype: list
        """
        return self.source_list

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
