.PHONY: all check package figures

all:
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
	cp build/main.pdf main.pdf

figures:
	python export_figures.py

check: all
	python validate.py

package: check figures
	python package.py
