#
# count_anc.py - Ancestor counting plugin for gramps
#
# Copyright (C) 2001  Jesper Zedlitz
# Copyright (C) 2004  Donald Allingham
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

"View/Number of ancestors"

import os
import Utils
from gettext import gettext as _

from gnome.ui import *
import gtk
import gtk.glade

def report(database,person):
    try:
        CountAncestors(database,person)
    except:
        import DisplayTrace
        DisplayTrace.DisplayTrace()

class CountAncestors:
    
    def __init__(self,database,person):
        
        text = ""
        glade_file = "%s/summary.glade" % os.path.dirname(__file__)
        topDialog = gtk.glade.XML(glade_file,"summary","gramps")
        topDialog.signal_autoconnect({
            "destroy_passed_object" : Utils.destroy_passed_object,
            })
        thisgen = []
        allgen = []
        thisgen.append(person.get_handle())
        title = _("Number of ancestors of \"%s\" by generation") % person.get_primary_name().get_name()
        text = text + title + ':\n'
        thisgensize = 1
        gen = 1
        while thisgensize > 0:
            thisgensize = 0
            if thisgen:
                thisgensize = len( thisgen )
                gen = gen - 1
                if thisgensize == 1 :
                    text = text + _("Generation %d has 1 individual.\n") % (gen)
                else:
                    text = text + _("Generation %d has %d individuals.\n") % (gen, thisgensize)
            temp = thisgen
            thisgen = []
            for person_handle in temp:
                person = database.try_to_find_person_from_handle(person_handle)
                family_handle = person.get_main_parents_family_handle()
                if family_handle:
                    family = database.find_family_from_handle(family_handle)
                    father_handle = family.get_father_handle()
                    mother_handle = family.get_mother_handle()
                    if father_handle:
                        thisgen.append(father_handle)
                    if mother_handle:
                        thisgen.append(mother_handle)
            allgen = allgen + thisgen
	  
        text = text + _("Total ancestors in generations %d to -1 is %d.\n") % (gen, len(allgen))

        top = topDialog.get_widget("summary")
        textwindow = topDialog.get_widget("textwindow")
        topDialog.get_widget("title").set_text(title)
        textwindow.get_buffer().set_text(text)
        top.show()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
from Plugins import register_report

register_report(
    report,
    _("Number of ancestors"),
    category=_("View"),
    description=_("Counts number of ancestors of selected person")
    )

