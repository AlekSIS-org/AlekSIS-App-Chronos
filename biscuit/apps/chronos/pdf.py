import os
import subprocess

from django.template.loader import render_to_string
from django.utils import timezone
from django.utils import formats

from schoolapps.settings import BASE_DIR

# LaTeX constants
from untisconnect.sub import get_header_information

LOGO_FILENAME = os.path.join(BASE_DIR, "static", "common", "logo.png")
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
TEX_HEADER = TEX_HEADER_1 + LOGO_FILENAME + TEX_HEADER_2

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
    bash_command = "pdflatex -halt-on-error -output-directory {} {}.tex".format(os.path.join(BASE_DIR, "latex"),
                                                                                os.path.join(BASE_DIR, "latex", filename))
    print(bash_command)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)


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


def generate_class_tex(subs, date, header_info, hints=None):
    """Generate LaTeX for a PDF by a substitution table"""

    context = {
        "subs": subs,
        "date": date,
        "header_info": header_info,
        "LOGO_FILENAME": LOGO_FILENAME,
        "hints": hints
    }
    return render_to_string("timetable/latex/substitutions.tex", context)
