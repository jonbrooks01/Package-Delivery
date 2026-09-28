# WGUPS Package Delivery Routing Program

A delivery routing program for the Western Governors University Parcel Service.
The program reads a package manifest and a distance table, assigns forty
packages across three trucks under a set of delivery constraints, routes each
truck, and simulates one delivery day. A supervisor can then query the status of
any package at any moment and the mileage travelled by each truck.

The completed simulation delivers all forty packages with no missed deadline in
**123.3 miles**, against a limit of 140.

---

## The problem

The scenario supplies forty packages, twenty-seven delivery locations, three
trucks, and two drivers. A driver stays with one truck, so at most two trucks
are on the road at once and the third cannot leave until a driver returns. Each
truck holds sixteen packages and averages 18 miles per hour.

Seven constraints shape the solution:

- Fourteen packages carry a delivery deadline; one is due at 9:00 a.m. and
  thirteen at 10:30 a.m.
- Four packages may travel only on truck 2.
- Four packages are delayed on a flight and cannot be loaded before 9:05 a.m.
- One package has a wrong address on the manifest that is not corrected until
  10:20 a.m.
- Three co-delivery notes overlap, which makes six packages one indivisible
  group rather than three pairs.
- No truck may exceed sixteen packages.
- Combined mileage must stay below 140.

The constraints interact, which is what makes the problem more than a routing
exercise. Two of the delayed packages also carry 10:30 deadlines, so they must
ride the truck that waits for the flight rather than the truck that leaves
first. One member of the co-delivery group is due at 9:00, which pulls all six
onto the first truck out. The address correction arrives at 10:20, which is
later than the first driver's return, so the third truck waits on the data
rather than on the driver.

---

## Approach

The solution separates the two decisions. Which truck carries each package is a
rule problem, solved once before any truck moves. What order each truck drives
is a distance problem, solved continuously as the truck moves.

**Loading** uses a constraint-driven greedy assignment that places the most
constrained packages first. A package locked to one truck has few legal
placements and claims its slot before a package that could ride anywhere, which
ensures that no assignment has to be undone. The overlapping co-delivery notes
are collapsed into indivisible groups by a union-find structure with path
compression, which reaches the correct group of six regardless of the order the
notes are read in.

**Routing** uses a nearest-neighbour search extended with a deadline
feasibility test. At each stop the nearest remaining destination is selected,
then tested: if the truck went there first, could it still reach every remaining
deadline by driving straight there afterwards? A direct drive is the fastest
possible approach to any location, so a deadline that fails that test cannot be
met along that path under any ordering. When one fails, the most urgent at-risk
stop is served instead.

This is the self-adjusting part of the program. The decision is recomputed from
the truck's actual clock and actual remaining load at every stop, so a truck
running behind becomes deadline-driven while the same truck running ahead stays
distance-driven and saves miles. Nothing about the route is precomputed.

**Storage** uses a hash table with separate chaining, written without any
libraries or imported classes. The table measures its own load factor on each
insertion and rebuilds with a larger bucket array when the average chain passes
0.75. With the supplied manifest it settles at 71 buckets, zero collisions, and
a longest chain of one, so every look-up resolves in a single comparison.

Package status is derived rather than logged. Each package keeps three
timestamps, and the status at a given moment is worked out from them. This holds
the memory per package constant and allows a query about any instant, including
one already past — which is how the program correctly reports the *wrong*
address for a 9:00 a.m. query about the package corrected at 10:20.

---

## Results

| Truck | Packages | Miles | Departed | Returned |
| --- | --- | --- | --- | --- |
| 1 | 16 | 34.6 | 8:00 a.m. | 9:55 a.m. |
| 2 | 8 | 36.8 | 9:05 a.m. | 11:07 a.m. |
| 3 | 16 | 51.9 | 10:20 a.m. | 1:13 p.m. |
| **Combined** | **40** | **123.3** | | |

Truck 1 returns before truck 3 departs, which frees the second driver and
satisfies the two-driver constraint without an explicit scheduling rule.

---

## Layout

```
main.py          entry point and the query interface
hash_table.py    the package store: chaining, self-resizing, no imports
package.py       one package, plus parsing of the free-text special notes
locations.py     the 27x27 distance matrix and address resolution
time_utils.py    one time representation, and miles to minutes at 18 mph
truck.py         the vehicle model and its trip log
routing.py       loading rules and the nearest-neighbour search
data/            the cleaned package manifest and distance table
tests/           27 tests covering the data, the hash table, and every
                 scenario requirement
```

---

## Running it

Python 3.9 or later. There are no third-party dependencies.

```
python3 main.py
```

The menu offers a single package at a nominated time, all packages at a
nominated time, one truck's packages at a nominated time, and the mileage for
all trucks.

To run the test suite:

```
python3 -m unittest discover -s tests -v
```

The suite verifies both data files, exercises the hash table through five
hundred insertions and every resize, and asserts each scenario requirement
against the completed simulation.

---

## Design notes

Every rule comes from data rather than from code. No package number, address,
or deadline appears in the program logic: the special notes are parsed into
explicit constraint fields at load time, and the address correction is a
declared constant rather than a branch on a package ID. Running the program for
another city means supplying different CSV files.

Three scenario-shaped facts do remain in code — the 9:05 a.m. departure for the
truck that waits, and the rules routing delayed freight and corrected addresses
to particular trucks. Deriving those from the parsed `available_at` values
instead would make the schedule a consequence of the data as well, and is the
first change this program should receive.

The whole program is polynomial: O(n log n + n·v + v²) in time and O(n + v²) in
space, for *n* packages and *v* locations. An exact solution to the underlying
travelling salesman problem grows factorially and is not practical at this size.

---

## Academic context

This project was written for WGU course C950, Data Structures and Algorithms II.
It is published as a record of the work. It is not offered as a solution for
anyone else to submit.