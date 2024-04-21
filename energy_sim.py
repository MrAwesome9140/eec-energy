import math
import random

# The Memory Subsystem
# The memory subsystem consists of an L1 cache, an L2 cache, and DRAM. The L1 cache is direct mapped and has a 32KB for instructions and 32KB for data. The L2 cache is set-associa6ve with set associativity of 4 and has a combined cache of 256KB. The cache replacement algorithm is Random.
# The DRAM consists of an 8GB DDR-5 DIMM. Data access to main memory is done in units of 64 bytes, and the cache line size is 64 bytes (both L1 and L2). The read/write access times are:
# L1 cache: 0.5nsec L2 cache: 5nsec DRAM: 50nsec
# The power consumption of the caches and DRAM are given below:
# L1 cache: 0.5W idle and 1W during reads or writes.
# L2 cache: 0.8W idle and 2W during reads or writes. In addi6on, accessing the L2 cache will incur a 5pJ to account for the data transfer between the L1 and the L2.
# DRAM: 0.8W idle increasing to 4W during reads and writes. In addi6on, accessing the memory will add a penalty of 640pJ for every access (to account for the energy necessary for data transfer and accessing the bus).
# Your Task
# In this exercise, you will study the energy consump6on of cache and memory systems. You will use a trace driven simulator for the L1, L2 and DRAM subsystem. The traces follow the Dinero format (from the University of Wisconsin). The traces to be used in this exercise are provided with the homework document. You will need to write the following components:
# - A simulator for the L1 cache, including the directory and data.
# - A simulator for the L2 cache, including the directory and data.
# - A simulator for the DRAM 6ming and energy consump6on.

#  There are many public codes for cache simulators that are available. Feel free to use any package if you wish, or partially import some code into your code, or write your own from scratch.
# The operation:
# - You start the simulator by reading the addresses. You can assume that the processor runs at 2GHz (0.5nsec cycle 6me). Normally, the processor will issue the ﬁrst address at time zero. The next address will depend on whether there is a cache miss or not. If there is a cache miss, you will have to assign the 6me depending on whether the miss is in the L1, L1 and L2, or if you have to read from memory. Advance the clock based on the timing of the cache and memory as appropriate.
# - If the cache contains the item, then you move to the next address. If not, then there is a cache miss. You will need to simulate the time it takes to fetch the data for either a hit or a miss. Hint: You may wish to refresh your memory by inspec6ng your notes from CS429 or CS439.
# - For all memory accesses and also the idle time, you need to record the energy consumed by the L1, L2 and the memory.


# Notes
# The following are simplifying assump6ons:
# -         When writing to the cache, the entire cache line has to be present, or brought from the next level in the hierarchy. So a write miss will invoke a read operation before writing.
# -         Transfers between the L1 and L2, and between the L2 and memory are done in units of 64 bytes.

# Your Output
# In addition to the code, you will need to show a report detailing the misses and hits at the L1 and L2, energy consumption for both, and the overall average memory access 6me as seen from the processor. You will provide this for all the benchmarks in the trace ﬁle (included in the project page).
# Amendment: In addition to the above, study the impact of the associativity level of the cache on both the performance and energy consump6on. Use set associa6vity of 2, 4, and 8 to round up your study.

# Further Instructions:
# There are no "flush" operations in the trace files, and you don't have to implement it
# You have to implement write back to DRAM on update to L2 during eviction form L2 and write back to L2 on update to L1 and during eviction from L1. Remember that writes in general are asynchronous (they don't stall the pipeline unlike reads)
# While are evictions and transfers are in units of 64 bytes, the memory access are in units of 4 bytes only. You might not have to worry about 4 bytes traversing two cache lines

# More Clarifications:
# Read Operation:

# l1 hit: 0.5ns
# l1 miss, l2 hit: 5ns, +5pj
# l1 miss, l2 miss: 50ns, +5pj +640pj, l2 write back
# Write Operation:

# l1 hit, l2: 5ns (write through)
# l1 miss, l2 hit: 5ns
# l1 miss, l2 miss: 5ns, l2 write back
# Notes:

# writes are 5ns because only writes to l1,l2 are synchronous, and mark dirty bits.
# write backs only happen when a dirty line is being evicted. and they only happen from l2 if you used write through between l1 and l2.
# copy of data DRAM -> L2 and L2 -> DRAM on misses do not take extra time or extra active energy for the writes - this is included in penalty energy.
# in addition to energy penalties I mentioned above, static and active energies should be computed for l1, l2 and DRAM. For DRAM, write backs will remove equivalent static energy to add active energy. I am not actually sure if penalties apply for writes.
# random policy is to choose the address among a set (of size 2/4/8) to evict in l2
# there is no possibility of write backs or write operations in instruction l1 as it is read only
# latencies are additive - meaning access to l2 from l1 was 4.5ns and l2 is considered active for this entire period. Similarly 45ns for DRAM.

class CacheLine:
    def __init__(self, tag, dirty):
        self.tag = tag
        self.dirty = dirty
        self.valid = False

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

        # if not replace:
        #     for i in range(self.associativity):
        #         temp = self.cache[set_index][i]
        #         if temp.valid and temp.tag == tag:
        #             temp.dirty = True
        #             if self.parent:
        #                 self.parent.write(address)
        #             return None
        #     return False
        # else: 
        #     # Random replacement policy

        random_index = random.randint(0, self.associativity - 1)
        evict = self.cache[set_index][random_index]
        if self.parent and evict.valid and evict.dirty:
            self.parent.write(evict.tag)
        
        self.cache[set_index][random_index].tag = tag
        self.cache[set_index][random_index].valid = True
        self.cache[set_index][random_index].dirty = False


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

def simulate(trace_file):

    for associativity in [2, 4, 8]:
        l2_cache = Cache(256 * (2 ** 10), associativity, 5, 0.8, 2)
        l1_data_cache = Cache(32 * (2 ** 10), 1, 0.5, 0.5, 1, l2_cache)
        l1_instruction_cache = Cache(32 * (2 ** 10), 1, 0.5, 0.5, 1, l2_cache)
        dram = Memory(8 * (2 ** 20), 50, 0.8, 4)

        l2_transfer_penalty = 5
        dram_transfer_penalty = 640

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
        print(f"L1 Misses: {l1_misses}")
        print(f"L1 Hits: {l1_hits}")
        print(f"L1 Hit Rate: {l1_hits / total_memory_accesses}")

        print(f"L2 Misses: {l2_misses}")
        print(f"L2 Hits: {l2_hits}")
        # print(f"L2 Hit Rate: {l2_hits / total_memory_accesses}")
        print(f"L2 Hit Rate: {l2_hits / total_memory_accesses_l2}")

        print(f"L1 Energy Consumption: {l1_energy} pJ")
        print(f"L2 Energy Consumption: {l2_energy} pJ")
        print(f"DRAM Energy Consumption: {dram_energy} pJ")
        print(f"Average Memory Access Time: {average_memory_access_time} ns\n")

# Run the simulation
simulate(".\\Traces\\Spec_Benchmark\\039.wave5.din")
# simulate("/Users/anthony/eec-energy/039.wave5.din")
