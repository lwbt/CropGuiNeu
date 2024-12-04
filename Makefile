# cspell:ignore APPMETA metainfo pyproject aarch64 flathub APPNAME
FLATPAK_ID=io.github.lwbt.CropGuiNeu
MANIFEST=$(FLATPAK_ID).yml
APPMETA=$(FLATPAK_ID).metainfo.xml
APPNAME=CropGuiNeu
# TODO fetch from pyproject.toml
VERSION := 0.1
RUNTIME_VER=46
BUILD_DATE := $(shell date -I)
GH_ACCOUNT := $(shell gh auth status --active | grep "Logged in to github.com account" | cut -d " " -f 9)
ARCH ?= $(shell arch)

.PHONY: default
default: setup-sdk pkg bundle

.PHONY: all
all: setup-sdk-both pkg-both bundle-both

.PHONY: check
check: lint check-meta check-versions workflow-check

.PHONY: setup-sdk-builder
setup-sdk-builder:
	flatpak --user install -y flathub org.flatpak.Builder

.PHONY: setup-sdk-pip
setup-sdk-pip:
	git -c advice.detachedHead=false clone --depth 1 https://github.com/flatpak/flatpak-builder-tools.git
	python3 -m venv venv
	source venv/bin/activate
	pip3 install requirements-parser

# TODO: This is a mess, clean upm because this needs to be done regularly.
pypi-dependencies:
	source venv/bin/activate
	flatpak-builder-tools/pip/flatpak-pip-generator --runtime='org.freedesktop.Sdk//24.08' --requirements-file='requirements.txt' --output
	#flatpak-builder-tools/pip/flatpak-pip-generator --runtime='org.gnome.Platform//24.08' --requirements-file='requirements.txt' --output pypi-dependencies
	#flatpak-builder-tools/pip/flatpak-pip-generator --runtime='org.freedesktop.Sdk//24.08' --requirements-file='requirements.txt' --output pypi-dependencies
	#flatpak-builder-tools/poetry/flatpak-poetry-generator.py poetry.lock
	# npx prettier -w ...

.PHONY: setup-sdk-%
setup-sdk-%:
	flatpak --user install -y org.gnome.Platform/$*/$(RUNTIME_VER)
	flatpak --user install -y org.gnome.Sdk/$*/$(RUNTIME_VER)

.PHONY: setup-sdk
setup-sdk: setup-sdk-builder setup-sdk-$(ARCH)

.PHONY: setup-sdk-both
setup-sdk-both: setup-sdk-builder setup-sdk-x86_64 setup-sdk-aarch64

.PHONY: pkg-%
pkg-%: $(MANIFEST)
	flatpak --user run org.flatpak.Builder \
	  --user \
	  --arch $* \
	  --repo "repo" \
	  --force-clean \
	  "build-dir__$*" \
	  "$(MANIFEST)"

.PHONY: pkg
pkg: pkg-$(ARCH)

.PHONY: pkg-both
pkg-both: pkg-x86_64 pkg-aarch64

.PHONY: bundle-%
bundle-%:
	flatpak build-bundle \
	  "repo" \
	  --arch $* \
	  "$(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-$*.flatpak" \
	  "$(FLATPAK_ID)"

.PHONY: bundle
bundle: bundle-$(ARCH)
	sha512sum $(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-*.flatpak > checksums.txt

.PHONY: bundle-both
bundle-both: bundle-x86_64 bundle-aarch64
	sha512sum $(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-*.flatpak > checksums.txt

# Only use this when you have bundles built for both platforms.
.PHONY: releases
release:
	gh release create $(VERSION) \
	  --repo $(GH_ACCOUNT)/$(FLATPAK_ID) \
	  --title "$(VERSION) $(BUILD_DATE)" \
	  --notes "Update $(APPNAME) to $(VERSION). These are not CI/CD releases! The assets have been built on my workstation." \
	  --prerelease=false \
	  $(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-*.flatpak checksums.txt
#	  --draft \

.PHONY: lint
lint:
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest $(MANIFEST)
#	flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo

.PHONY: check-meta
check-meta:
	flatpak run --command=appstream-util org.flatpak.Builder validate $(APPMETA)

.PHONY: check-versions
check-versions:
	sed -i -e 's/#\(branch:\)/\1/g' "$(MANIFEST)"
	flatpak run org.flathub.flatpak-external-data-checker "$(MANIFEST)"

.PHONY: workflow-check
workflow-check:
	pre-commit autoupdate
