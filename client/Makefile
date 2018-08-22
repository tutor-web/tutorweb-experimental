GIT = git
NPM = npm
YARN = yarn
NODE = node
NODE != which node || which nodejs
NODE_CMD = NODE_PATH="$(CURDIR)" $(NODE)
SHELL=/bin/bash -o pipefail

OUTPUTS := coin index preview stage test/select_list test/progress

OUT_FILES = \
    www/geogebra \
    www/js/polyfill.min.js \
    www/js/libraries.min.js \
    www/css/libraries.min.css \
    $(foreach O,$(OUTPUTS),www/$(O).html www/js/$(O).min.js www/css/$(O).min.css)

LIBRARIES_JS = \
    jquery \

LIBRARIES_CSS = \
    node_modules/bootstrap/dist/css/bootstrap-reboot.min.css \
    node_modules/bootstrap/dist/css/bootstrap-grid.min.css \

all: test lint compile

www/geogebra:
	wget -O /tmp/ggb-bundle.zip https://download.geogebra.org/package/geogebra-math-apps-bundle
	unzip /tmp/ggb-bundle.zip -d $@
	rm /tmp/ggb-bundle.zip

compile: node_modules/ clean-unused $(OUT_FILES)

start: all

test: node_modules/
	$(NODE_CMD) node_modules/.bin/tape tests/test_*.js

coverage: node_modules/
	$(NODE_CMD) node_modules/istanbul/lib/cli.js cover node_modules/tape/bin/tape tests/test_*.js

lint: node_modules/
	$(NODE_CMD) node_modules/jslint/bin/jslint lib/*.js tests/*.js

clean:
	rm -r -- "node_modules/" || true
	rm -- $(OUT_FILES) || true

clean-unused:
	for f in $(filter-out \
	    $(foreach f,$(OUT_FILES),$(shell dirname $(f))/$(shell readlink $(f))), \
	    $(wildcard www/*/*.min.r*.*) \
	); do rm -- $$f; done

watch:
	while inotifywait -r lib; do make compile; done

node_modules/: package.json yarn.lock
	$(YARN)
	touch node_modules/

yarn.lock:
	touch $@

# Move minified output to a version with sha1 hash in it's name, symlink to proper output
sha1_symlink = \
    REV_FILE="www/$(1)/$$(basename $(3) .min.$(1)).min.r$$(sha1sum $(2) | head -c7).$(1)"; \
    mv $(2) $$REV_FILE; \
    ln -rsf $$REV_FILE $(3)

# Generate environment variables that point to the sha1 hash version
sha1_envvars = \
    for f in $(1); do \
        eval sha_$$(basename $$f | sed 's/\W/_/g')=$$(readlink $$f); \
    done;

www/js/libraries.min.js: package.json
	mkdir -p $(dir $@)
	(cd www/js && ln -sf ../../node_modules .)
	$(NODE_CMD) node_modules/.bin/browserify \
	        $(foreach l,$(LIBRARIES_JS),-r $(l)) \
	    | $(NODE_CMD) node_modules/.bin/uglifyjs \
	        --compress --mangle "reserved=['$$','require','exports']" \
	        --output $@.mktmp
	$(call sha1_symlink,js,$@.mktmp,$@)

www/css/libraries.min.css: package.json
	mkdir -p $(dir $@)
	(cd www/css && ln -sf ../../lib .)
	cat $(LIBRARIES_CSS) > $@.mktmp
	$(call sha1_symlink,css,$@.mktmp,$@)

www/js/%.min.js: lib/%.js lib/*.js package.json
	mkdir -p $(dir $@)
	(cd www/js && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/.bin/browserify --debug \
	        $(foreach l,$(LIBRARIES_JS),-x $(l)) \
	        $< \
	    | $(NODE_CMD) node_modules/.bin/uglifyjs \
	        --compress --mangle "reserved=['$$','require','exports']" \
	        --source-map "content='inline',url='$(notdir $@).map'" \
	        --output $@.mktmp
	mv $@.mktmp.map $@.map
	$(call sha1_symlink,js,$@.mktmp,$@)

www/css/%.min.css: lib/%.css lib/*.css package.json
	mkdir -p $(dir $@)
	(cd www/css && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/postcss-cli/bin/postcss \
	    --config postcss.config.js \
	    -o $@ \
	    $<
	$(call sha1_symlink,css,$@,$@)

www/%.html: lib/%.html lib/base.html $(filter-out %.html,$(OUT_FILES)) \
    ../.local-conf \
    build/html_compile.js \
    package.json
	set -a; \
	    [ -f ../.local-conf ] && . ../.local-conf; \
	    $(call sha1_envvars,$(OUT_FILES)) \
	    $(NODE_CMD) build/html_compile.js $< $@.mktmp $^
	mv $@.mktmp $@

www/tw.appcache: www/*.html www/tw.js www/polyfill.js www/mathjax-config.js www/*.css www/*.jpg
	@echo "CACHE MANIFEST\n" > $@
	@for f in $+; do basename $$f; done >> $@
	@echo "mathjax/MathJax.js" >> $@
	@echo "mathjax/MathJax.js?config=../../mathjax-config.js" >> $@
	@echo "mathjax/extensions/tex2jax.js" >> $@
	@echo "mathjax/extensions/MathMenu.js" >> $@
	@echo "mathjax/extensions/MathZoom.js" >> $@
	@echo "mathjax/extensions/MathEvents.js" >> $@
	@echo "mathjax/extensions/TeX/AMSmath.js" >> $@
	@echo "mathjax/extensions/TeX/AMSsymbols.js" >> $@
	@echo "mathjax/extensions/TeX/noErrors.js" >> $@
	@echo "mathjax/extensions/TeX/noUndefined.js" >> $@
	@echo "mathjax/extensions/TeX/cancel.js" >> $@
	@echo "mathjax/jax/input/TeX/config.js" >> $@
	@echo "mathjax/jax/input/TeX/jax.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/config.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/imageFonts.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/jax.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/annotation-xml.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/maction.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/menclose.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/mglyph.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/mmultiscripts.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/ms.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/mtable.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/autoload/multiline.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/fontdata.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/fontdata-extra.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/Arrows.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/BBBold.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/BoxDrawing.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/Dingbats.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/EnclosedAlphanum.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/GeneralPunctuation.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/GeometricShapes.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/GreekAndCoptic.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/Latin1Supplement.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/LatinExtendedA.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/LetterlikeSymbols.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/MathOperators.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/MiscMathSymbolsB.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/MiscSymbols.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/MiscTechnical.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/PUA.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/SpacingModLetters.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/AMS/Regular/SuppMathOperators.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Caligraphic/Bold/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Caligraphic/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Bold/BasicLatin.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Bold/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Bold/Other.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Bold/PUA.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Regular/BasicLatin.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Regular/Other.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Fraktur/Regular/PUA.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Greek/BoldItalic/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Greek/Bold/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Greek/Italic/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Greek/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/Arrows.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/CombDiactForSymbols.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/GeneralPunctuation.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/GeometricShapes.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/Latin1Supplement.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/LatinExtendedA.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/LatinExtendedB.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/LetterlikeSymbols.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/MathOperators.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/MiscMathSymbolsA.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/MiscSymbols.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/MiscTechnical.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/SpacingModLetters.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/SupplementalArrowsA.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Bold/SuppMathOperators.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Italic/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Italic/GeneralPunctuation.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Italic/Latin1Supplement.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Italic/LetterlikeSymbols.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Italic/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Regular/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Regular/GeometricShapes.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Regular/MiscSymbols.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Main/Regular/SpacingModLetters.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Math/BoldItalic/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Math/Italic/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Bold/BasicLatin.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Bold/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Bold/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Bold/Other.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Italic/BasicLatin.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Italic/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Italic/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Italic/Other.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Regular/BasicLatin.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Regular/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/SansSerif/Regular/Other.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Script/Regular/BasicLatin.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Script/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Script/Regular/Other.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Size1/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Size2/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Size3/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Size4/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Typewriter/Regular/BasicLatin.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Typewriter/Regular/CombDiacritMarks.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Typewriter/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/Typewriter/Regular/Other.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/WinChrome/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/WinIE6/Regular/AMS.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/WinIE6/Regular/Bold.js" >> $@
	@echo "mathjax/jax/output/HTML-CSS/fonts/TeX/WinIE6/Regular/Main.js" >> $@
	@echo "mathjax/jax/output/NativeMML/config.js" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_AMS-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Caligraphic-Bold.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Caligraphic-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Fraktur-Bold.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Fraktur-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Main-Bold.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Main-Italic.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Main-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Math-BoldItalic.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Math-Italic.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Math-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_SansSerif-Bold.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_SansSerif-Italic.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_SansSerif-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Script-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Size1-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Size2-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Size3-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Size4-Regular.woff" >> $@
	@echo "mathjax/fonts/HTML-CSS/TeX/woff/MathJax_Typewriter-Regular.woff" >> $@
	@echo "mathjax/jax/element/mml/jax.js" >> $@
	@echo "" >> $@
	@echo "NETWORK:\n" >> $@
	@echo "*" >> $@
	@echo "" >> $@
	@echo -n "# " >> $@
	@cat $+ | md5sum | cut -d' ' -f1 >> $@

.PHONY: compile test start lint clean clean-unused watch
