#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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

#------------------------------------------------------------------------
#
# gramps modules
#
#------------------------------------------------------------------------
import TextDoc
import Plugins
import Errors
import ImgManip
from intl import gettext as _

#------------------------------------------------------------------------
#
# ReportLab python/PDF modules
#
#------------------------------------------------------------------------

try:
    import reportlab.platypus.tables
    from reportlab.platypus import *
    from reportlab.lib.units import cm
    from reportlab.lib.colors import Color
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
    import reportlab.lib.styles
except ImportError:
    raise Errors.PluginError( _("The ReportLab modules are not installed"))

#------------------------------------------------------------------------
#
# GrampsDocTemplate
#
#------------------------------------------------------------------------
class GrampsDocTemplate(BaseDocTemplate):
    """A document template for the ReportLab routines."""
    
    def build(self,flowables):
        """Override the default build routine, to recalculate
        for any changes in the document (margins, etc.)"""
        self._calc()	
        BaseDocTemplate.build(self,flowables)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class PdfDoc(TextDoc.TextDoc):

    def open(self,filename):
        if filename[-4:] != ".pdf":
            self.filename = "%s.pdf" % filename
        else:
            self.filename = filename
            
        self.pagesize = (self.width*cm,self.height*cm)

        self.doc = GrampsDocTemplate(self.filename, 
	                             pagesize=self.pagesize,
                                     allowSplitting=1,
                                     _pageBreakQuick=0,
                                     leftMargin=self.lmargin*cm,
                                     rightMargin=self.rmargin*cm,
                                     topMargin=self.tmargin*cm,
                                     bottomMargin=self.bmargin*cm)
        frameT = Frame(0,0,self.width*cm,self.height*cm,
                       self.lmargin*cm, self.bmargin*cm, 
                       self.rmargin*cm,self.tmargin*cm,
                       id='normal')
        ptemp = PageTemplate(frames=frameT,pagesize=self.pagesize)
        self.doc.addPageTemplates([ptemp])

        self.pdfstyles = {}

        for style_name in self.style_list.keys():
            style = self.style_list[style_name]
            font = style.get_font()

	    pdf_style = reportlab.lib.styles.ParagraphStyle(name=style_name)
            pdf_style.fontSize = font.get_size()
            pdf_style.bulletFontSize = font.get_size()
            
            if font.get_type_face() == TextDoc.FONT_SERIF:
                if font.get_bold():
                    if font.get_italic():
                        pdf_style.fontName = "Times-BoldItalic"
                    else:
                        pdf_style.fontName = "Times-Bold"
                else:
                    if font.get_italic():
                        pdf_style.fontName = "Times-Italic"
                    else:
                        pdf_style.fontName = "Times-Roman"
            else:
                if font.get_bold():
                    if font.get_italic():
                        pdf_style.fontName = "Helvetica-BoldOblique"
                    else:
                        pdf_style.fontName = "Helvetica-Bold"
                else:
                    if font.get_italic():
                        pdf_style.fontName = "Helvetica-Oblique"
                    else:
                        pdf_style.fontName = "Helvetica"
            pdf_style.bulletFontName = pdf_style.fontName

            right = style.get_right_margin()*cm
            left = style.get_left_margin()*cm
            first = left + style.get_first_indent()*cm

            pdf_style.rightIndent = right
            pdf_style.leftIndent = left
            pdf_style.firstLineIndent = first
            pdf_style.bulletIndent = first

	    align = style.get_alignment()
            if align == TextDoc.PARA_ALIGN_RIGHT:
		pdf_style.alignment = TA_RIGHT
            elif align == TextDoc.PARA_ALIGN_LEFT:
		pdf_style.alignment = TA_LEFT
            elif align == TextDoc.PARA_ALIGN_CENTER:
		pdf_style.alignment = TA_CENTER
            else:
		pdf_style.alignment = TA_JUSTIFY
            pdf_style.spaceBefore = style.get_padding()
            pdf_style.spaceAfter = style.get_padding()
            pdf_style.textColor = make_color(font.get_color())
	    self.pdfstyles[style_name] = pdf_style

	self.story = []
	self.in_table = 0

    def close(self):
        self.doc.build(self.story)

    def end_page(self):
        self.story.append(PageBreak())

    def start_paragraph(self,style_name,leader=None):
        self.current_para = self.pdfstyles[style_name]
        self.my_para = self.style_list[style_name]
        if leader==None:
            self.text = ''
        else:
            self.text = '<bullet>%s</bullet>' % leader
        self.image = 0

    def end_paragraph(self):
        if self.in_table == 0 and self.image == 0:
	    self.story.append(Paragraph(self.text,self.current_para))
	    self.story.append(Spacer(1,0.5*cm))
        else:
            self.image = 0

    def start_bold(self):
        self.text = self.text + '<b>'

    def end_bold(self):
        self.text = self.text + '</b>'

    def start_table(self,name,style_name):
        self.in_table = 1
        self.cur_table = self.table_styles[style_name]
        self.row = -1
        self.col = 0
        self.cur_row = []
        self.table_data = []

	self.tblstyle = []
        self.cur_table_cols = []
        width = float(self.cur_table.get_width()/100.0) * self.get_usable_width()
	for val in range(self.cur_table.get_columns()):
            percent = float(self.cur_table.get_column_width(val))/100.0
            self.cur_table_cols.append(int(width * percent * cm))

    def end_table(self):
        ts = reportlab.platypus.tables.TableStyle(self.tblstyle)
	tbl = reportlab.platypus.tables.Table(data=self.table_data,
                                              colWidths=self.cur_table_cols,
                                              style=ts)
	self.story.append(tbl)
        self.in_table = 0

    def start_row(self):
	self.row = self.row + 1
        self.col = 0
        self.cur_row = []

    def end_row(self):
        self.table_data.append(self.cur_row)

    def start_cell(self,style_name,span=1):
        self.span = span
        self.my_table_style = self.cell_styles[style_name]
        pass

    def end_cell(self):
        if self.span == 1:
            self.cur_row.append(Paragraph(self.text,self.current_para))
        else:
            self.cur_row.append(self.text)
        for val in range(1,self.span):
            self.cur_row.append("")

	p = self.my_para
        f = p.get_font()
        if f.get_type_face() == TextDoc.FONT_SANS_SERIF:
            if f.get_bold():
                fn = 'Helvetica-Bold'
            else:
                fn = 'Helvetica'
        else:
            if f.get_bold():
                fn = 'Times-Bold'
            else:
                fn = 'Times-Roman'

        black = Color(0,0,0)
        
        for inc in range(self.col,self.col+self.span):
            loc = (inc,self.row)
            self.tblstyle.append(('FONT', loc, loc, fn, f.get_size()))
            if self.span == 1 or inc == self.col + self.span - 1:
                if self.my_table_style.get_right_border():
                    self.tblstyle.append(('LINEAFTER', loc, loc, 1, black))
            if self.span == 1 or inc == self.col:
                if self.my_table_style.get_left_border():
                    self.tblstyle.append(('LINEBEFORE', loc, loc, 1, black))
            if self.my_table_style.get_top_border():
                self.tblstyle.append(('LINEABOVE', loc, loc, 1, black))
            if self.my_table_style.get_bottom_border():
                self.tblstyle.append(('LINEBELOW', loc, loc, 1, black))
            if p.get_alignment() == TextDoc.PARA_ALIGN_LEFT:
                self.tblstyle.append(('ALIGN', loc, loc, 'LEFT'))
            elif p.get_alignment() == TextDoc.PARA_ALIGN_RIGHT:
                self.tblstyle.append(('ALIGN', loc, loc, 'RIGHT'))
            else:
                self.tblstyle.append(('ALIGN', loc, loc, 'CENTER'))
            self.tblstyle.append(('VALIGN', loc, loc, 'TOP'))

        self.col = self.col + self.span

    def add_photo(self,name,pos,x_cm,y_cm):
        img = ImgManip.ImgManip(name)
        x,y = img.size()

        ratio = float(x_cm)*float(y)/(float(y_cm)*float(x))

        if ratio < 1:
            act_width = x_cm
            act_height = y_cm*ratio
        else:
            act_height = y_cm
            act_width = x_cm/ratio

        self.story.append(Image(name,act_width*cm,act_height*cm))
        self.story.append(Spacer(1,0.5*cm))
        self.image = 1

    def write_text(self,text):
        text = text.replace('&','&amp;');       # Must be first
        text = text.replace('<','&lt;');
        self.text =  self.text + text.replace('>','&gt;');

#------------------------------------------------------------------------
#
# Convert an RGB color tulple to a Color instance
#
#------------------------------------------------------------------------
def make_color(c):
    return Color(float(c[0])/255.0, float(c[1])/255.0, float(c[2])/255.0)

#------------------------------------------------------------------------
#
# Register the document generator with the GRAMPS plugin system
#
#------------------------------------------------------------------------

Plugins.register_text_doc(
    name=_("PDF"),
    classref=PdfDoc,
    table=1,
    paper=1,
    style=1,
    ext="pdf"
    )
