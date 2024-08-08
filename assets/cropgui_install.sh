#!/bin/bash

# ORIGINAL LICENSE -- https://github.com/jepler/cropgui
#
#    installation script for cropgui, a graphical front-end for lossless jpeg
#    cropping
#    Copyright (C) 2009 Jeff Epler <jepler@unpythonic.net>
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# LICENSE SUPPLEMENTAL
#
#    Copyright (C) 2024 Benjamin Tegge (GitHub.com/lwbt)
#    License itself remains unchanged.

# CHANGELOG
#
# 2024-08:
#
# * Added uninstall function
# * Reformatted with advice from shfmt and shellcheck
# * Documented installation and uninstallation
#
# INSTALLATION / UNINSTALLATION
#
# Dependencies on newer Ubuntu systems:
# python3-pil libjpeg-turbo-progs libimage-exiftool-perl
#
# Preferred installation:
# ./install.sh -f gtk
#
# After that you need to add something like the following to your environment
# to be able to run the program. I put it in `~/.bashrc`, but your setup may be
# different. On systems where I install modern tooling like pipx, this is
# handled for me and binaries are placed in `${HOME}/.local/bin` instead of
# `${HOME}/bin`.
#
# # --- Required by cropgui START
# export PATH="${PATH}:${HOME}/bin:${HOME}/lib"
# export PYTHONPATH="${HOME}/lib/python"
# # --- Required by cropgui END
#
# Uninstall:
# ./install.sh -r
#
# Uninstall
# sudo ./install.sh -r -p /usr -P /usr/bin/python

PYTHON="python3"
BINDIR="$HOME/bin"
LIBDIR="$HOME/lib/python"
SHAREDIR="$HOME/share"
UNINSTALL="no"

BGRED="\033[41m"
NC="\033[0m"

default_flavor() {
  if ! "$PYTHON" -c 'import gtk' > /dev/null 2>&1 \
    && "$PYTHON" -c 'import tkinter' > /dev/null 2>&1; then
    echo tk
  else
    echo gtk
  fi
}

site_packages() {
  $PYTHON -c 'import distutils.sysconfig; print(distutils.sysconfig.get_python_lib())'
}

err_fatal() {
  echo >&2 -e "${BGRED}ERR${NC} $(date --rfc-3339=sec):\n $*"
  echo >&2 "Aborting."
  exit 1
}

usage() {
  cat << EOF
Usage: ./install.sh [-f tk|gtk] [-u|-p PREFIX] [-P PYTHON] [-t TARGET]
    -f: choose the flavor to install
    -u: install to $HOME
    -p: install to $PREFIX
    -P: Python executable to use
    -t: install inside TARGET (for package building)
    -r: Remove/uninstall
EOF
  exit
}

install_desktop_assets() {
  install --mode=644 "cropgui.desktop" "$TARGET$SHAREDIR/applications"
  install --mode=644 "cropgui.png" "$TARGET$SHAREDIR/pixmaps"
}

install_gtk() {
  echo "Installing gtk version of cropgui"
  install --mode=755 \
    "cropgtk.py" \
    "$TARGET$BINDIR/cropgui" \
    || err_fatal "Installation of cropgtk (1/2) failed."
  install --mode=644 \
    "cropgui_common.py" \
    "filechooser.py" \
    "cropgui.glade" \
    "stock-rotate-90-16.png" \
    "stock-rotate-270-16.png" \
    "$TARGET$LIBDIR" \
    || err_fatal "Installation of cropgtk (2/2) failed."
}

install_tk() {
  echo "Installing tkinter version of cropgui"
  install --mode=755 \
    "cropgui.py" \
    "$TARGET$BINDIR/cropgui" \
    || err_fatal "Installation of croptk (1/2) failed."
  install --mode=644 \
    "log.py" \
    "cropgui_common.py" \
    "$TARGET$LIBDIR" \
    || err_fatal "Installation of croptk (2/2) failed."
}

uninstall_all() {
  echo "Uninstalling cropgui files."
  rm -v \
    "$TARGET$BINDIR/cropgui" \
    "$TARGET$LIBDIR/cropgui.glade" \
    "$TARGET$LIBDIR/cropgui_common.py" \
    "$TARGET$LIBDIR/filechooser.py" \
    "$TARGET$LIBDIR/log.py" \
    "$TARGET$LIBDIR/stock-rotate-270-16.png" \
    "$TARGET$LIBDIR/stock-rotate-90-16.png" \
    "$TARGET$SHAREDIR/applicationsi/cropgui.desktop" \
    "$TARGET$SHAREDIR/pixmaps/cropgui.png"

  exit
}

main() {
  while getopts "f:ut:p:P:r:" opt; do
    case "$opt" in
      f) FLAVOR="$OPTARG" ;;
      u)
        BINDIR="$HOME/bin"
        LIBDIR="$HOME/lib/python"
        SHAREDIR="$HOME/share"
        ;;
      t) TARGET=$OPTARG ;;
      P) PYTHON=$OPTARG ;;
      p)
        FPYTHON="$(which "$PYTHON")"
        BINDIR="$(dirname "$FPYTHON")"
        SHAREDIR="$(dirname "$BINDIR")/share"
        LIBDIR="$(site_packages "$PYTHON")"
        ;;
      r) UNINSTALL="yes" ;;
      *) usage ;;
    esac
  done

  [[ -z "$FLAVOR" ]] && FLAVOR="$(default_flavor)"

  [[ "$UNINSTALL" == "yes" ]] && uninstall_all

  mkdir -p \
    "$TARGET$BINDIR" \
    "$TARGET$LIBDIR" \
    "$TARGET$SHAREDIR/applications" \
    "$TARGET$SHAREDIR/pixmaps"

  install_desktop_assets

  case $FLAVOR in
    gtk) install_gtk ;;
    tk) install_tk ;;
    *) err_fatal "Unknown flavor $FLAVOR" ;;
  esac

  chmod +x "$TARGET$BINDIR/cropgui"

  # TODO: Explain what this does and why.
  if [[ -z "$TARGET" ]] && ! (
    cd "/tmp"
    $PYTHON -c 'import cropgui_common'
  ) > /dev/null 2>&1; then
    echo "*** Failed to import cropgui_common.py"
    echo "    You must add $LIBDIR to PYTHONPATH"
    exit 1
  fi

  echo "Installed cropgui $FLAVOR"
}

main "$@"
