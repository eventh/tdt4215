report:
	@echo "Building LaTeX files"
	@mkdir .tmp -p
	@pdflatex -output-directory .tmp index.tex
	@pdflatex -output-directory .tmp index.tex
	@mv .tmp/index.pdf presentation.pdf
	evince presentation.pdf

clean:
	@echo "Removing LaTeX build files"
	@rm -f *.out *.aux *.toc *.log *.lof *.bbl *.blg *.acn
	@rm -fr results/*.out results/*.aux *.toc *.log *.lof *.bbl *.blg *.acn
	@rm -fr .tmp/

