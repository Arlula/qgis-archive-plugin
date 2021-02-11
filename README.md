# Arlula QGIS plugin
**An _experimental_ interface between QGIS and the Arlula Satellite Imagery API**

## About
The Arlula API allows users to query databases of satellite imagery from vendors around the world. This powerful tool allows users to search and compare the quality of global image datasets and order them at scale. The Arlula API is a new way in which people from around the world can access timely satellite imagery and create their own data streams from space!  
The Arlula QGIS plugin makes it easy to access all of the API functionality without having to do any of the hard work.

This plugin requires an active Arlula account and access to the API credentials. If you don't have an account, you can create one at [api.arlula.com/signup](https://api.arlula.com/signup).

## Features
This plugin currently supports:
- Searching the Arlula satellite imagery archives for imagery
- Viewing details of all search results
- Adding thumbnails of search results to the QGIS window
- List orders
- Download and view high-quality satellite imagery from orders
- Ordering of imagery

It is **Windows only** for the time being, with support for Mac and Linux to come shortly.

In the future it will support:
- Signing up to the Arlula API

## For developers
- Use `paver` to manage dependencies into `extlibs` before uploading plugin versions
- plugin format for QGIS release should be:
```
arlula.zip
+-- arlula/
|   +-- extlibs/
|   +-- __init__.py
|   +-- ...
|   +-- resources.qrc
```

Stay tuned for our official release!