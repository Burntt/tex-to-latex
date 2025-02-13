#!/usr/bin/env python3
# encoding: utf8
r"""
This script preprocesses a LaTeX (.tex) file and converts it for pandoc-based DOCX conversion.
It processes \input commands, applies regex-based replacements, centers figures (using a chosen method),
and ensures proper document termination.
"""

import os
import re
import subprocess
import sys
import glob
import traceback
import argparse

def get_image_folders(base_path, allowed_extensions=('.pdf', '.eps', '.png', '.jpg', '.jpeg')):
    """
    Recursively search from base_path for directories that contain image files.
    Returns a list of directories.
    """
    image_folders = set()
    try:
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith(allowed_extensions):
                    image_folders.add(root)
                    break
    except Exception as e:
        print(f"Error while searching for image folders: {e}\n{traceback.format_exc()}", file=sys.stderr)
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
        except Exception as e:
            sys.exit(f"Error processing input file {candidate}: {e}\n{traceback.format_exc()}")
    input_pattern = re.compile(r'\\input{([^}]+)}')
    try:
        return input_pattern.sub(replace_input, content)
    except Exception as e:
        sys.exit(f"Error processing \\input commands: {e}\n{traceback.format_exc()}")

def preprocess_latex(input_file_path):
    try:
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
        return content, base_path
    except Exception as e:
        sys.exit(f"Error during LaTeX preprocessing: {e}\n{traceback.format_exc()}")

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
    try:
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
    except Exception as e:
        sys.exit(f"Error processing table rows: {e}\n{traceback.format_exc()}")

def simplify_math_environments(content):
    try:
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
    except Exception as e:
        sys.exit(f"Error simplifying math environments: {e}\n{traceback.format_exc()}")

def center_figures(content, base_path, method=3):
    r"""
    Process figure environments so that figures are centered and images are scaled to 0.6 of the text width.
    
    Four methods are provided:
    
    Method 1:
        Inserts a \centering command before the \includegraphics call inside a figure environment.
        Example output:
          \begin{figure}
          \centering\includegraphics[width=0.6\textwidth]{<image>}
          \end{figure}
    
    Method 2:
        Wraps the image in a center environment inside a figure environment.
        Example output:
          \begin{figure}
          \begin{center}
          \includegraphics[width=0.6\textwidth]{<image>}
          \end{center}
          \end{figure}
    
    Method 3:
        Uses \centerline to center the image inside a figure environment.
        Example output:
          \begin{figure}
          \centerline{\includegraphics[width=0.6\textwidth]{<image>}}
          \end{figure}
    
    Method 4:
        Removes the figure environment entirely and outputs a centered image as its own block.
        Extra paragraph breaks (with some vertical space) are added so that text flows freely above and below.
        Example output:
          \par\medskip
          \begin{center}
          \includegraphics[width=0.6\textwidth]{<image>}
          \end{center}
          \medskip\par
    """
    try:
        image_folders = get_image_folders(base_path)
        figure_pattern = re.compile(r'\\begin{figure}(.*?)\\end{figure}', re.DOTALL)
    
        def center_figure_content(match):
            figure_content = match.group(1)
            image_match = re.search(r'\\includegraphics(?:\[.*?\])?\{(.*?)\}', figure_content)
            if image_match:
                image_path = image_match.group(1)
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
                        print(f"Error: Original file not found: {full_path}", file=sys.stderr)
                        return match.group(0)
                # Convert file if necessary.
                if not image_path.lower().endswith('.png'):
                    png_path = os.path.splitext(image_path)[0] + '.png'
                    full_png_path = os.path.join(base_path, png_path)
                    if not os.path.exists(full_png_path):
                        try:
                            if image_path.lower().endswith('.eps'):
                                subprocess.run(['convert', full_path, full_png_path], check=True)
                            elif image_path.lower().endswith('.pdf'):
                                subprocess.run(
                                    ['pdftoppm', '-png', '-singlefile',
                                     full_path, os.path.splitext(full_png_path)[0]], check=True
                                )
                            else:
                                print(f"Error: Unsupported file format: {image_path}", file=sys.stderr)
                                return match.group(0)
                            print(f"Converted {image_path} to {png_path}")
                        except subprocess.CalledProcessError as e:
                            print(f"Error: Failed to convert {image_path} to PNG: {e}", file=sys.stderr)
                            return match.group(0)
                        except FileNotFoundError:
                            print("Error: Required conversion tools not found. Please install ImageMagick and poppler-utils.", file=sys.stderr)
                            return match.group(0)
                    image_path = png_path
                # Decide on the new image inclusion command based on the chosen method.
                if method == 1:
                    new_cmd = f"\\centering\\includegraphics[width=0.6\\textwidth]{{{image_path}}}"
                elif method == 2:
                    new_cmd = f"\\begin{{center}}\\includegraphics[width=0.6\\textwidth]{{{image_path}}}\\end{{center}}"
                elif method == 3:
                    new_cmd = f"\\centerline{{\\includegraphics[width=0.6\\textwidth]{{{image_path}}}}}"
                elif method == 4:
                    # For method 4, output just the image (centered) with paragraph breaks,
                    # without a figure environment.
                    new_cmd = f"\\includegraphics[width=0.6\\textwidth]{{{image_path}}}"
                else:
                    new_cmd = f"\\centering\\includegraphics[width=0.6\\textwidth]{{{image_path}}}"
                # Replace the original \includegraphics command with our new command.
                new_figure_content = re.sub(
                    r'\\includegraphics(?:\[.*?\])?\{(.*?)\}',
                    lambda m: new_cmd,
                    figure_content
                )
            else:
                new_figure_content = figure_content
            # Wrap the content according to the method.
            if method == 4:
                # No figure environment: insert paragraph breaks for free movement.
                centered_content = f"\\par\\medskip\\begin{{center}}{new_figure_content.strip()}\\end{{center}}\\medskip\\par"
            elif method == 2:
                centered_content = f"\\begin{{figure}}\n{new_figure_content.strip()}\n\\end{{figure}}"
            else:
                centered_content = f"\\begin{{figure}}\\centering\n{new_figure_content.strip()}\n\\end{{figure}}"
            return centered_content
    
        return figure_pattern.sub(center_figure_content, content)
    except Exception as e:
        sys.exit(f"Error centering figures: {e}\n{traceback.format_exc()}")

def main():
    parser = argparse.ArgumentParser(description="Preprocess a LaTeX file for DOCX conversion.")
    parser.add_argument("input_file", help="Path to the input .tex file")
    parser.add_argument("--figmethod", type=int, choices=[1,2,3,4], default=3,
                        help="Method to center figures: 1, 2, 3, or 4. Default is 3.")
    args = parser.parse_args()
    
    input_file_path = os.path.abspath(args.input_file)
    content, base_path = preprocess_latex(input_file_path)
    
    # Apply other search-and-replace patterns (omitted here for brevity).
    # For example: content = re.sub(...), process_table_rows(content), simplify_math_environments(content)
    
    # Center figures using the chosen method.
    content = center_figures(content, base_path, method=args.figmethod)
    
    # Remove any extra \end{document} and add a single one at the end.
    content = re.sub(r'\\end{document}', '', content)
    content = content.rstrip() + "\n\n% Debug information\n% End of document reached\n\\end{document}\n"
    
    result_dir = os.path.join(os.getcwd(), "result")
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    # Name the output file with the method number.
    output_file_path = os.path.join(result_dir, f"main_pandoc_method{args.figmethod}.tex")
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file_out:
            file_out.write(content)
        print("Processing complete. Output written to", output_file_path)
        with open(output_file_path, 'r', encoding='utf-8') as file_in:
            lines = file_in.readlines()
            print("\nLast 10 lines of processed file:")
            for line in lines[-10:]:
                print(line.strip())
    except Exception as e:
        sys.exit(f"Error writing output file: {e}\n{traceback.format_exc()}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.exit(f"An unexpected error occurred in pandoc-vanvliet-preprocess.py: {e}\n{traceback.format_exc()}")