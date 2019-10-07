import os
import subprocess
import inspect

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


def equal(sub1, sub2):
    if sub1.classes == sub2.classes and sub1.sub and sub2.sub and \
        sub1.sub.teacher_old == sub2.sub.teacher_old and \
        sub1.sub.teacher_new == sub2.sub.teacher_new and \
        sub1.sub.subject_old == sub2.sub.subject_old and \
        sub1.sub.subject_new == sub2.sub.subject_new and \
        sub1.sub.room_old == sub2.sub.room_old and \
        sub1.sub.room_new == sub2.sub.room_new and \
        sub1.sub.text == sub2.sub.text:
        print("Treffer:", sub1.classes, '=', sub2.classes, '\n',
            sub1.sub.teacher_old, '=', sub2.sub.teacher_old, '\n',
            sub1.sub.teacher_new, '=', sub2.sub.teacher_old, '\n',
            sub1.sub.subject_old, '=', sub2.sub.subject_old, '\n',
            sub1.sub.subject_new, '=', sub2.sub.subject_new, '\n',
            sub1.sub.room_old, '=', sub2.sub.room_new, '\n',
            sub1.sub.text, '=', sub2.sub.text)
        return True


def merge_subs(subs):
    new_subs = []
    i = 0
    print("Länge:",len(subs))
    while i < len(subs) - 1:
        j = 1
        # Hier geht's schon los: Warum ist sub.teacher_old der gesuchte String, aber sub.subject_old ist ein Objekt?
#        print('Komplett:',subs[i].classes, subs[i].sub.teacher_old.shortcode, subs[i].sub.subject_old, subs[i].sub.room_old, subs[i].sub.text)
#         sub = inspect.getmembers(subs[i])
#         for s in sub:
#             print('sub:',len(s), s[0], s[1])
        while equal(subs[i], subs[i + j]):
            j += 1
            if i + j > len(subs) - 1:
                break
        if j > 1:
            new_sub = subs[i]
            new_sub.lesson = subs[i].lesson + '-' + subs[i + j - 1].lesson
            print('lesson',new_sub.lesson)
            new_subs.append(new_sub)
        else:
            new_subs.append(subs[i])
            # get last item
            if i == len(subs) - 2:
                new_subs.append(subs[i+1])
                break
        i += j
    return(new_subs)


def generate_class_tex(subs, date, header_info, hints=None):
    """Generate LaTeX for a PDF by a substitution table"""
    subs = merge_subs(subs)
    context = {
        "subs": subs,
        "date": date,
        "header_info": header_info,
        "LOGO_FILENAME": LOGO_FILENAME,
        "hints": hints
    }
    return render_to_string("timetable/latex/substitutions.tex", context)
