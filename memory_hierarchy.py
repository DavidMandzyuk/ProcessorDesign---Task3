from __future__ import annotations
"""
CSC 4210 Computer Architecture - Spring 2026
Processor Design Semester Project - Task 3
Memory Hierarchy Simulation (SSD -> DRAM -> Cache)
"""

import random
from collections import deque, OrderedDict



# Memory Level Base Class

class MemoryLevel:
    # Base class representing a single level of the memory hierarchy

    def __init__(self, name: str, capacity: int, latency: int, bandwidth: int):
        """
        Args:
            name:      Human-readable label (e.g. 'SSD', 'DRAM', 'L3')
            capacity:  Maximum number of 32-bit instructions storable
            latency:   Clock cycles required to complete a transfer FROM this level
            bandwidth: Maximum instructions transferable per clock cycle
        """
        self.name = name
        self.capacity = capacity
        self.latency = latency
        self.bandwidth = bandwidth
        # Storage is a list of instruction values (integers)
        self.storage: list[int] = []

    # Helpers

    def is_full(self) -> bool:
        return len(self.storage) >= self.capacity

    def is_empty(self) -> bool:
        return len(self.storage) == 0

    def free_slots(self) -> int:
        return self.capacity - len(self.storage)

    def utilization(self) -> float:
        return len(self.storage) / self.capacity if self.capacity else 0.0

    # Data movement primitives

    def push(self, instruction: int) -> bool:
        # Add one instruction; returns False if full
        if self.is_full():
            return False
        self.storage.append(instruction)
        return True

    def pop_front(self) -> int | None:
        # Remove and return the oldest instruction (FIFO)
        return self.storage.pop(0) if self.storage else None

    def peek(self) -> int | None:
        # View the oldest instruction without removing it
        return self.storage[0] if self.storage else None

    def __repr__(self) -> str:
        return (f"{self.name}(cap={self.capacity}, used={len(self.storage)}, "
                f"lat={self.latency}, bw={self.bandwidth})")


# Cache with Replacement Policy

class Cache(MemoryLevel):
    """
    A cache level that supports LRU, FIFO, or Random eviction policies
    Tracks hit / miss statistics
    """

    POLICIES = ("LRU", "FIFO", "RANDOM")

    def __init__(self, name: str, capacity: int, latency: int,
                 bandwidth: int, policy: str = "LRU"):
        super().__init__(name, capacity, latency, bandwidth)
        if policy not in self.POLICIES:
            raise ValueError(f"Unknown policy '{policy}'. Choose from {self.POLICIES}")
        self.policy = policy
        self.hits = 0
        self.misses = 0
        # LRU uses an OrderedDict
        self._lru_map: OrderedDict[int, None] = OrderedDict()
        # FIFO uses a plain deque
        self._fifo_queue: deque[int] = deque()

    # Lookup

    def lookup(self, instruction: int) -> bool:
        # Return True (hit) / False (miss), updates LRU order on hit, caller tracks stats
        if instruction in self.storage:
            if self.policy == "LRU":
                self._lru_map.move_to_end(instruction)
            return True
        return False

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    # Eviction

    def _evict(self) -> int:
        # Remove and return the eviction candidate according to the policy
        if self.policy == "LRU":
            victim, _ = self._lru_map.popitem(last=False)
            if victim in self.storage:
                self.storage.pop(self.storage.index(victim))
            return victim
        elif self.policy == "FIFO":
            victim = self._fifo_queue.popleft()
            if victim in self.storage:
                self.storage.pop(self.storage.index(victim))
            return victim
        else:
            idx = random.randrange(len(self.storage))
            return self.storage.pop(idx)

    # Override push to handle eviction

    def push(self, instruction: int) -> bool:
        if self.is_full():
            self._evict()
        self.storage.append(instruction)
        if self.policy == "LRU":
            self._lru_map[instruction] = None
            self._lru_map.move_to_end(instruction)
        elif self.policy == "FIFO":
            self._fifo_queue.append(instruction)
        return True


# Pending Transfer

class PendingTransfer:
    # Represents an in-flight batch transfer between two adjacent levels

    def __init__(self, src: MemoryLevel, dst: MemoryLevel,
                 instructions: list[int], latency: int):
        self.src = src
        self.dst = dst
        self.instructions = instructions
        self.remaining = latency

    def tick(self) -> bool:
        # Advance by one cycle, returns True when the transfer is complete
        self.remaining -= 1
        return self.remaining <= 0

    def commit(self):
        # Deliver instructions to destination
        for instr in self.instructions:
            self.dst.push(instr)


# Memory Hierarchy Simulator

class MemoryHierarchySimulator:
    """
    Manages a five-level memory hierarchy:
    SSD -> DRAM -> L3 -> L2 -> L1 -> CPU

    The strict hierarchy rule is enforced that data may only move one level
    at a time and cannot skip any level
    """

    def __init__(
        self,
        ssd_size: int = 1024,
        dram_size: int = 512,
        l3_size: int = 128,
        l2_size: int = 64,
        l1_size: int = 16,
        ssd_latency: int = 8,
        dram_latency: int = 4,
        l3_latency: int = 3,
        l2_latency: int = 2,
        l1_latency: int = 1,
        bandwidth: int = 4,
        cache_policy: str = "LRU",
    ):
        # Validate hierarchy sizes
        assert ssd_size > dram_size > l3_size > l2_size > l1_size, (
            "Hierarchy size rule violated: SSD > DRAM > L3 > L2 > L1")

        # Instantiate levels
        self.ssd   = MemoryLevel("SSD",  ssd_size,  ssd_latency,  bandwidth)
        self.dram  = MemoryLevel("DRAM", dram_size, dram_latency, bandwidth)
        self.l3    = Cache("L3", l3_size, l3_latency, bandwidth, cache_policy)
        self.l2    = Cache("L2", l2_size, l2_latency, bandwidth, cache_policy)
        self.l1    = Cache("L1", l1_size, l1_latency, bandwidth, cache_policy)

        # Ordered list used for iteration/display
        self.levels: list[MemoryLevel] = [self.ssd, self.dram, self.l3, self.l2, self.l1]

        # Simulation state
        self.clock: int = 0
        self.cpu_fetched: list[int] = []
        self.write_back_log: list[tuple] = []
        self.pending_transfers: list[PendingTransfer] = []

        # Event log, one line per meaningful event
        self._events: list[str] = []

        # Track total arrivals per level for the data movement summary
        self._arrivals: dict[str, int] = {lvl.name: 0 for lvl in self.levels}

    # Internal event recorder

    def _event(self, msg: str):
        # Appends to event log without printing during the run
        self._events.append(f"[Cycle {self.clock:3d}] {msg}")

    # Configuration Summary

    def print_config(self):
        w = 58
        print("=" * w)
        print("  MEMORY HIERARCHY CONFIGURATION")
        print("=" * w)
        print(f"  {'Level':<7} {'Size (instr)':>13} {'Latency':>10} {'Bandwidth':>12}")
        print("  " + "-" * (w - 2))
        for lvl in self.levels:
            pol = f"  [{lvl.policy}]" if isinstance(lvl, Cache) else ""
            print(f"  {lvl.name:<7} {lvl.capacity:>10} ins"
                  f"  {lvl.latency:>5} cyc"
                  f"  {lvl.bandwidth:>5} ins/cyc{pol}")
        print("=" * w)
        print()

    # SSD Loading

    def load_ssd(self, instructions: list[int]):
        # Populate SSD with a list of 32-bit instruction values
        for instr in instructions:
            if not self.ssd.push(instr & 0xFFFFFFFF):
                break
        print(f"  Loaded {len(self.ssd.storage)} instructions into SSD.\n")

    # Transfer Initiation

    def _initiate_transfer(self, src: MemoryLevel, dst: MemoryLevel):
        # Move up to bandwidth instructions from src to dst, returns None if no data to move
        if src.is_empty():
            return None
        count = min(src.bandwidth, len(src.storage), dst.free_slots())
        if count <= 0:
            return None
        batch = [src.pop_front() for _ in range(count)]
        xfer = PendingTransfer(src, dst, batch, src.latency)
        self.pending_transfers.append(xfer)
        return xfer

    # Clock Tick

    def tick(self):
        # Advance simulation by one clock cycle
        self.clock += 1

        # Advance all pending transfers
        completed = []
        for xfer in self.pending_transfers:
            if xfer.tick():
                xfer.commit()
                completed.append(xfer)
                self._arrivals[xfer.dst.name] += len(xfer.instructions)
                self._event(f"  {len(xfer.instructions)} instr(s) arrived at {xfer.dst.name}"
                            f"  (from {xfer.src.name})")
        for xfer in completed:
            self.pending_transfers.remove(xfer)

        # Propagate data upward through the hierarchy
        pairs = [
            (self.ssd,  self.dram),
            (self.dram, self.l3),
            (self.l3,   self.l2),
            (self.l2,   self.l1),
        ]
        for src, dst in pairs:
            if not src.is_empty() and dst.free_slots() > 0:
                self._initiate_transfer(src, dst)

    # Read Operation

    def read(self, instruction: int) -> str:
        """
        Simulate a CPU fetch of a specific instruction value
        Walks L1 -> L2 -> L3 -> DRAM -> SSD looking for the data
        Returns a string describing where the hit occurred
        """
        caches = [self.l1, self.l2, self.l3]

        # Check caches L1 -> L2 -> L3, on hit in lower cache, promote to L1
        for i, cache in enumerate(caches):
            if cache.lookup(instruction):
                cache.hits += 1
                # Record a miss on all higher-level caches that were checked first
                for j in range(i):
                    caches[j].misses += 1
                result = f"HIT in {cache.name}"
                # Promote to L1 if found in L2 or L3
                if i > 0:
                    if instruction in cache.storage:
                        cache.storage.remove(instruction)
                    if hasattr(cache, '_lru_map') and instruction in cache._lru_map:
                        del cache._lru_map[instruction]
                    try:
                        cache._fifo_queue.remove(instruction)
                    except (AttributeError, ValueError):
                        pass
                    self.l1.push(instruction)
                    result += f"  ->  promoted to L1"
                print(f"  READ  0x{instruction:08X}  ->  {result}")
                self._event(f"READ 0x{instruction:08X} -> {result}")
                self.cpu_fetched.append(instruction)
                return f"HIT:{cache.name}"

        # Full miss across all caches
        for cache in caches:
            cache.misses += 1

        # Check DRAM
        if instruction in self.dram.storage:
            self.dram.storage.remove(instruction)
            self.l1.push(instruction)
            print(f"  READ  0x{instruction:08X}  ->  MISS caches  ->  found in DRAM, loaded to L1")
            self._event(f"READ 0x{instruction:08X} -> MISS caches, found in DRAM -> L1")
            self.cpu_fetched.append(instruction)
            return "HIT:DRAM->L1"

        # Check SSD
        if instruction in self.ssd.storage:
            # Must travel SSD -> DRAM -> L3 -> L2 -> L1 each step one at a time
            self.ssd.storage.remove(instruction)
            self.dram.push(instruction)
            self.l3.push(instruction)
            self.l2.push(instruction)
            self.l1.push(instruction)
            print(f"  READ  0x{instruction:08X}  ->  FULL MISS  ->  pipeline load SSD->DRAM->L3->L2->L1")
            self._event(f"READ 0x{instruction:08X} -> FULL MISS, pipeline load from SSD")
            self.cpu_fetched.append(instruction)
            return "HIT:SSD->pipeline"

        print(f"  READ  0x{instruction:08X}  ->  NOT FOUND in any level")
        self._event(f"READ 0x{instruction:08X} -> NOT FOUND")
        return "MISS"

    # Write Operation

    def write(self, instruction: int, target_level: str = "SSD"):
        # Pushes data from CPU toward a lower memory level, enforces the hierarchy
        level_map = {lvl.name: lvl for lvl in self.levels}
        if target_level not in level_map:
            print(f"  WRITE ERROR: unknown level '{target_level}'")
            return
        level_map[target_level].push(instruction & 0xFFFFFFFF)
        self.write_back_log.append((self.clock, instruction, target_level))
        print(f"  WRITE 0x{instruction:08X}  ->  {target_level}")
        self._event(f"WRITE 0x{instruction:08X} -> {target_level}")

    # Run N cycles

    def run(self, cycles: int):
        # Advance the simulation by cycles clock cycles
        start = self.clock
        for _ in range(cycles):
            self.tick()
        print(f"  Ran cycles {start+1}-{self.clock}  "
              f"(pending transfers remaining: {len(self.pending_transfers)})")

    # Final State Report

    def print_state(self):
        w = 58
        print()
        print("=" * w)
        print("  FINAL STATE OF EACH MEMORY LEVEL")
        print("=" * w)
        for lvl in self.levels:
            used = len(lvl.storage)
            pct  = lvl.utilization() * 100
            bar_len = int(pct / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"  {lvl.name:<5} [{bar}] {used:>5}/{lvl.capacity} ({pct:5.1f}%)")
            if isinstance(lvl, Cache):
                print(f"        Hits={lvl.hits}  Misses={lvl.misses}  "
                      f"Hit-rate={lvl.hit_rate*100:.1f}%  Policy={lvl.policy}")
        print("-" * w)
        print(f"  CPU fetched : {len(self.cpu_fetched)} instruction(s)")
        if self.cpu_fetched:
            sample = ", ".join(f"0x{v:08X}" for v in self.cpu_fetched[:6])
            suffix = "..." if len(self.cpu_fetched) > 6 else ""
            print(f"               {sample}{suffix}")
        print(f"  Clock       : cycle {self.clock}")
        print("=" * w)

    # Instruction Access Trace

    def print_trace(self):
        w = 58
        print()
        print("=" * w)
        print("  EVENT LOG (arrivals + read/write operations only)")
        print("=" * w)
        for entry in self._events:
            print(entry)
        print("=" * w)
        # Data movement summary table
        print()
        print("  DATA MOVEMENT SUMMARY")
        print("  " + "-" * 40)
        print(f"  {'Level':<8} {'Instructions Received':>22}")
        print("  " + "-" * 40)
        for lvl in self.levels:
            if lvl.name != "SSD":
                print(f"  {lvl.name:<8} {self._arrivals[lvl.name]:>18} instr(s)")
        print("  " + "-" * 40)
