"""Tests for the data files and your loaders. Complete -- run, don't edit."""

import csv
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestPackageFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "packages.csv"), newline="") as f:
            cls.rows = list(csv.reader(f))

    def test_shape(self):
        self.assertEqual(len(self.rows), 41, "expected a header plus 40 packages")
        self.assertTrue(all(len(r) == 8 for r in self.rows),
                        "every row should have exactly 8 columns")

    def test_ids_are_1_to_40_in_order(self):
        self.assertEqual([r[0] for r in self.rows[1:]],
                         [str(i) for i in range(1, 41)])

    def test_the_scenario_facts_are_present(self):
        notes = {int(r[0]): r[7] for r in self.rows[1:]}
        self.assertEqual(sorted(k for k, v in notes.items() if "truck 2" in v),
                         [3, 18, 36, 38])
        self.assertEqual(sorted(k for k, v in notes.items() if "9:05" in v),
                         [6, 25, 28, 32])
        self.assertEqual(sorted(k for k, v in notes.items() if "Wrong address" in v),
                         [9])
        self.assertEqual(sorted(k for k, v in notes.items() if "delivered with" in v),
                         [14, 16, 20])

    def test_deadline_counts(self):
        tally = {}
        for r in self.rows[1:]:
            tally[r[5]] = tally.get(r[5], 0) + 1
        self.assertEqual(tally.get("9:00 AM"), 1)
        self.assertEqual(tally.get("10:30 AM"), 13)
        self.assertEqual(tally.get("EOD"), 26)


class TestDistanceFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "distances.csv"), newline="") as f:
            cls.rows = list(csv.reader(f))

    def test_shape(self):
        self.assertEqual(len(self.rows), 27, "27 locations: the hub plus 26 stops")
        self.assertTrue(all(len(r) == 29 for r in self.rows),
                        "2 label columns plus 27 distance columns")

    def test_lower_triangle_is_intact(self):
        filled = [sum(1 for j in range(2, 29) if r[j].strip()) for r in self.rows]
        self.assertEqual(filled, list(range(1, 28)),
                         "row k should have k+1 distances filled")

    def test_diagonal_is_zero(self):
        for i, r in enumerate(self.rows):
            self.assertEqual(float(r[2 + i]), 0.0,
                             "the distance from a location to itself must be 0")

    def test_it_mirrors_to_a_complete_symmetric_matrix(self):
        n = 27
        m = [[None] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                v = self.rows[i][2 + j].strip()
                if v:
                    m[i][j] = float(v)
        for i in range(n):
            for j in range(n):
                if m[i][j] is None:
                    m[i][j] = m[j][i]
        holes = [(i, j) for i in range(n) for j in range(n) if m[i][j] is None]
        self.assertEqual(holes, [], "mirroring left holes in the matrix")
        for i in range(n):
            for j in range(n):
                self.assertEqual(m[i][j], m[j][i])


class TestEveryPackageAddressIsOnTheMap(unittest.TestCase):
    """The one that catches the 5383 South / 5383 S mismatch."""

    def test_all_40_resolve(self):
        try:
            import locations
        except ImportError:
            self.skipTest("locations.py not importable yet")
        try:
            names, addresses, zips, matrix = locations.load(
                os.path.join(ROOT, "data", "distances.csv"))
            index = locations.build_address_index(addresses)
        except NotImplementedError:
            self.skipTest("locations.py not implemented yet")

        with open(os.path.join(ROOT, "data", "packages.csv"), newline="") as f:
            rows = list(csv.reader(f))[1:]

        unresolved = []
        for r in rows:
            try:
                locations.resolve(index, r[1])
            except Exception:
                unresolved.append((r[0], r[1]))
        self.assertEqual(unresolved, [],
                         "these package addresses did not match the map: %s"
                         % unresolved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
