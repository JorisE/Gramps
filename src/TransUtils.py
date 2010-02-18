#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2009       Brian G. Matherly
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

# $Id:TransUtils.py 9912 2008-01-22 09:17:46Z acraphae $

"""
Provide translation assistance
"""

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import gettext
import sys
import os
import locale

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const

#-------------------------------------------------------------------------
#
# Public Constants
#
#-------------------------------------------------------------------------
if "GRAMPSI18N" in os.environ:
    LOCALEDIR = os.environ["GRAMPSI18N"]
elif os.path.exists( os.path.join(const.ROOT_DIR, "lang") ):
    LOCALEDIR = os.path.join(const.ROOT_DIR, "lang")
else:
    LOCALEDIR = os.path.join(const.PREFIXDIR, "share/locale")

LOCALEDOMAIN = 'gramps'

#-------------------------------------------------------------------------
#
# Public Functions
#
#-------------------------------------------------------------------------
def setup_gettext():
    """
    Setup the gettext environment.

    :returns: Nothing.

    """
    gettext.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
    gettext.textdomain(LOCALEDOMAIN)
    try:
        locale.bindtextdomain(LOCALEDOMAIN, LOCALEDIR)
    except ValueError:
        print 'Failed to bind text domain, gtk.Builder() has no translation'
    
    #following installs _ as a python function, we avoid this as TransUtils is
    #used sometimes:
    #gettext.install(LOCALEDOMAIN, LOCALEDIR, unicode=1)

def setup_windows_gtk():
    """ function to decide if needed on windows
    This function should be called on windows instead of locale.bindtextdomain
    """
    import ctypes
    try:
        import webkit
        # Webkit installed, try to find path to  libintl-8.dll
        os_path = os.environ['PATH']
        for subpath in os_path.split(';'):
            path2file = subpath + '\\libintl-8.dll'
            if os.path.isfile(path2file):
                break
        libintl = ctypes.cdll.LoadLibrary(path2file)
    except:
        # If WebKit not installed, use this
        libintl = ctypes.cdll.intl #LoadLibrary('c:\\WINDOWS\\system\\intl.dll')
    # The intl.dll in c:\\Program\\GTK2-Runtime\\bin\\ does not give any Glade translations.
    #libintl = ctypes.cdll.LoadLibrary('c:\\Program\\GTK2-Runtime\\bin\\intl.dll')
    libintl.bindtextdomain(LOCALEDOMAIN,
        LOCALEDIR.encode(sys.getfilesystemencoding()))
    libintl.textdomain(LOCALEDOMAIN)
    libintl.bind_textdomain_codeset(LOCALEDOMAIN, "UTF-8")

def get_localedomain():
    """
    Get the LOCALEDOMAIN used for the Gramps application.
    """
    return LOCALEDOMAIN

def get_addon_translator(filename=None, domain="addon"):
    """
    Get a translator for an addon. 

       filename - filename of a file in directory with full path, or
                  None to get from running code
       domain   - the name of the .mo file under the LANG/LC_MESSAGES dir
       returns  - a gettext.translation object

    The return object has the following properties and methods:
      .gettext
      .info
      .lgettext
      .lngettext
      .ngettext
      .output_charset
      .plural
      .set_output_charset
      .ugettext
      .ungettext

    Assumes path/filename
            path/locale/LANG/LC_MESSAGES/addon.mo.
    """
    if filename is None:
        filename = sys._getframe(1).f_code.co_filename
    gramps_translator = gettext.translation(LOCALEDOMAIN, LOCALEDIR,
                                            fallback=True)
    path = os.path.dirname(os.path.abspath(filename))
    addon_translator = gettext.translation(domain, os.path.join(path,"locale"),
                                           fallback=True)
    gramps_translator.add_fallback(addon_translator)
    return gramps_translator # with a language fallback
    
def get_available_translations():
    """
    Get a list of available translations.

    :returns: A list of translation languages.
    :rtype: unicode[]
    
    """
    languages = ["en"]
    
    for langdir in os.listdir(LOCALEDIR):
        mofilename = os.path.join( LOCALEDIR, langdir, 
                                   "LC_MESSAGES", "%s.mo" % LOCALEDOMAIN )
        if os.path.exists(mofilename):
            languages.append(langdir)

    languages.sort()

    return languages
