# BRANDSWOT Modular — build
#   make build   regenerate sources from the pixel file and compile all fonts
#   make test    run FontBakery (Google Fonts profile)
#   make web     refresh web/npm/specimen copies of the fonts
#   make zip     desktop download zip

VERSION := 2.100
SOURCES := sources/BRANDSWOTModular.pixels sources/build_ufos.py

.PHONY: build sources test web zip clean

build: sources
	gftools builder sources/config.yaml
	$(MAKE) web

sources: $(SOURCES)
	cd sources && python3 build_ufos.py

test:
	fontbakery check-googlefonts -l WARN --succinct \
	  --html fontbakery-report.html \
	  "fonts/variable/BRANDSWOTModular[wght].ttf" \
	  "fonts/variable/BRANDSWOTModular-Italic[wght].ttf"

web:
	python3 scripts/build_site.py
	mkdir -p docs/fonts
	cp "fonts/webfonts/BRANDSWOTModular[wght].woff2" docs/fonts/BRANDSWOTModular-VF.woff2
	cp "fonts/webfonts/BRANDSWOTModular-Italic[wght].woff2" docs/fonts/BRANDSWOTModular-Italic-VF.woff2

zip:
	python3 scripts/make_zip.py $(VERSION)

clean:
	rm -rf fonts sources/*.ufo sources/instances
