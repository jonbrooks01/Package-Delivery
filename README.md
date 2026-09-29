# WGUPS Package Delivery Routing Program

A delivery routing program for the Western Governors University Parcel Service.
The program reads a package manifest and a distance table. It assigns forty
packages across three trucks under a set of delivery constraints, routes each
truck, and simulates one delivery day. A supervisor can then look up the status
of any package at any time and the mileage traveled by each truck.

The completed simulation delivers all forty packages with no missed deadline in
**123.3 miles**, against a limit of 140.

---

## The problem

The scenario supplies forty packages, twenty-seven delivery locations, three
trucks, and two drivers. A driver stays with one truck. This means at most two
trucks are on the road at once, and the third truck cannot leave until a driver
returns. Each truck holds sixteen packages and averages 18 miles per hour.

Seven constraints shape the solution:

- Fourteen packages carry a delivery deadline. One is due at 9:00 a.m. and
  thirteen are due at 10:30 a.m.
- Four packages may travel only on truck 2.
- Four packages are delayed on a flight and cannot be loaded before 9:05 a.m.
- One package has a wrong address on the manifest. It is not corrected until
  10:20 a.m.
- Three co-delivery notes overlap. This makes six packages one indivisible
  group rather than three pairs.
- No truck may carry more than sixteen packages.
- Combined mileage must stay below 140.

The constraints interact. This is what makes the problem more than a routing
exercise. Two of the delayed packages also carry 10:30 deadlines, so they must
ride the truck that waits for the flight rather than the truck that leaves
first. One member of the co-delivery group is due at 9:00, which pulls all six
onto the first truck out. The address correction arrives at 10:20. That is
later than the first driver's return, so the third truck waits on the data
rather than on the driver.

---

## Approach

The solution separates the two decisions. Which truck carries each package is a
rule problem, and it is solved once before any truck moves. What order each
truck drives is a distance problem, and it is solved continuously as the truck
moves.

**Loading** uses a constraint-driven greedy assignment that places the most
constrained packages first. A package locked to one truck has few legal
placements, so it claims its slot before a package that could ride anywhere.
This ensures that no assignment has to be undone. The overlapping co-delivery
notes are collapsed into indivisible groups by a union-find structure with path
compression. This reaches the correct group of six no matter what order the
notes are read in.

**Routing** uses a nearest neighbor search extended with a deadline feasibility
test. At each stop the nearest remaining destination is selected and then
tested. The test asks whether the truck could still reach every remaining
deadline by driving straight there afterward. A direct drive is the fastest
possible approach to any location, so a deadline that fails the test cannot be
met along that path under any ordering. When one fails, the most urgent at-risk
stop is served instead.

This is the self-adjusting part of the program. The decision is recomputed from
the truck's actual clock and its actual remaining load at every stop. A truck
running behind becomes deadline-driven, while the same truck running ahead
stays distance-driven and saves miles. Nothing about the route is precomputed.

**Storage** uses a hash table with separate chaining, written without any
libraries or imported classes. The table reads its own load factor on each
insertion and rebuilds with a larger bucket array when the load factor passes
0.75. With the supplied manifest it settles at 71 buckets, zero collisions, and
a longest chain of one. This ensures that every look-up resolves in a single
comparison.

Package status is derived rather than logged. Each package keeps three
timestamps, and the status at a given moment is worked out from them. This
helps in two ways. It holds the memory per package constant, and it allows a
query about any moment, including one already past. That is how the program
correctly reports the wrong address for a 9:00 a.m. query about the package
corrected at 10:20.

---

## Results

| Truck | Packages | Miles | Departed | Returned |
| --- | --- | --- | --- | --- |
| 1 | 16 | 34.6 | 8:00 a.m. | 9:55 a.m. |
| 2 | 8 | 36.8 | 9:05 a.m. | 11:07 a.m. |
| 3 | 16 | 51.9 | 10:20 a.m. | 1:13 p.m. |
| **Combined** | **40** | **123.3** | | |

Truck 1 returns before truck 3 departs. This frees the second driver and
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
routing.py       loading rules and the nearest neighbor search
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

The menu offers a single package at a chosen time, all packages at a chosen
time, one truck's packages at a chosen time, and the mileage for all trucks.

To run the test suite:

```
python3 -m unittest discover -s tests -v
```

The suite verifies both data files. It also exercises the hash table through
five hundred insertions and every resize, and it asserts each scenario
requirement against the completed simulation.

---

## Design notes

Every rule comes from data rather than from code. No package number, address,
or deadline appears in the program logic. The special notes are parsed into
explicit constraint fields at load time, and the address correction is a
declared constant rather than a branch on a package ID. Running the program for
another city means supplying different CSV files.

Three scenario-shaped facts do remain in code. These are the 9:05 a.m.
departure for the truck that waits, and the rules that route delayed freight
and corrected addresses to particular trucks. Deriving those from the parsed
availability times instead would make the schedule a consequence of the data as
well. This is the first change the program should receive.

The whole program is polynomial. It runs in O(n log n + n*v + v^2) time and
O(n + v^2) space, for n packages and v locations. An exact solution to the
underlying traveling salesman problem grows factorially and is not practical at
this size.

---

## Academic context

This project was written for WGU course C950, Data Structures and Algorithms II.
It is published as a record of the work. It is not offered as a solution for
anyone else to submit.
