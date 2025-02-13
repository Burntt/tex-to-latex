#!/usr/bin/env python3
# Encoding: utf8
"""
This script preprocesses a LaTeX (.tex) file and then converts it to DOCX using pandoc with the vanvliet filter.
It runs the preprocessing script (pandoc-vanvliet-preprocess.py) from the processor directory and then invokes pandoc.
It also automatically detects a .bib file located in the same folder as the input paper (or under a 'paper' subdirectory),
and outputs the new processed LaTeX file to the "result" folder as well as the DOCX file.
Usage:
  python3 run_converter.py input_file.tex [-o output.docx] [--refdoc <template_path>] [--figmethod {1,2,3,auto}]
Example:
  python3 run_converter.py input_papers/AERO/main_paper.tex --figmethod auto
"""

import subprocess
import sys
import os
import glob
import argparse
import traceback

def detect_bib_file(input_dir):
    """
    Detect a .bib file in the same directory as the input file.
    First, search in the input file's directory; if not found, look in the 'paper' subdirectory.
    """
    try:
        bib_files = glob.glob(os.path.join(input_dir, "*.bib"))
        if not bib_files:
            bib_files = glob.glob(os.path.join(input_dir, "paper", "*.bib"))
        if bib_files:
            return bib_files[0]
    except Exception as e:
        print(f"Error detecting bibliography file: {e}", file=sys.stderr)
    return None

def run_preprocess(input_file, fig_method):
    """
    Run the LaTeX preprocessing script from the processor directory.
    The script takes an additional parameter '--figmethod' which controls the centering method.
    It is expected to output a processed file named "main_pandoc_methodX.tex" in the "result" folder
    (where X is the figure method number).
    """
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        preprocess_script = os.path.join(script_dir, "processor", "pandoc-vanvliet-preprocess.py")
        if not os.path.exists(preprocess_script):
            print(f"Preprocess script not found: {preprocess_script}", file=sys.stderr)
            sys.exit(1)
        # Build command. If a specific method is given, pass it.
        cmd = ["python3", preprocess_script, input_file, "--figmethod", str(fig_method)]
        print("Preprocessing LaTeX file with command:")
        print(" ".join(cmd))
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error: Preprocessing failed with error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during preprocessing: {e}\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

def run_pandoc(processed_file, bib_file, output_file, ref_doc, resource_path):
    """
    Run pandoc command to convert the preprocessed LaTeX file to DOCX.
    The resource_path is set to the original paper directory so that images and other assets can be located.
    """
    try:
        # Locate the pandoc filter (pandoc-vanvliet.py) in the 'processor' directory.
        script_dir = os.path.dirname(os.path.realpath(__file__))
        filter_path = os.path.join(script_dir, "processor", "pandoc-vanvliet.py")
        if not os.path.exists(filter_path):
            print(f"Pandoc filter not found: {filter_path}", file=sys.stderr)
            sys.exit(1)
        
        cmd = [
            "pandoc",
            "-s", processed_file,
            "-f", "latex+raw_tex",
            "--citeproc"
        ]
        
        if bib_file:
            cmd.extend(["--bibliography", bib_file])
        else:
            print("Warning: No .bib file detected. Proceeding without bibliography.")
        
        cmd.extend(["-F", filter_path, "--resource-path", resource_path])
        
        if ref_doc:
            cmd.extend(["--reference-doc", ref_doc])
        
        cmd.extend(["-o", output_file])
        
        print("Running pandoc conversion with command:")
        print(" ".join(cmd))
        
        subprocess.run(cmd, check=True)
        print(f"Conversion successful! Output file: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error: Pandoc conversion failed with error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during pandoc conversion: {e}\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Convert a LaTeX (.tex) file to DOCX using pandoc with vanvliet filter."
    )
    parser.add_argument("input", help="Path to the input .tex file")
    parser.add_argument("-o", "--output", help="Base path for the output DOCX file (suffix will be added if using multiple figmethods)")
    parser.add_argument("--refdoc", default="template/pandoc_template.docx", help="Path to the reference DOCX file")
    parser.add_argument("--figmethod", default="3", help="Method to center figures: 1, 2, 3 or 'auto'. Default is 3.")
    args = parser.parse_args()
    
    if not args.input.lower().endswith(".tex"):
        sys.exit("Error: Input file must have a .tex extension.")
    
    input_file = os.path.abspath(args.input)
    original_input_dir = os.path.dirname(input_file)
    bib_file = detect_bib_file(original_input_dir)
    if bib_file:
        print("Detected bibliography file:", bib_file)
    else:
        print("No bibliography file detected in", original_input_dir)
    
    # Determine the reference document to use.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    if args.refdoc == "template/pandoc_template.docx":
        default_template = os.path.abspath(os.path.join(script_dir, "template", "pandoc_template.docx"))
        if sys.stdin.isatty():
            print(f"Default reference template is available: {default_template}")
            print("It is common to use the standard pandoc template.")
            user_input = input("Press Y to use it, or type a new path to a custom reference template: ").strip()
            if user_input and user_input.lower() != 'y':
                ref_doc = os.path.abspath(user_input)
            else:
                ref_doc = default_template
        else:
            ref_doc = default_template
    else:
        ref_doc = os.path.abspath(args.refdoc)
    
    # Decide which figure centering methods to use.
    if args.figmethod.lower() == "auto":
        methods = [1, 2, 3]
    else:
        try:
            methods = [int(args.figmethod)]
        except ValueError:
            sys.exit("Error: --figmethod must be 1, 2, 3 or 'auto'.")
    
    # For each method, run preprocessing and conversion.
    for m in methods:
        print(f"\n=== Converting with figure centering method {m} ===")
        run_preprocess(input_file, m)
        # The preprocessor outputs a file named "main_pandoc_method{m}.tex"
        preprocessed_file = os.path.join(os.getcwd(), "result", f"main_pandoc_method{m}.tex")
        if not os.path.exists(preprocessed_file):
            sys.exit(f"Error: Preprocessed file not found: {preprocessed_file}")
        print("Using preprocessed file:", preprocessed_file)
        # Determine output DOCX file. If no base output is provided, default to a suffixed file in "result".
        if args.output:
            base, ext = os.path.splitext(os.path.abspath(args.output))
            output_file = f"{base}_method{m}.docx"
        else:
            output_file = os.path.join(os.getcwd(), "result", f"main_pandoc_method{m}.docx")
        run_pandoc(preprocessed_file, bib_file, output_file, ref_doc, original_input_dir)
        
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An unexpected error occurred in run_converter.py: {e}\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)
