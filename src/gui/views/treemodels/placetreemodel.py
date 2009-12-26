#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009    Nick Hall
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
Place tree model.
"""
#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger(".gui.views.treemodels.placetreemodel")

#-------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gui.views.treemodels.placebasemodel import PlaceBaseModel
from gui.views.treemodels.treebasemodel import TreeBaseModel

#-------------------------------------------------------------------------
#
# Internationalization
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# PlaceTreeModel
#
#-------------------------------------------------------------------------
class PlaceTreeModel(PlaceBaseModel, TreeBaseModel):
    """
    Hierarchical place model.
    """
    def __init__(self, db, scol=0, order=gtk.SORT_ASCENDING, search=None,
                 skip=set(), sort_map=None):

        self.hmap = [self.column_header] + [None]*12

        PlaceBaseModel.__init__(self, db)
        TreeBaseModel.__init__(self, db, scol=scol, order=order,
                                tooltip_column=13,
                                search=search, skip=skip, sort_map=sort_map,
                                nrgroups = 3,
                                group_can_have_handle = True)

    def get_tree_levels(self):
        """
        Return the headings of the levels in the hierarchy.
        """
        return ['Country', 'State', 'County', 'Place Name']

    def add_row(self, handle, data):
        """
        Add nodes to the node map for a single place.

        handle      The handle of the gramps object.
        data        The object data.
        """
        if data[5] is None:
            # No primary location
            level = [''] * 5
        else:
            level = [data[5][0][i] for i in range(4,-1,-1)]

        node1 = (level[0], )
        node2 = (level[1], level[0])
        node3 = (level[2], level[1], level[0])
        sort_key = self.sort_func(data)

        if not (level[3] or level[4]):
            if level[2]:
                self.add_node(None, node1, level[0], None, add_parent=False)
                self.add_node(node1, node2, level[1], None, add_parent=False)
                self.add_node(node2, handle, level[2], handle, add_parent=False)
            elif level[1]:
                self.add_node(None, node1, level[0], None, add_parent=False)
                self.add_node(node1, handle, level[1], handle, add_parent=False)
            elif level[0]:
                self.add_node(None, handle, level[0], handle, add_parent=False)
            else:
                self.add_node(None, handle, sort_key, handle, add_parent=False)
               
        else:        
            self.add_node(None, node1, level[0], None, add_parent=False)
            self.add_node(node1, node2, level[1], None, add_parent=False)
            self.add_node(node2, node3, level[2], None, add_parent=False)
            self.add_node(node3, handle, sort_key, handle, add_parent=False)

    def column_name(self, data):
        if data[5] is not None:
            level = [data[5][0][i] for i in range(4,-1,-1)]
            if not (level[3] or level[4]):
                return unicode(level[2] or level[1] or level[0])
            elif level[3] and level[4]:
                return unicode(level[3] + ', ' + level[4])
            elif level[3] or level[4]:
                return unicode(level[3] or level[4])
            else:
                return unicode(data[2])
        return unicode(data[2])
        
    def column_header(self, node):
        """
        Return a column heading.  This is called for nodes with no associated
        Gramps handle.
        """
        return node[0]
