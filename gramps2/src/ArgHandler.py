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

#
# Written by Alex Roitman
#

"""
Module responsible for handling the command line arguments for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import getopt

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import ReadXML
import GrampsMime
import DbPrompter
import QuestionDialog
import GrampsCfg

#-------------------------------------------------------------------------
#
# ArgHandler
#
#-------------------------------------------------------------------------
class ArgHandler:
    """
    This class is responsible for handling command line arguments (if any)
    given to gramps. The valid arguments are:

    FILE                :   filename to open. 
                            All following arguments will be ignored.
    -i, --import=FILE   :   filename to import.
    -o, --output=FILE   :   filename to export.
    -f, --format=FORMAT :   format of the file preceding this option.
    
    If the filename (no flags) is specified, the interactive session is 
    launched using data from filename. If the filename is not a natvive (grdb) format, dialog will
    be presented to set up a grdb database.
    
    If no filename or -i option is given, a new interactive session (empty
    database) is launched, since no data is goven anyway.
    
    If -i option is given, but no -o or -a options are given, and interactive
    session is launched with the FILE (specified with -i). 
    
    If both -i and -o or -a are given, interactive session will not be 
    launched. 
    """

    def __init__(self,parent,args):
        self.parent = parent
        self.args = args

        self.open = None
        self.exports = []
        self.actions = []
        self.imports = []

        self.parse_args()
        self.handle_args()

    #-------------------------------------------------------------------------
    #
    # Argument parser: sorts out given arguments
    #
    #-------------------------------------------------------------------------
    def parse_args(self):
        """
        Fill in lists with open, exports, imports, and actions options.
        """

        try:
            options,leftargs = getopt.getopt(self.args[1:],
                        const.shortopts,const.longopts)
        except getopt.GetoptError:
            # return without filling anything if we could not parse the args
            print "Error parsing arguments: %s " % self.args[1:]
            return

        if leftargs:
            # if there were an argument without option, use it as a file to 
            # open and return
            self.open = leftargs[0]
            print "Trying to open: %s ..." % leftargs[0]
            return

        for opt_ix in range(len(options)):
            o,v = options[opt_ix]
            if o in ( '-i', '--import'):
                fname = v
                ftype = GrampsMime.get_type(os.path.abspath(os.path.expanduser(fname)))
                if opt_ix<len(options)-1 \
                            and options[opt_ix+1][0] in ( '-f', '--format'): 
                    format = options[opt_ix+1][1]
                    if format not in ('gedcom','gramps-xml','gramps-pkg','grdb'):
                        print "Invalid format:  %s" % format
                        print "Ignoring input file:  %s" % fname
                        continue
                elif ftype == "application/x-gedcom":
                    format = 'gedcom'
                elif ftype == "application/x-gramps-package":
                    format = 'gramps-pkg'
                elif ftype == "x-directory/normal":
                    format = 'gramps-xml'
                elif ftype == "application/x-gramps":
                    format = 'grdb'
                else:
                    print "Unrecognized format for input file %s" % fname
                    print "Ignoring input file:  %s" % fname
                    continue
                self.imports.append((fname,format))
            elif o in ( '-o', '--output' ):
                outfname = v
                if opt_ix<len(options)-1 \
                            and options[opt_ix+1][0] in ( '-f', '--format'): 
                    outformat = options[opt_ix+1][1]
                    if outformat not in ('gedcom','gramps-xml','gramps-pkg','grdb','iso','wft'):
                        print "Invalid format:  %s" % outformat
                        print "Ignoring output file:  %s" % outfname
                        continue
                elif outfname[-3:].upper() == "GED":
                    outformat = 'gedcom'
                elif outfname[-4:].upper() == "GPKG":
                    outformat = 'gramps-pkg'
                elif outfname[-3:].upper() == "WFT":
                    outformat = 'wft'
                elif not os.path.isfile(outfname):
                    if not os.path.isdir(outfname):
                        try:
                            os.makedirs(outfname,0700)
                        except:
                            print "Cannot create directory %s" % outfname
                            print "Ignoring output file:  %s" % outfname
                            continue
                    outformat = 'gramps-xml'
                elif fname[-3:].upper() == "GRDB":
                    format = 'grdb'
                else:
                    print "Unrecognized format for output file %s" % outfname
                    print "Ignoring output file:  %s" % outfname
                    continue
                self.exports.append((outfname,outformat))
            elif o in ( '-a', '--action' ):
                action = v
                if action not in ( 'check', 'summary' ):
                    print "Unknown action: %s. Ignoring." % action
                    continue
                self.actions.append(action)
            
    #-------------------------------------------------------------------------
    #
    # Overall argument handler: 
    # sorts out the sequence and details of operations
    #
    #-------------------------------------------------------------------------
    def handle_args(self):
        """
        Depending on the given arguments, import or open data, launch
        session, write files, and/or perform actions.
        """

        if self.open:
            # Filename was given. Open a session with that file. Forget
            # the rest of given arguments.
            filename = os.path.abspath(os.path.expanduser(self.open))
            filetype = GrampsMime.get_type(filename) 
            if filetype == "application/x-gramps":
                print "Type: GRAMPS database"
                if self.parent.auto_save_load(filename):
                    print "Opened successfully!"
                else:
                    print "Cannot open %s. Exiting..."
            elif filetype in ("application/x-gedcom","x-directory/normal",
	    	    	    	    "application/x-gramps-package"):
                QuestionDialog.OkDialog( _("Opening non-native format"), 
                            _("New GRAMPS database has to be set up when opening non-native formats. The following dialog will let you select the new database."),
                            self.parent.topWindow)
                prompter = DbPrompter.NewNativeDbPrompter(self.parent)
		if not prompter.chooser():
                    QuestionDialog.ErrorDialog( 
                        _("New GRAMPS database was not set up"),
                        _('GRAMPS cannot open non-native data without setting up new GRAMPS database.'))
                    print "Cannot continue without native database. Exiting..." 
    	            os._exit(1)
		elif filetype == "application/x-gedcom":
                    print "Type: GEDCOM"
                    self.parent.read_gedcom(filename)
            	elif filetype == "x-directory/normal":
                    print "Type: GRAMPS XML"
                    self.parent.read_xml(filename)
    	        elif filetype == "application/x-gramps-package":
                    print "Type: GRAMPS package"
                    self.parent.read_pkg(filename)
    	    else:
                print "Unknown file type: %s" % filetype
                QuestionDialog.ErrorDialog( 
                        _("Cannot open file: unknown type"),
                        _('File type "%s" is unknown to GRAMPS.\n\nValid types are: GRAMPS database, GRAMPS XML, GRAMPS package, and GEDCOM.') % filetype)
                print "Exiting..." 
    	        os._exit(1)
            return
           
        if self.imports:
            self.parent.cl = bool(self.exports or self.actions)

            # Create dir for imported database(s)
            self.impdir_path = os.path.expanduser("~/.gramps/import" )
            self.imp_db_path = os.path.expanduser("~/.gramps/import/import_db.grdb" )
            if not os.path.isdir(self.impdir_path):
                try:
                    os.mkdir(self.impdir_path,0700)
                except:
                    print "Could not create import directory %s. Exiting." \
                        % self.impdir_path 
                    os._exit(1)
            elif not os.access(self.impdir_path,os.W_OK):
                print "Import directory %s is not writable. Exiting." \
                    % self.impdir_path 
                os._exit(1)
            # and clean it up before use
            files = os.listdir(self.impdir_path) ;
            for fn in files:
                if os.path.isfile(os.path.join(self.impdir_path,fn)):
                    os.remove(os.path.join(self.impdir_path,fn))

            self.parent.load_database(self.imp_db_path)

            for imp in self.imports:
                print "Importing: file %s, format %s." % imp
                self.cl_import(imp[0],imp[1])

        elif len(self.args) > 1:
            print "No data was given -- will launch interactive session."
            print "To use in the command-line mode,", \
                "supply at least one input file to process."
            print "Launching interactive session..."

        if self.parent.cl:
            for expt in self.exports:
                print "Exporting: file %s, format %s." % expt
                self.cl_export(expt[0],expt[1])

            for action in self.actions:
                print "Performing action: %s." % action
                self.cl_action(action)
            
            print "Cleaning up."
            # remove import db after use
            os.remove(self.imp_db_path)
            print "Exiting."
            os._exit(0)

        if self.imports:
            self.parent.import_tool_callback()
        elif GrampsCfg.lastfile and GrampsCfg.autoload:
            if self.parent.auto_save_load(GrampsCfg.lastfile) == 0:
                DbPrompter.DbPrompter(self.parent,0)
        else:
	    DbPrompter.DbPrompter(self.parent,0)


    #-------------------------------------------------------------------------
    #
    # Import handler
    #
    #-------------------------------------------------------------------------
    def cl_import(self,filename,format):
        """
        Command-line import routine. Try to import filename using the format.
        Any errors will cause the os._exit(1) call.
        """
        if format == 'gedcom':
            import ReadGedcom
            filename = os.path.normpath(os.path.abspath(filename))
            try:
                g = ReadGedcom.GedcomParser(self.parent.db,filename,None)
                g.parse_gedcom_file()
                g.resolve_refns()
                del g
            except:
                print "Error importing %s" % filename
                os._exit(1)
        elif format == 'gramps-xml':
            try:
                dbname = os.path.join(filename,const.xmlFile)
                ReadXML.importData(self.parent.db,dbname,None,self.parent.cl)
            except:
                print "Error importing %s" % filename
                os._exit(1)
        elif format == 'gramps-pkg':
            # Create tempdir, if it does not exist, then check for writability
            tmpdir_path = os.path.expanduser("~/.gramps/tmp" )
            if not os.path.isdir(tmpdir_path):
                try:
                    os.mkdir(tmpdir_path,0700)
                except:
                    print "Could not create temporary directory %s" % tmpdir_path 
                    os._exit(1)
            elif not os.access(tmpdir_path,os.W_OK):
                print "Temporary directory %s is not writable" % tmpdir_path 
                os._exit(1)
            else:    # tempdir exists and writable -- clean it up if not empty
                files = os.listdir(tmpdir_path) ;
                for fn in files:
                    os.remove( os.path.join(tmpdir_path,fn) )

            try:
                import TarFile
                t = TarFile.ReadTarFile(filename,tmpdir_path)
                t.extract()
                t.close()
            except:
                print "Error extracting into %s" % tmpdir_path 
                os._exit(1)

            dbname = os.path.join(tmpdir_path,const.xmlFile)

            try:
                ReadXML.importData(self.parent.db,dbname,None)
            except:
                print "Error importing %s" % filename
                os._exit(1)
            # Clean up tempdir after ourselves
            files = os.listdir(tmpdir_path) 
            for fn in files:
                os.remove(os.path.join(tmpdir_path,fn))
            os.rmdir(tmpdir_path)
        else:
            print "Invalid format:  %s" % format
            os._exit(1)
        if not self.parent.cl:
            return self.parent.post_load(self.imp_db_path)

    #-------------------------------------------------------------------------
    #
    # Export handler
    #
    #-------------------------------------------------------------------------
    def cl_export(self,filename,format):
        """
        Command-line export routine. 
        Try to write into filename using the format.
        Any errors will cause the os._exit(1) call.
        """
        if format == 'gedcom':
            import WriteGedcom
            try:
                g = WriteGedcom.GedcomWriter(self.parent.db,None,1,filename)
                del g
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        elif format == 'gramps-xml':
            filename = os.path.normpath(os.path.abspath(filename))
            dbname = os.path.join(filename,const.xmlFile)
            if filename:
                try:
                    self.parent.save_media(filename)
                    self.parent.db.save(dbname,None)
                except:
                    print "Error exporting %s" % filename
                    os._exit(1)
        elif format == 'gramps-pkg':
            import TarFile
            import time
            import WriteXML
            from cStringIO import StringIO

            try:
                t = TarFile.TarFile(filename)
                mtime = time.time()
            except:
                print "Error creating %s" % filename
                os._exit(1)
        
            try:
                # Write media files first, since the database may be modified 
                # during the process (i.e. when removing object)
                for m_id in self.parent.db.get_object_keys():
                    mobject = self.parent.db.try_to_find_object_from_id(m_id)
                    oldfile = mobject.get_path()
                    base = os.path.basename(oldfile)
                    if os.path.isfile(oldfile):
                        g = open(oldfile,"rb")
                        t.add_file(base,mtime,g)
                        g.close()
                    else:
                        print "Warning: media file %s was not found," % base,\
                            "so it was ignored."
            except:
                print "Error exporting media files to %s" % filename
                os._exit(1)
            try:
                # Write XML now
                g = StringIO()
                gfile = WriteXML.XmlWriter(self.parent.db,None,1)
                gfile.write_handle(g)
                mtime = time.time()
                t.add_file("data.gramps",mtime,g)
                g.close()
                t.close()
            except:
                print "Error exporting data to %s" % filename
                os._exit(1)
        elif format == 'iso':
            import WriteCD
            try:
                WriteCD.PackageWriter(self.parent.db,1,filename)
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        elif format == 'wft':
            import WriteFtree
            try:
                WriteFtree.FtreeWriter(self.parent.db,None,1,filename)
            except:
                print "Error exporting %s" % filename
                os._exit(1)
        else:
            print "Invalid format: %s" % format
            os._exit(1)

    #-------------------------------------------------------------------------
    #
    # Action handler
    #
    #-------------------------------------------------------------------------
    def cl_action(self,action):
        """
        Command-line action routine. Try to perform specified action.
        Any errors will cause the os._exit(1) call.
        """
        if action == 'check':
            import Check
            checker = Check.CheckIntegrity(self.parent.db,None,None)
            checker.check_for_broken_family_links()
            checker.cleanup_missing_photos(1)
            checker.check_parent_relationships()
            checker.cleanup_empty_families(0)
            errs = checker.build_report(1)
            if errs:
                checker.report(1)
        elif action == 'summary':
            import Summary
            text = Summary.build_report(self.parent.db,None)
            print text
        else:
            print "Unknown action: %s." % action
            os._exit(1)
