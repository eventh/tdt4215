short:
	@echo "Building LaTeX files"
	@mkdir .tmp -p
	@pdflatex -output-directory .tmp index.tex
	@pdflatex -output-directory .tmp index.tex
	@mv .tmp/index.pdf report.pdf
	evince report.pdf

report:
	@echo "Building LaTeX files"
	@mkdir .tmp -p
	@pdflatex -output-directory .tmp index.tex
	@cp references.bib .tmp/references.bib
	@cd .tmp; bibtex index.aux
	@pdflatex -output-directory .tmp index.tex
	@pdflatex -output-directory .tmp index.tex
	@mv .tmp/index.pdf report.pdf
	evince report.pdf

tables:
	@echo "Building LaTeX tables standalone"
	@mkdir .tmp -p
	@pdflatex -output-directory .tmp standalone_tables.tex
	@pdflatex -output-directory .tmp standalone_tables.tex
	@mv .tmp/standalone_tables.pdf tables.pdf
	evince tables.pdf

clean:
	@echo "Removing LaTeX build files"
	@rm -fr *.aux *.toc *.log *.lof *.bbl *.blg *.acn
	@rm -fr .tmp/

