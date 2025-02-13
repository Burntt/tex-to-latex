#!/usr/bin/env python3
# encoding: utf8
r"""
This script preprocesses a LaTeX (.tex) file and converts it for pandoc-based DOCX conversion.
It processes \input commands, applies regex-based replacements, and ensures proper document termination.
"""

import os
import re
import subprocess
import sys
import glob

def get_image_folders(base_path, allowed_extensions=('.pdf', '.eps', '.png', '.jpg', '.jpeg')):
    """
    Recursively search from base_path for directories that contain image files.
    Returns a list of directories.
    """
    image_folders = set()
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(allowed_extensions):
                image_folders.add(root)
                break
    return list(image_folders)

def process_inputs(content, base_path):
    def ensure_tex(filename):
        return filename if filename.lower().endswith('.tex') else filename + '.tex'
    def replace_input(match):
        input_file = match.group(1)
        input_file_norm = os.path.normpath(input_file)
        candidate = os.path.join(base_path, input_file_norm)
        candidate = ensure_tex(candidate)
        if not os.path.exists(candidate) and input_file_norm.startswith("paper" + os.sep):
            alt = input_file_norm[len("paper" + os.sep):]
            alt = os.path.normpath(alt)
            candidate_alt = os.path.join(base_path, ensure_tex(alt))
            if os.path.exists(candidate_alt):
                candidate = candidate_alt
        try:
            with open(candidate, 'r', encoding='utf-8') as f:
                return process_inputs(f.read(), os.path.dirname(candidate))
        except FileNotFoundError:
            sys.exit(f"Error: Unable to locate input file: {candidate}")
    input_pattern = re.compile(r'\\input{([^}]+)}')
    return input_pattern.sub(replace_input, content)

def preprocess_latex(input_file_path):
    base_path = os.path.dirname(input_file_path)
    with open(input_file_path, 'r', encoding='utf-8') as file_in:
        content = file_in.read()
    # Process \input commands.
    content = process_inputs(content, base_path)
    # Remove unwanted column type commands.
    content = re.sub(r'\\newcolumntype{.*?}', '', content)
    content = re.sub(r'\\newcolumntype{L}\[1\]{>{\\raggedright\\let\\newline\\\\arraybackslash\\hspace{0pt}}m{#1}}', '', content)
    # Remove any existing \end{document} commands.
    content = re.sub(r'\\end{document}', '', content)
    # Replace aligned environments with gather.
    content = re.sub(r'\\begin{aligned}', r'\\begin{gather}', content)
    content = re.sub(r'\\end{aligned}', r'\\end{gather}', content)
    # Append a single final \end{document} with debug info.
    content = content.rstrip() + "\n\n% Debug information\n% End of document reached\n\\end{document}\n"
    result_dir = os.path.join(os.getcwd(), "result")
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    output_file_path = os.path.join(result_dir, 'main_pandoc.tex')
    with open(output_file_path, 'w', encoding='utf-8') as file_out:
        file_out.write(content)
    print(f"Processing complete. Output written to '{output_file_path}'")
    return output_file_path

# Search-and-replace patterns.
patterns = [
    (re.compile(r'\\begin{figure\*}'), r'\\begin{figure}'),
    (re.compile(r'\\end{figure\*}'), r'\\end{figure}'),
    (re.compile(r'\\tcov{\\mat{([^}]+)}}'), r'$\\mathbf{\\Sigma}_\\mathbf{\1}$'),
    (re.compile(r'\\tcov{\\emat{([^}]+)}}'), r'$\\mathbf{\\Sigma}_{\\widehat{\\mathbf{\1}}}$'),
    (re.compile(r'\\tcov{\\text{([^}]+)}}'), r'$\\mathbf{\\Sigma}_\\text{\1}$'),
    (re.compile(r'\\icov{\\emat{([^}]+)}}'), r'\\mathbf{\\Sigma}^{-1}_{\\widehat{\\mathbf{\1}}}'),
    (re.compile(r'\\ticov{\\emat{([^}]+)}}'), r'$\\mathbf{\\Sigma}^{-1}_{\\widehat{\\mathbf{\1}}}$'),
    (re.compile(r'\\mat{([^}]+)}'), r'\\mathbf{\1}'),
    (re.compile(r'\\vec{([^}]+)}'), r'\\mathbf{\1}'),
    (re.compile(r'\\tmat{([^}]+)}'), r'$\\mathbf{\1}$'),
    (re.compile(r'\\tvec{([^}]+)}'), r'$\\mathbf{\1}$'),
    (re.compile(r'\\emat{([^}]+)}'), r'\\widehat{\\mathbf{\1}}'),
    (re.compile(r'\\evec{([^}]+)}'), r'\\widehat{\\mathbf{\1}}'),
    (re.compile(r'\\temat{([^}]+)}'), r'$\\widehat{\\mathbf{\1}}$'),
    (re.compile(r'\\tevec{([^}]+)}'), r'$\\widehat{\\mathbf{\1}}$'),
    (re.compile(r'\\trans'), r'^\\mathsf{T}'),
    (re.compile(r'\\hermconj'), r'^\\mathsf{H}'),
    (re.compile(r'\\cov{([^}]+)}'), r'\\mathbf{\\Sigma}_\\mathbf{\1}'),
    (re.compile(r'\\icov{([^}]+)}'), r'\\mathbf{\\Sigma}^{-1}_\\mathbf{\1}'),
    (re.compile(r'\\tcov{([^}]+)}'), r'$\\mathbf{\\Sigma}_\\mathbf{\1}$'),
    (re.compile(r'\\ticov{([^}]+)}'), r'$\\mathbf{\\Sigma}^{-1}_\\mathbf{\1}$'),
    (re.compile(r'\\vspace{2ex}'), r''),
    (re.compile(r'\\begin{table\*?}'), r'\\begin{table}'),
    (re.compile(r'\\end{table\*?}'), r'\\end{table}'),
    (re.compile(r'\\begin{tabular}(\[.*?\])?{.*?}'), r'\\begin{tabular}'),
    (re.compile(r'\\end{tabular}'), r'\\end{tabular}'),
    (re.compile(r'\\hline'), r''),
    (re.compile(r'\\cline{.*?}'), r''),
    (re.compile(r'\\multicolumn{(\d+)}{.*?}{(.*?)}'), r'\2'),
    (re.compile(r'\\multirow{(\d+)}{.*?}{(.*?)}'), r'\2'),
]

def process_table_rows(content):
    lines = content.split('\n')
    processed_lines = []
    in_table = False
    for line in lines:
        if '\\begin{tabular}' in line:
            in_table = True
        elif '\\end{tabular}' in line:
            in_table = False
        if in_table:
            line = re.sub(r'&', ' | ', line)
            line = re.sub(r'\\\\', '', line)
        processed_lines.append(line)
    return '\n'.join(processed_lines)

def simplify_math_environments(content):
    def replace_complex_math(match):
        env_type = match.group(1)
        lines = match.group(2).split('\\\\')
        simplified = '\\begin{equation*}\n'
        for line in lines:
            line = line.strip()
            if env_type == 'gather':
                line = re.sub(r'&', '', line)
            line = re.sub(r'(\$\$?|\\\\?\(|\\\\?\[)', r'\\begin{math}', line)
            line = re.sub(r'(\$\$?|\\\\?\)|\\\\\])', r'\\end{math}', line)
            line = re.sub(r'\\\\([\w\s]+)', r'\\\\textbackslash{\1}', line)
            if line:
                simplified += line + '\\\\\n'
        simplified += '\\end{equation*}'
        return simplified
    content = re.sub(r'\\begin{(aligned|gather)}(.*?)\\end{\1}', replace_complex_math, content, flags=re.DOTALL)
    def replace_equation_star(match):
        lines = match.group(1).split('\\\\')
        simplified = '\\begin{equation*}\n'
        for line in lines:
            line = line.strip()
            line = re.sub(r'(\$\$?|\\\\?\(|\\\\?\[)', r'\\begin{math}', line)
            line = re.sub(r'(\$\$?|\\\\?\)|\\\\\])', r'\\end{math}', line)
            line = re.sub(r'\\\\([\w\s]+)', r'\\\\textbackslash{\1}', line)
            if line:
                simplified += line + '\\\\\n'
        simplified += '\\end{equation*}'
        return simplified
    content = re.sub(r'\\begin{equation\*}(.*?)\\end{equation\*}', replace_equation_star, content, flags=re.DOTALL)
    content = re.sub(r'(\\quad|\\,)', ' ', content)
    return content

def center_figures(content, base_path):
    image_folders = get_image_folders(base_path)
    figure_pattern = re.compile(r'\\begin{figure}(.*?)\\end{figure}', re.DOTALL)
    def center_figure_content(match):
        figure_content = match.group(1)
        image_match = re.search(r'\\includegraphics(\[.*?\])?\{(.*?)\}', figure_content)
        if image_match:
            image_path = image_match.group(2)
            if image_path.startswith("paper" + os.sep):
                image_path = image_path[len("paper" + os.sep):]
            full_path = os.path.join(base_path, image_path)
            if not os.path.exists(full_path):
                found = False
                for folder in image_folders:
                    candidate = os.path.join(folder, os.path.basename(image_path))
                    if os.path.exists(candidate):
                        full_path = candidate
                        try:
                            image_path = os.path.relpath(candidate, base_path)
                        except ValueError:
                            image_path = candidate
                        found = True
                        break
                if not found:
                    print(f"Error: Original file not found: {full_path}")
                    return match.group(0)
            if not image_path.lower().endswith('.png'):
                png_path = os.path.splitext(image_path)[0] + '.png'
                full_png_path = os.path.join(base_path, png_path)
                if not os.path.exists(full_png_path):
                    try:
                        if image_path.lower().endswith('.eps'):
                            subprocess.run(['convert', full_path, full_png_path], check=True)
                        elif image_path.lower().endswith('.pdf'):
                            subprocess.run(['pdftoppm', '-png', '-singlefile', full_path, os.path.splitext(full_png_path)[0]], check=True)
                        else:
                            print(f"Error: Unsupported file format: {image_path}")
                            return match.group(0)
                        print(f"Converted {image_path} to {png_path}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error: Failed to convert {image_path} to PNG: {e}")
                        return match.group(0)
                    except FileNotFoundError:
                        print("Error: Required conversion tools not found. Please install ImageMagick and poppler-utils.")
                        return match.group(0)
                image_path = png_path
            figure_content = re.sub(
                r'\\includegraphics(\[.*?\])?\{(.*?)\}',
                rf'\\centering\\includegraphics[width=0.8\\textwidth]{{{image_path}}}',
                figure_content
            )
        centered_content = f'\\begin{{figure}}\\centering\n{figure_content.strip()}\n\\end{{figure}}'
        return centered_content
    return figure_pattern.sub(center_figure_content, content)

def main():
    print("Arguments passed to preprocessor:", sys.argv)
    if len(sys.argv) > 1:
        input_file_path = sys.argv[1]
    else:
        sys.exit("Error: No input file specified to preprocess.")
    base_path = os.path.dirname(os.path.abspath(input_file_path))
    output_file_path = preprocess_latex(input_file_path)
    with open(output_file_path, 'r', encoding='utf-8') as file_in:
        content = file_in.read()
    for pat, rep in patterns:
        content = pat.sub(rep, content)
    content = process_table_rows(content)
    content = simplify_math_environments(content)
    content = center_figures(content, base_path)
    content = re.sub(r'\\end{document}', '', content)
    content = content.rstrip() + "\n\n% Debug information\n% End of document reached\n\\end{document}\n"
    with open(output_file_path, 'w', encoding='utf-8') as file_out:
        file_out.write(content)
    print("Processing complete. Output written to", output_file_path)
    with open(output_file_path, 'r', encoding='utf-8') as file_in:
        lines = file_in.readlines()
        print("\nLast 10 lines of processed file:")
        for line in lines[-10:]:
            print(line.strip())

if __name__ == '__main__':
    main()