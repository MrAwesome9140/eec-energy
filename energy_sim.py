import math
import sys
from pathlib import Path
import random

"""
Represents a cache line.

Attributes:
    tag (int): The tag of the cache line.
    dirty (bool): Whether the cache line is dirty.
    valid (bool): Whether the cache line is valid.
"""
class CacheLine:
    def __init__(self, tag, dirty):
        self.tag = tag
        self.dirty = dirty
        self.valid = False

"""
Represents a cache module.

Attributes:
    size (int): The size of the cache in bytes.
    associativity (int): The associativity of the cache.
    access_time (float): The time it takes to access the cache in seconds.
    idle_power (float): The power consumed by the cache when idle in watts.
    active_power (float): The power consumed by the cache when active in watts.
    parent (Cache): The parent cache of the cache module.
"""
class Cache:
    def __init__(self, size, associativity, access_time, idle_power, active_power, parent=None):
        self.size = size
        self.associativity = associativity
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power
        self.parent = parent
        # Array of sets, each set containing associativity number of CacheLine objects
        self.cache = [[CacheLine(-1, False) for _ in range(associativity)] for _ in range(size // (associativity * 64))]

    def read(self, address):
        set_index = (address >> 6) % (self.size // (self.associativity * 64))
        tag = address >> math.floor(math.log2(64 * (self.size // (self.associativity * 64))))

        for i in range(self.associativity):
            temp = self.cache[set_index][i]
            if temp.tag == tag and temp.valid:
                return True

        return False

    def write(self, address):
        set_index = (address // 64) % (self.size // (self.associativity * 64))
        tag = address // (self.size // (self.associativity * 64) * 64)

        random_index = random.randint(0, self.associativity - 1)
        evict = self.cache[set_index][random_index]
        if self.parent and evict.valid and evict.dirty:
            self.parent.write(evict.tag)
        
        self.cache[set_index][random_index].tag = tag
        self.cache[set_index][random_index].valid = True

        if not self.associativity == 1:
            # when writing to L2 set the dirty bit
            self.cache[set_index][random_index].dirty = True
        else:
            self.cache[set_index][random_index].dirty = False

"""
Represents a memory module.

Attributes:
    size (int): The size of the memory module in bytes.
    access_time (float): The time it takes to access the memory module in seconds.
    idle_power (float): The power consumed by the memory module when idle in watts.
    active_power (float): The power consumed by the memory module when active in watts.
"""
class Memory:

    def __init__(self, size, access_time, idle_power, active_power):
        self.size = size
        self.access_time = access_time
        self.idle_power = idle_power
        self.active_power = active_power


    def read(self, address):
        return True

    def write(self, address):
        return True

def simulate(trace_file, num_runs):

    for associativity in [2, 4, 8]:

        l2_cache = Cache(256 * (2 ** 10), associativity, 5, 0.8, 2)
        l1_data_cache = Cache(32 * (2 ** 10), 1, 0.5, 0.5, 1, l2_cache)
        l1_instruction_cache = Cache(32 * (2 ** 10), 1, 0.5, 0.5, 1, l2_cache)
        dram = Memory(8 * (2 ** 20), 50, 0.8, 4)

        l2_transfer_penalty = 0.005
        dram_transfer_penalty = 0.64

        l2_cache_ind_access_time = l2_cache.access_time - l1_data_cache.access_time
        dram_ind_access_time = dram.access_time - l2_cache.access_time

        total_access_time = 0
        total_memory_accesses = 0
        total_memory_accesses_l2 = 0
        l1_misses = 0
        l2_misses = 0
        l1_hits = 0
        l2_hits = 0
        l1_energy = 0
        l2_energy = 0
        dram_energy = 0

        for i in range(num_runs):
            with open(trace_file, 'r') as file:
                for line in file:
                    operation, address, data = line.strip().split()
                    operation = int(operation)
                    address = int(address, 16)
                    data = int(data, 16)

                    l1_cache = l1_data_cache if operation == 0 or operation == 1 else l1_instruction_cache
                    
                    if operation == 0 or operation == 2:  # Data read or instruction fetch
                        total_memory_accesses += 1
                        if not l1_cache.read(address):
                            l1_misses += 1
                            total_memory_accesses_l2 += 1
                            if not l2_cache.read(address):
                                l2_misses += 1
                                l1_energy += l1_cache.idle_power * (dram.access_time - l1_cache.access_time) + l1_cache.active_power * l1_cache.access_time + l1_cache.idle_power * dram.access_time
                                l2_energy += l2_cache.active_power * l2_cache_ind_access_time + l2_cache.idle_power * (dram.access_time - l2_cache.access_time) + l2_transfer_penalty
                                dram_energy += dram.active_power * dram_ind_access_time + dram.idle_power * l2_cache.access_time + dram_transfer_penalty
                                total_access_time += dram.access_time
                                l1_cache.write(address)
                                l2_cache.write(address)
                            else:
                                l2_hits += 1
                                l1_energy += l1_cache.idle_power * l2_cache_ind_access_time + l1_cache.active_power * l1_cache.access_time + l1_cache.idle_power * l2_cache.access_time
                                l2_energy += l2_cache.active_power * l2_cache_ind_access_time + l2_cache.idle_power * l1_cache.access_time + l2_transfer_penalty
                                dram_energy += dram.idle_power * l2_cache.access_time
                                total_access_time += l2_cache.access_time
                                l1_cache.write(address)
                        else:
                            l1_hits += 1
                            l1_energy += l1_cache.active_power * l1_cache.access_time + l1_cache.idle_power * l1_cache.access_time
                            l2_energy += l2_cache.idle_power * l1_cache.access_time
                            dram_energy += dram.idle_power * l1_cache.access_time
                            total_access_time += l1_cache.access_time
                    elif operation == 1:  # Data write
                        total_memory_accesses += 1
                        if not l1_cache.read(address):
                            l1_misses += 1
                            total_memory_accesses_l2 += 1
                            if not l2_cache.read(address):
                                l2_misses += 1
                                l1_energy += l1_cache.idle_power * l2_cache_ind_access_time + l1_cache.active_power * l1_cache.access_time + l1_cache.idle_power * l2_cache.access_time
                                dram_energy += dram.idle_power * l2_cache.access_time + dram_transfer_penalty
                                total_access_time += l2_cache.access_time
                                l2_cache.write(address)
                            else:
                                l2_hits += 1
                                l1_energy += l1_cache.idle_power * l2_cache_ind_access_time + l1_cache.active_power * l1_cache.access_time + l1_cache.idle_power * l2_cache.access_time
                                l2_energy += l2_cache.active_power * l2_cache_ind_access_time + l2_cache.idle_power * l1_cache.access_time
                                dram_energy += dram.idle_power * l2_cache.access_time
                                total_access_time += l2_cache.access_time
                        else:
                            l1_hits += 1

                            # added these counts to reflect write through to L2
                            total_memory_accesses_l2 += 1
                            l2_hits += 1

                            l1_energy += l1_cache.active_power * l1_cache.access_time + l1_cache.idle_power * l2_cache_ind_access_time + l1_cache.idle_power * l2_cache.access_time
                            l2_energy += l2_cache.idle_power * l1_cache.access_time + l2_cache.active_power * l2_cache_ind_access_time
                            dram_energy += dram.idle_power * l2_cache.access_time
                            total_access_time += l2_cache.access_time
                            l1_cache.write(address)
                            l2_cache.write(address)

        average_memory_access_time = total_access_time / total_memory_accesses

        # Print out misses, hits, miss rate, and energy consumption
        print(f"Trace File: {trace_file}")
        print(f"Associativity: {associativity}")
        print(f"Average L1 Misses: {l1_misses / num_runs}")
        print(f"Average L1 Hits: {l1_hits / num_runs}")
        print(f"Average L1 Hit Rate: {l1_hits / total_memory_accesses}")

        print(f"Average L2 Misses: {l2_misses / num_runs}")
        print(f"Average L2 Hits: {l2_hits / num_runs}")
        # print(f"L2 Hit Rate: {l2_hits / total_memory_accesses}")
        print(f"Average L2 Hit Rate: {l2_hits / total_memory_accesses_l2}")

        print(f"Average L1 Energy Consumption: {(l1_energy / num_runs) / (10 ** 9)} J")
        print(f"Average L2 Energy Consumption: {(l2_energy / num_runs) / (10 ** 9)} J")
        print(f"Average DRAM Energy Consumption: {(dram_energy / num_runs) / (10 ** 9)} J")
        print(f"Average Total Energy Consumption: {((l1_energy + l2_energy + dram_energy) / num_runs) / (10 ** 9)} J")
        print(f"Average Memory Access Time: {average_memory_access_time} ns\n")

# Run the simulation
num_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
specified_trace_file = sys.argv[2] if len(sys.argv) > 2 else None
# print(f"Number of Runs: {num_runs}")
# print(f"Specified Trace File: {specified_trace_file}\n")
if specified_trace_file:
    simulate("./Traces/Spec_Benchmark/" + specified_trace_file, num_runs)
else:
    folder = Path("./Traces/Spec_Benchmark")
    for i in folder.iterdir():
        if i.is_file() and i.suffix == ".din":            
            simulate("./Traces/Spec_Benchmark/" + i.name, num_runs)
            print("\n")
