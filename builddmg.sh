#!/bin/sh
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -r dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/Tyler.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/Tyler.dmg" && rm "dist/Tyler.dmg"
create-dmg \
  --volname "Tyler" \
  --volicon "statics/tile-icon.ico" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Tyler.app" 175 120 \
  --hide-extension "Tyler.app" \
  --app-drop-link 425 120 \
  "dist/Tyler.dmg" \
  "dist/dmg/"