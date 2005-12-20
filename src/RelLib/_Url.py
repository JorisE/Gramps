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
Url class for GRAMPS
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
from _BaseObject import BaseObject
from _PrivacyBase import PrivacyBase

#-------------------------------------------------------------------------
#
# Url for Person/Place/Repository
#
#-------------------------------------------------------------------------
class Url(BaseObject,PrivacyBase):
    """Contains information related to internet Uniform Resource Locators,
    allowing gramps to store information about internet resources"""

    UNKNOWN    = -1
    CUSTOM     = 0
    EMAIL      = 1
    WEB_HOME   = 2
    WEB_SEARCH = 3
    WEB_FTP    = 4
    
    def __init__(self,source=None):
        """creates a new URL instance, copying from the source if present"""
        BaseObject.__init__(self)
        PrivacyBase.__init__(self,source)
        if source:
            self.path = source.path
            self.desc = source.desc
            self.type = source.type
        else:
            self.path = ""
            self.desc = ""
            self.type = (Url.CUSTOM,"")

    def get_text_data_list(self):
        """
        Returns the list of all textual attributes of the object.

        @return: Returns the list of all textual attributes of the object.
        @rtype: list
        """
        return [self.path,self.desc]

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

    def set_type(self,the_type):
        """
        @param type: descriptive type of the Url
        @type type: str
        """
        if not type(the_type) == tuple:
            warn( "set_type now takes a tuple", DeprecationWarning, 2)
            # Wrapper for old API
            # remove when transitition done.
            if the_type in range(-1,5):
                the_type = (the_type,'')
            else:
                the_type = (Url.CUSTOM,the_type)
        self.type = the_type

    def get_type(self):
        """
        @returns: the descriptive type of the Url
        @rtype: str
        """
        return self.type

    def are_equal(self,other):
        """returns 1 if the specified URL is the same as the instance"""
        if other == None:
            return 0
        if self.path != other.path:
            return 0
        if self.desc != other.desc:
            return 0
        if self.type != other.type:
            return 0
        return 1
