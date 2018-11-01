import subprocess

from django.utils import timezone
from django.utils import formats

texheader = """\\documentclass[11pt]{article}
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
  
\\usepackage{helvet} %Helvetica als Standardschriftart
\\renewcommand{\\familydefault}{\\sfdefault} %Helvetica als Standardschriftart

\\definecolor{grey}{rgb}{0.95,0.95,0.95}
\\definecolor{darkgrey}{rgb}{0.6,0.6,0.6}
\\definecolor{white}{rgb}{1,1,1}

\\pagestyle{fancy}
%\\renewcommand{\\sectionmark}[1]{#1}
%\\lhead{\\rightmark}
\\lhead{\\includegraphics[width=5cm]{static/common/logo.png}}
\\lfoot{Katharineum zu Lübeck}
\\cfoot{\\thepage}
\\rfoot{Alle Angaben ohne Gewähr}

\\begin{document}"""

texfooter = '\end{document}'

texdirpath = 'latex'
teachertex = 'latex/teacher.tex'
teacherpdf = 'latex/teacher.pdf'
classtex = 'latex/class.tex'
classpdf = 'latex/class.pdf'


class SubRow(object):
    def __init__(self):
        self.color = "black"
        self.css_class = "black-text"
        self.lesson = ""
        self.classes = ""
        self.teacher = ""
        self.subject = ""
        self.room = ""
        self.text = ""
        self.extra = ""


def generate_sub_table(subs):
    sub_rows = []
    for sub in subs:
        sub_row = SubRow()

        if sub.type == 1 or sub.type == 2:
            sub_row.css_class = "green-text"
            sub_row.color = "green"
        elif sub.type == 3:
            sub_row.css_class = "blue-text"
            sub_row.color = "blue"

        if sub.type == 3:
            sub_row.lesson = "{}./{}".format(sub.lesson - 1, sub.lesson)
        else:
            sub_row.lesson = "{}.".format(sub.lesson)

        for class_ in sub.classes:
            sub_row.classes = class_.name

        if sub.type == 1:
            sub_row.teacher = "<s>{}</s>".format(sub.teacher_old.shortcode)

        elif sub.teacher_new and sub.teacher_old:
            sub_row.teacher = "<s>{}</s> → <strong>{}</strong>".format(sub.teacher_old.shortcode,
                                                                       sub.teacher_new.shortcode)
        elif sub.teacher_new and not sub.teacher_old:
            sub_row.teacher = "<strong>{}</strong>".format(sub.teacher_new.shortcode)
        else:
            sub_row.teacher = "<strong>{}</strong>".format(sub.teacher_old.shortcode)

        if sub.type == 3:
            sub_row.subject = "Aufsicht"
        elif sub.type == 1 or sub.type == 2:
            sub_row.subject = "<s>{}</s>".format(sub.subject_old.shortcode)
        elif sub.subject_new and sub.subject_old:
            sub_row.subject = "<s>{}</s> → <strong>{}</strong>".format(sub.subject_old.shortcode,
                                                                       sub.subject_new.shortcode)
        elif sub.subject_new and not sub.subject_old:
            sub_row.subject = "<strong>{}</strong>".format(sub.subject_new.shortcode)
        else:
            sub_row.subject = "<strong>{}</strong>".format(sub.subject_old.shortcode)

        if sub.type == 3:
            sub_row.room = sub.corridor.name
        elif sub.type == 1 or sub.type == 2:
            pass
        elif sub.room_new and sub.room_old:
            sub_row.room = "<s>{}</s> → <strong>{}</strong>".format(sub.room_old.shortcode, sub.room_new.shortcode)
        elif sub.room_new and not sub.room_old:
            sub_row.room = sub.room_new.shortcode
        else:
            sub_row.room = sub.room_old.shortcode

        sub_row.text = sub.text

        if sub.type == 1:
            sub_row.badge = "Schüler frei"
        elif sub.type == 2:
            sub_row.badge = "Lehrer frei"

        sub_row.extra = "{} {}".format(sub.id, sub.lesson_id)

        sub_rows.append(sub_row)
    return sub_rows


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
    texfile = open(filename + ".tex", "w")
    texfile.write(tex)
    texfile.close()

    bash_command = "pdflatex {}.tex".format(filename)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    # bash_command = "xreader {}.pdf".format(filename)
    # process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    return True


def replacer(str):
    str = str.replace("<strong>", "\\textbf{")
    str = str.replace("<s>", "\\sout{")
    str = str.replace("</strong>", "}")
    str = str.replace("</s>", "}")
    str = str.replace("→", "$\\rightarrow$")
    return str


def generate_class_pdf(subs, date):
    texbody = ""

    # Dates
    status_date = formats.date_format(date, format="j. F Y, \\K\\W W ")
    current_date = formats.date_format(timezone.datetime.now(), format="j. F Y H:i")
    head_date = formats.date_format(date, format="l, j. F Y")

    texbody += TEX_HEADER_CLASS % (status_date, current_date, head_date)

    # Begin table
    texbody += TEX_TABLE_HEADER_CLASS

    color_background = True
    for sub in subs:
        if color_background:
            texbody += '\\rowcolor{grey}'

        texbody += '\\textbf{' + sub.classes + '} & '
        for i in [sub.lesson, sub.teacher, sub.subject, sub.room]:
            texbody += replacer(i) + ' & '

        texbody += "\\textit{%s}\\\\\\hline\n" % (sub.text or "")
        color_background = not color_background
    # End table
    texbody += '\\end{longtable}'

    texcontent = texheader + texbody + texfooter
    return texcontent
