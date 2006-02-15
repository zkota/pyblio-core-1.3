FIGS = fig/hierarchy.pdf fig/tree.pdf

manual.pdf: manual.tex $(FIGS)
	pdflatex manual.tex
	pdflatex manual.tex

clean:
	rm -f manual.pdf $(FIGS)

%.pdf: %.eps
	epstopdf $<

%.eps: %.dia
	dia -e $@ -t eps-pango $<
