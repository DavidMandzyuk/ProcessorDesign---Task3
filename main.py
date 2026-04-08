"""
CSC 4210 Computer Architecture - Spring 2026
Processor Design Semester Project - Task 3
main.py  –  Demo driver for the Memory Hierarchy Simulator
"""

import random
from memory_hierarchy import MemoryHierarchySimulator


def demo_basic():
    
    print("Memory Hierarchy Simulation  –  CSC 4210/6210  Task 3")
    

    # 1. Create simulator with configurable sizes
    sim = MemoryHierarchySimulator(
        ssd_size    = 1024,
        dram_size   = 256,
        l3_size     = 64,
        l2_size     = 32,
        l1_size     = 8,
        ssd_latency  = 8,
        dram_latency = 4,
        l3_latency   = 3,
        l2_latency   = 2,
        l1_latency   = 1,
        bandwidth    = 4,
        cache_policy = "LRU",
    )

    # 2. Print configuration
    sim.print_config()

    # 3. Generate 200 random 32-bit instructions and load SSD
    random.seed(42)
    instructions = [random.randint(0x00000000, 0xFFFFFFFF) for _ in range(200)]
    sim.load_ssd(instructions)

    # 4. Run 30 clock cycles so data propagates through hierarchy
    #    SSD(8)+DRAM(4)+L3(3)+L2(2)+L1(1) = 18 cycles minimum
    sim.run(30)

    # 5. READ operations
    print("\n--- READ Operations ---")

    # (a) Read from L2  -> L2 HIT, instruction promoted to L1
    l2_sample = list(sim.l2.storage)[:3]
    print("\n[a] First read (expect L2 HITs, promoted to L1):")
    for instr in l2_sample:
        sim.read(instr)

    # (b) Re-read same instructions -> now in L1 -> L1 HIT
    print("\n[b] Second read of same instructions (expect L1 HITs):")
    for instr in l2_sample:
        sim.read(instr)

    # (c) Read instruction still in SSD -> full miss chain
    print("\n[c] Read instruction still in SSD (expect full MISS):")
    sim.read(instructions[-1])

    # 6. WRITE-BACK operations
    print("\n--- WRITE-BACK Operations ---")
    sim.write(0xDEADBEEF, "DRAM")
    sim.write(0xCAFEBABE, "SSD")

    # 7. Run a few more cycles
    sim.run(5)

    # 8. Final state of each memory level
    sim.print_state()

    # 9. Full instruction access trace
    sim.print_trace()


def demo_fifo():
    print("\n\n" + "=" * 62)
    print("  BONUS – FIFO CACHE REPLACEMENT POLICY")
    print("=" * 62)

    sim = MemoryHierarchySimulator(
        ssd_size=512, dram_size=128, l3_size=32,
        l2_size=16,   l1_size=4,
        bandwidth=2,  cache_policy="FIFO",
    )
    sim.print_config()
    instrs = list(range(0x1000, 0x1064))
    sim.load_ssd(instrs)
    sim.run(30)

    print("\n--- READ Operations (FIFO) ---")
    l2_sample = list(sim.l2.storage)[:4]
    print("[a] First read (expect L2 HITs):")
    for i in l2_sample:
        sim.read(i)
    print("[b] Second read (expect L1 HITs):")
    for i in l2_sample:
        sim.read(i)

    sim.print_state()


def demo_random_policy():
    print("\n\n" + "=" * 62)
    print("  BONUS – RANDOM CACHE REPLACEMENT POLICY")
    print("=" * 62)

    random.seed(7)
    sim = MemoryHierarchySimulator(
        ssd_size=512, dram_size=128, l3_size=32,
        l2_size=16,   l1_size=4,
        bandwidth=2,  cache_policy="RANDOM",
    )
    sim.print_config()
    instrs = list(range(0x2000, 0x2064))
    sim.load_ssd(instrs)
    sim.run(30)

    print("\n--- READ Operations (RANDOM) ---")
    l2_sample = list(sim.l2.storage)[:4]
    print("[a] First read (expect L2 HITs):")
    for i in l2_sample:
        sim.read(i)
    print("[b] Second read (expect L1 HITs):")
    for i in l2_sample:
        sim.read(i)

    sim.print_state()


if __name__ == "__main__":
    demo_basic()
    demo_fifo()
    demo_random_policy()
