# -*- coding: utf-8 -*-
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

# $Id:ToolTips.py 9912 2008-01-22 09:17:46Z acraphae $

#------------------------------------------------------------------------
#
# ToolTips
#
# The model provides a framework for generating tooltips for different
# gramps objects. The idea is to hide the task of generating these tips
# from the other parts of gramps and to provide a single place were
# a tooltip is generated so that it is consistent everywhere it is used.
#
# The tooltips generated by this module are meant to be passed to the
# TreeTips module for rendering.
#
# To add tooltips for a new object:
#
#    1. copy one of the existing <object>Tip classes and change the tooltip()
#       method to suit the new object.
#    2. add a new entry to the CLASS_MAP at the bottom of the file.
#    3. thats it.
#
# To use the tips, use one of the factory classes to generate the tips.
# The factory classes generate methods that TreeTips will execute only
# if the tip is needed. So the processing is deferred until required.
#------------------------------------------------------------------------

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
from xml.sax.saxutils import escape
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# gtk
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
import gen.lib
import DateHandler

#-------------------------------------------------------------------------
#
# Utility functions
#
#-------------------------------------------------------------------------

def short(val,size=60):
    if len(val) > size:
        return "%s..." % val[0:size]
    else:
        return val

#-------------------------------------------------------------------------
#
# Factory classes
#
#-------------------------------------------------------------------------

class TipFromFunction(object):
    """
    TipFromFunction generates a tooltip callable. 
    """
    def __init__(self,db,fetch_function):
        """
        fetch_function: a callable that will return a Rellib object
        when it is run. The function will not be run until the tooltip
        is required. Use a lambda function to currie any required
        arguments.
        """
        self._db = db
        self._fetch_function = fetch_function

    def get_tip(self):
        o = self._fetch_function()

        # check if we have a handler for the object type returned
        for cls, handler in CLASS_MAP.iteritems():
            if isinstance(o,cls):
                return handler(self._db, o)()
        return "no tip"

    __call__ = get_tip


#-------------------------------------------------------------------------
#
# Tip generator classes.
#
#-------------------------------------------------------------------------

class RepositoryTip(object):
    def __init__(self,db,repos):
        self._db = db
        self._obj = repos

    def get_tip(self):
        global escape
        s = "<big><b>%s:</b>\t%s</big>\n\n"\
            "\t<b>%s:</b>\n"\
            "\t\t%s\n"\
            "\t\t%s\n"\
            "\t\t%s\n"\
            "\t\t%s\n"\
            "\t\t%s\n"\
            "\t\t%s\n"\
            "\t<b>%s:</b>\t%s\n"\
            "\t<b>%s:</b>\t%s\n"\
            "\t<b>%s:</b>\t%s\n"\
            "\t<b>%s:</b>\t%s\n"\
            % (
            _("Repository"),escape(self._obj.get_name()),
            _("Location"),
            escape(self._obj.address.get_parish()),
            escape(self._obj.address.get_city()),
            escape(self._obj.address.get_county()),
            escape(self._obj.address.get_state()),
            escape(self._obj.address.get_postal_code()),
            escape(self._obj.address.get_country()),
            _("Telephone"), escape(self._obj.address.get_phone()),
            _("Email"), escape(self._obj.get_email()),
            _("Search Url"), escape(self._obj.get_search_url()),
            _("Home Url"), escape(self._obj.get_home_url()))    

        # Get the notes
        notelist = self._obj.get_note_list()
        for notehandle in notelist:
            note = self._db.get_note_from_handle(notehandle)
            s += "\t<b>%s:</b>\t%s\n" % (
                    _("Note"), escape(note.get()))

        # Get the list of sources that reference this repository
        repos_handle = self._obj.get_handle()
        source_list = [ src_handle for src_handle \
                        in self._db.get_source_handles() \
                        if self._db.get_source_from_handle(src_handle).has_repo_reference(repos_handle)]

        if len(source_list) > 0:
            s += "\n<big><b>%s</b></big>\n\n" % (_("Sources in repository"),)
                
            for src_handle in source_list:
                src = self._db.get_source_from_handle(src_handle)
                s += "\t<b>%s:</b>\t%s\n" % (
                    _("Name"),escape(short(src.get_title())))
                
        return s

    __call__ = get_tip

class PersonTip(object):
    def __init__(self,db,repos):
        self._db = db
        self._obj = repos

    def get_tip(self):
        global escape

        birth_str = ""
        birth_ref = self._obj.get_birth_ref()
        if birth_ref:
            birth = self._db.get_event_from_handle(birth_ref.ref)
            date_str = DateHandler.get_date(birth)
            if date_str != "":
                birth_str = escape(date_str)
                
        s = "<span size=\"larger\" weight=\"bold\">%s</span>\n"\
            "   <span weight=\"bold\">%s:</span> %s\n"\
            "   <span weight=\"bold\">%s:</span> %s\n" % (
            _("Person"),
            _("Name"),escape(self._obj.get_primary_name().get_name()),
            _("Birth"),birth_str)

        if len(self._obj.get_source_references()) > 0:
            psrc_ref = self._obj.get_source_references()[0]
            psrc_id = psrc_ref.get_reference_handle()
            psrc = self._db.get_source_from_handle(psrc_id)

            s += "\n<span size=\"larger\" weight=\"bold\">%s</span>\n"\
                 "   <span weight=\"bold\">%s:</span> %s\n" % (
                _("Primary source"),
                _("Name"),
                escape(short(psrc.get_title())))
                
        return s

    __call__ = get_tip

class FamilyTip(object):
    def __init__(self,db, obj):
        self._db = db
        self._obj = obj

    def get_tip(self):
        global escape

        fhandle = self._obj.get_father_handle()
        mhandle = self._obj.get_mother_handle()
                
        s = "<span size=\"larger\" weight=\"bold\">%s</span>" % _("Family")

        if fhandle:
            father = self._db.get_person_from_handle(fhandle)
            s +="\n   <span weight=\"bold\">%s:</span> %s" % (
                _("Father"),escape(father.get_primary_name().get_name()))

        if mhandle:
            mother = self._db.get_person_from_handle(mhandle)
            s +="\n   <span weight=\"bold\">%s:</span> %s" % (
                _("Mother"),escape(mother.get_primary_name().get_name()))

        for cref in self._obj.get_child_ref_list():
            child =  self._db.get_person_from_handle(cref.ref)
            s +="\n   <span weight=\"bold\">%s:</span> %s" % (
                _("Child"),escape(child.get_primary_name().get_name()))

        return s

    __call__ = get_tip


CLASS_MAP = {
    gen.lib.Repository : RepositoryTip,
    gen.lib.Person     : PersonTip,
    gen.lib.Family     : FamilyTip
    }
