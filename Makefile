# Makefile

AMPY_PORT  = /dev/ttyUSB0
AMPY_BAUD  = 115200
AMPY_DELAY = 0

.PHONY: all backup list push

all:
	@echo "Usage: make {push|list}"

backup:
	@PINOT_HOSTNAME=$$(scripts/pinot-hostname); \
	mkdir -p backup/$$PINOT_HOSTNAME; \
	scripts/pinot-mirror "ampy:" backup/$$PINOT_HOSTNAME

digest:
	@ampy run scripts/digest-files.py

diff:
	@scripts/pinot-mirror -d src ampy: | sed '/\/config\/.*\.json/d'

push:
	@scripts/pinot-mirror src ampy: | sed '/\/config\/.*\.json/d'
