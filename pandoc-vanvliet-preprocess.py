import os
import re

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
        centered_content = f'\\begin{{figure}}\\centering{figure_content}\\end{{figure}}'
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

# Center figures
content = center_figures(content)

with open('paper/main_pandoc.tex', 'w') as file_out:
    file_out.write(content)