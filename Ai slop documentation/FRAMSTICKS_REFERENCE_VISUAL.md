# FramsticksLibCompetition Reference & Visual Guide

Complete technical reference with diagrams and examples.

---

## 🏗️ Class Hierarchy

```
Native Framsticks Simulator
            ↓
     FramsticksLib
     (Basic interface)
            ↓
FramsticksLibCompetition
(Competition wrapper with limits)
            ↓
Your Algorithm
(Uses it like FramsticksLib)
```

### What Each Layer Does

| Layer | Responsibility | You Control |
|-------|---|---|
| **Framsticks Simulator** | Physics, creature morphology, COG tracking | ❌ No (black box) |
| **FramsticksLib** | Python bindings, mutation, crossover | ❌ No (read-only) |
| **FramsticksLibCompetition** | Limits, tracking, results saving | ✅ Config only (COMPETITOR_ID, etc) |
| **Your Algorithm** | Optimization strategy, population management | ✅ Yes (full control) |

---

## 📊 Data Flow Diagram

```
┌─────────────────────────┐
│  Your Algorithm         │
│  (Evolutionary Loop)    │
└────────────┬────────────┘
             │
             │ genotypes = ['llll', 'lll{||}', ...]
             ↓
┌─────────────────────────────────────────────┐
│ frams_lib.evaluate(genotypes)               │
│ (FramsticksLibCompetition)                  │
└────────┬──────────────────────────────┬─────┘
         │                              │
         │ Checks                       │
         ├─→ evaluation_count > 100k?   │
         ├─→ time > 3600s?              │
         │ If yes: call end() & exit    │
         │                              │
         │ Otherwise: proceed           │
         ↓                              │
    ┌────────────────────────────────┐ │
    │ For each genotype:             │ │
    │  - Time evaluation            │ │
    │  - Call Framsticks simulator  │ │
    │  - Extract COG path           │ │
    │  - Compute fitness (TEST_FN)  │ │
    │  - Track best_fitness         │ │
    └────────────────────────────────┘ │
         │                              │
         ↓                              │
    fitnesses = [25.5, 31.2, None, 28.0, ...]
             │                              │
             └──────────────────┬───────────┘
                                ↓
                  Your Algorithm processes
                  fitness values, selects
                  parents, creates offspring
```

---

## 🎯 Fitness Computation Pipeline

```
Input: genotype string (e.g., "llllllll")
         ↓
    ╔═════════════════════════════════════╗
    ║ Framsticks Simulator                ║
    ║ - Parse genotype                    ║
    ║ - Create 3D creature morphology     ║
    ║ - Place in world with given physics ║
    ║ - Simulate for specified lifespan   ║
    ║ - Record COG (x,y,z) at each step   ║
    ╚═════════════════════════════════════╝
         ↓
    COG path = [
        [0.0,  0.0,  0.0],     # step 0: creature birth
        [0.1, -0.05, 0.02],    # step 1
        [0.2, -0.08, 0.05],    # step 2
        ...                    # step N-1
        [2.5,  1.3,  0.8]      # step N: creature death
    ]
         ↓
    ╔═════════════════════════════════════╗
    ║ _evaluate_path(path)                ║
    ║ Compute fitness based on TEST_FN:   ║
    ║                                     ║
    ║ if TEST_FUNCTION == 3:              ║
    ║   distance from birth to death      ║
    ║   fitness = norm(path[0] - path[-1])║
    ║                                     ║
    ║ if TEST_FUNCTION == 4:              ║
    ║   distance × height                 ║
    ║   d = norm(path[0] - path[-1])      ║
    ║   h = mean(max(0, path[:, 2]))      ║
    ║   fitness = d * h                   ║
    ║                                     ║
    ║ if TEST_FUNCTION == 5:              ║
    ║   z follows linear pattern          ║
    ║   expected_z = linspace(0,10,...)   ║
    ║   rmse = norm(...) / sqrt(len(...)) ║
    ║   fitness = 1000 - rmse             ║
    ╚═════════════════════════════════════╝
         ↓
    Output: fitness (float) or None
```

---

## 🔄 Class Structure Detail

### Initialization

```python
# How FramsticksLibCompetition is created:
from FramsticksLibCompetition import FramsticksLibCompetition

frams_lib = FramsticksLibCompetition(
    path_to_framsticks_library,
    sim_template_name = "eval-allcriteria.sim"
)

# After init, the object has:
# ✅ Connection to Framsticks simulator
# ✅ Internal evaluation counter = 0
# ✅ Internal timer started
# ✅ Best fitness = None
# ✅ Best solution = None
```

### Configuration Attributes

```python
class FramsticksLibCompetition:
    # ┌─ IDENTITY ─────────────────────────────────┐
    COMPETITOR_ID = 'AliceTeam'
    # └────────────────────────────────────────────┘
    # Used in results filename: base64_encode('AliceTeam') = 'QWxpY2VUZWF=' 
    # Final filename: QWxpY2VUZWF=.results
    
    # ┌─ FITNESS FORMAT ────────────────────────────┐
    SIMPLE_FITNESS_FORMAT = True  # or False
    FITNESS_DICT_KEY = 'COGpath'
    # └────────────────────────────────────────────┘
    # SIMPLE_FITNESS_FORMAT = True:
    #   evaluate() returns [25.5, 31.2, None, ...]
    #
    # SIMPLE_FITNESS_FORMAT = False:
    #   evaluate() returns [
    #       {
    #           'num': 0,
    #           'name': 'Creature 0',
    #           'evaluations': {
    #               '': {
    #                   'COGpath': 25.5,
    #                   'numparts': 3,
    #                   'numjoints': 2,
    #                   'numneurons': 0,
    #                   'numconnections': 0
    #               }
    #           }
    #       },
    #       ...
    #   ]
    
    # ┌─ TEST FUNCTION ─────────────────────────────┐
    TEST_FUNCTION = 3  # 3, 4, or 5
    # └────────────────────────────────────────────┘
    # TEST_FUNCTION defines which fitness metric
    # Used in _evaluate_path() method
    
    # ┌─ RESOURCE LIMITS ──────────────────────────┐
    MAX_EVALUATIONS = 100_000
    MAX_TIME = 60 * 60 * 1  # 3600 seconds
    # └────────────────────────────────────────────┘
    # Checked after each evaluate() call
    # If exceeded, automatically calls end()
    
    # ┌─ INTERNAL STATE (READ-ONLY) ────────────────┐
    _best_fitness = None              # Best seen so far
    _best_solution = None             # Genotype of best
    _evaluation_count = 0             # Total evaluations
    _evaluation_time = 0              # Seconds spent in sim
    _time0 = perf_counter()           # Start time
    # └────────────────────────────────────────────┘
```

---

## 📞 Methods Reference

### evaluate(genotype_list: List[str])

```python
# SIGNATURE
evaluate(genotype_list: List[str]) → List[Union[float, dict, None]]

# BEHAVIOR
genotypes = [
    'llllllll',          # Valid f0 genotype
    'lll{||}lll',        # f0 with neurons
    'invalid__genotype',  # Invalid (will return None)
    'p(Rq)q(C:2)',       # f1 format
]

fitnesses = frams_lib.evaluate(genotypes)

# RETURN (if SIMPLE_FITNESS_FORMAT = True):
# [25.5, 31.2, None, 28.9]
#            ↑ Invalid genotype → None
#
# RETURN (if SIMPLE_FITNESS_FORMAT = False):
# [{
#     'num': 0,
#     'name': 'Creature0',
#     'evaluations': {
#         '': {
#             'COGpath': 25.5,
#             'numparts': 3,
#             ...
#         }
#     }
# }, ... ]

# CHECKS PERFORMED BEFORE RETURNING:
# if self._evaluation_count > self.MAX_EVALUATIONS:
#     self.end()  # Automatic termination!
#
# if (perf_counter() - self._time0 - self._evaluation_time) > self.MAX_TIME:
#     self.end()  # Automatic termination!

# TIMING:
# eval_time0 = perf_counter()
# [evaluate each genotype]
# self._evaluation_time += perf_counter() - eval_time0
# The time spent here is EXCLUDED from the 1-hour limit
```

### mutate(genotype_list: List[str])

```python
# INHERITED FROM FramsticksLib

mutate(genotype_list) → List[str]

genotypes = ['llllllll', 'lll{||}lll']
mutated = frams_lib.mutate(genotypes)
# Returns: ['lllpllll', 'lll{|[]}lll']
#          (random changes applied)

# Does NOT use evaluation budget
# Used to create variation
```

### crossOver(geno1: str, geno2: str)

```python
# INHERITED FROM FramsticksLib

crossOver(geno1, geno2) → str

parent1 = 'llllllll'
parent2 = 'lll{||}lll'
offspring = frams_lib.crossOver(parent1, parent2)
# Returns: 'llll{||}lll' (mixed from both)

# Does NOT use evaluation budget
# Used to create variation
```

### getSimplest(genetic_format: str)

```python
# INHERITED FROM FramsticksLib

getSimplest(genetic_format) → str

# Get simplest creature in f0 format:
simple_f0 = frams_lib.getSimplest('0')
# Returns: 'llllllll' (linear chain)

# Get simplest creature in f1 format:
simple_f1 = frams_lib.getSimplest('1')
# Returns: 'p' (single part)

# Does NOT use evaluation budget
# Used for population initialization
```

### end()

```python
# UNIQUE TO FramsticksLibCompetition

end() → None (exits program)

# EFFECTS:
# 1. Print best solution found
# 2. Prepare results data:
#    - Timestamp
#    - Team name
#    - Test function ID
#    - Evaluation count
#    - Wall-clock time
#    - Runtime (excluding eval time)
#    - Best fitness
#    - Best genotype
# 3. Write to file: <base64_team_id>.results
# 4. Print filename and team name
# 5. Call sys.exit() → PROGRAM TERMINATES

# EXAMPLE OUTPUT:
# Finishing... best solution = 42.7
# 2026-05-04 14:30	myteam	3	87234	3599.2	3598.1	42.7	llllllll[...]
# Saved 'QWxpY2VUZWF=.results' (myteam)

# CRITICAL: You MUST call this!
# If not called:
#   ✗ Results won't be saved
#   ✗ Competition won't receive your solution
#   ✗ Algorithm won't officially complete
```

---

## 🎯 Typical Usage Pattern

```python
from FramsticksLibCompetition import FramsticksLibCompetition
import sys

# PHASE 1: INITIALIZATION
frams_lib = FramsticksLibCompetition(framsticks_path)

# Create initial population
population = [
    frams_lib.getSimplest('0') 
    for _ in range(population_size)
]

best_fitness = None
best_genotype = None

# PHASE 2: MAIN LOOP
for generation in range(max_generations):
    # Evaluate population
    # (THIS uses evaluation budget!)
    fitnesses = frams_lib.evaluate(population)
    
    # Track best
    for genotype, fitness in zip(population, fitnesses):
        if fitness is not None:  # Valid solution
            if best_fitness is None or fitness > best_fitness:
                best_fitness = fitness
                best_genotype = genotype
                print(f"New best: {best_fitness}")
    
    # Create next generation
    offspring = []
    for i in range(population_size):
        # Variety through mutation/crossover
        # (These DON'T use evaluation budget)
        if random() < mutation_rate:
            parent = population[best_index]
            child = frams_lib.mutate([parent])[0]
        else:
            parent1 = population[select()]
            parent2 = population[select()]
            child = frams_lib.crossOver(parent1, parent2)
        offspring.append(child)
    
    population = offspring
    
    # Check if auto-stop happened
    # (FramsticksLibCompetition calls end() automatically if limits exceeded)

# PHASE 3: FINALIZATION
# When you're done (or limits force you out):
try:
    frams_lib.end()  # Save results, exit
except SystemExit:
    pass  # end() calls sys.exit()
```

---

## 🔍 Example Runs

### Example 1: Simple Population

```python
population = ['llllllll', 'lll{||}lll', 'llllpllll']
fitnesses = frams_lib.evaluate(population)

print(fitnesses)
# Output: [25.5, 31.2, 28.9]
#
# Interpretation:
# - First creature: fitness = 25.5
# - Second creature: fitness = 31.2 (best)
# - Third creature: fitness = 28.9
```

### Example 2: Invalid Genotypes

```python
population = ['llllllll', 'invalid_', 'lll{||}lll']
fitnesses = frams_lib.evaluate(population)

print(fitnesses)
# Output: [25.5, None, 31.2]
#                ↑ Invalid syntax, failed evaluation
#
# Handling in algorithm:
for genotype, fitness in zip(population, fitnesses):
    if fitness is not None:
        update_best(genotype, fitness)
    # else: skip invalid solution
```

### Example 3: With Mutation

```python
best_genotype = 'llllllll'

# Mutate to create variation
children = []
for _ in range(10):
    child = frams_lib.mutate([best_genotype])[0]
    children.append(child)

# Evaluate children
fitnesses = frams_lib.evaluate(children)
# [28.3, 29.1, 27.5, 30.2, ...]

# This might produce better solutions
# Because we started from a good parent
```

### Example 4: Crossover

```python
parent1 = 'llllllll'
parent2 = 'lll{||}lll'

# Create offspring through crossover
offspring1 = frams_lib.crossOver(parent1, parent2)
offspring2 = frams_lib.crossOver(parent1, parent2)

print(offspring1)  # 'll{||}lll' (mixed)
print(offspring2)  # 'llll{||}ll' (different mix)

# Evaluate them
fitnesses = frams_lib.evaluate([offspring1, offspring2])
```

---

## ⏱️ Time Accounting

```
Total Wall Clock Time
    ↓
┌───────────────────────────────────────┐
│ Evaluation Time                       │ ← Excluded from limit
│ (Framsticks simulation running)       │   1 hour ≠ algorithm overhead
│ frams_lib.evaluate() is executing     │   
│ Simulator is busy                     │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ Algorithm Time (< 1 hour limit)       │ ← Counted against limit
│ ✓ Population initialization           │   
│ ✓ Parent selection                    │
│ ✓ Mutation/crossover operations       │
│ ✓ Fitness tracking                    │
│ ✓ Any other Python code you write     │
└───────────────────────────────────────┘

# Time check in code:
total_running_time = perf_counter() - self._time0  # Full time
reported_time = total_running_time - self._evaluation_time  # Used for limit

# Algorithm gets 1 hour of "thinking time" while Framsticks works
```

---

## 📈 Evaluation Budget Breakdown

Assuming 100,000 evaluations total:

```
Scenario 1: Small population
population_size = 10
generations = 10,000
total_evals = 10 × 10,000 = 100,000
More generations, simpler algorithm

Scenario 2: Medium population
population_size = 50
generations = 2,000
total_evals = 50 × 2,000 = 100,000
Balanced approach

Scenario 3: Large population
population_size = 200
generations = 500
total_evals = 200 × 500 = 100,000
Fewer generations, high diversity per gen

Scenario 4: Adaptive
gen_1-100: pop=100 (10k evals)
gen_101-500: pop=50 (20k evals)
gen_501-1000: pop=20 (10k evals)
reserve: 60k for adaptation
```

---

## 🐞 Common Mistakes

### ❌ Mistake 1: Forgetting to call end()
```python
# WRONG:
best_fitness = 42.7
print(f"Done! Best: {best_fitness}")
# No call to end()
# Results NOT saved
# Competition doesn't get submission

# RIGHT:
best_fitness = 42.7
print(f"Done! Best: {best_fitness}")
frams_lib.end()  # Saves and exits
```

### ❌ Mistake 2: Ignoring None values
```python
# WRONG:
fitnesses = frams_lib.evaluate(population)
best = max(fitnesses)  # Crash if any None values!

# RIGHT:
fitnesses = frams_lib.evaluate(population)
valid_fitnesses = [f for f in fitnesses if f is not None]
best = max(valid_fitnesses) if valid_fitnesses else 0
```

### ❌ Mistake 3: Too many evaluations at once
```python
# WRONG:
# Evaluate entire population of 10,000
fitnesses = frams_lib.evaluate(very_large_population)
# Might blow memory or exceed limits

# RIGHT:
# Evaluate in batches
batch_size = 100
fitnesses = []
for i in range(0, len(population), batch_size):
    batch = population[i:i+batch_size]
    fitnesses.extend(frams_lib.evaluate(batch))
```

### ❌ Mistake 4: Not handling time limit
```python
# WRONG:
for generation in range(10000):  # Infinite loop potential
    fitnesses = frams_lib.evaluate(population)
    # Algorithm continues indefinitely

# RIGHT:
# Let FramsticksLibCompetition handle limit
# It calls end() automatically when limit exceeded
# Your code doesn't need to check explicitly
```

---

## ✨ Best Practices

### ✅ Practice 1: Log Progress
```python
for generation in range(max_generations):
    fitnesses = frams_lib.evaluate(population)
    valid_count = sum(1 for f in fitnesses if f is not None)
    
    if (generation + 1) % 10 == 0:
        print(f"Gen {generation+1}: "
              f"valid={valid_count}/{len(population)}, "
              f"best={best_fitness:.2f}")
```

### ✅ Practice 2: Handle Graceful Termination
```python
try:
    run_evolution()
finally:
    try:
        frams_lib.end()
    except SystemExit:
        pass  # end() exits, catch it here
```

### ✅ Practice 3: Validate Genotypes
```python
# Before evaluating, check basic validity
def is_valid_genotype(genotype):
    return isinstance(genotype, str) and len(genotype) > 0

population = [g for g in population if is_valid_genotype(g)]
fitnesses = frams_lib.evaluate(population)
```

### ✅ Practice 4: Batch Evaluate
```python
# Evaluate in reasonable batches
batch_size = 100
for i in range(0, len(population), batch_size):
    batch = population[i:i+batch_size]
    fitnesses[i:i+batch_size] = frams_lib.evaluate(batch)
    # Check progress between batches if desired
```

---

## 🎓 Learning Path

1. **Start**: Read `IMPLEMENTATION_QUICK_START.md`
2. **Understand**: Study this reference document
3. **Code**: Implement basic algorithm
4. **Test**: Run with `TEST_FUNCTION = 3`
5. **Extend**: Add advanced techniques
6. **Optimize**: Improve parameters
7. **Submit**: Package and send

---

## 📞 When to Use What

| Question | Answer |
|----------|--------|
| How do I get a simple creature? | `getSimplest('0')` |
| How do I mutate? | `mutate(genotypes)` |
| How do I crossover? | `crossOver(geno1, geno2)` |
| How do I evaluate? | `evaluate(genotypes)` |
| How do I save results? | Call `end()` |
| How do I start over? | Can't restart `FramsticksLibCompetition` instance |
| What if fitness is None? | Genotype was invalid, skip it |
| What if time runs out? | `end()` is called automatically |
| What if evaluations exceed 100k? | `end()` is called automatically |

---

## 🔗 File Organization Reference

```
Your Algorithm Directory
├── my_algorithm.py         # Main entry point
├── FramsticksLibCompetition.py  # (Copy from framspy)
├── requirements.txt        # pip packages
└── README.txt             # Setup instructions

When run:
python my_algorithm.py -path C:\Framsticks

Output generated:
QWxpY2VUZWF=.results       # Results (base64_team_name + ".results")
```

Good luck with your competition entry! 🚀
