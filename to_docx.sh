# python3 pandoc-vanvliet-preprocess.py
# pandoc -s beamformer_framework_pandoc.tex -f latex+raw_tex --citeproc --bibliography beamformer_framework.bib -F ./pandoc-vanvliet.py --resource-path ./paper --reference-doc template.docx -o beamformer_framework.docx
# pandoc -s paper/beamformer_framework.tex -f latex+raw_tex --citeproc --bibliography beamformer_framework.bib --resource-path ./paper -o beamformer_framework.json
# python3 -m json.tool beamformer_framework.json > beamformer_framework_formatted.json



#!/bin/bash

# Preprocess the LaTeX file
python3 pandoc-vanvliet-preprocess.py

# Convert to DOCX
pandoc -s paper/main_pandoc.tex -f latex+raw_tex --citeproc --bibliography paper/references.bib -F ./pandoc-vanvliet.py --resource-path ./paper --reference-doc template.docx -o output.docx

pandoc -s paper_aroma/main_pandoc.tex -f latex+raw_tex --citeproc --bibliography paper_aroma/MyCollection.bib -F ./pandoc-vanvliet.py --resource-path ./paper_aroma -o ./output_aroma.docx

# # Convert to JSON (optional, for debugging)
# pandoc -s paper/main_pandoc.tex -f latex+raw_tex --citeproc --bibliography paper/references.bib --resource-path ./paper -o paper/main.json

# # Format JSON (optional, for debugging)
# python3 -m json.tool paper/main.json > paper/main_formatted.json
