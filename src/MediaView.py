#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2003  Donald N. Allingham
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
import string
import os

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
# gramps modules
#
#-------------------------------------------------------------------------
import RelLib
import Utils
import GrampsCfg
import const
import ImageSelect
import RelImage

from QuestionDialog import QuestionDialog, ErrorDialog, WarningDialog

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# MediaView
#
#-------------------------------------------------------------------------
class MediaView:
    def __init__(self,db,glade,update):
        self.db = db
        self.list = glade.get_widget("media_list")
        self.mid = glade.get_widget("mid")
        self.mtype = glade.get_widget("mtype")
        self.mdesc = glade.get_widget("mdesc")
        self.mpath = glade.get_widget("mpath")
        self.mdetails = glade.get_widget("mdetails")
        self.preview = glade.get_widget("preview")

        self.column_headers = [(_('Title'),4,350), (_('ID'),1,50),
                               (_('Type'),2,70), ('Path',3,150), ('',4,0) ]

        self.id2col = {}
        self.selection = self.list.get_selection()

        colno = 0
        for title in self.column_headers:
            renderer = gtk.CellRendererText ()
            column = gtk.TreeViewColumn (title[0], renderer, text=colno)
            colno = colno + 1
            column.set_clickable (gtk.TRUE)
            if title[0] == '':
                column.set_visible(gtk.FALSE)
            else:
                column.set_resizable(gtk.TRUE)
                column.set_visible(gtk.TRUE)
            if title[1] >= 0:
                column.set_sort_column_id(title[1])
            column.set_min_width(title[2])
            self.list.append_column(column)

        self.list.set_search_column(0)
        self.model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                                   gobject.TYPE_STRING, gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        self.list.set_model(self.model)
        self.list.get_column(0).clicked()

        t = [ ('STRING', 0, 0),
              ('text/plain',0,0),
              ('text/uri-list',0,2),
              ('application/x-rootwin-drop',0,1)]

        self.list.drag_source_set(gtk.gdk.BUTTON1_MASK|gtk.gdk.BUTTON3_MASK,
                                  t,gtk.gdk.ACTION_COPY)
        self.list.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                                t,gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE)


        self.list.connect("drag_data_received", self.on_drag_data_received)
        self.list.connect("drag_data_get", self.on_drag_data_get)
        self.list.connect("drag_begin", self.on_drag_begin)

        self.update = update
        self.list.connect('button-press-event',self.on_button_press_event)
        self.selection.connect('changed',self.on_select_row)
        if not (RelImage.is_pil() or RelImage.is_cnv() ):
	    WarningDialog(_("Thumbnails not available")
                ,_("There is no suitable tool to generate thumbnails for the images. "
                "If you would like to enable this feature, "
                "install Python Imaging Library (PIL), available at http://www.pythonware.com/products/pil/ "
                "or ImageMagick, available at http://www.imagemagick.org/"))

    def goto(self,id):
        self.selection.unselect_all()
        self.selection.select_iter(self.id2col[id])

    def change_db(self,db):
        self.db = db

    def on_select_row(self,obj):
        fexists = 1

        store,iter = self.selection.get_selected()
        if not iter:
            return
        
        id = store.get_value(iter,1)
        
        mobj = self.db.findObjectNoMap(id)
        type = mobj.getMimeType()
        type_name = Utils.get_mime_description(type)
        path = mobj.getPath()
        thumb_path = Utils.thumb_path(self.db.getSavePath(),mobj)
        pexists = os.path.exists(path)
        if pexists and os.path.exists(thumb_path):
            self.preview.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(thumb_path))
        else:
            icon_image = gtk.gdk.pixbuf_new_from_file(Utils.find_icon(type))
            self.preview.set_from_pixbuf(icon_image)
            if not pexists:
                fexists = 0
        
        self.mid.set_text(mobj.getId())
        self.mtype.set_text(type_name)
        self.mdesc.set_text(mobj.getDescription())
        if len(path) == 0 or fexists == 0:
            self.mpath.set_text(_("The file no longer exists"))
        elif path[0] == "/":
            self.mpath.set_text(path)
        else:
            self.mpath.set_text("<local>")
        self.mdetails.set_text(Utils.get_detail_text(mobj,0))

    def on_button_press_event(self,obj,event):
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            self.on_edit_clicked(obj)
            return 1
        elif event.button == 3:
            self.build_context_menu()
            return 1
        return 0

    def build_context_menu(self):
        menu = gtk.Menu()
        menu.set_title(_("Media Object"))

        store,iter = self.selection.get_selected()
        if iter:
            id = store.get_value(iter,1)
            object = self.db.findObjectNoMap(id)
            self.obj = object
            Utils.add_menuitem(menu,_("View in the default viewer"),None,self.popup_view_photo)
            if object.getMimeType()[0:5] == "image":
                Utils.add_menuitem(menu,_("Edit with the GIMP"),\
                                   None,self.popup_edit_photo)
            if object.getLocal() == 0:
                Utils.add_menuitem(menu,_("Convert to local copy"),None,
                                   self.popup_convert_to_private)
            item = gtk.MenuItem()
            item.show()
            menu.append(item)
            sel_sensitivity = 1
        else:
            sel_sensitivity = 0
        
        entries = [
            (gtk.STOCK_ADD, self.on_add_clicked,1),
            (gtk.STOCK_REMOVE, self.on_delete_clicked,sel_sensitivity),
            (_("Edit properties"), self.on_edit_clicked,sel_sensitivity),
        ]

        for stock_id,callback,sensitivity in entries:
            item = gtk.ImageMenuItem(stock_id)
            if callback:
                item.connect("activate",callback)
            item.set_sensitive(sensitivity)
            item.show()
            menu.append(item)
        menu.popup(None,None,None,0,0)

    def popup_view_photo(self, obj):
        Utils.view_photo(self.obj)
    
    def popup_edit_photo(self, obj):
        if os.fork() == 0:
            os.execvp(const.editor,[const.editor, self.obj.getPath()])
    
    def popup_convert_to_private(self, obj):
        path = self.db.getSavePath()
        id = self.obj.getId()
        name = RelImage.import_media_object(self.obj.getPath(),path,id)
        if name:
            self.obj.setPath(name)
            self.obj.setLocal(1)

    def popup_change_description(self, obj):
        ImageSelect.GlobalMediaProperties(self.db,self.obj,self.load_media)

    def load_media(self):
        self.model.clear()
        self.id2col = {}

        objects = self.db.getObjectMap().values()

        for src in objects:
            title = src.getDescription()
            id = src.getId()
            type = Utils.get_mime_description(src.getMimeType())
            if src.getLocal():
                path = "<local copy>"
            else:
                path = src.getPath()
            stitle = string.upper(title)

            iter = self.model.append()
            self.id2col[id] = iter
            self.model.set(iter, 0, title, 1, id, 2, type, 3, path, 4, stitle)


    def on_add_clicked(self,obj):
        """Add a new media object to the media list"""
        import AddMedia
        am = AddMedia.AddMediaObject(self.db,self.load_media)
        am.run()

    def on_edit_clicked(self,obj):
        """Edit the properties of an existing media object in the media list"""

        list_store, iter = self.selection.get_selected()
        if iter:
            id = list_store.get_value(iter,1)
            object = self.db.getObject(id)
            ImageSelect.GlobalMediaProperties(self.db,object,self.load_media)

    def on_delete_clicked(self,obj):
        store,iter = self.selection.get_selected()
        if not iter:
            return

        id = store.get_value(iter,1)
        mobj = self.db.getObject(id)
        if self.is_object_used(mobj):
            ans = ImageSelect.DeleteMediaQuery(mobj,self.db,self.update)
            QuestionDialog(_('Delete Media Object?'),
                           _('This media object is currently being used. '
                             'If you delete this object, it will be removed '
                             'from the database and from all records that '
                             'reference it.'),
                           _('_Delete Media Object'),
                           ans.query_response)
        else:
            self.db.removeObject(mobj.getId())
            Utils.modified()
            self.update(0)

    def is_object_used(self,mobj):
        for p in self.db.getFamilyMap().values():
            for o in p.getPhotoList():
                if o.getReference() == mobj:
                    return 1
        for key in self.db.getPersonKeys():
            p = self.db.getPerson(key)
            for o in p.getPhotoList():
                if o.getReference() == mobj:
                    return 1
        for key in self.db.getSourceKeys():
            p = self.db.getSource(key)
            for o in p.getPhotoList():
                if o.getReference() == mobj:
                    return 1
        for key in self.db.getPlaceKeys():
            p = self.db.getPlace(key)
            for o in p.getPhotoList():
                if o.getReference() == mobj:
                    return 1
        return 0

    def on_drag_begin(self,obj,context):
        store,iter = self.selection.get_selected()
        if not iter:
            return
        if (const.dnd_images):
            object = self.db.getObject(store.get_value(iter,1))
            mtype = object.getMimeType()
            name = Utils.thumb_path(self.db.getSavePath(),object)
            pix = gtk.gdk.pixbuf_new_from_file(name)
            context.set_icon_pixbuf(pix,0,0)

    def on_drag_data_get(self,w, context, selection_data, info, time):
        if info == 1:
            return

        store,iter = self.selection.get_selected()
        if not iter:
            return
        id = store.get_value(iter,1)
        selection_data.set(selection_data.target, 8, id)	

    def on_drag_data_received(self,w, context, x, y, data, info, time):
        import urlparse
        if data and data.format == 8:
            d = string.strip(string.replace(data.data,'\0',' '))
            protocol,site,file, j,k,l = urlparse.urlparse(d)
            if protocol == "file":
                name = file
                mime = Utils.get_mime_type(name)
                photo = RelLib.Photo()
                photo.setPath(name)
                photo.setMimeType(mime)
                description = os.path.basename(name)
                photo.setDescription(description)
                self.db.addObject(photo)
                Utils.modified()
                self.load_media()
                if GrampsCfg.mediaref == 0:
                    name = RelImage.import_media_object(name,
                                                        self.db.getSavePath(),
                                                        photo.getId())
                    if name:
                        photo.setPath(name)
                        photo.setLocal(1)
                Utils.modified()
                if GrampsCfg.globalprop:
                    ImageSelect.GlobalMediaProperties(self.db,photo,self.load_media)
            elif protocol != "":
                import urllib
                u = urllib.URLopener()
                try:
                    tfile,headers = u.retrieve(d)
                except IOError, msg:
                    ErrorDialog(_('Image import failed'),str(msg))
                    return
                mime = Utils.get_mime_type(tfile)
                photo = RelLib.Photo()
                photo.setMimeType(mime)
                photo.setDescription(d)
                photo.setLocal(1)
                photo.setPath(tfile)
                self.db.addObject(photo)
                oref = RelLib.ObjectRef()
                oref.setReference(photo)
                try:
                    id = photo.getId()
                    path = self.db.getSavePath()
                    name = RelImage.import_media_object(tfile,path,id)
                    if name:
                        photo.setLocal(1)
                        photo.setPath(name)
                except:
                    photo.setPath(tfile)
                    return
                Utils.modified()
                if GrampsCfg.globalprop:
                    ImageSelect.GlobalMediaProperties(self.db,photo,None)

    
