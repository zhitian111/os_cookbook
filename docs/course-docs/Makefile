XELATEX := xelatex
FLAGS := -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build

.PHONY: all combined spec lab-manual clean prepare

all: combined spec lab-manual

prepare:
	mkdir -p build

combined: prepare
	$(XELATEX) $(FLAGS) main.tex
	$(XELATEX) $(FLAGS) main.tex

spec: prepare
	$(XELATEX) $(FLAGS) spec.tex
	$(XELATEX) $(FLAGS) spec.tex

lab-manual: prepare
	$(XELATEX) $(FLAGS) lab-manual.tex
	$(XELATEX) $(FLAGS) lab-manual.tex

clean:
	rm -rf build
