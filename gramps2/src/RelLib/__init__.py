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

"""The core library of GRAMPS objects"""

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

# Secondary objects
from _Address import Address
from _Location import Location
from _Attribute import Attribute
from _EventRef import EventRef
from _LdsOrd import LdsOrd
from _MediaRef import MediaRef 
from _Name import Name
from _Note import Note
from _RepoRef import RepoRef
from _SourceRef import SourceRef
from _Url import Url
from _Witness import Witness

# Primary objects
from _PrimaryObject import PrimaryObject
from _Person import Person
from _Family import Family
from _Event import Event
from _Place import Place
from _Source import Source
from _MediaObject import MediaObject
from _Repository import Repository

# These are actually metadata
from _GenderStats import GenderStats
from _Researcher import Researcher
