import os
import subprocess

from schoolapps.settings import BASE_DIR


def convert_markdown_2_latex(s):
    try:
        # Write markdown file
        md_file = open(os.path.join(BASE_DIR, "latex", "m2l.md"), "w", encoding="utf8")
        md_file.write(s)
        md_file.close()

        # Execute pandoc to convert markdown to latex
        bash_command = "pandoc --from markdown --to latex --output {} {}".format(
            os.path.join(BASE_DIR, "latex", "m2l.tex"),
            os.path.join(BASE_DIR, "latex", "m2l.md"))
        process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print("[MD TO LATEX]", output)
        print("[RETURN CODE]", process.returncode)

        # Read converted latex from file
        tex_file = open(os.path.join(BASE_DIR, "latex", "m2l.tex"), "r", encoding="utf8")
        r = tex_file.read()
        tex_file.close()

        # Replace some things
        r = r.replace("\subparagraph", "\subsubsection")
        r = r.replace("\paragraph", "\subsubsection")
        r = r.replace("section", "section*")

        # Return latex
        return r
    except Exception as e:
        # Print error
        print("[MD TO LATEX]", e)
        return ""
