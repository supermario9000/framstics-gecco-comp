# GECCO Competition: Optimizing 3D Simulated Agents

SouperTeam submission for the Framsticks-based evolutionary optimization competition.

---

## 📋 Table of Contents
- [Competition Overview](#competition-overview)
- [Core Task](#core-task)
- [Evaluation Criteria](#evaluation-criteria)
- [Repository Structure](#repository-structure)
- [Algorithm Constraints](#algorithm-constraints)
- [Competition Settings](#competition-settings)
- [Technical Reference](#technical-reference)
- [Submission Requirements](#submission-requirements)

---

## 🎯 Competition Overview

This competition focuses on developing an efficient optimization algorithm to evolve 3D simulated agents (robots) in the **Framsticks simulator**. Participants must implement a Python-based search algorithm that discovers agents whose center of gravity (COG) follows desired movement patterns.

### Key Facts
- **Environment**: Framsticks simulator with Python binding
- **Encoding**: f0 or f1 genetic encodings (or custom variants)
- **Optimization**: 10 different world configurations × 20 repeated runs each
- **Deadline**: June 15, 2026
- **Winner Criterion**: Highest average normalized fitness across all 10 settings (must exceed baseline)

---

## 🤖 Core Task

### What You're Optimizing
- **Goal**: Design agents whose **center of gravity (COG) trajectory** matches a desired path or behavior
- **Desired Movements** (examples):
  - Following a specific 3D path (straight line, curve, etc.)
  - Swinging or jumping motion
  - Climbing (vertical movement following a function)
  - Custom patterns defined by hidden fitness functions

### Test Functions (Examples)
The actual fitness functions are unknown but will evaluate COG movement similarity. Examples:

| Test | Fitness Function | Interpretation |
|------|------------------|-----------------|
| **TEST_FUNCTION = 3** | `distance(COG_birth, COG_death)` | Maximize straight-line distance traveled |
| **TEST_FUNCTION = 4** | `distance × avg_height` | Travel far AND stay high above ground |
| **TEST_FUNCTION = 5** | `1000 - RMSE(z_coordinate, linear_function)` | z-coordinate should grow linearly during lifespan |

---

## 📊 Evaluation Criteria

### Scoring Pipeline
1. **Run Algorithm** in each of 10 settings
2. **Record best fitness** from each run (20 runs per setting)
3. **Average** the 20 best fitness values per setting
4. **Normalize** the average using all submissions in that setting
5. **Final Score** = Average of 10 normalized values

### Normalization
- Each submission's score in a setting is normalized relative to other submissions
- This ensures fair comparison despite varying fitness scales across different test functions

### Baseline Comparison
- A baseline algorithm (previous year's winner) is run under identical conditions
- **Success**: Submit a score that exceeds the baseline
- **No winner announced** if best submission ≤ baseline

---

## 📂 Repository Structure

```
framstics-gecco-comp/
├── README.md                          # This file
├── FramsticksEvolution.py             # Example algorithm (DEAP-based)
├── FramsticksLibCompetition.py        # [NOT in repo] Competition wrapper class
│                                       # Must be downloaded from official source
└── [Your Algorithm Here]              # Your custom optimization algorithm
```

### What You Need to Implement
You must create an optimization algorithm that:
1. Uses `FramsticksLibCompetition` class (not plain `FramsticksLib`)
2. Represents solutions using **f0/f1 encodings** or custom variants
3. Respects **constraints** on genotype complexity
4. Returns **best fitness found** when time/evaluations exceed
5. **Calls `.end()`** when algorithm completes gracefully

---

## ⚙️ Algorithm Constraints

### Resource Limits (Hard Stops)
| Constraint | Limit | Notes |
|-----------|-------|-------|
| **Evaluations** | 100,000 | Function calls must not exceed this |
| **Runtime** | 1 hour | Excluding evaluation time (wall clock) |
| **Memory** | 2 GB | Single process limit |
| **Threading** | Single-threaded | No GPU, no parallelization |

### World Configuration Constraints (Variable Per Setting)
These are **checked dynamically** and may penalize or reject solutions:

| Metric | Variable | Example Constraint |
|--------|----------|-------------------|
| Genotype Length | `numgenocharacters` | ≤ 3000 characters |
| Body Parts | `numparts` | ≤ 50 parts |
| Joints | `numjoints` | ≤ 100 joints |
| Neurons | `numneurons` | ≤ 1000 neurons |
| Connections | `numconnections` | ≤ 30 connections |

### Stopping Conditions (Algorithm Terminates When)
1. ✅ Evaluation count > 100,000
2. ✅ Wall-clock time > 1 hour (excluding eval time)
3. ✅ Algorithm calls `end()` method
4. ✅ Unhandled Python exception
5. ✅ Memory exceeds 2 GB

---

## 🌍 Competition Settings

### Variable World Configurations
Each of the **10 settings** may modify:

| Parameter | Purpose | Competition Impact |
|-----------|---------|-------------------|
| **Lifespan** | Starting energy, idle metabolism | Affects evolution speed |
| **World Size** | Map dimensions | Scale of movement |
| **Heightfield** | Terrain topology | Movement difficulty |
| **Water Level** | Buoyancy effects | Physics simulation |
| **Gravity** | Acceleration (0-9.8+ m/s²) | Movement constraints |
| **Stabilization Period** | Settling time before eval | Creature initialization |
| **Body Constraints** | Min/max joint lengths | Morphology restrictions |

### Unknown Factors
- ❌ Exact fitness functions (hidden)
- ❌ Specific world parameters for each setting
- ❌ Terrain details
- ❌ Desired movement patterns

---

## 🔧 Technical Reference

### FramsticksLibCompetition Class

This is your **interface to the competition**. Key methods and attributes:

```python
class FramsticksLibCompetition:
    # Configuration (Edit these)
    COMPETITOR_ID = 'AliceTeam'  # Your team name
    SIMPLE_FITNESS_FORMAT = True # True → returns float; False → dict structure
    FITNESS_DICT_KEY = 'COGpath' # Key name when SIMPLE_FITNESS_FORMAT = False
    TEST_FUNCTION = 3             # Which test function (3, 4, or 5)
    
    # Don't exceed these
    MAX_EVALUATIONS = 100_000     # Hard limit
    MAX_TIME = 60 * 60 * 1        # 1 hour in seconds
    
    # Methods
    evaluate(genotype_list)        # Evaluate multiple solutions at once
                                    # Returns: list of fitness values (float or dict)
                                    #          or None for invalid genotypes
    
    end()                          # Call this when your algorithm finishes
                                    # Saves results and exits program
```

### Inheritance Hierarchy
```
FramsticksLibCompetition
    ↓ (extends)
FramsticksLib
    ↓ (extends)
(Framsticks native simulator bindings)
```

### What Gets Recorded
```python
# Per run:
- Best fitness discovered
- Evaluation count
- Wall-clock time (excluding eval time)
- Winning genotype

# Saved to: <base64_team_id>.results
```

### Genetic Encoding Formats

#### f0 Encoding (Simplest)
```
llllllllllllll     # Simple linear creature
lll{||}lll        # With neurons: {||}
lll(W:0.5)lll     # With weights: (W:value)
```
- Recommended for quick evolution
- Limited morphological complexity

#### f1 Encoding (Complex)
```
p(Rq)q(C:2)       # Parts with properties
p(As:-2.2)        # Joint angles and strengths
jjj(D:1.5)        # Multiple joints with details
```
- More expressiveness
- Larger search space
- Requires sophisticated search algorithms

---

## 📋 Submission Requirements

### Deadline: June 15, 2026

### Required Files (zipped)
```
submission.zip
├── algorithm.py              # Your main algorithm implementation
├── README.txt                # Installation & execution instructions
├── requirements.txt          # Python dependencies (pip format)
├── algorithm_description.md  # 1-2 page concise description
└── [supporting files]        # Any additional modules/data
```

### Submission Checklist
- [ ] Algorithm uses `FramsticksLibCompetition` class
- [ ] Implements original search strategy (not just DEAP example)
- [ ] Respects all constraints (time, evaluations, memory)
- [ ] Calls `.end()` when finished
- [ ] Works in clean environment (no dev dependencies)
- [ ] README includes installation steps
- [ ] requirements.txt lists all packages
- [ ] Algorithm description explains approach

### Send to
📧 `maciej.komosinski@cs.put.poznan.pl`

### Include in Email
1. Zipped algorithm source code
2. User/team/algorithm name
3. Concise algorithm description
4. Installation & execution instructions
5. Team member names and affiliations
6. Interest in GECCO certificate (if applicable)
7. Consent to publish names (if classified)
8. Consent to publish/reuse algorithm code

---

## 🚀 Getting Started

### Step 1: Environment Setup
```bash
# Download Framsticks simulator
# Download framspy (Python interface)
# Install DEAP and dependencies
pip install deap numpy

# Copy .sim files to Framsticks data/ directory
# Verify setup
python frams-test.py <path-to-frams-objects-library>
```

### Step 2: Understand the Interface
- Study `FramsticksLibCompetition.py`
- Understand `evaluate()` return format
- Test with `TEST_FUNCTION = 3` first (simplest)

### Step 3: Implement Your Algorithm
- Use f0/f1 encodings with mutation/crossover
- Implement selection strategy
- Track best fitness internally
- Handle constraint violations

### Step 4: Test Locally
```bash
# Test with FramsticksLibCompetition
python your_algorithm.py -path <frams-lib-path> -sim "eval-allcriteria.sim" -generations 20

# Verify:
# - Respects time/evaluation limits
# - Produces valid output file
# - Works in clean environment
```

### Step 5: Submit
- Package files as specified
- Test in clean VM/environment
- Send before deadline

---

## 📚 References

### Official Resources
- [Competition Website](https://www.framsticks.com/gecco-competition)
- Framsticks Tutorial (parts 1-5 for introduction)
- Contact: support@framsticks.com

### Previous Results
- 2024 competition results: `experiments-automated-design-competition-2024.pdf`
- 2025 competition results: `experiments-automated-design-competition-2025.pdf`

### Related Files
- `FramsticksEvolution.py` - Example DEAP-based algorithm
- `FramsticksLib.py` - Base simulator interface
- `*.sim` files - World configuration templates

---

## ❓ FAQ

**Q: Can I modify fitness function weights?**  
A: Yes, mutation and crossover probabilities can be adjusted. The actual fitness function is unknown but examples are provided.

**Q: What if my algorithm finds invalid genotypes?**  
A: Return `None` (or special value) for invalid solutions. Constraints are checked automatically by the simulator.

**Q: Can I use parallel processing?**  
A: No. Single-process, single-threaded only.

**Q: How do I know if I'll exceed the time limit?**  
A: `FramsticksLibCompetition` tracks this and calls `end()` automatically if limits are exceeded.

**Q: Can I submit multiple times?**  
A: No. One submission per participant/team only.

**Q: What counts as "runtime"?**  
A: Wall-clock time minus evaluation time (Framsticks sim time is excluded).

---

## 📝 Notes

- Start with `TEST_FUNCTION = 3` (simplest test case)
- The actual competition uses hidden fitness functions
- Previous winners used specialized evolutionary strategies
- Baseline performance is available for reference
- All code is evaluated in controlled environment (no internet)

