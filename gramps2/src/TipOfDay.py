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

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import xml.parsers.expat
from random import Random

#-------------------------------------------------------------------------
#
# GTK/GNOME modules
#
#-------------------------------------------------------------------------
import gtk
import gtk.glade

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import const
import GrampsGconfKeys

#-------------------------------------------------------------------------
#
# Tip Display class
#
#-------------------------------------------------------------------------
class TipOfDay:
    def __init__(self):
        xml = gtk.glade.XML(const.gladeFile, "tod", "gramps")
        top = xml.get_widget("tod")
        tip = xml.get_widget("tip")
        use = xml.get_widget('usetips')
        
        tp = TipParser()
        tip_list = tp.get()
        use.set_active(GrampsGconfKeys.get_usetips())

        new_index = range(len(tip_list))
        Random().shuffle(new_index)

        index = 0
        rval = 0
        while rval == 0:
            tip.set_text(tip_list[new_index[index]])
            tip.set_use_markup(1)
            rval = top.run()
            if index >= len(tip_list)-1:
                index = 0
            else:
                index += 1
        
        GrampsGconfKeys.save_usetips(use.get_active())
        top.destroy()

#-------------------------------------------------------------------------
#
# Tip parser class
#
#-------------------------------------------------------------------------
class TipParser:
    """
    Interface to the document template file
    """
    def __init__(self):
        """
        Creates a template parser. The parser loads map of tempate names
        to the file containing the tempate.

        data - dictionary that holds the name to path mappings
        fpath - filename of the XML file
        """

        self.mylist = []
        xml_file = open(const.tipdata)
        self.tlist = []
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.startElement
        p.EndElementHandler = self.endElement
        p.CharacterDataHandler = self.characters
        p.ParseFile(xml_file)
        xml_file.close()

    def get(self):
        return self.mylist
    
    def setDocumentLocator(self,locator):
        """Sets the XML document locator"""
        self.locator = locator

    def startElement(self,tag,attrs):
        """
        Loads the dictionary when an XML tag of 'template' is found. The format
        XML tag is <template title=\"name\" file=\"path\">
        """
        if tag == "tip":
            self.tlist = []
        elif tag != "tips":
            # let all the other tags through, except for the "tips" tag
            self.tlist.append("<%s>" % tag)

    def endElement(self,tag):
        if tag == "tip":
            text = ''.join(self.tlist)
            self.mylist.append(' '.join(text.split()))
        elif tag != "tips":
            # let all the other tags through, except for the "tips" tag
            self.tlist.append("</%s>" % tag)

    def characters(self, data):
        self.tlist.append(data)
