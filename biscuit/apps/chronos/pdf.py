import os
import subprocess

from django.utils import timezone
from django.utils import formats

from schoolapps.settings import BASE_DIR

# LaTeX constants
from untisconnect.sub import get_header_information

DIR = os.path.join(BASE_DIR, "static", "common", "logo.png")
TEX_HEADER_1 = """\\documentclass[11pt]{article}
\\usepackage[ngerman]{babel}
\\usepackage[sfdefault]{cabin}
\\usepackage[utf8]{inputenc}
\\usepackage[a4paper,left=1cm,right=1cm,top=2cm,bottom=2cm,bindingoffset=0mm]{geometry}

% Packages
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

% Badge box
\\usepackage{tcolorbox}
\\newtcbox{\\badge}{nobeforeafter,colframe=green,colback=green,boxrule=0.5pt,arc=4pt,
  boxsep=0pt,left=5pt,right=5pt,top=5pt,bottom=5pt,tcbox raise base,
  grow to left by=0pt,
  grow to right by=-3pt,
  enlarge top by=3pt,
  enlarge bottom by=3pt,coltext=white}

% Define colors
\\definecolor{grey}{RGB}{208, 208, 208}
\\definecolor{darkgrey}{rgb}{0.6,0.6,0.6}
\\definecolor{white}{rgb}{1,1,1}
\\definecolor{green}{RGB}{76,175,80}

% Define header
\\pagestyle{fancy}
% Left header: logo
\\lhead{\\includegraphics[width=5cm]{"""

TEX_HEADER_2 = """}}
% Define footer
\\lfoot{Katharineum zu Lübeck}
\\cfoot{\\thepage}
\\rfoot{\\small Umsetzung: © 2018--2019 by Computer-AG}

\\begin{document}"""
TEX_HEADER = TEX_HEADER_1 + DIR + TEX_HEADER_2

TEX_FOOTER = '\end{document}'

TEX_TABLE_HEADER_CLASS = """
% Init table
\def\\arraystretch{1.5}
\\begin{longtable}{p{20mm}p{8mm}p{32mm}p{25mm}p{30mm}p{45mm}}
\\textbf{Klassen} & 
\\textbf{Std.} & 
\\textbf{Lehrer} & 
\\textbf{Fach} & 
\\textbf{Raum} & 
\\textbf{Hinweis}\\\\
\\hline
\\endhead
"""

TEX_HEADER_CLASS = """
\\rhead{\\textbf{Vertretungen %s}\\\\Stand: %s\\\\ }
\\Large
\\subsubsection*{}
\\section*{\\Huge Vertretungen %s}
\n"""

TEX_HEADER_BOX_START = """
\\fbox{\\parbox{0.27\\linewidth}{
"""

TEX_HEADER_BOX_MIDDLE = """
}\\parbox{0.73\\linewidth}{
"""

TEX_HEADER_BOX_END = """
}} \n\n
"""

TEX_HEADER_BOX_ROW_A = """
\\textbf{%s} 
"""

TEX_HEADER_BOX_ROW_B = """
%s 
"""


def generate_pdf(tex, filename):
    """Generate a PDF by LaTeX code"""

    # Read LaTeX file
    tex_file = open(os.path.join(BASE_DIR, "latex", filename + ".tex"), "w", encoding="utf8")

    tex_file.write(tex)
    tex_file.close()

    # Execute pdflatex to generate the PDF
    bash_command = "pdflatex -output-directory {} {}.tex".format(os.path.join(BASE_DIR, "latex"),
                                                                 os.path.join(BASE_DIR, "latex", filename))
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


def generate_class_tex(subs, date, header_info):
    """Generate LaTeX for a PDF by a substitution table"""

    tex_body = ""

    # Format dates
    status_date = formats.date_format(date, format="j. F Y, \\K\\W W ")
    current_date = formats.date_format(timezone.datetime.now(), format="j. F Y H:i")
    head_date = formats.date_format(date, format="l, j. F Y")

    # Generate header with dates
    tex_body += TEX_HEADER_CLASS % (status_date, current_date, head_date)

    if header_info.is_box_needed():
        tex_body += TEX_HEADER_BOX_START
        for row in header_info.rows:
            tex_body += TEX_HEADER_BOX_ROW_A % row[0]
        tex_body += TEX_HEADER_BOX_MIDDLE
        for row in header_info.rows:
            tex_body += TEX_HEADER_BOX_ROW_B % row[1]
        tex_body += TEX_HEADER_BOX_END
    # Begin table
    tex_body += TEX_TABLE_HEADER_CLASS

    color_background = True
    last_classes = ""
    for sub in subs:
        # Color groups of classes in grey/white
        if last_classes != sub.classes:
            color_background = not color_background

        last_classes = sub.classes

        if color_background:
            tex_body += '\\rowcolor{grey}'

        # Get color tag for row
        color = "\color{%s}" % sub.color

        # Print classes
        # print(sub.classes)
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
        tex_body += "\\Large\\textit{%s}\\\\\n" % (sub.text or "")

    # End table
    tex_body += '\\end{longtable}'

    # Connect header, body and footer
    tex_content = TEX_HEADER + tex_body + TEX_FOOTER
    return tex_content
