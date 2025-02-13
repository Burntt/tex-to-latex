#!/usr/bin/env python3
# Encoding: utf8
"""
This script preprocesses a LaTeX (.tex) file and then converts it to DOCX using pandoc with the vanvliet filter.
It runs the preprocessing script (pandoc-vanvliet-preprocess.py) and then invokes pandoc.
It also automatically detects a .bib file located next to pandoc-vanvliet.py (or under the 'paper' subdirectory).
Usage:
  python3 run_converter.py input_file.tex [-o output.docx] [--refdoc template.docx]
"""

import subprocess
import sys
import os
import glob
import argparse

def detect_bib_file():
    """
    Detect a .bib file located next to pandoc-vanvliet.py.
    First, search in the current script directory;
    if not found, look in the 'paper' subdirectory.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    bib_files = glob.glob(os.path.join(script_dir, "*.bib"))
    if not bib_files:
        # Try the 'paper' subdirectory
        bib_files = glob.glob(os.path.join(script_dir, "paper", "*.bib"))
    if bib_files:
        # If multiple .bib files are found, pick the first one.
        return bib_files[0]
    return None

def run_preprocess(input_file):
    """
    Run the LaTeX preprocessing script.
    If the preprocess script supports an input argument, it will be passed.
    Otherwise, the script is expected to handle its own configuration.
    """
    preprocess_script = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pandoc-vanvliet-preprocess.py")
    if not os.path.exists(preprocess_script):
        print(f"Preprocess script not found: {preprocess_script}", file=sys.stderr)
        sys.exit(1)
    
    cmd = ["python3", preprocess_script]
    # Append the input file if the preprocess script accepts an argument.
    if input_file:
        cmd.append(input_file)
    
    print("Preprocessing LaTeX file with command:")
    print(" ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit("Error: Preprocessing failed.")

def run_pandoc(input_file, bib_file, output_file, ref_doc):
    """
    Run pandoc command to convert the LaTeX file to DOCX.
    """
    # Determine resource path: use the directory of the input file.
    input_dir = os.path.dirname(os.path.abspath(input_file))
    resource_path = input_dir

    # Locate the pandoc filter (pandoc-vanvliet.py) in the same directory as this script
    filter_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pandoc-vanvliet.py")
    if not os.path.exists(filter_path):
        print(f"Pandoc filter not found: {filter_path}", file=sys.stderr)
        sys.exit(1)
    
    cmd = [
        "pandoc",
        "-s", input_file,
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
    parser.add_argument("-o", "--output", default="output.docx", help="Path for the output DOCX file")
    parser.add_argument("--refdoc", default="template.docx", help="Path to the reference DOCX file")
    args = parser.parse_args()
    
    # Validate input file extension
    if not args.input.lower().endswith(".tex"):
        sys.exit("Error: Input file must have a .tex extension.")
    
    input_file = os.path.abspath(args.input)
    output_file = os.path.abspath(args.output)
    ref_doc = os.path.abspath(args.refdoc) if args.refdoc else None
    
    # Detect bibliography file next to pandoc-vanvliet.py
    bib_file = detect_bib_file()
    if bib_file:
        print("Detected bibliography file:", bib_file)
    else:
        print("No bibliography file detected.")
    
    # Step 1: Preprocess the LaTeX file
    run_preprocess(input_file)
    
    # Assume the preprocess script either modifies the input file in place
    # or produces the same output filename; adjust if necessary.
    preprocessed_file = input_file

    # Step 2: Convert the preprocessed LaTeX file to DOCX
    run_pandoc(preprocessed_file, bib_file, output_file, ref_doc)

if __name__ == "__main__":
    main()
