#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2003  Donald N. Allingham
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

from gettext import gettext as _

import gtk
import gtk.gdk
import gobject

import const

_gramps_png = "%s/gramps.png" % const.rootDir
_splash_jpg = "%s/splash.jpg" % const.rootDir
_format = '<span weight="bold" size="xx-large">%s</span>'

class Assistant(gtk.Object):
    """ A tabbed dialog box used to implement Assistant interfaces."""

    __gproperties__ = {}

    __gsignals__ = { 'page-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                         (gobject.TYPE_INT,)),
                     'before-page-next' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                              (gobject.TYPE_INT,)),
                     'after-page-next' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                              (gobject.TYPE_INT,)),
                     'before-page-back' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                              (gobject.TYPE_INT,)),
                     'after-page-back' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                              (gobject.TYPE_INT,)),
                     'complete' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                              ())
                     }
    
    def __init__(self,title,complete):
        gobject.GObject.__init__(self)
         
        self.complete = complete
        self.fg_color = gtk.gdk.color_parse('#7d684a')
        self.bg_color = gtk.gdk.color_parse('#e1dbc5')
        self.logo = gtk.gdk.pixbuf_new_from_file(_gramps_png)
        self.splash = gtk.gdk.pixbuf_new_from_file(_splash_jpg)

        self.current_page = 0
        self.max_page = 1
        
        self.window = gtk.Window()
        titlebox = gtk.HBox()
        self.title_text = []
        self.title_text.append(_format % title)
        
        self.title = gtk.Label(self.title_text[0])
        self.title.set_alignment(0,0.5)
        self.title.set_use_markup(True)
        self.conclude_text = "No finish text specified"

        titlebox.pack_start(self.title,True)
        image = gtk.Image()
        image.set_from_file(_gramps_png)
        titlebox.pack_end(image,False)
        
        self.notebook = gtk.Notebook()
        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)
        
        vbox = gtk.VBox(spacing=6)
        vbox.set_border_width(6)
        hbox = gtk.HButtonBox()
        hbox.set_spacing(6)
        hbox.set_layout(gtk.BUTTONBOX_END)

        self.cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.cancel.connect('clicked',lambda x: self.window.destroy())
        self.back   = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.back.set_sensitive(False)
        self.back.connect('clicked',self.back_clicked)
        self.next   = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.next.connect('clicked',self.next_clicked)
        
        hbox.add(self.cancel)
        hbox.add(self.back)
        hbox.add(self.next)

        vbox.pack_start(titlebox,False)
        vbox.pack_start(self.notebook,True)
        vbox.pack_start(hbox,False)

        self.window.add(vbox)

    def do_get_property(self, prop):
        '''Return the gproperty's value.'''
        raise AttributeError, 'unknown property %s' % prop.name

    def do_set_property(self, prop, value):
        '''Set the property of writable properties.'''
        raise AttributeError, 'unknown or read only property %s' % prop.name


    def update_title(self):
        self.title.set_label(self.title_text[self.current_page])
        self.title.set_use_markup(True)
    
    def back_clicked(self,obj):
        self.emit('before-page-back',self.notebook.get_current_page())
        if self.current_page == 1:
            self.back.show()
            self.back.set_sensitive(False)
            self.cancel.show()
        self.current_page -= 1
        self.notebook.set_current_page(self.current_page)
        self.update_title()
        self.next.set_label(gtk.STOCK_GO_FORWARD)
        self.next.set_use_stock(True)
        self.cancel.show()
        
        self.emit('after-page-back',self.notebook.get_current_page())
        self.emit('page-changed',self.notebook.get_current_page())

    def next_clicked(self,obj):
        self.emit('before-page-next',self.notebook.get_current_page())
        if self.current_page == self.max_page:
            self.emit('complete')
            self.complete()
            self.window.destroy()
        else:
            self.current_page += 1
            self.notebook.set_current_page(self.current_page)
            self.update_title()
            if self.current_page == self.max_page:
                self.next.set_label(gtk.STOCK_OK)
                self.next.set_use_stock(True)
                self.back.hide()
                self.cancel.hide()
            else:
                self.next.set_label(gtk.STOCK_GO_FORWARD)
                self.next.set_use_stock(True)
                self.back.show()
                self.back.set_sensitive(True)
                self.cancel.show()

        self.emit('after-page-next',self.notebook.get_current_page())
        self.emit('page-changed',self.notebook.get_current_page())

    def set_intro(self,text):
        hbox = gtk.HBox(spacing=12)
        image = gtk.Image()
        image.set_from_file(_splash_jpg)
        hbox.pack_start(image,False)
        label = gtk.Label(text)
        label.set_line_wrap(True)
        hbox.add(label)
        self.notebook.append_page(hbox)

    def set_conclusion(self,title,text):
        self.conclude_text = text

    def add_page(self, title, child):
        self.title_text.append(_format % title)
        self.notebook.append_page(child)
        self.max_page += 1

    def show(self):
        self.title_text.append(_format % _('Finished'))
        hbox = gtk.HBox(spacing=12)
        image = gtk.Image()
        image.set_from_file(_splash_jpg)
        hbox.pack_start(image,False)
        label = gtk.Label(self.conclude_text)
        label.set_line_wrap(True)
        hbox.add(label)
        self.notebook.append_page(hbox)
        self.window.show_all()
        self.notebook.set_current_page(0)
        
        self.emit('page-changed',self.notebook.get_current_page())


    def destroy(self):
        self.window.destroy()

if gtk.pygtk_version < (2,8,0):
    gobject.type_register(Assistant)

if __name__ == "__main__":

    def complete():
        gtk.main_quit()

    def make_label(table,val,y,x1,x2,x3,x4):
        label = gtk.Label(val)
        label.set_alignment(0,0.5)
        text = gtk.Entry()
        table.attach(label,x1,x2,y,y+1,gtk.SHRINK|gtk.FILL)
        table.attach(text,x3,x4,y,y+1,gtk.EXPAND|gtk.FILL)
        return text

    a = Assistant('Getting started',complete)
    a.set_intro('Welcome to GRAMPS, the Genealogical Research '
                     'and Analysis Management Programming System.\n'
                     'Several options and information need to be gathered '
                     'before GRAMPS is ready to be used. Any of this '
                     'information can be changed in the future in the '
                     'Preferences dialog under the Settings menu.')

    box = gtk.VBox()
    box.set_spacing(12)
    table = gtk.Table(8,4)
    table.set_row_spacings(6)
    table.set_col_spacings(6)
    
    make_label(table,_('Name:'),0,0,1,1,4)
    make_label(table,_('Address:'),1,0,1,1,4)
    make_label(table,_('City:'),2,0,1,1,2)
    make_label(table,_('State/Province:'),2,2,3,3,4)
    make_label(table,_('Country:'),3,0,1,1,2)
    make_label(table,_('ZIP/Postal code:'),3,2,3,3,4)
    make_label(table,_('Phone:'),4,0,1,1,4)
    make_label(table,_('Email:'),5,0,1,1,4)
    box.add(table)
    a.add_page('Researcher information',box)
    a.show()
    
    gtk.main()
