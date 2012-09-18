# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2007  Donald N. Allingham, Martin Hawlisch
# Copyright (C) 2009 Douglas S. Blank
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

# $Id$

## Based on the normal fanchart

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Pango
from gi.repository import Gtk
import math
from gi.repository import Gdk
try:
    import cairo
except ImportError:
    pass

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
from gen.plug import Gramplet
import gen.lib
from gen.errors import WindowActiveError
from gui.editors import EditPerson
import gui.utils
from gui.widgets.fanchartdesc import (FanChartDescWidget, FanChartDescGrampsGUI,
                                      ANGLE_WEIGHT)
from gui.widgets.fanchart import FORM_HALFCIRCLE, BACKGROUND_SCHEME1

class FanChartDescGramplet(FanChartDescGrampsGUI, Gramplet):
    """
    The Gramplet code that realizes the FanChartWidget. 
    """

    def __init__(self, gui, nav_group=0):
        Gramplet.__init__(self, gui, nav_group)
        FanChartDescGrampsGUI.__init__(self, self.on_childmenu_changed)
        self.maxgen = 6
        self.background = BACKGROUND_SCHEME1
        self.fonttype = 'Sans'
        self.grad_start = '#0000FF'
        self.grad_end = '#FF0000'
        self.dupcolor = '#888A85'  #light grey
        self.generic_filter = None
        self.alpha_filter = 0.2
        self.form = FORM_HALFCIRCLE
        self.angle_algo = ANGLE_WEIGHT
        self.set_fan(FanChartDescWidget(self.dbstate, self.uistate, self.on_popup))
        # Replace the standard textview with the fan chart widget:
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(self.fan)
        # Make sure it is visible:
        self.fan.show()

    def init(self):
        self.set_tooltip(_("Click to expand/contract person\nRight-click for options\nClick and drag in open area to rotate"))

    def active_changed(self, handle):
        """
        Method called when active person changes.
        """
        # Reset everything but rotation angle (leave it as is)
        self.update()

    def on_childmenu_changed(self, obj, person_handle):
        """Callback for the pulldown menu selection, changing to the person
           attached with menu item."""
        self.set_active('Person', person_handle)
        return True
