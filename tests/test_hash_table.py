"""Tests for hash table. """

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hash_table import ChainingHashTable


def sample(pid, status="At the hub"):
    """One package's components, in the order insert() takes them."""
    return (pid, "195 W Oakland Ave", "10:30 AM", "Salt Lake City",
            "84115", 21, status)


class TestInsertAndLookup(unittest.TestCase):

    def test_insert_then_lookup_returns_the_components(self):
        t = ChainingHashTable()
        t.insert(*sample(1))
        got = t.lookup(1)
        self.assertIsNotNone(got, "lookup returned None for a key just inserted")
        self.assertEqual(len(got), 6,
                         "lookup should return the six components: "
                         "address, deadline, city, zip, weight, status")
        self.assertEqual(list(got), ["195 W Oakland Ave", "10:30 AM",
                                     "Salt Lake City", "84115", 21, "At the hub"])

    def test_lookup_unknown_id_returns_none(self):
        t = ChainingHashTable()
        t.insert(*sample(1))
        self.assertIsNone(t.lookup(99))

    def test_insert_updates_instead_of_duplicating(self):
        t = ChainingHashTable()
        t.insert(*sample(1, "At the hub"))
        t.insert(*sample(1, "Delivered at 8:42 AM"))
        self.assertEqual(t.lookup(1)[5], "Delivered at 8:42 AM")
        self.assertEqual(len(t.keys()), 1,
                         "re-inserting the same ID must replace, not append")

    def test_remove(self):
        t = ChainingHashTable()
        t.insert(*sample(1))
        self.assertTrue(t.remove(1))
        self.assertIsNone(t.lookup(1))
        self.assertFalse(t.remove(1), "removing twice should report False")


class TestResizing(unittest.TestCase):


    def test_500_keys_survive_every_resize(self):
        t = ChainingHashTable(capacity=5)
        for pid in range(1, 501):
            t.insert(*sample(pid, "status-%d" % pid))

        self.assertEqual(len(t.keys()), 500)
        for pid in range(1, 501):
            got = t.lookup(pid)
            self.assertIsNotNone(got, "package %d was lost during a resize" % pid)
            self.assertEqual(got[5], "status-%d" % pid,
                             "package %d came back with the wrong data" % pid)

    def test_load_factor_stays_bounded(self):
        t = ChainingHashTable(capacity=5)
        for pid in range(1, 501):
            t.insert(*sample(pid))
        self.assertLessEqual(t.load_factor, ChainingHashTable.MAX_LOAD_FACTOR,
                             "the table grew past its own load-factor limit")

    def test_chains_stay_short(self):
        t = ChainingHashTable(capacity=5)
        for pid in range(1, 501):
            t.insert(*sample(pid))
        self.assertLessEqual(t.longest_chain(), 5,
                             "chains this long mean resizing is not working")


class TestNoExtraLibraries(unittest.TestCase):


    def test_hash_table_module_imports_nothing(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "hash_table.py")
        offenders = []
        for n, line in enumerate(open(path), start=1):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                offenders.append("line %d: %s" % (n, stripped))
        self.assertEqual(offenders, [],
                         "hash_table.py must not import anything:\n  "
                         + "\n  ".join(offenders))

    def test_no_dict_or_set_used_for_storage(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "hash_table.py")
        source = open(path).read()
        # Strip comments and docstrings crudely, then look for the builtins.
        code = "\n".join(l.split("#")[0] for l in source.splitlines())
        for banned in ("dict(", "set(", "{}"):
            self.assertNotIn(banned, code,
                             "found %r in hash_table.py -- build it from plain "
                             "lists instead" % banned)


if __name__ == "__main__":
    unittest.main(verbosity=2)
