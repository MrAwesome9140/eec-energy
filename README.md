# Overview

The cache simulator is a write-through simulator that simulates a memory subsystem
with an L1 instruction cache, L1 data cache, L2 unified cache, and DRAM. The simulator
outputs the average hit rate and energy consumption over a user-specified number
of runs for the L1 cache, L2 cache, and DRAM.


# Run Instructions

To run the simulator, run the run.sh file with 2 possible flags following it to specify the amount of times each testcase should run, and any specific trace file to run. Each run of the simulator will run the trace file specified or all trace files at the 2, 4, and 8 associativity levels for the L2 cache.

1) -r: The number of times to run each test case. If left unspecified, the default is 1, so each test case will run one time

2) -n: Name of the file to run. The file must be in the Traces/Spec_Benchmark folder. If left unspecified, all trace files will be run.


# Examples

1) To run all traces and take the average of each over 10 runs, run the following command
> ./run.sh -r 10

2) To run only the "093.nasa7.din" trace and take the average over 5 runs for each associativity level, run the following command
> ./run.sh -r 5 -n 093.nasa7.din

3) To run only the "039.wave5.din" trace and take the average over 1 run for each associativity level, run the following command
> ./run.sh -n 039.wave5.din
