# Jonathan Brooks, Student ID: 010890040
#
# main.py -- WGUPS Routing Program
# C950 Data Structures and Algorithms II

# COMPLEXITY NOTATION USED IN EVERY FILE
#   n = number of packages (40 here)
#   v = number of locations (27 here)
#
# WHOLE-PROGRAM COMPLEXITY
#   Time  O(n log n + n*v + v^2)  -- n log n from sorting during assignment,
#                                    n*v from resolving and grouping, v^2 from
#                                    the matrix load and the routing search
#   Space O(n + v^2)              -- the hash table plus the distance matrix
# Polynomial in both, so the program scales predictably
# An exact travelling-salesman solution would be factorial.

import hash_table
import locations
import package
import routing
import time_utils

PACKAGE_FILE = "data/packages.csv"
DISTANCE_FILE = "data/distances.csv"

# Package 9's address is wrong on the manifest and is not corrected until
# 10:20 a.m.

CORRECTIONS = [
    (9, "410 S State St", "Salt Lake City", "UT", "84111",
     time_utils.parse_clock("10:20 AM")),
]

ROW = "%-4s %-38s %-17s %-6s %-9s %-7s %-6s %s"


def header():
    return ROW % ("ID", "Address", "City", "Zip", "Deadline",
                  "Weight", "Truck", "Status")


def format_row(one_package, moment):

    return ROW % (
        one_package.package_id,
        one_package.address_at(moment)[:38],
        one_package.city[:17],
        one_package.zip_at(moment),
        time_utils.format_clock(one_package.deadline),
        "%.0f kg" % one_package.weight,
        one_package.truck_id,
        one_package.status_at(moment),
    )

def build_day():
    """Load the data files and simulate the whole delivery day once.
         Time O(n log n + n*v + v^2).  Space O(n + v^2).
    """
    table = hash_table.ChainingHashTable()
    packages = package.load_packages(PACKAGE_FILE, table)

    names, addresses, zips, matrix = locations.load(DISTANCE_FILE)
    address_index = locations.build_address_index(addresses)

    day = routing.run_day(packages, table, address_index, matrix, CORRECTIONS)
    day["names"] = names
    day["address_index"] = address_index
    day["matrix"] = matrix
    return day

def show_single_package(table, packages, moment):
    """Goes through the packages and shows the results for an individual package."""
    entered = input("  Package ID (1-40): ").strip()
    if not entered.isdigit() or int(entered) not in packages:
        print("  No package with that ID.\n")
        return
    print()
    print(header())
    print(format_row(packages[int(entered)], moment))
    print()


def show_all_packages(table, packages, moment):
    """Shows the results for all packages."""
    print()
    print(header())
    for package_id in sorted(packages):
        print(format_row(packages[package_id], moment))
    print()


def show_truck(table, packages, trucks, truck_id, moment):
    """Shows the packages loaded on one truck."""
    truck = trucks[truck_id]
    print()
    print("  Truck %d -- departed %s, %.1f miles, %d stops"
          % (truck_id,
             time_utils.format_clock(truck.departure_time),
             truck.mileage,
             len(truck.trip_log)))
    print()
    print(header())
    for package_id in sorted(truck.manifest):
        print(format_row(packages[package_id], moment))
    print()


def show_mileage(trucks):
    """Shows the mileage of each truck"""
    print()
    total = 0.0
    for truck_id in sorted(trucks):
        truck = trucks[truck_id]
        legs = sum(leg["miles"] for leg in truck.trip_log)
        total += truck.mileage
        print("  Truck %d: %6.1f miles  (%d legs, re-added: %.1f)"
              % (truck_id, truck.mileage, len(truck.trip_log), legs))
    print("  " + "-" * 46)
    print("  Combined: %5.1f miles" % total)
    print()

def ask_for_time(prompt="  Time (e.g. 9:35 AM, or 13:00): "):
    """Reads input from the user for the time inputted"""
    while True:
        entered = input(prompt).strip()
        if not entered:
            return None
        try:
            return time_utils.parse_clock(entered)
        except (ValueError, IndexError):
            print("  Could not read that. Try 9:35 AM or 13:00, "
                  "or press Enter to cancel.")


def menu():
    """This is what loads when main.py runs"""
    print("\n  WGUPS Routing Program")
    print("  Simulating the delivery day...", end=" ", flush=True)
    day = build_day()
    print("done. %.1f miles, %d packages.\n"
          % (day["total_mileage"], len(day["packages"])))

    table = day["table"]
    packages = day["packages"]
    trucks = day["trucks"]

    while True:
        print("  1. Look up one package at a time")
        print("  2. All packages at a time")
        print("  3. One truck's packages at a time")
        print("  4. Mileage for all trucks")
        print("  5. Quit")

        choice = input("  Choice: ").strip()

        if choice == "1":
            moment = ask_for_time()
            if moment is not None:
                show_single_package(table, packages, moment)
        elif choice == "2":
            moment = ask_for_time()
            if moment is not None:
                show_all_packages(table, packages, moment)
        elif choice == "3":
            entered = input("  Truck (1, 2 or 3): ").strip()
            if entered not in ("1", "2", "3"):
                print("  No such truck.\n")
                continue
            moment = ask_for_time()
            if moment is not None:
                show_truck(table, packages, trucks, int(entered), moment)
        elif choice == "4":
            show_mileage(trucks)
        elif choice == "5":
            print("  Goodbye.\n")
            return
        else:
            print("  Enter 1 through 5.\n")

if __name__ == "__main__":
    menu()