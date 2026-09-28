# locations.py
#
#   Maps the locations that are on the CSV and creates the distances that connects them
#


import csv
import re

HUB_INDEX = 0

def load(path):
    """Loads the address from the CSV file."""
    names = []
    addresses = []
    zips = []
    raw = []

    with open(path, newline="") as handle:
        for row in csv.reader(handle):
            if not row or not row[0].strip():
                continue

            names.append(row[0].strip())

            address_field = row[1].strip()
            if "(" in address_field:
                street, _, zip_part = address_field.partition("(")
                addresses.append(street.strip())
                zips.append(zip_part.strip(") "))
            else:
                addresses.append(address_field)
                zips.append("")

            raw.append(row[2:])

    size = len(names)
    assert size == 27, "expected 27 locations, read %d" % size


    matrix = [[0.0] * size for _ in range(size)]
    for i in range (size):
        for j in range (size):
            cell = raw[i][j].strip() if j < len(raw[i]) else ""
            if cell:
                matrix[i][j] = float(cell)

    for i in range (size):
        for j in range (size):
            if matrix[i][j] ==0.0 and i != j:
                matrix[i][j] = matrix[j][i]

    return names, addresses, zips, matrix

DIRECTIONS = {"north": "n", "south": "s", "east": "e", "west": "w"}

def normalize(address):
    """Changes the address to make it easier to read"""
    text = address.lower().strip()
    text = text.split("(")[0]
    text = re.sub(r"#\s*\d+", "", text)
    words = [DIRECTIONS.get(w,w) for w in text.split()]
    return " ".join(words)

def build_address_index(addresses):

    index = {}
    for position, address in enumerate(addresses):
        if address.upper() == "HUB":
            continue
        index[normalize(address)] = position
    return index


def resolve(address_index, address):

    key = normalize(address)
    if key not in address_index:
        raise KeyError("address not on the map: %r" % address)
    return address_index[key]


def distance(matrix, i, j):
    return matrix[i][j]
