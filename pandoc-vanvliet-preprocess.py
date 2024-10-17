import os
import re
import subprocess

# Search-and-replace patterns
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

author_pattern = re.compile(r"\\author\[(.*)\]{(.*)}")
affil_pattern = re.compile(r"\\affil\[(.*)\]{(.*)}")

def process_inputs(content, base_path):
    def replace_input(match):
        input_file = match.group(1)
        input_path = os.path.join(base_path, input_file)
        if not input_path.endswith('.tex'):
            input_path += '.tex'
        with open(input_path, 'r') as f:
            return process_inputs(f.read(), os.path.dirname(input_path))
    
    input_pattern = re.compile(r'\\input{([^}]+)}')
    return input_pattern.sub(replace_input, content)

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
    # Replace aligned and gather environments with a simpler structure
    def replace_complex_math(match):
        lines = match.group(1).split('\\\\')
        simplified = '\\begin{equation*}\n'
        for line in lines:
            simplified += line.strip() + '\n'
        simplified += '\\end{equation*}'
        return simplified

    content = re.sub(r'\\begin{(aligned|gather)}(.*?)\\end{\1}', replace_complex_math, content, flags=re.DOTALL)
    
    # Remove \quad and \, from math environments
    content = re.sub(r'(\\quad|\\,)', ' ', content)
    
    return content

def center_figures(content):
    figure_pattern = re.compile(r'\\begin{figure}(.*?)\\end{figure}', re.DOTALL)
    
    def center_figure_content(match):
        figure_content = match.group(1)
        
        image_match = re.search(r'\\includegraphics(\[.*?\])?\{(.*?)\}', figure_content)
        if image_match:
            image_path = image_match.group(2)
            full_path = os.path.join('paper', image_path)
            
            if not image_path.lower().endswith('.png'):
                png_path = os.path.splitext(image_path)[0] + '.png'
                full_png_path = os.path.join('paper', png_path)
                
                if not os.path.exists(full_path):
                    print(f"Error: Original file not found: {full_path}")
                    return match.group(0)  # Return original if file not found
                
                if not os.path.exists(full_png_path):
                    try:
                        if image_path.lower().endswith('.eps'):
                            subprocess.run(['convert', full_path, full_png_path], check=True)
                        elif image_path.lower().endswith('.pdf'):
                            subprocess.run(['pdftoppm', '-png', '-singlefile', full_path, os.path.splitext(full_png_path)[0]], check=True)
                        else:
                            print(f"Error: Unsupported file format: {image_path}")
                            return match.group(0)  # Return original for unsupported formats
                        print(f"Converted {image_path} to {png_path}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error: Failed to convert {image_path} to PNG: {e}")
                        return match.group(0)  # Return original if conversion fails
                    except FileNotFoundError:
                        print("Error: Required conversion tools not found. Please install ImageMagick and poppler-utils.")
                        return match.group(0)  # Return original if tools are missing
                
                figure_content = figure_content.replace(image_path, png_path)
            
            # Set a consistent width for all images and center them
            figure_content = re.sub(
                r'\\includegraphics(\[.*?\])?\{(.*?)\}',
                r'\\centering\\includegraphics[width=0.8\\textwidth]{\2}',
                figure_content
            )
        
        # Ensure the figure is centered within the figure environment
        centered_content = f'\\begin{{figure}}\\centering\n{figure_content.strip()}\n\\end{{figure}}'
        return centered_content
    
    return figure_pattern.sub(center_figure_content, content)

base_path = os.path.dirname('paper/main.tex')
with open('paper/main.tex', 'r') as file_in:
    content = file_in.read()

# Process \input commands
content = process_inputs(content, base_path)

# Apply other patterns
for pat, rep in patterns:
    content = pat.sub(rep, content)

# Process table rows
content = process_table_rows(content)

# Simplify math environments
content = simplify_math_environments(content)

# Center figures and convert EPS to PDF
content = center_figures(content)

# Remove any existing \end{document} commands
content = re.sub(r'\\end{document}', '', content)

# Add debugging information and ensure there's only one \end{document}
content = content.rstrip() + "\n\n% Debug information\n% End of document reached\n\\end{document}\n"

with open('paper/main_pandoc.tex', 'w') as file_out:
    file_out.write(content)

print("Processing complete. Output written to 'paper/main_pandoc.tex'")

# Print the last 10 lines of the processed file
with open('paper/main_pandoc.tex', 'r') as file_in:
    lines = file_in.readlines()
    print("\nLast 10 lines of processed file:")
    for line in lines[-10:]:
        print(line.strip())
