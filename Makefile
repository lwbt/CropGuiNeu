FLATPAK_ID=io.github.lwbt.CropGuiNeu
MANIFEST=$(FLATPAK_ID).yml
APPMETA=$(FLATPAK_ID).metainfo.xml
APPNAME=CropGuiNeu
# TODO fetch from pyproject.toml
VERSION := 0.1
#RUNTIME_VER=24.08
RUNTIME_VER=46
BUILD_DATE := $(shell date -I)
GH_ACCOUNT := $(shell gh auth status --active | grep "Logged in to github.com account" | cut -d " " -f 9)

.PHONY: all setup-sdk pkg-% pkg pkg-x64 pkg-arm64 pkg-x86_64 pkg-aarch64 bundle-% bundle bundle-x64 bundle-arm64 bundle-x86_64 bundle-aarch64 lint check-meta check-versions

# TODO: Does not work, why?
#pkg-%:
#	flatpak --user run org.flatpak.Builder \
#	  --user \
#	  --arch $* \
#	  --repo "repo" \
#	  --force-clean \
#	  "build-dir_$*" \
#	  "$(MANIFEST)"
#bundle-%:
#	flatpak build-bundle \
#	  "repo" \
#	  --arch $* \
#	  "$(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-$*.flatpak" \
#	  "$(FLATPAK_ID)"

# TODO: Replace and document the shorthands
all: setup-sdk pkg-x64 bundle-x64

# TODO: Split into different arches
setup-sdk:
	flatpak --user install -y flathub org.flatpak.Builder
	flatpak --user install -y org.gnome.Platform/x86_64/$(RUNTIME_VER)
	flatpak --user install -y org.gnome.Sdk/x86_64/$(RUNTIME_VER)
#	flatpak --user install -y org.gnome.Platform/aarch64/$(RUNTIME_VER)
#	flatpak --user install -y org.gnome.Sdk/aarch64/$(RUNTIME_VER)

pkg: pkg-x64 pkg-arm64
#pkg: pkg-x86_64 pkg-aarch64

#pkg-x64: pkg-x86_64
#pkg-x64: pkg-x86_64 $(MANIFEST)
#pkg-x86_64: pkg-x86_64 $(MANIFEST)
pkg-x64: $(MANIFEST)
	flatpak --user run org.flatpak.Builder \
	  --user \
	  --arch x86_64 \
	  --repo "repo" \
	  --force-clean \
	  "build-dir_x86_64" \
	  "$(MANIFEST)"

#pkg-arm64: pkg-aarch64
#pkg-arm64: pkg-aarch64 $(MANIFEST)
#pkg-aarch64: pkg-aarch64 $(MANIFEST)
pkg-arm64: $(MANIFEST)
	flatpak --user run org.flatpak.Builder \
	  --user \
	  --arch aarch64 \
	  --repo "repo" \
	  --force-clean \
	  "build-dir_aarch64" \
	  "$(MANIFEST)"

#bundle: bundle-x86_64 bundle-aarch64
bundle: bundle-x64 bundle-arm64
	sha512sum $(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-*.flatpak > checksums.txt

#bundle-x64: bundle-x86_64
#bundle-x86_64: bundle-x86_64
bundle-x64:
	flatpak build-bundle \
	  "repo" \
	  --arch x86_64 \
	  "$(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-amd64.flatpak" \
	  "$(FLATPAK_ID)"

#bundle-arm64: bundle-aarch64
#bundle-aarch64: bundle-aarch64
bundle-arm64:
	flatpak build-bundle \
	  "repo" \
	  --arch aarch64 \
	  "$(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-arm64.flatpak" \
	  "$(FLATPAK_ID)"

# Only use this when you have bundles built for both platforms.
release:
	gh release create $(VERSION) \
	  --repo $(GH_ACCOUNT)/$(FLATPAK_ID) \
	  --title "$(VERSION) $(BUILD_DATE)" \
	  --notes "Update $(APPNAME) to $(VERSION). These are not CI/CD releases! The assets have been built on my workstation." \
	  --prerelease=false \
	  $(APPNAME)-$(VERSION)-TESTING-$(BUILD_DATE)-*.flatpak checksums.txt
#	  --draft \

lint:
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest $(MANIFEST)
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo

check-meta:
	flatpak run --command=appstream-util org.flatpak.Builder validate $(APPMETA)

check-versions:
	sed -i -e 's/#\(branch:\)/\1/g' "$(MANIFEST)"
	flatpak run org.flathub.flatpak-external-data-checker "$(MANIFEST)"

workflow-check:
	pre-commit autoupdate
