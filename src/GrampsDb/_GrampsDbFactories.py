#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2005 Donald N. Allingham
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
This module contains factory methods for accessing the different
GrampsDb backends. These methods should be used obtain the correct class
for a database backend.

The app_* constants in const.py can be used to indicate which backend is
required e.g.:

>     # To get the class for the grdb backend
>     db_class = GrampsDb.gramps_db_factory(db_type = const.APP_GRAMPS)
>
>     # To get a XML writer
>     GrampsDb.gramps_db_writer_factory(db_type = const.APP_GRAMPS_XML)
>
>     # To get a Gedcom reader
>     GrampsDb.gramps_db_reader_factory(db_type = const.APP_GEDCOM)
     
"""
import gen.db.dbconst as const
from gen.db.exceptions import GrampsDbException

import logging
log = logging.getLogger(".GrampDb")

try:
    import Config
    config = Config
except:
    log.warn("No Config module available, using defaults.")
    config = None
    

def gramps_db_factory(db_type):
    """Factory class for obtaining a Gramps database backend.

    @param db_type: the type of backend required.
    @type db_type: one of the app_* constants in const.py

    Raises GrampsDbException if the db_type is not recognised.
    """

    if db_type == const.APP_GRAMPS:
        from _GrampsBSDDB import GrampsBSDDB
        cls = GrampsBSDDB
#    elif db_type == const.APP_GRAMPS_XML:
#        from _GrampsXMLDB import GrampsXMLDB
#        cls = GrampsXMLDB
    elif db_type == const.APP_GEDCOM:
        from _GrampsGEDDB import GrampsGEDDB
        cls = GrampsGEDDB
    elif db_type == 'x-directory/normal':
        from _GrampsDBDir import GrampsDBDir
        cls = GrampsDBDir
    else:
        raise GrampsDbException("Attempt to create unknown "
                                "database backend class: "
                                "db_type = %s" % (str(db_type),))
    
    cls.__config__ = config
    return cls



        
