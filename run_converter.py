#!/usr/bin/env python3
# Encoding: utf8
"""
This script preprocesses a LaTeX (.tex) file and then converts it to DOCX using pandoc with the vanvliet filter.
It runs the preprocessing script (pandoc-vanvliet-preprocess.py) from the processor directory and then invokes pandoc.
It also automatically detects a .bib file located in the same folder as the input paper (or under a 'paper' subdirectory),
and outputs the new processed LaTeX file to the "result" folder as well as the DOCX file.
Usage:
  python3 run_converter.py input_file.tex [-o output.docx] [--refdoc <template_path>]
Example:
  python3 run_converter.py input_papers/AERO/main_paper.tex
"""

import subprocess
import sys
import os
import glob
import argparse

def detect_bib_file(input_dir):
    """
    Detect a .bib file in the same directory as the input file.
    First, search in the input file's directory; if not found, look in the 'paper' subdirectory.
    """
    bib_files = glob.glob(os.path.join(input_dir, "*.bib"))
    if not bib_files:
        bib_files = glob.glob(os.path.join(input_dir, "paper", "*.bib"))
    if bib_files:
        return bib_files[0]
    return None

def run_preprocess(input_file):
    """
    Run the LaTeX preprocessing script from the processor directory.
    The preprocess script is expected to output a processed file named "main_pandoc.tex" in the "result" folder.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    preprocess_script = os.path.join(script_dir, "processor", "pandoc-vanvliet-preprocess.py")
    if not os.path.exists(preprocess_script):
        print(f"Preprocess script not found: {preprocess_script}", file=sys.stderr)
        sys.exit(1)
    
    cmd = ["python3", preprocess_script]
    if input_file:
        cmd.append(input_file)
    
    print("Preprocessing LaTeX file with command:")
    print(" ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit("Error: Preprocessing failed.")

def run_pandoc(processed_file, bib_file, output_file, ref_doc, resource_path):
    """
    Run pandoc command to convert the preprocessed LaTeX file to DOCX.
    The resource_path is set to the original paper directory so that images and other assets can be located.
    """
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
    
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit("Error: Pandoc conversion failed.")
    else:
        print(f"Conversion successful! Output file: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert a LaTeX (.tex) file to DOCX using pandoc with vanvliet filter."
    )
    parser.add_argument("input", help="Path to the input .tex file")
    parser.add_argument("-o", "--output", help="Path for the output DOCX file")
    # Set default to our standard template
    parser.add_argument("--refdoc", default="template/pandoc_template.docx", help="Path to the reference DOCX file")
    args = parser.parse_args()
    
    if not args.input.lower().endswith(".tex"):
        sys.exit("Error: Input file must have a .tex extension.")
    
    input_file = os.path.abspath(args.input)
    # Use the original input file's directory as the resource path,
    # since that is where assets (e.g. images) are located.
    original_input_dir = os.path.dirname(input_file)
    # If no output file is provided, place the DOCX in the "result" folder
    output_file = os.path.abspath(args.output) if args.output else os.path.join(os.getcwd(), "result", "main_pandoc.docx")
    
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
    
    # Step 1: Preprocess the LaTeX file.
    run_preprocess(input_file)
    preprocessed_file = os.path.join(os.getcwd(), "result", "main_pandoc.tex")
    if not os.path.exists(preprocessed_file):
        sys.exit(f"Error: Preprocessed file not found: {preprocessed_file}")
    
    print("Using preprocessed file:", preprocessed_file)
    
    # Step 2: Convert the preprocessed LaTeX file to DOCX.
    run_pandoc(preprocessed_file, bib_file, output_file, ref_doc, original_input_dir)

if __name__ == "__main__":
    main()
