#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007  B. Malengier
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

"""
Display a person's relations to the home person
"""
#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------

from Simple import SimpleAccess, SimpleDoc
from gettext import gettext as _
from PluginUtils import register_quick_report
from ReportBase import CATEGORY_QR_PERSON

from PluginUtils import Tool, relationship_class, register_tool

# define the formatting string once as a constant. Since this is reused

_FMT      = "%-3d %s"
_FMT_VOID = "    %s"
_FMT_DET1 = "%-3s %-15s"
_FMT_DET2 = "%-30s %-15s\t%-10s %-2s"

    
def run(database, document, person):
    """ 
    Create the report class, and produce the quick report
    """
    report = AllRelReport(database, document, person)
    report.run()
    
class AllRelReport():
    """
    Obtains all relationships, displays the relations, and in details, the 
    relation path
    """
    def __init__(self, database, document, person):
        self.database = database
        self.person   = person
        self.sdb = SimpleAccess(database)
        self.sdoc = SimpleDoc(document)
        self.rel_class = relationship_class()

    def run(self):
        #get home_person
        self.home_person = self.database.get_default_person()
        if not self.home_person :
            self.sdoc.paragraph(_("Home person not set."))
            return

        self.print_title()

        p2 = self.sdb.name(self.home_person)
        p1 = self.sdb.name(self.person)
        if self.person.handle == self.home_person.handle :
            self.sdoc.paragraph(_FMT_VOID % (
                            _("%s and %s are the same person.") % ( p1, p2)) 
                          )
            return

        #check if not a family too:
        is_spouse = self.rel_class.is_spouse(self.database, self.person, 
                                             self.home_person)
        if is_spouse:
            rel_string = is_spouse
            rstr = _("%(person)s is the %(relationship)s of %(active_person)s."
                         ) % {'person' : p2, 'relationship' : rel_string,
                              'active_person' : p1 }
            self.sdoc.paragraph(_FMT_VOID % (rstr))
            self.sdoc.paragraph("")

        #obtain all relationships, assume home person has largest tree
        common, self.msg_list = self.rel_class.get_relationship_distance_new(
                    self.database, self.person, self.home_person,
                    all_families=True, 
                    all_dist=True, 
                    only_birth=False,
                    max_depth=20)
        
        #all relations
        if (not common or common[0][0]== -1 ) and not is_spouse:
            rstr = _("%(person)s and %(active_person)s are not "
                     "directly related.") % {'person' : p2, 
                                             'active_person' : p1 }
            self.sdoc.paragraph(_FMT_VOID % (rstr))
            self.sdoc.paragraph("")

        #collapse common so parents of same fam in common are one line
        commonnew = self.rel_class.collapse_relations(common)
        self.print_details(commonnew, self.home_person, self.person, 
                           first=True)
        self.print_details(commonnew, self.home_person, self.person, 
                           first=False) 
        
        if not common or common[0][0]== -1 :
            self.remarks(self.msg_list)
            #check inlaw relation next
        else:
            #stop
            return
        
        #we check the inlaw relationships if not partners.
        if is_spouse:
            return
        handles_done = [(self.person.handle, self.home_person.handle)]
        inlaws_pers = [self.person] + self.get_inlaws(self.person)
        inlaws_home = [self.home_person] + self.get_inlaws(self.home_person)
        #remove overlap:
        inlaws_home = [x for x in inlaws_home if x not in inlaws_pers]
        inlawwritten = False
        for inlawpers in inlaws_pers:
            for inlawhome in inlaws_home:
                if (inlawpers, inlawhome) in handles_done :
                    continue
                else:
                    handles_done.append((inlawpers, inlawhome))
                common, self.msg_list = \
                    self.rel_class.get_relationship_distance_new(
                            self.database, inlawpers, inlawhome,
                            all_families=True, 
                            all_dist=True, 
                            only_birth=False,
                            max_depth=20)
                if common and not common[0][0] == -1:
                    if not inlawwritten:
                        rstr = _("%(person)s and %(active_person)s have "
                                 "following in-law relations:"
                                ) % {'person' : p2, 
                                     'active_person' : p1 }
                        self.sdoc.paragraph(_FMT_VOID % (rstr))
                        self.sdoc.paragraph("")
                        inlawwritten = True
                else: 
                    continue
                commonnew = self.rel_class.collapse_relations(common)
                inlawb = not inlawpers.handle == self.person.handle
                inlawa = not inlawhome.handle == self.home_person.handle
                self.print_details(commonnew, inlawhome, inlawpers,
                                first=True, inlawa = inlawa, inlawb = inlawb)
                self.print_details(commonnew, inlawhome, inlawpers,
                                first=False, inlawa = inlawa, inlawb = inlawb)

    def get_inlaws(self, person):
        inlaws = []
        family_handles = person.get_family_handle_list()
        for handle in family_handles:
            fam = self.database.get_family_from_handle(handle)
            if fam.father_handle and \
                    not fam.father_handle == person.handle:
                inlaws.append(self.database.get_person_from_handle(
                                                        fam.father_handle))
            elif fam.mother_handle and \
                    not fam.mother_handle == person.handle:
                inlaws.append(self.database.get_person_from_handle(
                                                        fam.mother_handle))
        return inlaws


    def print_title(self):
        """ print the title
        """
        p2 = self.sdb.name(self.home_person)
        p1 = self.sdb.name(self.person)
        self.sdoc.title(_("Relationships of %s to %s") % (p1 ,p2))
        self.sdoc.paragraph("")

    def print_details(self, relations, pers1, pers2, 
                            inlawa=False, inlawb=False, first=True):
        if not relations or relations[0][0] == -1:
            return

        sdoc = self.sdoc
        rel_class = self.rel_class
        p2 = self.sdb.name(self.home_person)
        p1 = self.sdb.name(self.person)
        pers = p2
        inlaw = inlawa
        if first:
            pers = p1
            inlaw = inlawb
            count = 1
            for relation in relations: 
                birth = self.rel_class.only_birth(relation[2])\
                            and self.rel_class.only_birth(relation[4])
                distorig = len(relation[4])
                distother = len(relation[2])
                if distorig == 1 or distother ==1 :
                    rel_str = self.rel_class.get_sibling_relationship_string(
                                self.rel_class.get_sibling_type(
                                    self.database, pers1, pers2), 
                                self.home_person.get_gender(),
                                pers2.get_gender())
                rel_str = self.rel_class.get_single_relationship_string(
                                        distorig, distother, 
                                        self.home_person.get_gender(), 
                                        pers2.get_gender(),
                                        relation[4], relation[2], 
                                        only_birth = birth,
                                        in_law_a = inlawa, in_law_b = inlawb)
                sdoc.paragraph(_FMT % (count, rel_str))
                count += 1
            self.remarks(self.msg_list)
        
        sdoc.paragraph("")
        sdoc.header1(_("Detailed path from %(person)s to common ancestor"
                      ) % {'person':pers})
        sdoc.paragraph("")
        sdoc.header2(_FMT_DET1 % (_('   '), _('Name Common ancestor')))
        sdoc.header2(_FMT_DET2 % (' ', _('Parent'), _('Birth'), _('Family')))
        sdoc.paragraph("")
        count = 1
        for relation in relations: 
            counter = str(count)
            name = _('Unknown')
            if relation[1]:
                name = self.sdb.name(self.database.get_person_from_handle(
                                                            relation[1][0]))
                for handle in relation[1][1:]:
                    name += ' ' + _('and') + ' ' + self.sdb.name(
                                self.database.get_person_from_handle(handle))
            sdoc.paragraph(_FMT_DET1 % (counter, name))
            if inlaw:
                sdoc.paragraph(_FMT_DET2 % (' ', _('Partner'), ' ', ' '))
            if first:
                ind1 = 2
                ind2 = 3
            else:
                ind1 = 4
                ind2 = 5
            for rel,fam in zip(relation[ind1],relation[ind2]) :
                par_str = _('Unknown') #when sibling, parent is unknown
                if rel == rel_class.REL_MOTHER \
                        or rel == rel_class.REL_MOTHER_NOTBIRTH:
                    par_str = _('Mother')
                if rel == rel_class.REL_FATHER \
                        or rel == rel_class.REL_FATHER_NOTBIRTH:
                    par_str = _('Father')
                if (rel == rel_class.REL_FAM_BIRTH 
                        or rel == rel_class.REL_FAM_NONBIRTH 
                        or rel == rel_class.REL_FAM_BIRTH_MOTH_ONLY
                        or rel == rel_class.REL_FAM_BIRTH_FATH_ONLY):
                    par_str = _('Parents')
                birth_str = _('Yes')
                if (rel == rel_class.REL_MOTHER_NOTBIRTH 
                        or rel == rel_class.REL_FATHER_NOTBIRTH 
                        or rel == rel_class.REL_FAM_NONBIRTH):
                    birth_str = _('No')
                elif (rel == rel_class.REL_FAM_BIRTH_FATH_ONLY 
                        or rel == rel_class.REL_FAM_BIRTH_MOTH_ONLY):
                    birth_str = _('Partial')
                famstr = ''
                if isinstance(fam, list):
                    famstr = str(fam[0]+1)
                    for val in fam :
                        famstr = famstr + ', ' + str(val+1)
                else:
                    famstr = str(fam+1)
                sdoc.paragraph(_FMT_DET2 % (' ', par_str, birth_str, famstr))
                counter=''
                name = ''
            count += 1
            
    def remarks(self, msg_list):
        if msg_list :
            sdoc = self.sdoc
            sdoc.paragraph("")
            sdoc.header1(_("Remarks"))
            sdoc.paragraph("")
            sdoc.paragraph(_("The following problems where encountered:"))
            for msg in msg_list :
                sdoc.paragraph(msg)
            sdoc.paragraph("")
            sdoc.paragraph("")
        

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
register_quick_report(
    name = 'all_relations',
    category = CATEGORY_QR_PERSON,
    run_func = run,
    translated_name = _("Relation to Home Person"),
    status = _("Stable"),
    description= _("Display all relationships between person and home person."),
    author_name="B. Malengier",
    author_email="benny.malengier@gramps-project.org"
    )
