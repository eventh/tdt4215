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

results:
	@echo "Building LaTeX tables standalone"
	@pdflatex tables_standalone.tex
	@pdflatex tables_standalone.tex
	@mv tables_standalone.pdf tables.pdf
	evince tables.pdf

eval:
	@echo "Building LaTeX evaluation standalone"
	@pdflatex -output-directory .tmp evaluation_standalone.tex
	@pdflatex -output-directory .tmp evaluation_standalone.tex
	@mv .tmp/evaluation_standalone.pdf evaluation.pdf
	evince evaluation.pdf

clean:
	@echo "Removing LaTeX build files"
	@rm -f *.out *.aux *.toc *.log *.lof *.bbl *.blg *.acn
	@rm -fr results/*.out results/*.aux *.toc *.log *.lof *.bbl *.blg *.acn
	@rm -fr .tmp/

