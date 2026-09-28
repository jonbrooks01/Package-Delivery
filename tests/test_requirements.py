"""Every scenario requirement, checked against your finished program.

These skip until build_day() works, then they become your rubric F2 evidence.
Run them before you take the D1-D3 and E screenshots.
"""

import os
import sys
import unittest



ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import time_utils

class TestTheDay(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import main
        cls.day = main.build_day()

    def test_all_40_delivered(self):
        packages = self.day["packages"]
        self.assertEqual(len(packages), 40)
        undelivered = [i for i, p in packages.items() if p.delivery_time is None]
        self.assertEqual(undelivered, [])

    def test_no_deadline_missed(self):
        late = [i for i, p in self.day["packages"].items()
                if p.has_deadline and p.delivery_time > p.deadline]
        self.assertEqual(late, [])

    def test_combined_mileage_under_140(self):
        total = sum(leg["miles"]
                    for truck in self.day["trucks"].values()
                    for leg in truck.trip_log)
        self.assertLess(total, 140.0)

    def test_no_truck_over_16_packages(self):
        oversized = [tid for tid, t in self.day["trucks"].items()
                     if len(t.manifest) > 16]
        self.assertEqual(oversized, [], "capacity is 16 per the assumptions")

    def test_truck_2_only_packages_rode_truck_2(self):
        packages = self.day["packages"]
        for package_id in (3, 18, 36, 38):
            self.assertEqual(packages[package_id].truck_id, 2,
                             "package %d is noted truck 2 only" % package_id)

    def test_grouped_packages_shared_a_truck(self):
        packages = self.day["packages"]
        group = (13, 14, 15, 16, 19, 20)
        carried_by = {packages[p].truck_id for p in group}
        self.assertEqual(len(carried_by), 1,
                         "the overlapping notes merge into ONE group of six")

    def test_delayed_packages_did_not_leave_before_905(self):
        packages = self.day["packages"]
        flight = time_utils.parse_clock("9:05 AM")
        for package_id in (6, 25, 28, 32):
            self.assertGreaterEqual(packages[package_id].departure_time, flight,
                                    "package %d is on the delayed flight" % package_id)

    def test_package_9_left_after_its_correction(self):
        nine = self.day["packages"][9]
        self.assertGreaterEqual(nine.departure_time,
                                time_utils.parse_clock("10:20 AM"))
        self.assertEqual(nine.address, "410 S State St")
        self.assertEqual(nine.zip_code, "84111")
        # And a query about an earlier moment still reports the OLD address.
        self.assertEqual(nine.address_at(time_utils.parse_clock("9:00 AM")),
                         "300 State St")

    def test_at_most_two_trucks_on_the_road_at_once(self):
        trips = [(t.departure_time, t.return_time)
                 for t in self.day["trucks"].values()]
        # The count can only rise when a truck leaves, so checking at each
        # departure is enough to catch a violation.
        for moment, _ in trips:
            on_the_road = sum(1 for out, back in trips if out <= moment < back)
            self.assertLessEqual(on_the_road, 2, "three trucks, two drivers")


if __name__ == "__main__":
    unittest.main(verbosity=2)
