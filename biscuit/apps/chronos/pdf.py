import os
import subprocess

from django.template.loader import render_to_string

from schoolapps.settings import BASE_DIR
from debug.models import register_log_with_filename


LOGO_FILENAME = os.path.join(BASE_DIR, "static", "common", "logo.png")


def generate_pdf(tex, filename):
    """Generate a PDF by LaTeX code"""

    # Write LaTeX file
    tex_file = open(os.path.join(BASE_DIR, "latex", filename + ".tex"), "w", encoding="utf8")
    tex_file.write(tex)
    tex_file.close()

    # Execute pdflatex to generate the PDF
    bash_command = "pdflatex -halt-on-error -output-directory {} {}.tex".format(os.path.join(BASE_DIR, "latex"),
                                                                                os.path.join(BASE_DIR, "latex",
                                                                                             filename))
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    del output

    # Register log file in debugging tool
    register_log_with_filename("latex_{}".format(filename), "latex", "{}.log".format(filename), process.returncode)

def generate_class_tex_header():
    """Generate LaTeX for a PDF by a substitution table"""

    context = {
        "LOGO_FILENAME": LOGO_FILENAME,
    }
    return render_to_string("timetable/latex/header.tex", context)


def generate_class_tex_body(subs, date, header_info, hints=None):
    """Generate LaTeX for a PDF by a substitution table"""

    context = {
        "subs": subs,
        "date": date,
        "header_info": header_info,
        "LOGO_FILENAME": LOGO_FILENAME,
        "hints": hints
    }
    return render_to_string("timetable/latex/substitutions.tex", context)