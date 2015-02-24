#!/usr/bin/env python

import jinja2
import pycountry
import shapefile
import sys

from datetime import datetime
from math import acos, asin, cos, log, pi, sin, tan
from pytz import timezone

from override import TZ_OVERRIDE, INVALID, \
    NAME_OVERRIDE, CITIES_OVERRIDE, TZ_LABELS, \
    TZ_LINES, DAY_LINES


MAX_FONT_SIZE = 48
MIN_FONT_SIZE = 8
MIN_PTS_DIST = 0.01
MIN_SHAPE_NORMAL = 0.3
MIN_SHAPE_CIRCLE = 0.2
WIDTH = 6000
HEIGHT = 4400
HEIGHT_RATIO = 2 * 180 * 1.25 * log(tan(0.25 * pi + 0.4 * pi * 90 / 180.0))
COLORS = [
    '#bf201f',
    '#ef302f',
    '#ff2a29',
    '#f7f7f7',
    '#2962ff',
    '#2f6aef',
    '#1f4abf',
    ]


def readFipsCodes():
    c = open("fips_codes.txt").readlines()
    ret = {}
    for d in c:
        d = d.split(' ', 1)
        ret[d[0]] = d[1].strip().decode('utf-8')
    return ret


def std_tx(x):
    return (WIDTH / 360.0) * (x + 180)


def std_ty(y):
    return (HEIGHT / HEIGHT_RATIO) * (-y + HEIGHT_RATIO / 2.0)


def tx(xy):
    return std_tx(xy[0])


def ty(xy):
    return std_ty(180 * 1.25 * log(tan(0.25 * pi + 0.4 * pi * xy[1] / 180.0)))


def drawPoint(p):
    return "%g,%g" % (tx(p), ty(p))


def drawLine(line):
    return " ".join(drawPoint(p) for p in line)


def largestBb(bbox):
    return max(bbox[2] - bbox[0], bbox[3] - bbox[1])


def computeSizePositionAndSpacing(name, b):
    override = NAME_OVERRIDE.get(name, {})
    if override is None:
        return None, None, None, None
    name = override.get('name', name)
    name = name.replace('-', ' ')
    name = name.split(',')[0]
    name = name.upper()
    name = name.replace("REPUBLIC", "REP.")
    nameLen = len(name)
    if name.find(" ") != -1:
        bestIdx = name.find(" ")
        idx = bestIdx
        while idx != -1:
            if abs(len(name) / 2.0 - idx) < abs(len(name) / 2.0 - bestIdx):
                bestIdx = idx
            idx = name.find(" ", idx + 1)
        name = name[:bestIdx] + '\n' + name[bestIdx + 1:]
        nameLen = max(bestIdx, nameLen - bestIdx + 1)

    left = 100000
    right = -100000
    top = -100000
    bottom = 100000
    for p in b:
        x = tx(p)
        y = ty(p)
        right = max(right, x)
        left = min(left, x)
        top = max(top, y)
        bottom = min(bottom, y)

    avgX = (right + left) / 2.0
    avgY = (top + bottom) / 2.0
    w = right - left
    h = top - bottom
    if w + h < 20.0:
        return name, 0, (0, 0), 0
    spacing = 0
    size = (w + h / 8.0)**1.25 / (10 * len(name)**0.8)
    size *= override.get('size', 1)
    size = max(size, MIN_FONT_SIZE)
    if size > MAX_FONT_SIZE:
        spacing = size - MAX_FONT_SIZE
        spacing *= override.get('size', 1)
        spacing = min(MAX_FONT_SIZE * 2, spacing)
        size = MAX_FONT_SIZE

    avgX += override.get('x', 0)
    avgY += override.get('y', 0)
    lines = len(name.split('\n'))
    return name, size, (avgX, avgY - (size * (lines - 1)) / 2), spacing


def tzOffset(tz_name):
    if tz_name in TZ_OVERRIDE:
        return TZ_OVERRIDE[tz_name][0]
    tz = timezone(tz_name)
    dec = datetime(2014, 12, 30)
    jun = datetime(2015, 6, 30)
    if not tz.dst(dec, is_dst=False):
        td = tz.utcoffset(dec, is_dst=False)
    elif not tz.dst(jun, is_dst=False):
        td = tz.utcoffset(jun, is_dst=False)
    else:
        print tz_name
        raise Exception()
    return int(td.days * 24 * 60 + td.seconds  / 60.0)


def findTimezones():
    print "Reading timezones..."
    r = shapefile.Reader("./tz_world/tz_world.shp")

    timezones = dict()
    for s in r.shapeRecords():
        for tz in s.record:
            if tz not in timezones:
                timezones[tz] = list()
            timezones[tz].append(s)

    offsets = dict()
    for tz in timezones:
        offset = tzOffset(tz)
        if offset not in offsets:
            offsets[offset] = list()
        offsets[offset] += timezones[tz]
    return offsets


def getShapeParts(shape):
    starts = []
    for start in shape.parts:
        starts.append(start)
    starts.append(len(shape.points))

    parts = []
    for start, end in zip(starts, starts[1:]):
        part = []
        pts = shape.points[start:end]
        prev = (999, 999)
        for i, p in enumerate(pts):
            if -MIN_PTS_DIST < prev[0] - p[0] < MIN_PTS_DIST and \
               -MIN_PTS_DIST < prev[1] - p[1] < MIN_PTS_DIST:
                continue
            part.append(p)
            prev = p
        parts.append(part)
    return parts


def splitParts(parts):
    newparts = []
    for part in parts:
        split = []
        prev = 999
        currentparts = []
        currentpart = []
        for i in range(len(part)):
            x = part[i][0] % 360
            while x > 180:
                x = x - 360
            if ((x > 180 - 20 and prev < -180 + 20)
                or (prev > 180 - 20 and x < -180 + 20)):
                if len(currentpart) > 0:
                    currentparts.append(currentpart)
                currentpart = [(x, part[i][1])]
            else:
                currentpart.append((x, part[i][1]))
            prev = x
        currentparts.append(currentpart)
        evens = [x for x in range(len(currentparts)) if x % 2 == 0]
        odds = [x for x in range(len(currentparts)) if x % 2 == 1]
        if evens != []:
            newparts.append(sum([currentparts[x] for x in evens], []))
        if odds != []:
            newparts.append(sum([currentparts[x] for x in odds], []))
    return newparts


def getTimezones():
    offsets = findTimezones()
    timezones = []
    filtered = 0
    for offset in offsets:
        timezone = {}
        if offset == INVALID:
            timezone["offset"] = "uninhabited"
            timezone["offsetPx"] = "uninhabited"
        else:
            timezone["offset"] = offset
            timezone["offsetPx"] = tx((offset * 360.0 / 24 / 60 - 52.5, 0))
        timezone["circles"] = []
        timezone["parts"] = []
        for s in offsets[offset]:
            bb = largestBb(s.shape.bbox)
            if bb >= MIN_SHAPE_NORMAL:
                timezone["parts"] += splitParts(getShapeParts(s.shape))
            elif bb >= MIN_SHAPE_CIRCLE:
                cx = (s.shape.bbox[0] + s.shape.bbox[2]) / 2.0
                cy = (s.shape.bbox[1] + s.shape.bbox[3]) / 2.0
                timezone["circles"] += [(tx((cx, cy)), ty((cx, cy)))]
            else:
                filtered += 1
        timezones.append(timezone)
    print "Shapes filtered out:", filtered
    return timezones


def getHours():
    hours = []
    for x in xrange(-180, 181, 15):
        line = []
        for y in range(-90, 91, 30):
            line.append((x + 7.5, y + 0.01))
        hours.append({
            "line": line,
            "hour": "%+d" % (x / 15),
            "center": tx((x, 0)),
        })
    return hours


def getCountries():
    print "Reading countries..."
    r = shapefile.Reader("./fips10c/fips10c.shp")
    fips = readFipsCodes()
    boundaries = []
    names = []
    namesDone = {}
    namesDone[''] = []
    for s in r.shapeRecords():
        boundary = splitParts(getShapeParts(s.shape))
        boundaries += boundary
        biggest = []
        for b in boundary:
            if len(b) > len(biggest):
                biggest = b
        name = fips.get(s.record[0], '')
        if name not in namesDone or len(biggest) > len(namesDone[name]):
            namesDone[name] = biggest
    for name, b in namesDone.iteritems():
        if name == '':
            continue
        name, size, pos, spacing = computeSizePositionAndSpacing(name, b)
        if name is not None and size > 0:
            names.append({
                'name': name.split('\n'),
                'spacing': spacing,
                'size': size,
                'x': pos[0],
                'y': pos[1]
            })
    return {"names": names,
            "boundaries": boundaries}


def getCities():
    print "Reading cities..."
    r = shapefile.Reader("./cities/cities.shp")
    cities = []
    for s in r.shapeRecords():
        inhabitants = s.record[2]
        capital = s.record[3]
        importance = 0
        override = CITIES_OVERRIDE.get(s.record[0], {})
        cities.append({
            "x": tx(s.shape.points[0]),
            "y": ty(s.shape.points[0]),
            "inhabitants": inhabitants,
            "capital": capital == "Y",
            "name": s.record[0],
            "anchor": override.get('x_anchor', 'start'),
            "dy": 0
        })
        dy = override.get('y_anchor', 'top')
        if dy == 'middle':
            cities[-1]['dy'] += capital == "Y" and 6 or 4
        elif dy == 'bottom':
            cities[-1]['dy'] += capital == "Y" and 12 or 8
    return cities


def getTzLabels():
    labels = TZ_LABELS
    for label in labels:
        for i, pos in enumerate(labels[label]):
            labels[label][i] = (tx(pos), ty(pos))
    return labels


def getData():
    return {
        "WIDTH": WIDTH,
        "HEIGHT": HEIGHT,
        "COLORS": COLORS,
        "drawLine": drawLine,
        "hours": getHours(),
        "timezones": getTimezones(),
        "countries": getCountries(),
        "cities": getCities(),
        "tzLabels": getTzLabels(),
        "tzLines": TZ_LINES,
        "dayLines": DAY_LINES,
    }


if __name__ == "__main__":
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("./"),
                             trim_blocks=True,
                             lstrip_blocks=True)
    template = env.get_template("template.svg")
    with open("./output/base.svg", "w") as f:
        f.write(template.render(getData()).encode("UTF-8"))
