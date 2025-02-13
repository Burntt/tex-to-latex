# Convert to DOCX
pandoc -s paper/main_pandoc.tex -f latex+raw_tex --citeproc --bibliography paper/references.bib -F ./pandoc-vanvliet.py --resource-path ./paper --reference-doc template.docx -o output.docx

pandoc -s paper_aroma/main_pandoc.tex -f latex+raw_tex --citeproc --bibliography paper_aroma/MyCollection.bib -F ./pandoc-vanvliet.py --resource-path ./paper_aroma -o ./output_aroma.docx
