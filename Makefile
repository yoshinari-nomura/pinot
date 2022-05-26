# Makefile for Pinot project
#
# Yoshinari Nomura
#

.PHONY: backup fonts

export AMPY_PORT  ?= /dev/ttyUSB0
export AMPY_BAUD  ?= 115200
export AMPY_DELAY ?= 0

################################################################
## ampy

usage:
	@echo "Usage: make {push|list|...}"
	@echo "  make push | sh -v"

backup:
	@PINOT_HOSTNAME=$$(scripts/pinot-hostname); \
	mkdir -p backup/$$PINOT_HOSTNAME; \
	scripts/pinot-mirror "ampy:" backup/$$PINOT_HOSTNAME

digest:
	@ampy run scripts/digest-files.py

diff:
	@scripts/pinot-mirror -d src ampy: | sed '/\/config\/.*\.json/d'

push:
	@scripts/pinot-mirror src ampy: | sed '/\/config\/.*\.json/d; /'"'"'\/main\.py/d'

push-config:
	@PINOT_HOSTNAME=$$(scripts/pinot-hostname); \
	echo "ampy put 'config/$$PINOT_HOSTNAME/settings.json' /config/settings.json"

info:
	@scripts/pinot-hostname -v

################################################################
## fonts

BDFDIR  = fonts/shinonome-0.9.11/bdf
PFNDIR  = src/fonts
MAKEPFN = ./scripts/makepfn
DUMPPFN = ./scripts/dumppfn

TARGET_FONTS = shnmk12u.pfn shnmk14u.pfn shnmk16u.pfn

# fonts-test: $(PFN12) $(PFN14) $(PFN16)
# JISX0201 ISO88591 JISX0208
shnmk12u.pfn : $(BDFDIR)/shnm6x12r.bdf $(BDFDIR)/shnm6x12a.bdf $(BDFDIR)/shnmk12.bdf
shnmk14u.pfn : $(BDFDIR)/shnm7x14r.bdf $(BDFDIR)/shnm7x14a.bdf $(BDFDIR)/shnmk14.bdf
shnmk16u.pfn : $(BDFDIR)/shnm8x16r.bdf $(BDFDIR)/shnm8x16a.bdf $(BDFDIR)/shnmk16.bdf

%.pfn:
	$(MAKEPFN) -n $(basename $(notdir $@)) $^ > $@

fonts: $(TARGET_FONTS)

fonts-clean:
	rm $(TARGET_FONTS)

fonts-test: $(TARGET_FONTS)
	$(DUMPPFN) $< " ABC}~漢字ｲﾛﾊﾎﾟ｡¢§÷Α♪｝￣￥"
