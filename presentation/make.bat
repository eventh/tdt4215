@echo off
if "%1" == "clean" goto clean
echo "Building LaTeX files"
mkdir tmp
if "%1" == "" goto make
echo "Unknown command %1"
goto :eof

:make
	pdflatex -output-directory tmp index.tex
	pdflatex -output-directory tmp index.tex
	move /Y tmp\index.pdf presentation.pdf
	start presentation.pdf
	goto :eof

:clean
    echo "Removing LaTeX build files"
    del /S *.aux *.toc *.log *.out *.lof *.lot *.bbl *.blg *.acn
    rmdir /S /Q tmp
    goto :eof

