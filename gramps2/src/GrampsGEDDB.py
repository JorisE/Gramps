#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2004  Donald N. Allingham
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

from RelLib import *
from GrampsInMemDB import *

import ReadGedcom
import WriteGedcom

#-------------------------------------------------------------------------
#
# GrampsGEDDB
#
#-------------------------------------------------------------------------
class GrampsGEDDB(GrampsInMemDB):
    """GRAMPS database object. This object is a base class for other
    objects."""

    def __init__(self):
        """creates a new GrampsDB"""
        GrampsInMemDB.__init__(self)

    def load(self,name,callback):
        self.filename = name
        ReadGedcom.importData(self,name,use_trans=False)

        self.bookmarks = self.metadata.get('bookmarks')
        if self.bookmarks == None:
            self.bookmarks = []
        return 1

    def close(self):
        if len(self.undodb) > 0:
            writer = WriteGedcom.GedcomWriter(self,self.get_default_person())
            writer.export_data(self.filename)

