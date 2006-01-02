#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham, Martin Hawlisch
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
# Python modules
#
#-------------------------------------------------------------------------
from gettext import gettext as _
from cgi import escape

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gobject
import gtk
import gtk.gdk

#-------------------------------------------------------------------------
#
# Gramps Modules
#
#-------------------------------------------------------------------------
import RelLib
import PageView
import EditPerson
import Relationship
import NameDisplay
import Utils
import DateHandler
import ImgManip
import ReportUtils

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
_PERSON = "p"
_BORN = _('b.')
_DIED = _('d.')
_BAPT = _('bap.')
_CHRI = _('chr.')
_BURI = _('bur.')
_CREM = _('crem.')

class PersonBoxWidget_old( gtk.Button):
    def __init__(self,fh,person,maxlines,image=None):
        if person:
            gtk.Button.__init__(self, fh.format_person(person, maxlines))
            gender = person.get_gender()
            if gender == RelLib.Person.MALE:
                self.modify_bg( gtk.STATE_NORMAL, self.get_colormap().alloc_color("#F5FFFF"))
            elif gender == RelLib.Person.FEMALE:
                self.modify_bg( gtk.STATE_NORMAL, self.get_colormap().alloc_color("#FFF5FF"))
            else:
                self.modify_bg( gtk.STATE_NORMAL, self.get_colormap().alloc_color("#FFFFF5"))
        else:
            gtk.Button.__init__(self, "               ")
            #self.set_sensitive(False)
        self.fh = fh
        self.set_alignment(0.0,0.0)
        white = self.get_colormap().alloc_color("white")
        self.modify_bg( gtk.STATE_ACTIVE, white)
        self.modify_bg( gtk.STATE_PRELIGHT, white)
        self.modify_bg( gtk.STATE_SELECTED, white)

class PersonBoxWidget( gtk.DrawingArea):
    def __init__(self,fh,person,maxlines,image=None):
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)  # Required for popup menu
        self.add_events(gtk.gdk.ENTER_NOTIFY_MASK)  # Required for tooltip and mouse-over
        self.add_events(gtk.gdk.LEAVE_NOTIFY_MASK)  # Required for tooltip and mouse-over
        self.fh = fh
        self.person = person
        self.maxlines = maxlines
        self.image = image
        self.init_done = False
        self.connect("expose_event", self.expose)
        text = ""
        if self.person:
            text = self.fh.format_person(self.person,self.maxlines)
            self.connect("enter-notify-event", self.on_enter_cb)    # enable mouse-over
            self.connect("leave-notify-event", self.on_leave_cb)
        self.textlayout = self.create_pango_layout(text)
        s = self.textlayout.get_pixel_size()
        xmin = s[0] + 12
        ymin = s[1] + 11
        if image:
            xmin += image.get_width()
            ymin = max( ymin,image.get_height()+4)
        self.set_size_request(max(xmin,120),max(ymin,25))
    
    def on_enter_cb(self,widget,event):
        '''' On mouse-over hightlight border'''
        try:
            self.border_gc.line_width = 3
            self.queue_draw()
        except AttributeError:
            pass # ignore missing self.border_gc because we are not yet exposed
        
    def on_leave_cb(self,widget,event):
        try:
            self.border_gc.line_width = 1
            self.queue_draw()
        except AttributeError:
            pass # ignore missing self.border_gc because we are not yet exposed
    
    def expose(self,widget,event):
        if not self.init_done:
            self.bg_gc = self.window.new_gc()
            self.text_gc = self.window.new_gc()
            self.border_gc = self.window.new_gc()
            self.border_gc.line_style = gtk.gdk.LINE_SOLID
            self.border_gc.line_width = 1
            self.shadow_gc = self.window.new_gc()
            self.shadow_gc.line_style = gtk.gdk.LINE_SOLID
            self.shadow_gc.line_width = 4
            if self.person:
                self.border_gc.set_foreground( self.get_colormap().alloc_color("#000000"))
                if self.person.get_gender() == RelLib.Person.MALE:
                    self.bg_gc.set_foreground( self.get_colormap().alloc_color("#F5FFFF"))
                elif self.person.get_gender() == RelLib.Person.FEMALE:
                    self.bg_gc.set_foreground( self.get_colormap().alloc_color("#FFF5FF"))
                else:
                    self.bg_gc.set_foreground( self.get_colormap().alloc_color("#FFFFF5"))
            else:
                self.bg_gc.set_foreground( self.get_colormap().alloc_color("#eeeeee"))
                self.border_gc.set_foreground( self.get_colormap().alloc_color("#777777"))
            self.shadow_gc.set_foreground( self.get_colormap().alloc_color("#999999"))
            self.init_done = True
        alloc = self.get_allocation()
        # shadow
        self.window.draw_line(self.shadow_gc, 3, alloc.height-1, alloc.width, alloc.height-1)
        self.window.draw_line(self.shadow_gc, alloc.width-1, 3, alloc.width-1, alloc.height)
        # box background
        self.window.draw_rectangle(self.bg_gc, True, 1, 1, alloc.width-5, alloc.height-5)
        # text
        if self.person:
            self.window.draw_layout( self.text_gc, 5,4, self.textlayout)
        # image
        if self.image:
            self.window.draw_pixbuf( self.text_gc, self.image, 0,0, alloc.width-4-self.image.get_width(),1)
        # border
        if self.border_gc.line_width > 1:
            self.window.draw_rectangle(self.border_gc, False, 1, 1, alloc.width-6, alloc.height-6)
        else:
            self.window.draw_rectangle(self.border_gc, False, 0, 0, alloc.width-4, alloc.height-4)

class FormattingHelper:
    def __init__(self,db):
        self.db = db
    
    def change_db(self,db):
        self.db = db
        
    def format_relation( self, family, line_count):
        text = ""
        for event_ref in family.get_event_ref_list():
            event = self.db.get_event_from_handle(event_ref.ref)
            if event:
                if line_count < 3:
                    return DateHandler.get_date(event)
                i,s = event.get_type()
                name = Utils.family_relations[i]
                text += name
                text += "\n"
                text += DateHandler.get_date(event)
                text += "\n"
                text += self.get_place_name(event.get_place_handle())
                if line_count < 5:
                   return text;
                break
        return text

    def get_place_name( self, place_handle):
        text = ""
        place = self.db.get_place_from_handle(place_handle)
        if place:
            place_title = self.db.get_place_from_handle(place_handle).get_title()
            if place_title != "":
                if len(place_title) > 25:
                    text = place_title[:24]+"..."
                else:
                    text = place_title
        return text
        
    def format_person( self, person, line_count):
        if not person:
            return ""
        name = NameDisplay.displayer.display(person)
        if line_count < 3:
            return name
        bdate,bplace,bdate_full,bdate_mod,ddate,dplace,ddate_full,ddate_mod = \
                        ReportUtils.get_birth_death_strings(self.db,person)
        if line_count < 5:
            return "%s\n* %s\n+ %s" % (name,bdate,ddate)
        else:
            return "%s\n* %s\n  %s\n+ %s\n  %s" % (name,bdate,bplace,ddate,dplace)

#-------------------------------------------------------------------------
#
# PedigreeView
#
#-------------------------------------------------------------------------
class PedView(PageView.PersonNavView):

    def __init__(self,dbstate,uistate):
        PageView.PersonNavView.__init__(self,'Pedigree View',dbstate,uistate)
        dbstate.connect('database-changed',self.change_db)
        dbstate.connect('active-changed',self.goto_active_person)
        self.force_size = 0 # Automatic resize
        self.tree_style = 0 # Nice tree
        self.show_images = True # Show photos of persons
        self.show_marriage_data = 0 # Hide marriage data by default
        self.db = dbstate.db
        self.format_helper = FormattingHelper( self.db)

    def init_parent_signals_cb(self, widget, event):
        # required to properly bootstrap the signal handlers.
        # This handler is connected by build_widget. After the outside ViewManager
        # has placed this widget we are able to access the parent container.
        self.notebook.disconnect(self.bootstrap_handler)
        self.notebook.parent.connect("size-allocate", self.size_request_cb)
        self.size_request_cb(widget.parent,event)
        
    def add_table_to_notebook( self, table):
        frame = gtk.ScrolledWindow(None,None)
        frame.set_shadow_type(gtk.SHADOW_NONE)
        frame.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        frame.add_with_viewport(table)
        table.get_parent().set_shadow_type(gtk.SHADOW_NONE)
        table.set_row_spacings(1)
        table.set_col_spacings(0)
        try:
            self.notebook.append_page(frame,None)
        except:
            # for PyGtk < 2.4
            self.notebook.append_page(frame,gtk.Label(""))

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered with
        GNOME as a stock icon.
        """
        return 'gramps-pedigree'

    def build_widget(self):
        """
        Builds the interface and returns a gtk.Container type that
        contains the interface. This containter will be inserted into
        a gtk.Notebook page.
        """
        self.tooltips = gtk.Tooltips()
        self.tooltips.enable()
        
        self.notebook = gtk.Notebook()
        self.notebook.connect("button-press-event", self.on_show_option_menu_cb)
        self.bootstrap_handler = self.notebook.connect("expose-event", self.init_parent_signals_cb)
        self.notebook.set_show_border(False)
        self.notebook.set_show_tabs(False)
            
        self.table_2 = gtk.Table(1,1,False)
        self.table_2.connect("button-press-event", self.on_show_option_menu_cb)
        self.add_table_to_notebook( self.table_2)

        self.table_3 = gtk.Table(1,1,False)
        self.table_3.connect("button-press-event", self.on_show_option_menu_cb)
        self.add_table_to_notebook( self.table_3)

        self.table_4 = gtk.Table(1,1,False)
        self.table_4.connect("button-press-event", self.on_show_option_menu_cb)
        self.add_table_to_notebook( self.table_4)

        self.table_5 = gtk.Table(1,1,False)
        self.table_5.connect("button-press-event", self.on_show_option_menu_cb)
        self.add_table_to_notebook( self.table_5)

        self.rebuild_trees(None)

        return self.notebook

    def ui_definition(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
                <menuitem action="HomePerson"/>
                <separator/>
              </placeholder>
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
              <toolitem action="HomePerson"/>
            </placeholder>
          </toolbar>
        </ui>'''

    def define_actions(self):
        """
        Required define_actions function for PageView. Builds the action
        group information required. We extend beyond the normal here,
        since we want to have more than one action group for the PersonView.
        Most PageViews really won't care about this.

        Special action groups for Forward and Back are created to allow the
        handling of navigation buttons. Forward and Back allow the user to
        advance or retreat throughout the history, and we want to have these
        be able to toggle these when you are at the end of the history or
        at the beginning of the history.
        """

        PageView.PersonNavView.define_actions(self)
        self.add_action('HomePerson',gtk.STOCK_HOME,  "_Home",  callback=self.home)

    def change_db(self,db):
        """
        Callback associated with DbState. Whenenver the database
        changes, this task is called. In this case, we rebuild the
        columns, and connect signals to the connected database. Tere
        is no need to store the database, since we will get the value
        from self.state.db
        """
        self.db = db
        self.format_helper.change_db(db)
        db.connect('person-add', self.person_updated_cb)
        db.connect('person-update', self.person_updated_cb)
        db.connect('person-delete', self.person_updated_cb)
        db.connect('person-rebuild', self.person_rebuild)
        self.rebuild_trees(None)
 
    def goto_active_person(self,handle=None):
        if handle:
            person = self.db.get_person_from_handle(handle)
            self.rebuild_trees(person)
            self.handle_history(person.handle)
        else:
            self.rebuild_trees(None)
    
    def person_updated_cb(self,handle_list):
        self.rebuild_trees(self.dbstate.active)

    def person_rebuild(self):
        self.rebuild_trees(self.dbstate.active)

    def person_edited_cb(self, p1=None, p2=None):
        pass

    def request_resize(self):
        self.size_request_cb(self.notebook.parent,None,None)
        
    def size_request_cb(self, widget, event, data=None):
        if self.force_size == 0:
            v = widget.get_allocation()
            page_list = range(0,self.notebook.get_n_pages())
            page_list.reverse()
            for n in page_list:
                p = self.notebook.get_nth_page(n).get_child().get_child().get_allocation()
                if v.width >= p.width and v.height > p.height:
                    self.notebook.set_current_page(n)
                    break;
        else:
            self.notebook.set_current_page(self.force_size-2)

    def rebuild_trees(self,person):
        if self.tree_style == 1:
            # format of the definition is:
            # ((each box of the pedigree has a node here),
            #  ((person data), (connection line), (marriage data)),
            #  ((person box position and size),(parent relation box),(marriage data)),
            #   ((or for another design),((fater relation box),(mother relation box)),(marriage data)))
            pos_2 =(((0,3,3,3),((1,0,3),(1,6,3)),(3,3,2,3)),
                    ((2,0,3,3),None,None),
                    ((2,6,3,3),None,None))
            pos_3 =(((0,4,3,5),((1,1,3),(1,9,3)),(3,5,2,3)),
                    ((2,1,3,3),((3,0,1),(3,4,1)),(5,1,2,3)),
                    ((2,9,3,3),((3,8,1),(3,12,1)),(5,9,2,3)),
                    ((4,0,3,1),None,None),
                    ((4,4,3,1),None,None),
                    ((4,8,3,1),None,None),
                    ((4,12,3,1),None,None))
            pos_4 =(((0, 5,3,5),((1,2,3),(1,10,3)),(3, 6,2,3)),
                    ((2, 2,3,3),((3,1,1),(3,5,1)),(5, 3,2,1)),
                    ((2,10,3,3),((3,9,1),(3,13,1)),(5,11,2,1)),
                    ((4, 1,3,1),((5,0,1),(5,2,1)),(7,1,2,1)),
                    ((4, 5,3,1),((5,4,1),(5,6,1)),(7,5,2,1)),
                    ((4, 9,3,1),((5,8,1),(5,10,1)),(7,9,2,1)),
                    ((4,13,3,1),((5,12,1),(5,14,1)),(7,13,2,1)),
                    ((6, 0,3,1),None,None),
                    ((6, 2,3,1),None,None),
                    ((6, 4,3,1),None,None),
                    ((6, 6,3,1),None,None),
                    ((6, 8,3,1),None,None),
                    ((6,10,3,1),None,None),
                    ((6,12,3,1),None,None),
                    ((6,14,3,1),None,None),)
            pos_5 =(((0,10,3,11),((1,5,5),(1,21,5)),(3,13,2,5)),
                    ((2, 5,3,5),((3,2,3),(3,10,3)),(5, 6,2,3)),
                    ((2,21,3,5),((3,18,3),(3,26,3)),(5,22,2,3)),
                    ((4, 2,3,3),((5,1,1),(5,5,1)),(7,3,2,1)),
                    ((4,10,3,3),((5,9,1),(5,13,1)),(7,11,2,1)),
                    ((4,18,3,3),((5,17,1),(5,21,1)),(7,19,2,1)),
                    ((4,26,3,3),((5,25,1),(5,29,1)),(7,27,2,1)),
                    ((6, 1,3,1),((7,0,1),(7,2,1)),(9,1,2,1)),
                    ((6, 5,3,1),((7,4,1),(7,6,1)),(9,5,2,1)),
                    ((6, 9,3,1),((7,8,1),(7,10,1)),(9,9,2,1)),
                    ((6,13,3,1),((7,12,1),(7,14,1)),(9,13,2,1)),
                    ((6,17,3,1),((7,16,1),(7,18,1)),(9,17,2,1)),
                    ((6,21,3,1),((7,20,1),(7,22,1)),(9,21,2,1)),
                    ((6,25,3,1),((7,24,1),(7,26,1)),(9,25,2,1)),
                    ((6,29,3,1),((7,28,1),(7,30,1)),(9,29,2,1)),
                    ((8, 0,3,1),None,None),
                    ((8, 2,3,1),None,None),
                    ((8, 4,3,1),None,None),
                    ((8, 6,3,1),None,None),
                    ((8, 8,3,1),None,None),
                    ((8,10,3,1),None,None),
                    ((8,12,3,1),None,None),
                    ((8,14,3,1),None,None),
                    ((8,16,3,1),None,None),
                    ((8,18,3,1),None,None),
                    ((8,20,3,1),None,None),
                    ((8,22,3,1),None,None),
                    ((8,24,3,1),None,None),
                    ((8,26,3,1),None,None),
                    ((8,28,3,1),None,None),
                    ((8,30,3,1),None,None),)
        elif self.tree_style == 0:
            pos_2 =(((0,0,1,3),(1,0,3),(2,1,1,1)),
                    ((2,0,1,1),None,None),
                    ((2,2,1,1),None,None))
            pos_3 =(((0,2,1,3),(1,1,5),(2,3,1,1)),
                    ((2,0,1,3),(3,0,3),(4,1,1,1)),
                    ((2,4,1,3),(3,4,3),(4,5,1,1)),
                    ((4,0,1,1),None,None),
                    ((4,2,1,1),None,None),
                    ((4,4,1,1),None,None),
                    ((4,6,1,1),None,None))
            pos_4 =(((0,6,1,3),(1,3,9),(2,5,1,5)),
                    ((2,2,1,3),(3,1,5),(4,3,1,1)),
                    ((2,10,1,3),(3,9,5),(4,11,1,1)),
                    ((4,0,1,3),(5,0,3),(6,1,1,1)),
                    ((4,4,1,3),(5,4,3),(6,5,1,1)),
                    ((4,8,1,3),(5,8,3),(6,9,1,1)),
                    ((4,12,1,3),(5,12,3),(6,13,1,1)),
                    ((6,0,1,1),None,None),
                    ((6,2,1,1),None,None),
                    ((6,4,1,1),None,None),
                    ((6,6,1,1),None,None),
                    ((6,8,1,1),None,None),
                    ((6,10,1,1),None,None),
                    ((6,12,1,1),None,None),
                    ((6,14,1,1),None,None))
            pos_5 =(((0,14,1,3),(1,7,17),(2,13,1,5)),
                    ((2,6,1,3),(3,3,9),(4,5,1,5)),
                    ((2,22,1,3),(3,19,9),(4,21,1,5)),
                    ((4,2,1,3),(5,1,5),(6,3,1,1)),
                    ((4,10,1,3),(5,9,5),(6,11,1,1)),
                    ((4,18,1,3),(5,17,5),(6,19,1,1)),
                    ((4,26,1,3),(5,25,5),(6,27,1,1)),
                    ((6,0,1,3),(7,0,3),(8,1,1,1)),
                    ((6,4,1,3),(7,4,3),(8,5,1,1)),
                    ((6,8,1,3),(7,8,3),(8,9,1,1)),
                    ((6,12,1,3),(7,12,3),(8,13,1,1)),
                    ((6,16,1,3),(7,16,3),(8,17,1,1)),
                    ((6,20,1,3),(7,20,3),(8,21,1,1)),
                    ((6,24,1,3),(7,24,3),(8,25,1,1)),
                    ((6,28,1,3),(7,28,3),(8,29,1,1)),
                    ((8,0,1,1),None,None),
                    ((8,2,1,1),None,None),
                    ((8,4,1,1),None,None),
                    ((8,6,1,1),None,None),
                    ((8,8,1,1),None,None),
                    ((8,10,1,1),None,None),
                    ((8,12,1,1),None,None),
                    ((8,14,1,1),None,None),
                    ((8,16,1,1),None,None),
                    ((8,18,1,1),None,None),
                    ((8,20,1,1),None,None),
                    ((8,22,1,1),None,None),
                    ((8,24,1,1),None,None),
                    ((8,26,1,1),None,None),
                    ((8,28,1,1),None,None),
                    ((8,30,1,1),None,None))
        self.rebuild( self.table_2, pos_2, person)
        self.rebuild( self.table_3, pos_3, person)
        self.rebuild( self.table_4, pos_4, person)
        self.rebuild( self.table_5, pos_5, person)
        
        #gobject.idle_add(self.request_resize)


    def rebuild( self, table_widget, positions, active_person):
        # Build ancestor tree
        lst = [None]*31
        self.find_tree(active_person,0,1,lst)

        # Purge current table content
        for child in table_widget.get_children():
            child.destroy()
        table_widget.resize(1,1)
        
        xmax = 0
        ymax = 0
        for i in range(0,31):
            try:
                # Table placement for person data
                x = positions[i][0][0]+1
                y = positions[i][0][1]+1
                w = positions[i][0][2]
                h = positions[i][0][3]
            except IndexError:  # no position for this person defined
                continue
            if not lst[i]:
                # No person -> show empty box
                pw = PersonBoxWidget( self.format_helper, None, 0, None);
                if positions[i][0][2] > 1:
                    table_widget.attach(pw,x,x+w,y,y+h,gtk.FILL,gtk.FILL,0,0)
                else:
                    table_widget.attach(pw,x,x+w,y,y+h,gtk.FILL,gtk.FILL,0,0)
                if x+w > xmax:
                    xmax = x+w
                if y+h > ymax:
                    ymax = y+h
            else:
                # Get foto
                image = None
                if self.show_images and i < ((len(positions)-1)/2) and  positions[i][0][3] > 1:
                    media_list = lst[i][0].get_media_list()
                    if media_list:
                        ph = media_list[0]
                        object_handle = ph.get_reference_handle()
                        obj = self.db.get_object_from_handle(object_handle)
                        if obj:
                            mtype = obj.get_mime_type()
                            if mtype[0:5] == "image":
                                image = ImgManip.get_thumbnail_image(obj.get_path())
                pw = PersonBoxWidget( self.format_helper, lst[i][0], positions[i][0][3], image);
                if positions[i][0][3] < 7:
                    self.tooltips.set_tip(pw, self.format_helper.format_person(lst[i][0], 11))

                pw.set_data(_PERSON,lst[i][0].get_handle())
                pw.connect("button-press-event", self.build_full_nav_menu_cb)
                if positions[i][0][2] > 1:
                    table_widget.attach(pw,x,x+w,y,y+h,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)
                else:
                    table_widget.attach(pw,x,x+w,y,y+h,gtk.FILL,gtk.FILL,0,0)
                if x+w > xmax:
                    xmax = x+w
                if y+h > ymax:
                    ymax = y+h
                
            # Connection lines
            if positions[i][1] and len(positions[i][1]) == 2:
                # separate boxes for father and mother
                x = positions[i][1][0][0]+1
                y = positions[i][1][0][1]+1
                w = 1
                h = positions[i][1][0][2]
                line = gtk.DrawingArea()
                line.set_size_request(20,-1)
                line.connect("expose-event", self.line_expose_cb)
                line.set_data("idx", i*2+1)
                if lst[i*2+1]:
                    line.set_data("rela", lst[i*2+1][1])
                table_widget.attach(line,x,x+w,y,y+h,gtk.FILL,gtk.FILL,0,0)
                if x+w > xmax:
                    xmax = x+w
                if y+h > ymax:
                    ymax = y+h
                
                x = positions[i][1][1][0]+1
                y = positions[i][1][1][1]+1
                w = 1
                h = positions[i][1][1][2]
                line = gtk.DrawingArea()
                line.set_size_request(20,-1)
                line.connect("expose-event", self.line_expose_cb)
                line.set_data("idx", i*2+2)
                if lst[i*2+2]:
                    line.set_data("rela", lst[i*2+2][1])
                table_widget.attach(line,x,x+w,y,y+h,gtk.FILL,gtk.FILL,0,0)
                if x+w > xmax:
                    xmax = x+w
                if y+h > ymax:
                    ymax = y+h
            if positions[i][1] and len(positions[i][1]) == 3:
                # combined for father and mother
                x = positions[i][1][0]+1
                y = positions[i][1][1]+1
                w = 1
                h = positions[i][1][2]
                line = gtk.DrawingArea()
                line.set_size_request(20,-1)
                line.connect("expose-event", self.tree_expose_cb)
                line.set_data("height", h)
                if lst[i] and lst[i][2]:
                    line.add_events(gtk.gdk.ENTER_NOTIFY_MASK)  # Required for tooltip and mouse-over
                    line.add_events(gtk.gdk.LEAVE_NOTIFY_MASK)  # Required for tooltip and mouse-over
                    self.tooltips.set_tip(line, self.format_helper.format_relation(lst[i][2], 11))
                if lst[i*2+1]:
                    line.set_data("frela", lst[i*2+1][1])
                if lst[i*2+2]:
                    line.set_data("mrela", lst[i*2+2][1])
                table_widget.attach(line,x,x+w,y,y+h,gtk.FILL,gtk.FILL,0,0)
                if x+w > xmax:
                    xmax = x+w
                if y+h > ymax:
                    ymax = y+h
            
            # Show marriage data
            if self.show_marriage_data and positions[i][2]:
                if lst[i] and lst[i][2]:
                    text = self.format_helper.format_relation( lst[i][2], positions[i][2][3])
                else:
                    text = " "
                label = gtk.Label(text)
                label.set_justify(gtk.JUSTIFY_LEFT)
                label.set_line_wrap(True)
                label.set_alignment(0.1,0.5)
                x = positions[i][2][0]+1
                y = positions[i][2][1]+1
                w = positions[i][2][2]
                h = positions[i][2][3]
                table_widget.attach(label,x,x+w,y,y+h,gtk.FILL,gtk.FILL,0,0)
        
        # add dummy widgets into the corners of the table to allow the pedigree to be centered
        l = gtk.Label("")
        table_widget.attach(l,0,1,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)
        l = gtk.Label("")
        table_widget.attach(l,xmax,xmax+1,ymax,ymax+1,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL,0,0)

        debug = False
        if debug:
            used_cells = {}
            xmax = 0
            ymax = 0
            # iterate table to see which cells are used.
            for c in table_widget.get_children():
                l=table_widget.child_get_property(c,"left-attach")
                r=table_widget.child_get_property(c,"right-attach")
                t=table_widget.child_get_property(c,"top-attach")
                b=table_widget.child_get_property(c,"bottom-attach")
                for x in range(l,r):
                    for y in range(t,b):
                        try:
                            used_cells[x][y] = True;
                        except KeyError:
                            used_cells[x] = {}
                            used_cells[x][y] = True;
                        if y > ymax:
                            ymax = y
                    if x > xmax:
                        xmax = x
            for x in range(0,xmax+1):
                for y in range(0,ymax+1):
                    try:
                        tmp = used_cells[x][y]
                    except KeyError:
                        # fill unused cells
                        label=gtk.Label("%d,%d"%(x,y))
                        frame = gtk.ScrolledWindow(None,None)
                        frame.set_shadow_type(gtk.SHADOW_NONE)
                        frame.set_policy(gtk.POLICY_NEVER,gtk.POLICY_NEVER)
                        frame.add_with_viewport(label)
                        table_widget.attach(frame,x,x+1,y,y+1,gtk.FILL,gtk.FILL,0,0)
        table_widget.show_all()

    def line_expose_cb(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        idx = area.get_data("idx")
        rela = area.get_data("rela")
        if not rela:
            gc.line_style = gtk.gdk.LINE_ON_OFF_DASH
        else:
            gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 3
        if idx %2 == 0:
            area.window.draw_line(gc, alloc.width, alloc.height/2, alloc.width/2,alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, 0, alloc.width/2,alloc.height/2)
        else:
            area.window.draw_line(gc, alloc.width, alloc.height/2, alloc.width/2,alloc.height/2)
            area.window.draw_line(gc, alloc.width/2, alloc.height, alloc.width/2,alloc.height/2)

    def tree_expose_cb(self, area, event):
        gc = area.window.new_gc()
        alloc = area.get_allocation()
        h = area.get_data("height")
        gap = alloc.height / (h*2)
        frela = area.get_data("frela")
        mrela = area.get_data("mrela")
        if not frela and not mrela:
            gc.line_style = gtk.gdk.LINE_ON_OFF_DASH
        else:
            gc.line_style = gtk.gdk.LINE_SOLID
        gc.line_width = 3
        rela = area.get_data("mrela")
        area.window.draw_line(gc, 0, alloc.height/2, alloc.width/2,alloc.height/2)

        if not frela:
            gc.line_style = gtk.gdk.LINE_ON_OFF_DASH
        else:
            gc.line_style = gtk.gdk.LINE_SOLID
        area.window.draw_line(gc, alloc.width/2, alloc.height/2, alloc.width/2,gap)
        area.window.draw_line(gc, alloc.width/2, gap, alloc.width,gap)
        
        if not mrela:
            gc.line_style = gtk.gdk.LINE_ON_OFF_DASH
        else:
            gc.line_style = gtk.gdk.LINE_SOLID
        area.window.draw_line(gc, alloc.width/2, alloc.height/2, alloc.width/2,alloc.height-gap)
        area.window.draw_line(gc, alloc.width/2, alloc.height-gap, alloc.width,alloc.height-gap)

    def home(self,obj):
        defperson = self.dbstate.db.get_default_person()
        if defperson:
            self.dbstate.change_active_person(defperson)

    def edit_person_cb(self,obj):
        person_handle = obj.get_data(_PERSON)
        person = self.db.get_person_from_handle(person_handle)
        if person:
            EditPerson.EditPerson(self.dbstate, self.uistate, [], person, self.person_edited_cb)
            return True
        return False

    def on_show_option_menu_cb(self,obj,data=None):
        myMenu = gtk.Menu()
        self.add_settings_to_menu(myMenu)
        myMenu.popup(None,None,None,0,0)
        return(True);
    
    def on_show_child_menu(self,obj):
        """User clicked button to move to child of active person"""

        if self.dbstate.active:
            # Build and display the menu attached to the left pointing arrow
            # button. The menu consists of the children of the current root
            # person of the tree. Attach a child to each menu item.

            childlist = find_children(self.db,self.dbstate.active)
            if len(childlist) == 1:
                child = self.db.get_person_from_handle(childlist[0])
                if child:
                    self.dbstate.change_active_person(child)
            elif len(childlist) > 1:
                myMenu = gtk.Menu()
                for child_handle in childlist:
                    child = self.db.get_person_from_handle(child_handle)
                    cname = NameDisplay.displayer.display(child)
                    menuitem = gtk.MenuItem(None)
                    if find_children(self.db,child):
                        label = gtk.Label('<b><i>%s</i></b>' % cname)
                    else:
                        label = gtk.Label(cname)
                    label.set_use_markup(True)
                    label.show()
                    label.set_alignment(0,0)
                    menuitem.add(label)
                    myMenu.append(menuitem)
                    menuitem.set_data(_PERSON,child_handle)
                    menuitem.connect("activate",self.on_childmenu_changed)
                    menuitem.show()
                myMenu.popup(None,None,None,0,0)
            return 1
        return 0

    def on_childmenu_changed(self,obj):
        """Callback for the pulldown menu selection, changing to the person
           attached with menu item."""

        person_handle = obj.get_data(_PERSON)
        if person_handle:
            self.dbstate.change_active_handle(person_handle)
            return True
        return False
    
    def change_force_size_cb(self,event,data):
        if data in [0,2,3,4,5]:
            self.force_size = data
            self.size_request_cb(self.notebook.parent,None) # switch to matching size

    def change_tree_style_cb(self,event,data):
        if data in [0,1]:
            if self.tree_style != data:
                self.tree_style = data
                self.rebuild_trees(self.dbstate.active) # Rebuild using new style

    def change_show_images_cb(self,event):
        self.show_images = not self.show_images
        self.rebuild_trees(self.dbstate.active) # Rebuild using new style

    def change_show_marriage_cb(self,event):
        self.show_marriage_data = not self.show_marriage_data
        self.rebuild_trees(self.dbstate.active) # Rebuild using new style

    def find_tree(self,person,index,depth,lst,val=0):
        """Recursively build a list of ancestors"""

        if depth > 5 or person == None:
            return
        lst[index] = (person,val,None)

        parent_families = person.get_parent_family_handle_list()
        if parent_families:
            (family_handle,m,f) = parent_families[0]
        else:
            return
        if family_handle:
            mrel = m != RelLib.Person.CHILD_BIRTH
            frel = f != RelLib.Person.CHILD_BIRTH

        family = self.db.get_family_from_handle(family_handle)
        if family != None:
            lst[index] = (person,val,family)
            father_handle = family.get_father_handle()
            if father_handle != None:
                father = self.db.get_person_from_handle(father_handle)
                self.find_tree(father,(2*index)+1,depth+1,lst,frel)
            mother_handle = family.get_mother_handle()
            if mother_handle != None:
                mother = self.db.get_person_from_handle(mother_handle)
                self.find_tree(mother,(2*index)+2,depth+1,lst,mrel)

    def add_nav_portion_to_menu(self,menu):
        """
        This function adds a common history-navigation portion 
        to the context menu. Used by both build_nav_menu() and 
        build_full_nav_menu() methods. 
        """
        #back_sensitivity = self.parent.hindex > 0 
        #fwd_sensitivity = self.parent.hindex + 1 < len(self.parent.history)
        entries = [
            #(gtk.STOCK_GO_BACK,self.parent.back_clicked,back_sensitivity),
            #(gtk.STOCK_GO_FORWARD,self.parent.fwd_clicked,fwd_sensitivity),
            #FIXME: revert to stock item when German gtk translation is fixed
            #(gtk.STOCK_HOME,self.parent.on_home_clicked,1),
            (_("Home"),self.home,1),
            (None,None,0),
            #(_("Set anchor"),self.on_anchor_set,1),
            #(_("Remove anchor"),self.on_anchor_removed,1),
        ]

        for stock_id,callback,sensitivity in entries:
            item = gtk.ImageMenuItem(stock_id)
            #FIXME: remove when German gtk translation is fixed
            if stock_id == _("Home"):
                im = gtk.image_new_from_stock(gtk.STOCK_HOME,gtk.ICON_SIZE_MENU)
                im.show()
                item.set_image(im)
            if callback:
                item.connect("activate",callback)
            item.set_sensitive(sensitivity)
            item.show()
            menu.append(item)

    def add_settings_to_menu(self,menu):
        entry = gtk.ImageMenuItem(_("Show images"))
        if self.show_images:
            current_show_images_image = gtk.image_new_from_stock(gtk.STOCK_APPLY,gtk.ICON_SIZE_MENU)
            current_show_images_image.show()
            entry.set_image(current_show_images_image)
        entry.connect("activate", self.change_show_images_cb)
        entry.show()
        menu.append(entry)

        entry = gtk.ImageMenuItem(_("Show marriage data"))
        if self.show_marriage_data:
            current_show_marriage_image = gtk.image_new_from_stock(gtk.STOCK_APPLY,gtk.ICON_SIZE_MENU)
            current_show_marriage_image.show()
            entry.set_image(current_show_marriage_image)
        entry.connect("activate", self.change_show_marriage_cb)
        entry.show()
        menu.append(entry)

        item = gtk.MenuItem(_("Tree style"))
        item.set_submenu(gtk.Menu())
        style_menu = item.get_submenu()

        current_style_image = gtk.image_new_from_stock(gtk.STOCK_APPLY,gtk.ICON_SIZE_MENU)
        current_style_image.show()

        entry = gtk.ImageMenuItem(_("Version A"))
        entry.connect("activate", self.change_tree_style_cb,0)
        if self.tree_style == 0:
            entry.set_image(current_style_image)
        entry.show()
        style_menu.append(entry)

        entry = gtk.ImageMenuItem(_("Version B"))
        entry.connect("activate", self.change_tree_style_cb,1)
        if self.tree_style == 1:
            entry.set_image(current_style_image)
        entry.show()
        style_menu.append(entry)

        style_menu.show()
        item.show()
        menu.append(item)


        item = gtk.MenuItem(_("Tree size"))
        item.set_submenu(gtk.Menu())
        size_menu = item.get_submenu()
        
        current_size_image = gtk.image_new_from_stock(gtk.STOCK_APPLY,gtk.ICON_SIZE_MENU)
        current_size_image.show()

        entry = gtk.ImageMenuItem(_("Automatic"))
        entry.connect("activate", self.change_force_size_cb,0)
        if self.force_size == 0:
            entry.set_image(current_size_image)
        entry.show()
        size_menu.append(entry)

        for n in range(2,6):
            entry = gtk.ImageMenuItem(_("%d generations") % n)
            if self.force_size == n:
                entry.set_image(current_size_image)
            entry.connect("activate", self.change_force_size_cb,n)
            entry.show()
            size_menu.append(entry)
        
        size_menu.show()
        item.show()
        menu.append(item)
        

    def build_full_nav_menu_cb(self,obj,event):
        """
        Builds the full menu (including Siblings, Spouses, Children, 
        and Parents) with navigation.
        """
        
        menu = gtk.Menu()
        menu.set_title(_('People Menu'))

        person_handle = obj.get_data(_PERSON)
        person = self.db.get_person_from_handle(person_handle)
        if not person:
            return 0

        go_image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
        go_image.show()
        go_item = gtk.ImageMenuItem(NameDisplay.displayer.display(person))
        go_item.set_image(go_image)
        go_item.set_data(_PERSON,person_handle)
        go_item.connect("activate",self.on_childmenu_changed)
        go_item.show()
        menu.append(go_item)

        #edit_image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
        #edit_image.show()
        edit_item = gtk.ImageMenuItem(gtk.STOCK_EDIT)
        #edit_item.set_image(edit_image)
        edit_item.set_data(_PERSON,person_handle)
        edit_item.connect("activate",self.edit_person_cb)
        edit_item.show()
        menu.append(edit_item)

        # collect all spouses, parents and children
        linked_persons = []
        
        # Go over spouses and build their menu
        item = gtk.MenuItem(_("Spouses"))
        fam_list = person.get_family_handle_list()
        no_spouses = 1
        for fam_id in fam_list:
            family = self.db.get_family_from_handle(fam_id)
            if family.get_father_handle() == person.get_handle():
                sp_id = family.get_mother_handle()
            else:
                sp_id = family.get_father_handle()
            spouse = self.db.get_person_from_handle(sp_id)
            if not spouse:
                continue

            if no_spouses:
                no_spouses = 0
                item.set_submenu(gtk.Menu())
                sp_menu = item.get_submenu()

            go_image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
            go_image.show()
            sp_item = gtk.ImageMenuItem(NameDisplay.displayer.display(spouse))
            sp_item.set_image(go_image)
            sp_item.set_data(_PERSON,sp_id)
            linked_persons.append(sp_id)
            sp_item.connect("activate",self.on_childmenu_changed)
            sp_item.show()
            sp_menu.append(sp_item)

        if no_spouses:
            item.set_sensitive(0)

        item.show()
        menu.append(item)
        
        # Go over siblings and build their menu
        item = gtk.MenuItem(_("Siblings"))
        pfam_list = person.get_parent_family_handle_list()
        no_siblings = 1
        for (f,mrel,frel) in pfam_list:
            fam = self.db.get_family_from_handle(f)
            sib_list = fam.get_child_handle_list()
            for sib_id in sib_list:
                if sib_id == person.get_handle():
                    continue
                sib = self.db.get_person_from_handle(sib_id)
                if not sib:
                    continue

                if no_siblings:
                    no_siblings = 0
                    item.set_submenu(gtk.Menu())
                    sib_menu = item.get_submenu()

                if find_children(self.db,sib):
                    label = gtk.Label('<b><i>%s</i></b>' % escape(NameDisplay.displayer.display(sib)))
                else:
                    label = gtk.Label(escape(NameDisplay.displayer.display(sib)))

                go_image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
                go_image.show()
                sib_item = gtk.ImageMenuItem(None)
                sib_item.set_image(go_image)
                label.set_use_markup(True)
                label.show()
                label.set_alignment(0,0)
                sib_item.add(label)
                sib_item.set_data(_PERSON,sib_id)
                linked_persons.append(sib_id)
                sib_item.connect("activate",self.on_childmenu_changed)
                sib_item.show()
                sib_menu.append(sib_item)

        if no_siblings:
            item.set_sensitive(0)
        item.show()
        menu.append(item)
        
        # Go over children and build their menu
        item = gtk.MenuItem(_("Children"))
        no_children = 1
        childlist = find_children(self.db,person)
        for child_handle in childlist:
            child = self.db.get_person_from_handle(child_handle)
            if not child:
                continue
        
            if no_children:
                no_children = 0
                item.set_submenu(gtk.Menu())
                child_menu = item.get_submenu()

            if find_children(self.db,child):
                label = gtk.Label('<b><i>%s</i></b>' % escape(NameDisplay.displayer.display(child)))
            else:
                label = gtk.Label(escape(NameDisplay.displayer.display(child)))

            go_image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
            go_image.show()
            child_item = gtk.ImageMenuItem(None)
            child_item.set_image(go_image)
            label.set_use_markup(True)
            label.show()
            label.set_alignment(0,0)
            child_item.add(label)
            child_item.set_data(_PERSON,child_handle)
            linked_persons.append(child_handle)
            child_item.connect("activate",self.on_childmenu_changed)
            child_item.show()
            child_menu.append(child_item)

        if no_children:
            item.set_sensitive(0)
        item.show()
        menu.append(item)

        # Go over parents and build their menu
        item = gtk.MenuItem(_("Parents"))
        no_parents = 1
        par_list = find_parents(self.db,person)
        for par_id in par_list:
            par = self.db.get_person_from_handle(par_id)
            if not par:
                continue

            if no_parents:
                no_parents = 0
                item.set_submenu(gtk.Menu())
                par_menu = item.get_submenu()

            if find_parents(self.db,par):
                label = gtk.Label('<b><i>%s</i></b>' % escape(NameDisplay.displayer.display(par)))
            else:
                label = gtk.Label(escape(NameDisplay.displayer.display(par)))

            go_image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
            go_image.show()
            par_item = gtk.ImageMenuItem(None)
            par_item.set_image(go_image)
            label.set_use_markup(True)
            label.show()
            label.set_alignment(0,0)
            par_item.add(label)
            par_item.set_data(_PERSON,par_id)
            linked_persons.append(par_id)
            par_item.connect("activate",self.on_childmenu_changed)
            par_item.show()
            par_menu.append(par_item)

        if no_parents:
            item.set_sensitive(0)
        item.show()
        menu.append(item)
    
        # Go over parents and build their menu
        item = gtk.MenuItem(_("Related"))
        no_related = 1
        for p_id in find_witnessed_people(self.db,person):
            #if p_id in linked_persons:
            #    continue    # skip already listed family members
            
            per = self.db.get_person_from_handle(p_id)
            if not per:
                continue

            if no_related:
                no_related = 0
                item.set_submenu(gtk.Menu())
                per_menu = item.get_submenu()

            label = gtk.Label(escape(NameDisplay.displayer.display(per)))

            go_image = gtk.image_new_from_stock(gtk.STOCK_JUMP_TO,gtk.ICON_SIZE_MENU)
            go_image.show()
            per_item = gtk.ImageMenuItem(None)
            per_item.set_image(go_image)
            label.set_use_markup(True)
            label.show()
            label.set_alignment(0,0)
            per_item.add(label)
            per_item.set_data(_PERSON,p_id)
            per_item.connect("activate",self.on_childmenu_changed)
            per_item.show()
            per_menu.append(per_item)
        
        if no_related:
            item.set_sensitive(0)
        item.show()
        menu.append(item)
            
        
        # Add separator
        item = gtk.MenuItem(None)
        item.show()
        menu.append(item)

        # Add history-based navigation
        self.add_nav_portion_to_menu(menu)
        self.add_settings_to_menu(menu)
        menu.popup(None,None,None,event.button,event.time)
        return 1
            

#-------------------------------------------------------------------------
#
# Function to return children's list of a person
#
#-------------------------------------------------------------------------
def find_children(db,p):
    """
    Returns the list of all children's IDs for a person.
    """
    childlist = []
    for family_handle in p.get_family_handle_list():
        family = db.get_family_from_handle(family_handle)
        for child_handle in family.get_child_handle_list():
            childlist.append(child_handle)
    return childlist

#-------------------------------------------------------------------------
#
# Function to return parent's list of a person
#
#-------------------------------------------------------------------------
def find_parents(db,p):
    """
    Returns the unique list of all parents' IDs for a person.
    """
    parentlist = []
    for (f,mrel,frel) in p.get_parent_family_handle_list():
        family = db.get_family_from_handle(f)
        father_handle = family.get_father_handle()
        mother_handle = family.get_mother_handle()
        if father_handle not in parentlist:
            parentlist.append(father_handle)
        if mother_handle not in parentlist:
            parentlist.append(mother_handle)
    return parentlist

#-------------------------------------------------------------------------
#
# Function to return persons, that share the same event.
# This for example links witnesses to the tree
#
#-------------------------------------------------------------------------
def find_witnessed_people(db,p):
    people = []
    for event_ref in p.get_event_ref_list():
        for l in db.find_backlink_handles( event_ref.ref):
            if l[0] == 'Person' and l[1] != p.get_handle():
                people.append(l[1])
            if l[0] == 'Family':
                fam = db.get_family_from_handle(l[1])
                if fam:
                    father_handle = fam.get_father_handle()
                    if father_handle and father_handle != p.get_handle():
                        people.append(father_handle)
                    mother_handle = fam.get_mother_handle()
                    if mother_handle and mother_handle != p.get_handle():
                        people.append(mother_handle)
    for f in p.get_family_handle_list():
        family = db.get_family_from_handle(f)
        for event_ref in family.get_event_ref_list():
            for l in db.find_backlink_handles( event_ref.ref):
                if l[0] == 'Person' and l[1] != p.get_handle():
                    people.append(l[1])
    return people

#-------------------------------------------------------------------------
#
# Functions to build the text displayed in the details view of a DispBox
# aditionally used by PedigreeView to get the largest area covered by a DispBox
#
#-------------------------------------------------------------------------
def build_detail_string(db,person):

    detail_text = NameDisplay.displayer.display(person)

    def format_event(db, label, event):
        if not event:
            return u""
        ed = DateHandler.get_date(event)
        ep = None
        place_handle = event.get_place_handle()
        if place_handle:
            place_title = db.get_place_from_handle(place_handle).get_title()
            if place_title != "":
                if len(place_title) > 15:
                    ep = place_title[:14]+"..."
                else:
                    ep = place_title
        if ep:
            return u"\n%s %s, %s" % (label,ed,ep)
        return u"\n%s %s" % (label,ed)

    
    birth_ref = person.get_birth_ref()
    if birth_ref:
        detail_text += format_event(db, _BORN,
                                    db.get_event_from_handle(birth_ref.ref))
    else:
        for event_ref in person.get_event_ref_list():
            event = db.get_event_from_handle(event_ref.ref)
            if event and event.get_type()[0] == RelLib.Event.BAPTISM:
                detail_text += format_event(db, _BAPT, event)
                break
            if event and event.get_type()[0] == RelLib.Event.CHRISTEN:
                detail_text += format_event(db, _CHRI, event)
                break

    death_ref = person.get_death_ref()
    if death_ref:
        detail_text += format_event(db, _DIED,
                                    db.get_event_from_handle(death_ref.ref))
    else:
        for event_ref in person.get_event_ref_list():
            event = db.get_event_from_handle(event_ref.ref)
            if event and event.get_type()[0] == RelLib.Event.BURIAL:
                detail_text += format_event(db, _BURI, event)
                break
            if event and event.get_type()[0] == RelLib.Event.CREMATION:
                detail_text += format_event(db, _CREM, event)
                break

    return detail_text
