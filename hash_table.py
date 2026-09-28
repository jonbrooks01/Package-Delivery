# hash_table.py
# Stores the packages in a self-adjusting hash table
#


class ChainingHashTable:
 
    INITIAL_CAPACITY = 17
    MAX_LOAD_FACTOR = 0.75
 
    def __init__(self, capacity = INITIAL_CAPACITY) -> None:
 
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0
        self._collisions = 0
        self._resizes = 0
 
    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
 
    def _bucket_index(self, package_id):
 
        return package_id % len(self._buckets)
 
    def lookup(self, package_id):
        bucket = self._buckets[self._bucket_index(package_id)]
        for entry in bucket:
            if entry[0] == package_id:
                return entry[1:]
        return None
 
    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
 
    def insert(self, package_id, address, deadline, city, zip_code, weight, status):
        """ Builds the entry for the individual package. So the package can be updated or a new one can be created. """

        entry = [package_id, address, deadline, city, zip_code, weight, status]
 
        bucket = self._buckets[self._bucket_index(package_id)]

        for position, existing in enumerate(bucket):
            if existing[0] == package_id:
                bucket[position] = entry
                return
 
        if bucket:  # non-empty bucket = collision
            self._collisions += 1
 
        bucket.append(entry)
        self._size += 1
 
        if self.load_factor > self.MAX_LOAD_FACTOR:
            self._resize()
 
    def remove(self, package_id):
        """ Removes a package"""
        bucket = self._buckets[self._bucket_index(package_id)]
        for position, entry in enumerate(bucket):
            if entry[0] == package_id:
                del bucket[position]
                self._size -= 1
                return True
        return False
 
    def _resize(self):
        """ Resizes the buckets so they have the same capacity."""
        old_buckets = self._buckets  # hold the old array
        new_capacity = len(old_buckets) * 2 + 1  # double, keep it odd
        self._buckets = [[] for _ in range(new_capacity)]  # fresh bigger array
        self._resizes += 1
 
        for bucket in old_buckets:  # every old bucket
            for entry in bucket:  # every entry in it
                index = entry[0] % new_capacity  # re-hash to NEW size
                self._buckets[index].append(entry)
 
    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
 
    @property
    def capacity(self):
        """Number of buckets currently allocated."""
        return len(self._buckets)
 
    @property
    def load_factor(self):
        """Entries per bucket -- the signal that drives resizing."""
        return self._size / len(self._buckets)
 
    def keys(self):
        """Every key in the table.  O(n + capacity)."""
        return [entry[0] for bucket in self._buckets for entry in bucket]
 
    def longest_chain(self):
        """Longest bucket chain -- a direct measure of collision damage."""
        return max((len(bucket) for bucket in self._buckets), default=0)
 