# routing.py
#
# Creates two separate variables for the requirement:
#   1. WHICH TRUCK carries each package  (assign_to_trucks)
#   2. WHAT ORDER each truck drives (choose_next_stop)
#

import time_utils
from truck import Truck
import locations
# Drivers leave no earlier than 8:00 per the assumptions.
DAY_START = time_utils.parse_clock("8:00 AM") # set this using time_utils.parse_clock("8:00")
END_OF_DAY = time_utils.parse_clock("11:59 PM")

TRUCK_IDS = (1, 2, 3)
DRIVER_COUNT = 2


def merge_groups(packages):
    """ Merges packages into groups for loading and delivery"""

    # Every package starts as its own group: parent[x] == x means "x is a root".
    parent = {pid: pid for pid in packages}

    def find(pid):
        while parent[pid] != pid:
            parent[pid] = parent[parent[pid]]   # path compression
            pid = parent[pid]
        return pid

    def union(a, b):
        """Merge the two groups containing a and b."""
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    # One union per relation stated in the notes. Order does not matter --
    # that is the property that makes the overlap collapse correctly.
    for package_id, package in packages.items():
        for other_id in package.co_delivery_ids:
            if other_id in parent:
                union(package_id, other_id)

    # Collect: everything sharing a root in one group.
    collected = {}
    for package_id in packages:
        collected.setdefault(find(package_id), []).append(package_id)

    return [sorted(members) for members in collected.values()]


def assign_to_trucks(groups, packages, address_index, matrix):
    """Assign every group to a truck using most-constrained-first."""

    trucks = {truck_id: Truck(truck_id) for truck_id in TRUCK_IDS}

    # Truck 1 goes out at 8:00. Truck 2 waits for the 9:05 flight. Truck 3's
    # departure is set in run_day(), when a driver actually returns.
    trucks[1].departure_time = DAY_START
    trucks[2].departure_time = time_utils.parse_clock("9:05 AM")
    trucks[3].departure_time = None

    def group_needs_truck(members):
        """The truck this group is locked to, or None if it is free."""
        for package_id in members:
            required = packages[package_id].required_truck
            if required is not None:
                return required
        return None

    def group_is_delayed(members):
        return any(packages[p].available_at > DAY_START for p in members)

    def group_has_wrong_address(members):
        return any(packages[p].address_is_wrong for p in members)

    def group_has_deadline(members):
        return any(packages[p].has_deadline for p in members)

    def place(members, truck_id):
        """Load a whole group onto one truck. Raises if it will not fit."""
        truck = trucks[truck_id]
        if truck.space_remaining < len(members):
            raise ValueError(
                "group %s will not fit on truck %d (%d slots left)"
                % (members, truck_id, truck.space_remaining))
        for package_id in members:
            truck.load(package_id)
            packages[package_id].truck_id = truck_id

    unassigned = list(groups)

    # --- every group with a forced placement ---------------
    still_free = []
    for members in unassigned:
        required = group_needs_truck(members)
        if required is not None:
            place(members, required)
        elif group_is_delayed(members):
            place(members, 2)
        elif group_has_wrong_address(members):
            place(members, 3)
        elif group_has_deadline(members):
            place(members, 1)
        else:
            still_free.append(members)

    # Truck 3 carries only end-of-day freight, so discretionary packages go
    # there first;
    for members in sorted(still_free, key=len, reverse=True):
        for truck_id in (3, 1, 2):
            if trucks[truck_id].space_remaining >= len(members):
                place(members, truck_id)
                break
        else:
            raise ValueError("no truck has room for group %s" % members)

    return trucks


def choose_next_stop(current_location, current_time, remaining, packages, matrix):
    """Pick the next stop: nearest, unless that would strand a deadline."""
    if not remaining:
        return None

    def earliest_deadline(location_index):
        """The tightest deadline among packages still bound for that stop."""
        deadlines = [packages[p].deadline for p in remaining[location_index]
                     if packages[p].has_deadline]
        return min(deadlines) if deadlines else None

    # --- the greedy choice: the closest stop still on the list ---------
    candidate = min(remaining, key=lambda loc: matrix[current_location][loc])

    # --- the feasibility check, before committing to it ----------------
    # If the truck goes to `candidate` first, it arrives here:
    arrival = current_time + time_utils.travel_time(
        matrix[current_location][candidate])

    # From there, could it still reach every other deadline by driving
    # STRAIGHT to it? A direct drive is the fastest possible approach, so a
    # deadline that fails this test cannot be met along this path at all.
    at_risk = []
    for location_index in remaining:
        if location_index == candidate:
            continue
        deadline = earliest_deadline(location_index)
        if deadline is None:
            continue
        straight_there = arrival + time_utils.travel_time(
            matrix[candidate][location_index])
        if straight_there > deadline:
            at_risk.append((deadline, location_index))

    # --- if anything would be stranded, chooses the most urgent instead --
    if at_risk:
        at_risk.sort()
        return at_risk[0][1]

    return candidate

def run_route(truck, packages, address_index, matrix):
    """Drive one loaded truck through its route and record what happened."""

    remaining = {}
    for package_id in truck.manifest:
        location = locations.resolve(address_index, packages[package_id].address)
        remaining.setdefault(location, []).append(package_id)

    truck.current_location = 0            # the hub
    truck.current_time = truck.departure_time
    for package_id in truck.manifest:
        packages[package_id].departure_time = truck.departure_time

    while remaining:
        next_stop = choose_next_stop(truck.current_location, truck.current_time,
                                     remaining, packages, matrix)

        miles = matrix[truck.current_location][next_stop]
        arrival = truck.current_time + time_utils.travel_time(miles)

        delivered = remaining.pop(next_stop)
        for package_id in delivered:
            packages[package_id].delivery_time = arrival

        truck.record_leg(next_stop, packages[delivered[0]].address,
                         miles, arrival, delivered)

    miles = matrix[truck.current_location][0]
    arrival = truck.current_time + time_utils.travel_time(miles)
    truck.record_leg(0, "HUB", miles, arrival, [])
    truck.return_time = arrival

    return truck


def run_day(packages, table, address_index, matrix, corrections):
    """Load, route and simulate all three trucks for one delivery day."""

    groups = merge_groups(packages)
    trucks = assign_to_trucks(groups, packages, address_index, matrix)

    # 1. Two drivers, so trucks 1 and 2 are the two that can be out at once.
    run_route(trucks[1], packages, address_index, matrix)
    run_route(trucks[2], packages, address_index, matrix)

    # 2. The scheduled corrections land while those two are on the road.
    for package_id, address, city, state, zip_code, effective_time in corrections:
        packages[package_id].apply_correction(address, city, state,
                                              zip_code, effective_time)

    # 3. Truck 3 needs BOTH a driver and deliverable freight. A driver is free
    #    when the first of the other two returns; package 9 is not deliverable
    #    until its address is corrected. Whichever is later decides departure.
    driver_available = min(trucks[1].return_time, trucks[2].return_time)
    corrections_needed = [effective_time
                          for (package_id, _a, _c, _s, _z, effective_time) in corrections
                          if package_id in trucks[3].manifest]
    trucks[3].departure_time = max([driver_available] + corrections_needed)

    run_route(trucks[3], packages, address_index, matrix)

    # 4. Write final state back into the hash table.
    for package_id, package in packages.items():
        table.insert(package_id, package.address, package.deadline,
                     package.city, package.zip_code, package.weight,
                     package.status_at(END_OF_DAY))

    return {
        "trucks": trucks,
        "packages": packages,
        "table": table,
        "total_mileage": sum(t.mileage for t in trucks.values()),
    }