"""
package.py
==========
Retrieves the CSV data and parses it into a Package object.

"""

import re
import csv
from dataclasses import dataclass, field
from time_utils import format_clock, parse_clock
from typing import List, Optional
from datetime import timedelta

@dataclass
class Package:

    # -- manifest data -------------------------------------------------
    package_id: int
    address: str
    city: str
    state: str
    zip_code: str
    deadline: Optional[timedelta]       # None means end of day
    weight: float
    special_note: str = ""

    # -- parsed constraints -------------------------------------------

    required_truck: Optional[int] = None

    available_at: timedelta = field(default_factory=lambda: timedelta(hours=8))

    co_delivery_ids: List[int] = field(default_factory=list)

    address_is_wrong: bool = False

    correction_time: Optional[timedelta] = None
    original_address: Optional[str] = None
    original_zip_code: Optional[str] = None

    # -- simulation state ---------------------------------------------
    truck_id: Optional[int] = None
    departure_time: Optional[timedelta] = None
    delivery_time: Optional[timedelta] = None

    # ------------------------------------------------------------------
    # Derived values
    # ------------------------------------------------------------------

    @property
    def has_deadline(self) -> bool:
        return self.deadline is not None

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def apply_correction(self, address, city, state, zip_code, effective_time):
        """Replaces the address with the correct one."""
        if self.correction_time is None:
            self.original_address = self.address
            self.original_zip_code = self.zip_code
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.correction_time = effective_time
        self.address_is_wrong = False

    def status_at(self, moment):
        """Status of the package at the moment."""
        if self.delivery_time is not None and moment >= self.delivery_time:
            return "Delivered at " + format_clock(self.delivery_time)

        if self.departure_time is not None and moment >= self.departure_time:
            return "En route"

        if moment < self.available_at:
            return "Delayed"

        return "At the hub"

    def address_at(self, moment):
        if self.correction_time is not None and moment < self.correction_time:
            return self.original_address
        return self.address

    def zip_at(self, moment):
        if self.correction_time is not None and moment < self.correction_time:
            return self.original_zip_code
        return self.zip_code

    def components(self):
        return (self.package_id, self.address, self.deadline,
                self.city, self.zip_code, self.weight, "At the hub")


# ----------------------------------------------------------------------
# Special-note parsing
# ----------------------------------------------------------------------

TRUCK_PATTERN         = re.compile(r"only be on truck (\d+)",        re.I)
DELAY_PATTERN         = re.compile(r"until (\d{1,2}:\d{2}\s*[ap]m)", re.I)
GROUP_PATTERN         = re.compile(r"must be delivered with ([\d,\s]+)", re.I)
WRONG_ADDRESS_PATTERN = re.compile(r"wrong address",                 re.I)

def parse_note(package):
    note = package.special_note or ""
    if not note.strip():
        return package                     # nothing to do, and no crash

    match = TRUCK_PATTERN.search(note)
    if match:
        package.required_truck = int(match.group(1))

    match = DELAY_PATTERN.search(note)
    if match:
        package.available_at = parse_clock(match.group(1))

    match = GROUP_PATTERN.search(note)
    if match:
        ids = [int(n) for n in re.findall(r"\d+", match.group(1))]
        package.co_delivery_ids = [i for i in ids if i != package.package_id]

    if WRONG_ADDRESS_PATTERN.search(note):
        package.address_is_wrong = True

    return package

def load_packages(path, table):
    """Read the CSV, build a Package per row, insert into the hash table."""
    packages = {}  # package_id -> Package object

    with open(path, newline="") as handle:
        reader = csv.reader(handle)
        next(reader)  # throw away the header row

        for row in reader:
            if not row or not row[0].strip():
                continue  # skip a trailing blank line

            deadline = None if row[5].strip().upper() == "EOD" else parse_clock(row[5])

            package = Package(
                package_id=int(row[0]),
                address=row[1].strip(),
                city=row[2].strip(),
                state=row[3].strip(),
                zip_code=row[4].strip(),
                deadline=deadline,
                weight=float(row[6]),
                special_note=row[7].strip(),
            )

            parse_note(package)  # fills the four constraint fields

            packages[package.package_id] = package
            table.insert(*package.components())

    if len(packages) != 40:
        raise ValueError("expected 40 packages, read %d" % len(packages))

    return packages