# FramsticksLibCompetition Technical Analysis

**Purpose**: This document explains exactly what `FramsticksLibCompetition` expects from your algorithm and how to use it correctly.

---

## 📌 Quick Summary

`FramsticksLibCompetition` is a **wrapper around FramsticksLib** that:
- ✅ Enforces evaluation/time limits
- ✅ Tracks best solution found
- ✅ Records results automatically
- ✅ Provides simple fitness values
- ✅ Handles competition-specific scoring

You interact with it **exactly like FramsticksLib**, but with constraints.

---

## 🔍 Class Structure

### Class Attributes (Configuration)

```python
class FramsticksLibCompetition:
    # Team Configuration
    COMPETITOR_ID = 'AliceTeam'  # Your team name (alphanumeric becomes filename)
    
    # Fitness Format
    SIMPLE_FITNESS_FORMAT = True  # IMPORTANT: True = float, False = dict structure
    FITNESS_DICT_KEY = 'COGpath'  # Only used if SIMPLE_FITNESS_FORMAT = False
    
    # Test Function Selection (3, 4, or 5)
    TEST_FUNCTION = 3             # Which test to run
    
    # Resource Limits (Hard Constraints)
    MAX_EVALUATIONS = 100_000      # Stop after this many evaluate() calls
    MAX_TIME = 60 * 60 * 1         # 1 hour = 3600 seconds (excludes eval time)
    
    # Internal State (Read-Only)
    _best_fitness = None           # Best fitness found so far
    _best_solution = None          # Genotype of best solution
    _evaluation_count = 0          # Number of evaluations performed
    _evaluation_time = 0           # Cumulative time spent in evaluate()
    _time0 = perf_counter()        # Start time of algorithm
```

### Inherited Methods (from FramsticksLib)

```python
# These methods are inherited and work the same as FramsticksLib:

evaluate(genotype_list: List[str]) -> List
    """Evaluate one or more genotypes"""
    # YOUR USAGE:
    # genotypes = ['llllllll', 'lll{||}lll', ...]
    # results = frams_lib.evaluate(genotypes)
    # returns: list of fitness values (depends on SIMPLE_FITNESS_FORMAT)

mutate(genotype_list: List[str]) -> List[str]
    """Mutate genotypes"""
    # YOUR USAGE:
    # new_genotypes = frams_lib.mutate(genotypes)
    # returns: mutated versions

crossOver(geno1: str, geno2: str) -> str
    """Cross over two genotypes"""
    # YOUR USAGE:
    # offspring = frams_lib.crossOver(parent1, parent2)
    # returns: single offspring

getSimplest(genetic_format: str) -> str
    """Get simplest possible genotype"""
    # YOUR USAGE:
    # simple = frams_lib.getSimplest('0')  # f0 format
    # OR
    # simple = frams_lib.getSimplest('1')  # f1 format
    # returns: 'llllllll' or equivalent
```

### Unique Methods

```python
end()
    """Finalize algorithm and save results"""
    # MUST CALL THIS when your algorithm completes
    # Saves results to: <base64_team_id>.results
    # Calls sys.exit() - program terminates
    
    # YOUR USAGE:
    # at the end of your algorithm:
    # if best_fitness_found:
    #     frams_lib.end()
```

---

## 📊 Return Value Formats

### SIMPLE_FITNESS_FORMAT = True

```python
# evaluate() returns: List[float] or List[None]

# Example:
genotypes = ['llllllll', 'lll{||}lll', 'invalid_genotype']
fitnesses = frams_lib.evaluate(genotypes)
# Returns: [25.5, 31.2, None]  or similar
#                             ↑ None = invalid/failed evaluation

# Handle in your code:
for genotype, fitness in zip(genotypes, fitnesses):
    if fitness is not None:  # Valid solution
        track_best(genotype, fitness)
    else:  # Invalid solution
        skip_this_solution()
```

**Advantages**:
- Simple to work with
- Just a number per solution
- Easy for custom algorithms

### SIMPLE_FITNESS_FORMAT = False

```python
# evaluate() returns: List[dict] or complex structure
# Each dict has the format:
# {
#     'num': <genotype_id>,
#     'name': '<creature_name>',
#     'evaluations': {
#         '': {
#             'COGpath': <fitness_value>,  # This is FITNESS_DICT_KEY
#             'numparts': <integer>,       # Constraint metrics
#             'numjoints': <integer>,
#             'numneurons': <integer>,
#             'numconnections': <integer>,
#             ... more metrics ...
#         }
#     }
# }

# Example:
fitnesses = frams_lib.evaluate(['llllllll'])
# Returns:
# [{
#     'num': 0,
#     'name': 'Unnamed',
#     'evaluations': {
#         '': {
#             'COGpath': 25.5,
#             'numparts': 3,
#             'numjoints': 2,
#             ...
#         }
#     }
# }]

# Handle in your code:
for result in fitnesses:
    if result['evaluations'] is not None:
        fitness = result['evaluations'][''][FITNESS_DICT_KEY]
        constraints = result['evaluations']['']
        # Check constraints manually
        if constraints['numparts'] > max_parts:
            skip_this_solution()
    else:
        skip_this_solution()
```

**When to use**:
- When you need constraint metrics
- When compatibility with existing code is required
- When you want detailed evaluation info

---

## 🚨 Important Behavior

### Automatic Limit Checking

Inside `_evaluate_single_genotype()`:

```python
# The library checks:
if self._evaluation_count > self.MAX_EVALUATIONS:
    print('The allowed time or the maximum number of evaluations exceeded')
    self.end()  # ← Automatic termination!

if perf_counter() - self._time0 - self._evaluation_time > self.MAX_TIME:
    print('The allowed time or the maximum number of evaluations exceeded')
    self.end()  # ← Automatic termination!
```

**This means**:
- ✅ You don't need to check limits yourself
- ✅ `end()` is called automatically when limits exceed
- ✅ Results are saved automatically
- ⚠️ Your algorithm terminates immediately (no graceful shutdown)

### Time Tracking

```python
# The library tracks:
eval_time0 = perf_counter()
fitnesses = [self._evaluate_single_genotype(genotype) 
             for genotype in genotype_list]
self._evaluation_time += perf_counter() - eval_time0

# The reported "runtime" is:
total_running_time = perf_counter() - self._time0
reported_time = total_running_time - self._evaluation_time
#                 ↑ Evaluation time is SUBTRACTED
```

**Implication**:
- Your algorithm gets 1 hour of "thinking time"
- Simulation time (Framsticks evaluation) doesn't count
- Optimization work happens while Framsticks is busy

---

## 🎯 How It Evaluates COG Movement

### The _evaluate_path() Method

```python
def _evaluate_path(self, path):
    path = np.array(path)
    
    if self.TEST_FUNCTION == 3:
        # Simple: distance from birth to death
        return np.linalg.norm(path[0] - path[-1])
    
    elif self.TEST_FUNCTION == 4:
        # Distance × height: travel far AND stay high
        distance = np.linalg.norm(path[0] - path[-1])
        avg_height = np.mean(np.maximum(0, path[:, 2]))
        return distance * avg_height
    
    elif self.TEST_FUNCTION == 5:
        # RMSE: z-coordinate should follow linear function
        # z(t) = 0.5 + 0.1*sin(t/100)
        expected_z = np.linspace(0, 10, len(path), endpoint=True)
        rmse = np.linalg.norm(expected_z - path[:, 2]) / np.sqrt(len(path))
        return 1000 - rmse  # Negate RMSE, offset to ensure positive
```

**What is `path`?**
- Array of shape `(timesteps, 3)`
- Columns: [x, y, z] coordinates of COG
- Rows: One per simulation step
- Origin: Creature's starting position

**Why TEST_FUNCTION matters**:
- Different metrics reward different behaviors
- Your algorithm must adapt to each setting
- You won't know which test function is used until evaluation

---

## ✅ Checklist: Using FramsticksLibCompetition

### Must-Do Items

- [ ] Import and instantiate: `frams_lib = FramsticksLibCompetition(...)`
- [ ] Set `COMPETITOR_ID` to your team name
- [ ] Choose `SIMPLE_FITNESS_FORMAT` (recommended: `True` for simplicity)
- [ ] Call `evaluate()` with list of genotypes
- [ ] Handle `None` values (invalid solutions)
- [ ] **CALL `.end()` when algorithm finishes**
- [ ] Test in clean environment (no extra files)

### Should-Do Items

- [ ] Log best fitness periodically (for debugging)
- [ ] Track evaluation count (though not required)
- [ ] Store best genotype separately
- [ ] Use f0 or f1 encodings properly
- [ ] Implement constraint-aware selection

### Don't Do

- ❌ Don't use plain `FramsticksLib` (no limit enforcement)
- ❌ Don't forget `.end()` (results won't save)
- ❌ Don't exceed 100k evaluations intentionally
- ❌ Don't use parallel processing
- ❌ Don't manually check time (it's automatic)

---

## 🔄 Typical Algorithm Loop

```python
from FramsticksLibCompetition import FramsticksLibCompetition

# Initialize
frams_lib = FramsticksLibCompetition()
population = [frams_lib.getSimplest('0') for _ in range(population_size)]

# Main loop (keep going until limits hit)
generation = 0
while generation < max_generations:
    # Evaluate all
    fitnesses = frams_lib.evaluate(population)
    
    # Find best
    for genotype, fitness in zip(population, fitnesses):
        if fitness is not None and fitness > best_fitness:
            best_fitness = fitness
            best_genotype = genotype
    
    # Selection + Reproduction
    # (Your selection strategy here)
    
    # Create next generation through mutation/crossover
    offspring = []
    for _ in range(len(population)):
        if random() < mutation_rate:
            parent = select_best()
            child = frams_lib.mutate([parent])[0]
        else:
            p1 = select_best()
            p2 = select_best()
            child = frams_lib.crossOver(p1, p2)
        offspring.append(child)
    
    population = offspring
    generation += 1
    
    # Check progress
    if generation % 10 == 0:
        print(f"Gen {generation}: best={best_fitness}")

# Save results when done
print(f"Final best: {best_fitness}")
frams_lib.end()  # ← CRITICAL: Call this!
```

---

## 🐛 Debugging Tips

### "The allowed time or the maximum number of evaluations exceeded"

This message appears when:
1. You've called `evaluate()` more than 100k times total
2. Wall-clock time since start - evaluation time > 1 hour

**Solution**: Your algorithm should wrap up before this happens. Use fewer evaluations per generation.

### "evaluation is: [...]"

If you uncomment this debug line:
```python
print("Evaluated '%s'" % genotype, 'evaluation is:', data)
```

You'll see the full return structure. Useful for understanding fitness format.

### No Results File Created

If `<base64_team_id>.results` is not created:
- ✅ Did you call `.end()`? (Required)
- ✅ Is `COMPETITOR_ID` set to valid alphanumeric?
- ✅ Did the algorithm reach that line (print statement shows it)?

### fitness is None

When `evaluate()` returns `None` for a solution:
- Genotype is malformed (invalid syntax)
- Creature failed to stabilize (physics simulation issue)
- Constraint violation (depends on world config)
- Other simulator error

This is **normal and expected**. Just skip these solutions.

---

## 📈 Performance Considerations

### Evaluation Budget Allocation

If you have 100k evaluations and 10 settings:
- **Naive**: 10k evaluations per setting
- **Smart**: Fewer evaluations early, more later (with better solutions)
- **Smarter**: Allocate based on convergence speed

Example strategy:
```python
# Generations with budget
generations = [
    100,  # Gen 1-100: explore broadly (1000 evals)
    50,   # Gen 101-150: refine (500 evals)
    30,   # Gen 151-180: exploit (300 evals)
    20,   # Gen 181-200: polish (200 evals)
    # Total: ~2000 evaluations per setting
    # Leaves room for adaptation
]
```

### Population Size Trade-off

```python
pop_size = 10
gens = 10000  # 100k evaluations / 10 pop_size = 10k generations

pop_size = 100
gens = 1000   # 100k evaluations / 100 pop_size = 1k generations
```

Smaller populations = more generations but less diversity per generation.

### Fitness Diversity

Track:
- Best fitness per generation
- Average population fitness
- Fitness standard deviation

This helps detect premature convergence.

---

## 🎓 Learning Resources

1. **First Time?**
   - Read this document
   - Study `FramsticksEvolution.py` (DEAP example)
   - Run with `TEST_FUNCTION = 3` (simplest)

2. **Need Genetic Operators?**
   - `mutate()` - random changes
   - `crossOver()` - combine two genotypes
   - `getSimplest()` - starting point

3. **Understanding Encodings?**
   - f0: Linear creatures ('llllllll')
   - f1: Complex morphologies ('p(Rq)q(C:2)')
   - Start with f0, graduate to f1

4. **Evolutionary Strategies?**
   - See `FramsticksEvolution.py` for DEAP example
   - See competition results PDFs for previous winners
   - Experiment with selection (tournament, roulette, etc.)

---

## ❓ FAQ

**Q: Why can `fitness` be `None`?**  
A: Invalid genotypes fail evaluation. Skip them and continue. Don't treat as "bad fitness," treat as "no fitness."

**Q: Should I set `SIMPLE_FITNESS_FORMAT = False`?**  
A: Only if you need constraint info or compatibility. `True` is simpler and recommended.

**Q: Can I modify `MAX_EVALUATIONS` or `MAX_TIME`?**  
A: You can in your local testing, but competition will enforce original values.

**Q: What's in `result[0]['evaluations']['']['COGpath']`?**  
A: The fitness value (numerical score) for that genotype. It's nested deeply because of the evaluation structure.

**Q: If I call `evaluate()` 100,001 times, what happens?**  
A: The 100,001st call triggers automatic `end()`. Results are saved with evaluations up to that point.

**Q: Does my algorithm's time include `evaluate()` calls?**  
A: No. Only wall-clock time minus simulator time counts toward the 1-hour limit.

---

## 🔗 Related Files

- `FramsticksEvolution.py` - Complete DEAP-based example
- `FramsticksLib.py` - Base library (reference)
- `run-deap-examples.cmd` - Setup example
- `*.sim` - World configuration files (copy to Framsticks data/)
