# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009         Douglas S. Blank <doug.blank@gmail.com>
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
#

"""
Main view handlers
Each object can be operated on with the following actions:
   view: show the data
   delete: delete the object (FIXME: needs undo)
   edit: show the data in its editing widget
     save: action in the form in edit mode; write data to db
   add: show blank data in their editing widget
     create: action in the form in edit mode; add new data to db
"""

import os
import cPickle
import base64

#------------------------------------------------------------------------
#
# Django Modules
#
#------------------------------------------------------------------------
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import Context, RequestContext
from django.db.models import Q
from django.forms.models import modelformset_factory

#------------------------------------------------------------------------
#
# Gramps Modules
#
#------------------------------------------------------------------------
import webapp
from webapp.utils import _, build_args
from webapp.grampsdb.models import *
from webapp.grampsdb.view import *
from webapp.dbdjango import DbDjango
import cli.user
import gen.proxy
from gen.const import VERSION

# Menu: (<Nice name>, /<path>/, <Model> | None, Need authentication ) 
MENU = [
    (_('Browse'), 'browse', None, False),
    (_('Reports'), 'report', Report, True),
    (_('User'), 'user', None, True),
]
# Views: [(<Nice name plural>, /<name>/handle, <Model>), ]
VIEWS = [
    (_('People'), 'person', Name), 
    (_('Families'), 'family', Family),
    (_('Events'), 'event', Event),
    (_('Notes'), 'note', Note),
    (_('Media'), 'media', Media),
    (_('Citations'), 'citation', Citation),
    (_('Sources'), 'source', Source),
    (_('Places'), 'place', Place),
    (_('Repositories'), 'repository', Repository),
    (_('Tags'), 'tag', Tag),
    ]

def context_processor(request):
    """
    This function is executed before template processing.
    takes a request, and returns a dictionary context.
    """
    global SITENAME
    context = {}
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        context["css_theme"] = profile.theme_type.name
    else:
        context["css_theme"] = "Web_Mainz.css"
    # Other things for all environments:
    context["gramps_version"] = VERSION
    context["views"] = VIEWS
    context["menu"] = MENU
    context["None"] = None
    context["True"] = True
    context["False"] = False
    context["sitename"] = Config.objects.get(setting="sitename").value
    context["default"] = ""

    search = request.GET.get("search", "") or request.POST.get("search", "")
    page = request.GET.get("page", "") or request.POST.get("page", "")
    context["page"] = page 
    context["search"] = search 
    context["args"] = build_args(search=search, page=page)
    return context

def main_page(request):
    """
    Show the main page.
    """
    context = RequestContext(request)
    context["view"] = 'home'
    context["tview"] = _('Home')
    return render_to_response("main_page.html", context)
                              
def logout_page(request):
    """
    Logout a user.
    """
    context = RequestContext(request)
    context["view"] = 'home'
    context["tview"] = _('Home')
    logout(request)
    return HttpResponseRedirect('/')

def make_message(request, message):
    if request.user.is_authenticated():
        request.user.message_set.create(message = message)
    else:
        request.session['message'] = message

def browse_page(request):
    """
    Show the main list under 'Browse' on the main menu.
    """
    context = RequestContext(request)
    context["view"] = 'browse'
    context["tview"] = _('Browse')
    return render_to_response('browse_page.html', context)

def user_page(request, username=None):
    """
    Show the user page.
    """
    if request.user.is_authenticated():
        if username is None:
            profile = request.user.get_profile()
            username = profile.user.username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404(_('Requested user not found.'))
        context = RequestContext(request)
        context["username"] =  username
        context["view"] = 'user'
        context["tview"] = _('User')
        return render_to_response('user_page.html', context)
    else:
        raise Http404(_("Requested page is not accessible."))

def send_file(request, filename, mimetype):
    """                                                                         
    Send a file through Django without loading the whole file into              
    memory at once. The FileWrapper will turn the file object into an           
    iterator for chunks of 8KB.                                                 
    """
    from django.core.servers.basehttp import FileWrapper
    wrapper = FileWrapper(file(filename))
    response = HttpResponse(wrapper, mimetype=mimetype)
    path, base = os.path.split(filename)
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = 'attachment; filename=%s' % base
    return response

def process_report_run(request, handle):
    """
    Run a report or export.
    """
    from webapp.reports import import_file, export_file, download
    from cli.plug import run_report
    import traceback
    db = DbDjango()
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        report = Report.objects.get(handle=handle)
        args = {"off": "pdf", "iff": "ged"} # basic defaults
        # override from given defaults in table:
        if report.options:
            for pair in str(report.options).split(" "):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    args[key] = value
        # override from options on webpage:
        if request.GET.has_key("options"):
            options = str(request.GET.get("options"))
            if options:
                for pair in options.split(" "): # from webpage
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        args[key] = value
        #############################################################################
        if report.report_type == "report":
            filename = "/tmp/%s-%s.%s" % (str(profile.user.username), str(handle), args["off"])
            run_report(db, handle, of=filename, **args)
            mimetype = 'application/%s' % args["off"]
        elif report.report_type == "export":
            filename = "/tmp/%s-%s.%s" % (str(profile.user.username), str(handle), args["off"])
            export_file(db, filename, cli.user.User()) # callback
            mimetype = 'text/plain'
        elif report.report_type == "import":
            filename = download(args["i"], "/tmp/%s-%s.%s" % (str(profile.user.username), 
                                                              str(handle),
                                                              args["iff"]))
            if filename is not None:
                if True: # run in background, with error handling
                    import threading
                    def background():
                        try:
                            import_file(db, filename, cli.user.User()) # callback
                        except:
                            make_message(request, "import_file failed: " + traceback.format_exc())
                    threading.Thread(target=background).start()
                    make_message(request, "Your data is now being imported...")
                    return redirect("/report/")
                else:
                    success = import_file(db, filename, cli.user.User()) # callback
                    if not success:
                        make_message(request, "Failed to load imported.")
                    return redirect("/report/")
            else:
                make_message(request, "No filename was provided or found.")
                return redirect("/report/")
        else:
            make_message(request, "Invalid report type '%s'" % report.report_type)
            return redirect("/report/")
        if os.path.exists(filename):
            return send_file(request, filename, mimetype)
        else:
            context = RequestContext(request)
            make_message(request, "Failed: '%s' is not found" % filename)
            return redirect("/report/")
    # If failure, just fail for now:
    context = RequestContext(request)
    context["message"] = "You need to be logged in."
    return render_to_response("process_action.html", context)

def view_list(request, view):
    """
    Borwse each of the primary tables.
    """
    context = RequestContext(request)
    search = ""
    if view == "event":
        context["tviews"] = _("Events")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_event_query(request, search)
        object_list = Event.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_events.html'
        total = Event.objects.all().count()
    elif view == "media":
        context["tviews"] = _("Media")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_media_query(request, search)
        object_list = Media.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_media.html'
        total = Media.objects.all().count()
    elif view == "note":
        context["tviews"] = _("Notes")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_note_query(request, search)
        object_list = Note.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_notes.html'
        total = Note.objects.all().count()
    elif view == "person":
        context["tviews"] = _("People")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_person_query(request, search)
        object_list = Name.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_people.html'
        total = Name.objects.all().count()
    elif view == "family":
        context["tviews"] = _("Families")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_family_query(request, search)
        object_list = Family.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_families.html'
        total = Family.objects.all().count()
    elif view == "place":
        context["tviews"] = _("Places")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_place_query(request, search)
        object_list = Place.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_places.html'
        total = Place.objects.all().count()
    elif view == "repository":
        context["tviews"] = _("Repositories")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_repository_query(request, search)
        object_list = Repository.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_repositories.html'
        total = Repository.objects.all().count()
    elif view == "citation":
        context["tviews"] = _("Citations")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_citation_query(request, search)
        object_list = Citation.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_citations.html'
        total = Citation.objects.all().count()
    elif view == "source":
        context["tviews"] = _("Sources")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_source_query(request, search)
        object_list = Source.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_sources.html'
        total = Source.objects.all().count()
    elif view == "tag":
        context["tviews"] = _("Tags")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_tag_query(request, search)
        object_list = Tag.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_tags.html'
        total = Tag.objects.all().count()
    elif view == "report":
        context["tviews"] = _("Reports")
        search = request.GET.get("search") if request.GET.has_key("search") else ""
        query, order, terms = build_report_query(request, search)
        object_list = Report.objects \
            .filter(query) \
            .distinct() \
            .order_by(*order)
        view_template = 'view_report.html'
        total = Report.objects.all().count()
    else:
        raise Http404("Requested page type '%s' not known" % view)

    if request.user.is_authenticated():
        paginator = Paginator(object_list, 20) 
    else:
        paginator = Paginator(object_list, 20) 

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)

    context["search_terms"] = ", ".join(terms)
    context["page"] = page
    context["view"] = view
    context["tview"] = _(view.title())
    context["search"] = search
    context["total"] = total
    context["object_list"] = object_list
    context["next"] = "/%s/" % view
    if search:
        context["search_query"] = ("&search=%s" % search)
    else:
        context["search_query"] = ""
    return render_to_response(view_template, context)

def check_access(request, context, obj, action):
    """
    Check to see if user has access to object. We don't need to
    sanitize here, just check to see if we even acknowledge it exists.
    """
    if request.user.is_authenticated():
        if request.user.is_superuser:
            return True
        else:
            return action in ["view"]
    else: # outside viewer
        return not obj.private

def add_share(request, view, item, handle):
    """
    Add a reference to an existing <view> referenced from <item>.
    """
    # /view/share/person/handle
    raise Http404(_('Not implemented yet.'))

def add_to(request, view, item, handle):
    """
    Add a new <view> referenced from <item>.
    """
    # /view/add/person/handle
    return action(request, view, None, "add", (item, handle))

def action(request, view, handle, action, add_to=None):
    """
    View a particular object given /object/handle (implied view),
    /object/handle/action, or /object/add.
    """
    # redirect:
    rd = None
    obj = None
    context = RequestContext(request)
    if request.POST.has_key("action"):
        action = request.POST.get("action")
    context["action"] = action
    context["view"] = view
    context["tview"] = _('Browse')
    if view == "event":
        if action not in ["add", "create"]:
            try:
                obj = Event.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        if not check_access(request, context, obj, action):
            raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_event_detail.html'
        rd = process_event(request, context, handle, action, add_to)
    elif view == "family":
        if action not in ["add", "create"]:
            try:
                obj = Family.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_family_detail.html'
        rd = process_family(request, context, handle, action, add_to)
    elif view == "media":
        if action not in ["add", "create"]:
            try:
                obj = Media.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_media_detail.html'
        rd = process_media(request, context, handle, action, add_to)
    elif view == "note":
        if action not in ["add", "create"]:
            try:
                obj = Note.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_note_detail.html'
        rd = process_note(request, context, handle, action, add_to)
    elif view == "person":
        if action not in ["add", "create"]:
            try:
                obj = Person.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_person_detail.html'
        rd = process_person(request, context, handle, action, add_to)
    elif view == "place":
        if action not in ["add", "create"]:
            try:
                obj = Place.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_place_detail.html'
        rd = process_place(request, context, handle, action, add_to)
    elif view == "repository":
        if action not in ["add", "create"]:
            try:
                obj = Repository.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_repository_detail.html'
        rd = process_repository(request, context, handle, action, add_to)
    elif view == "citation":
        if action not in ["add", "create"]:
            try:
                obj = Citation.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_citation_detail.html'
        rd = process_citation(request, context, handle, action, add_to)
    elif view == "source":
        if action not in ["add", "create"]:
            try:
                obj = Source.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_source_detail.html'
        rd = process_source(request, context, handle, action, add_to)
    elif view == "tag":
        if action not in ["add", "create"]:
            try:
                obj = Tag.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_tag_detail.html'
        rd = process_tag(request, context, handle, action, add_to)
    elif view == "report":
        if action not in ["add", "create"]:
            try:
                obj = Report.objects.get(handle=handle)
            except:
                raise Http404(_("Requested %s does not exist.") % view)
        view_template = 'view_report_detail.html'
        rd = process_report(request, context, handle, action)
    else:
        raise Http404(_("Requested page type not known"))
    if rd:
        return rd
    if obj:
        context[view] = obj
        context["object"] = obj
        context["next"] = "/%s/%s" % (view, obj.handle)
    return render_to_response(view_template, context)

def process_report(request, context, handle, action):
    """
    Process action on report. Can return a redirect.
    """
    if action == "run":
        return process_report_run(request, handle)
    context["tview"] = _("Report")
    context["tviews"] = _("Reports")

def build_person_query(request, search):
    """
    Build and return a Django QuerySet and sort order for the Person
    table.
    """
    protect = not request.user.is_authenticated()
    ### Build the order:
    terms = ["surname", "given"]
    if protect:
        # Do this to get the names sorted by private/alive 
        query = Q(private=False) & Q(person__private=False)
        order = ["surname__surname", "private", "person__probably_alive", 
                 "first_name"]
    else:
        query = Q()
        order = ["surname__surname", "first_name"]
    ### Build the query:
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "surname":
                    query &= Q(surname__surname__istartswith=value)
                elif field == "given":
                    if protect:
                        query &= Q(first_name__istartswith=value) & Q(person__probably_alive=False)
                    else:
                        query &= Q(first_name__istartswith=value)
                elif field == "private":
                    if not protect:
                        query &= Q(person__private=boolean(value))
                elif field == "birth":
                    if protect:
                        query &= Q(person__birth__year1=safe_int(value)) & Q(person__probably_alive=False)
                    else:
                        query &= Q(person__birth__year1=safe_int(value))
                elif field == "death":
                    if protect:
                        query &= Q(person__death__year1=safe_int(value)) & Q(person__probably_alive=False)
                    else:
                        query &= Q(person__death__year1=safe_int(value))
                elif field == "id":
                    query &= Q(person__gramps_id__icontains=value)
                elif field == "gender":
                    query &= Q(person__gender_type__name=value.title())
                else:
                    make_message(request, "Invalid query field '%s'" % field)
        else: # no search fields, just raw search
            if protect:
                query &= (Q(surname__surname__icontains=search) | 
                              Q(surname__prefix__icontains=search) |
                              Q(person__gramps_id__icontains=search))
            else:
                query &= (Q(surname__surname__icontains=search) | 
                              Q(first_name__icontains=search) |
                              Q(suffix__icontains=search) |
                              Q(surname__prefix__icontains=search) |
                              Q(title__icontains=search) |
                              Q(person__gramps_id__icontains=search))
    else: # no search
        pass # nothing else to do
    #make_message(request, query)
    return query, order, terms

def build_family_query(request, search):
    """
    Build and return a Django QuerySet and sort order for the Family
    table.
    """
    terms = ["father", "mother", "id", "type"]
    protect = not request.user.is_authenticated()
    if protect:
        query = (Q(private=False) & Q(father__private=False) & 
                 Q(mother__private=False))
        order = ["father__name__surname__surname", 
                 "father__private", "father__probably_alive", 
                 "father__name__first_name",
                 "mother__name__surname__surname", 
                 "mother__private", "mother__probably_alive", 
                 "mother__name__first_name"]
    else:
        query = Q()
        order = ["father__name__surname__surname", 
                 "father__name__first_name",
                 "mother__name__surname__surname", 
                 "mother__name__first_name"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        make_message("Ignoring value without specified field")
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "surnames":
                    query &= (Q(father__name__surname__surname__istartswith=value) |
                              Q(mother__name__surname__surname__istartswith=value))
                elif field == "father":
                    query &= Q(father__name__surname__surname__istartswith=value)
                elif field == "mother":
                    query &= Q(mother__name__surname__surname__istartswith=value)
                elif field == "type":
                    query &= Q(family_rel_type__name__icontains=value)
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                else:
                    make_message(request, message="Invalid query field '%s'" % field)
        else: # no search fields, just raw search
            if protect:
                query &= (Q(gramps_id__icontains=search) |
                          Q(family_rel_type__name__icontains=search) |
                          Q(father__name__surname__surname__icontains=search) |
                          Q(mother__name__surname__surname__icontains=search))
            else:
                query &= (Q(gramps_id__icontains=search) |
                          Q(family_rel_type__name__icontains=search) |
                          Q(father__name__surname__surname__icontains=search) |
                          Q(mother__name__surname__surname__icontains=search))
    else: # no search
        pass # nothing left to do
    #make_message(request, query)
    return query, order, terms

def build_media_query(request, search):
    terms = ["id"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q(private=False) # general privacy
        order = ["gramps_id"]
    else:
        query = Q()
        order = ["gramps_id"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= Q(gramps_id__icontains=search)
            else:
                query &= Q(gramps_id__icontains=search)
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_note_query(request, search):
    terms = ["id", "type", "text"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q(private=False) # general privacy
        order = ["gramps_id"]
    else:
        query = Q()
        order = ["gramps_id"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                elif field == "type":
                    query &= Q(note_type__name__icontains=value)
                elif field == "text":
                    query &= Q(text__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= (Q(gramps_id__icontains=search) |
                          Q(note_type__name__icontains=search) |
                          Q(text__icontains=search))
            else:
                query &= (Q(gramps_id__icontains=search) |
                          Q(note_type__name__icontains=search) |
                          Q(text__icontains=search))
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_place_query(request, search):
    terms = ["id", "title"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q(private=False) # general privacy
        order = ["gramps_id"]
    else:
        query = Q()
        order = ["gramps_id"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                elif field == "title":
                    query &= Q(title__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= (Q(gramps_id__icontains=search) |
                          Q(title__icontains=search))
            else:
                query &= (Q(gramps_id__icontains=search) |
                          Q(title__icontains=search))
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_repository_query(request, search):
    terms = ["id", "name", "type"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q(private=False) # general privacy
        order = ["gramps_id"]
    else:
        query = Q()
        order = ["gramps_id"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                elif field == "name":
                    query &= Q(name__icontains=value)
                elif field == "type":
                    query &= Q(repository_type__name__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= (Q(gramps_id__icontains=search) |
                          Q(name__icontains=search) |
                          Q(repository_type__name__icontains=search)
                          )
            else:
                query &= (Q(gramps_id__icontains=search) |
                          Q(name__icontains=search) |
                          Q(repository_type__name__icontains=search)
                          )
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_citation_query(request, search):
    terms = ["id"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q(private=False) # general privacy
        order = ["gramps_id"]
    else:
        query = Q()
        order = ["gramps_id"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= (Q(gramps_id__icontains=search))
            else:
                query &= (Q(gramps_id__icontains=search))
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_source_query(request, search):
    terms = ["id"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q(private=False) # general privacy
        order = ["gramps_id"]
    else:
        query = Q()
        order = ["gramps_id"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= Q(gramps_id__icontains=search)
            else:
                query &= Q(gramps_id__icontains=search)
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_tag_query(request, search):
    terms = ["name"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q() # general privacy
        order = ["name"]
    else:
        query = Q()
        order = ["name"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "name":
                    query &= Q(name__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= Q(name__icontains=search)
            else:
                query &= Q(name__icontains=search)
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_report_query(request, search):
    terms = ["name"]
    # NOTE: protection is based on super_user status
    protect = not request.user.is_superuser
    if protect:
        query = ~Q(report_type="import") # general privacy
        order = ["name"]
    else:
        query = Q()
        order = ["name"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "name":
                    query &= Q(name__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= Q(name__icontains=search)
            else:
                query &= Q(name__icontains=search)
    else: # no search
        pass # nothing left to do
    return query, order, terms

def build_event_query(request, search):
    terms = ["id", "type", "place"]
    protect = not request.user.is_authenticated()
    if protect:
        query = Q(private=False) # general privacy
        order = ["gramps_id"]
    else:
        query = Q()
        order = ["gramps_id"]
    if search:
        if "," in search or "=" in search:
            for term in [term.strip() for term in search.split(",")]:
                if "=" in term:
                    field, value = [s.strip() for s in term.split("=")]
                else:
                    if terms:
                        field = terms.pop(0)
                        value = term
                    else:
                        continue
                if "." in field and not protect:
                    query &= Q(**{str(field.replace(".", "__")): value})
                elif field == "id":
                    query &= Q(gramps_id__icontains=value)
                elif field == "type":
                    query &= Q(event_type__name__icontains=value)
                elif field == "place":
                    query &= Q(place__title__icontains=value)
                else:
                    request.user.message_set.create(message="Invalid query field '%s'" % field)                
        else: # no search fields, just raw search
            if protect:
                query &= (Q(gramps_id__icontains=search) |
                          Q(event_type__name__icontains=search) |
                          Q(place__title__icontains=search))
            else:
                query &= (Q(gramps_id__icontains=search) |
                          Q(event_type__name__icontains=search) |
                          Q(place__title__icontains=search))
    else: # no search
        pass # nothing left to do
    return query, order, terms

def safe_int(num):
    """
    Safely try to convert num to an integer. Return -1 (which should
    not match).
    """
    try:
        return int(num)
    except:
        return -1

def process_reference(request, ref_by, handle, ref_to, order):
    # FIXME: can I make this work for all?
    context = RequestContext(request)
    ref_by_class = dji.get_model(ref_by)
    referenced_by = ref_by_class.objects.get(handle=handle)
    object_type = ContentType.objects.get_for_model(referenced_by)
    ref_to_class = dji.get_model("%sRef" % ref_to.title())
    exclude = ["last_changed_by", "last_changed", "object_type", "object_id", "ref_object"]
    if order == "new":
        referenced_to = ref_to_class.objects.filter(object_id=referenced_by.id, 
                                                    object_type=object_type,
                                                    order=0)
        form = modelformset_factory(ref_to_class, exclude=exclude, extra=1)(queryset=referenced_to)
    else:
        referenced_to = ref_to_class.objects.filter(object_id=referenced_by.id, 
                                                    object_type=object_type,
                                                    order=order)
        form = modelformset_factory(ref_to_class, exclude=exclude, extra=0)(queryset=referenced_to)
        form.model = referenced_to[0]
    context["form"] = form
    context["view"] = 'reference'
    context["tview"] = _('Reference')
    context["tviews"] = _('References')
    context["object"] = referenced_by
    context["handle"] = referenced_by.handle
    context["url"] = "/%s/%s" % (referenced_to[0].ref_object.__class__.__name__.lower(), 
                                 referenced_to[0].ref_object.handle)
    context["referenced_by"] = "/%s/%s" % (referenced_by.__class__.__name__.lower(),
                                           referenced_by.handle)
    context["action"] = "view"
    return render_to_response("reference.html", context)

