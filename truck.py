# truck.py

"""One truck for one trip out of the hub.

Creates the record of where the truck goes and how the packages get delivered.
"""


CAPACITY = 16

class Truck:

    def __init__(self, truck_id, capacity=CAPACITY):
        self.truck_id = truck_id
        self.capacity = capacity
        self.manifest = []  # package IDs, not Package objects
        self.mileage = 0.0
        self.current_location = 0  # index into the distance matrix; 0 = hub
        self.departure_time = None  # set when the truck actually leaves
        self.current_time = None  # advances as legs are recorded
        self.return_time = None  # set when it gets back to the hub
        self.trip_log = []

    @property
    def space_remaining(self):
        """Shows how much free space is remaining for the truck."""
        return self.capacity - len(self.manifest)

    def load(self, package_id):
        """Loads the packages to the truck and produces an error if full"""
        if len(self.manifest) >= self.capacity:
            raise ValueError("truck %d is full (capacity %d)"
                            %(self.truck_id, self.capacity))
        self.manifest.append(package_id)

    def record_leg(self, location_index, address, miles, arrival_time, package_ids):
        """Records the required information for the delivery"""
        self.mileage += miles
        self.current_location = location_index
        self.current_time = arrival_time

        self.trip_log.append({
            "location_index": location_index,
            "address": address,
            "miles": miles,
            "arrival_time": arrival_time,
            "package_ids": list(package_ids),
        })