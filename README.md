# Memory Hierarchy Simulator
## CSC 4210 Computer Architecture – Spring 2026 
## Processor Design Semester Project - Task 3

## Overview
This project is a **Memory Hierarchy Simulator**

It simulates how instructions move through a multi-level memory system:

**SSD -> DRAM -> L3 -> L2 -> L1 -> CPU**

The simulator models:
- Data movement between memory levels
- Cache hit/miss behavior
- Different cache replacement policies
- Latency and bandwidth constraints

---

## Features
- Five-level memory hierarchy simulation
- Configurable:
  - Memory sizes
  - Latencies
  - Bandwidth
- Cache replacement policies:
  - LRU (Least Recently Used)
  - FIFO (First-In First-Out)
  - RANDOM
- Instruction read/write simulation
- Clock-cycle based execution
- Detailed:
  - Event logs
  - Hit/miss statistics
  - Final memory state visualization

---

## File Structure
```
.
├── main.py
├── memory_hierarchy.py
└── README.md
```

---

## How It Works

### Memory Levels
Each level has:
- Capacity (number of instructions)
- Latency (cycles per transfer)
- Bandwidth (instructions per cycle)

### Data Movement Rules
- Data moves **one level at a time**
- No skipping levels
- Transfers are subject to:
  - Latency
  - Bandwidth limits

### Cache Behavior
- Lookup order: **L1 → L2 → L3**
- On hit:
  - Data may be promoted to L1
- On miss:
  - System searches DRAM, then SSD
  - Full miss triggers pipeline load through all levels

---

## Running the Program

### Execute
```bash
python main.py
```

---

## Demo Modes

### 1. Basic Simulation (`demo_basic`)
- Uses LRU policy
- Loads 200 random instructions
- Demonstrates:
  - Cache hits and misses
  - Promotion between levels
  - Write-back operations

### 2. FIFO Policy (`demo_fifo`)
- Demonstrates FIFO cache replacement behavior

### 3. Random Policy (`demo_random_policy`)
- Demonstrates RANDOM cache replacement behavior

---

## Example Output
- Memory configuration table
- Read/write operation logs
- Cache hit/miss statistics
- Final utilization of each memory level
- Event trace of all operations

---

## Key Classes

### `MemoryLevel`
Represents a generic memory level:
- Storage management
- Capacity tracking
- Data movement primitives

### `Cache (inherits MemoryLevel)`
Adds:
- Replacement policies (LRU, FIFO, RANDOM)
- Hit/miss tracking

### `PendingTransfer`
Represents in-flight data transfers between levels.

### `MemoryHierarchySimulator`
Main controller:
- Manages all memory levels
- Simulates clock cycles
- Handles reads/writes
- Tracks system state and statistics

---

## Concepts Demonstrated
- Cache hierarchy design
- Memory latency vs bandwidth trade-offs
- Cache replacement strategies
- Pipeline data movement
- Performance metrics (hit rate, utilization)

---

## Notes
- All instructions are treated as **32-bit integers**
- Simulation is deterministic when using fixed random seeds
