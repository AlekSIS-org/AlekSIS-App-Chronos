import os
import subprocess

from django.utils import timezone
from django.utils import formats

# LaTeX constants

TEX_HEADER = """\\documentclass[11pt]{article}
\\usepackage[ngerman]{babel}
\\usepackage[utf8]{inputenc}
\\usepackage[a4paper,left=1cm,right=1cm,top=2cm,bottom=2cm,bindingoffset=0mm]{geometry}

\\usepackage{fancyhdr}
\\usepackage{graphicx}

\\usepackage{longtable}
\\usepackage{multirow}
\\usepackage{color, colortbl}

\\usepackage{geometry}

\\usepackage{ulem, xpatch}
\\xpatchcmd{\\sout}
  {\\bgroup}
  {\\bgroup\def\\ULthickness{1.5pt}}
  {}{}
  
\\usepackage[framemethod=tikz]{mdframed}
\\newmdenv[
  roundcorner=5pt,
  backgroundcolor=green,
  linecolor=green,
  skipabove=0pt,
  skipbelow=0pt,
  leftmargin=0pt,
  rightmargin=0pt
]{badges}

\\usepackage{tcolorbox}
\\newtcbox{\\badge}{nobeforeafter,colframe=green,colback=green,boxrule=0.5pt,arc=4pt,
  boxsep=0pt,left=5pt,right=5pt,top=5pt,bottom=5pt,tcbox raise base,
  grow to left by=0pt,
  grow to right by=-3pt,
  enlarge top by=3pt,
  enlarge bottom by=3pt,coltext=white}

  
\\usepackage{helvet} %Helvetica als Standardschriftart
\\renewcommand{\\familydefault}{\\sfdefault} %Helvetica als Standardschriftart

\\definecolor{grey}{rgb}{0.95,0.95,0.95}
\\definecolor{darkgrey}{rgb}{0.6,0.6,0.6}
\\definecolor{white}{rgb}{1,1,1}
\\definecolor{green}{RGB}{76,175,80}

\\pagestyle{fancy}
%\\renewcommand{\\sectionmark}[1]{#1}
%\\lhead{\\rightmark}
\\lhead{\\includegraphics[width=5cm]{static/common/logo.png}}
\\lfoot{Katharineum zu Lübeck}
\\cfoot{\\thepage}
\\rfoot{\\small Umsetzung: © 2018 by Computer-AG}

\\begin{document}"""

TEX_FOOTER = '\end{document}'

TEX_TABLE_HEADER_CLASS = """
\def\\arraystretch{1.5}
\\begin{longtable}{|p{20mm}|p{10mm}|p{32mm}|p{25mm}|p{30mm}|p{35mm}|}
\\hline\n
\\rowcolor{darkgrey}
\\color{white}\\textbf{Klasse} & 
\\color{white}\\textbf{Std.} & 
\\color{white}\\textbf{Lehrer} & 
\\color{white}\\textbf{Fach} & 
\\color{white}\\textbf{Raum} & 
\\color{white}\\textbf{Hinweis}\\\\\\hline
"""

TEX_HEADER_CLASS = """
\\rhead{\\textbf{Vertretungen %s}\\\\Stand: %s\\\\ }
\\Large
\\subsubsection*{}
\\section*{\\Huge Vertretungen %s}
\n"""


def generate_pdf(tex, filename):
    """Generate a PDF by LaTeX code"""

    # Read LaTeX file
    tex_file = open(os.path.join("latex", filename + ".tex"), "w")
    tex_file.write(tex)
    tex_file.close()

    # Execute pdflatex to generate the PDF
    bash_command = "pdflatex -output-directory latex {}.tex".format(filename)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]


def tex_replacer(s):
    """Replace HTML tags by LaTeX tags"""

    # Strong text
    s = s.replace("<strong>", "\\textbf{")
    s = s.replace("</strong>", "}")

    # Struck out text
    s = s.replace("<s>", "\\sout{")
    s = s.replace("</s>", "}")

    # Arrow
    s = s.replace("→", "$\\rightarrow$")

    return s


def generate_class_tex(subs, date):
    """Generate LaTeX for a PDF by a substitution table"""
    tex_body = ""

    # Format dates
    status_date = formats.date_format(date, format="j. F Y, \\K\\W W ")
    current_date = formats.date_format(timezone.datetime.now(), format="j. F Y H:i")
    head_date = formats.date_format(date, format="l, j. F Y")

    # Generate header with dates
    tex_body += TEX_HEADER_CLASS % (status_date, current_date, head_date)

    # Begin table
    tex_body += TEX_TABLE_HEADER_CLASS

    color_background = True
    for sub in subs:
        # Color every second row in grey
        if color_background:
            tex_body += '\\rowcolor{grey}'

        # Get color tag for row
        color = "\color{%s}" % sub.color

        # Print classes
        tex_body += color
        tex_body += '\\textbf{' + sub.classes + '} & '

        # Print lesson number, teacher, subject and room
        for i in [sub.lesson, sub.teacher, sub.subject, sub.room]:
            tex_body += color
            tex_body += tex_replacer(i) + ' & '

        # Print badge (Cancellation)
        if sub.badge is not None:
            tex_body += """\\large\\badge{%s}""" % sub.badge

        # Print notice and new line
        tex_body += color
        tex_body += "\\Large\\textit{%s}\\\\\\hline\n" % (sub.text or "")

        # Change background
        color_background = not color_background
    # End table
    tex_body += '\\end{longtable}'

    # Connect header, body and footer
    tex_content = TEX_HEADER + tex_body + TEX_FOOTER
    return tex_content
