#!/bin/bash
set -e
echo "Updating version file..."

version_file="pyrandyos/_version.py"

# VENV=.hatchenv
# PIP=$VENV/bin/pip
# HATCH=$VENV/Scripts/hatch
PIP=pip
HATCH=hatchling

# Make sure hatch is available
# if [ ! -x $HATCH ]; then
if ! command -v $HATCH &> /dev/null; then
  # if [ ! -d $VENV ]; then
  #   python -m venv $VENV
  # fi
  $PIP install hatchling hatch-vcs
  # if [ ! -x $HATCH ]; then
  if ! command -v $HATCH &> /dev/null; then
    echo "Error: hatch not found. Please install hatch first."
    exit 1
  fi
fi

# VERSION=$($HATCH version)
# echo "Current version: $VERSION"
mkdir -p pyrandyos
$HATCH build --target wheel
# echo "Version file updated to $VERSION"

if git rev-parse --git-dir > /dev/null 2>&1; then
  if git diff --quiet "$version_file" 2>/dev/null; then
    echo "  (No changes to version file)"
  else
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" = "develop" ]; then
      git add "$version_file"
      echo "  Version file added to commit"
    else
      echo "  Version file updated but not on develop branch - not adding to commit"
    fi
  fi
else
  echo "  Not in a git repository - version file updated only"
fi

echo "$0 done"
