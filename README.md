Solar time vs standard time
===========================

This repository contains tools and data to draw an SVG map of the
difference between solar time and standard time.

See the discussion at <http://blog.poormansmath.net>.


Instructions
------------

1. Run `init_map.sh` to download the required data (this comes from
   Eric Muller and ESRI).

2. Run `draw.py` to create `base.svg`.

3. Use inkscape (at least 0.91) to convert the SVG intp a PNG 6000px
   wide, `base.png`.

4. A few corrections required because of the staleness of the
   shapefile data are included in the GIMP file `map.xcf`. Just add
   the PNG as the bottom layer of the XCF and export `map.png`.

5. Roll and crop the map running `finalize_map.sh`.


Other tools
-----------

`map_helper.html` is a static tool that uses Google Maps API to easily
get coordinates for one or more polylines, drawn directly on the map.
