# Implementation Quick Start Guide

A step-by-step guide to implementing your competition algorithm.

---

## 📋 Step 1: Understand Your Task (5 min read)

**Your goal**: Write an evolutionary algorithm that:
- ✅ Uses `FramsticksLibCompetition` (not plain `FramsticksLib`)
- ✅ Evolves f0 or f1 genotypes (robot designs)
- ✅ Optimizes for hidden fitness function
- ✅ Respects 100k evaluations, 1 hour time limit
- ✅ Calls `.end()` when done
- ✅ Finds the best solution it can

**You won't know**:
- ❌ Exact fitness function (learned through evolution)
- ❌ Which of 10 settings you're in
- ❌ Terrain or world parameters
- ❌ Expected movement pattern

**It's black-box optimization**: You only get a fitness number per solution.

---

## 🛠️ Step 2: Setup Your Environment

### Install Framsticks
```bash
# Download from: https://framsticks.com/download.html
# Choose your OS (Windows/Linux/macOS)
# Extract to: C:\Framsticks (or equivalent)
```

### Get Python Interface
```bash
# Download framspy (Python binding)
# Option 1 (recommended): git svn clone https://svn.framsticks.com/framspy
# Option 2: Manual download from repository
# Extract to: C:\framspy (or equivalent)
```

### Verify Installation
```bash
# In framspy directory:
python frams-test.py C:\Framsticks

# Expected output: "All tests passed"
```

### Install Dependencies
```bash
pip install deap numpy

# Optional for faster evaluation:
pip install scipy scikit-learn
```

### Copy Simulation Files
```bash
# Copy all .sim files from framspy to Framsticks/data/
copy C:\framspy\*.sim C:\Framsticks\data\
```

---

## 📝 Step 3: Create Your Algorithm File

Create `my_algorithm.py`:

```python
#!/usr/bin/env python3
"""
My Team's GECCO Competition Algorithm
Optimizes Framsticks creatures for desired COG movement patterns.
"""

import sys
import argparse
from random import random, randint, choice
from FramsticksLibCompetition import FramsticksLibCompetition

# Configuration
POPULATION_SIZE = 50
GENERATIONS = 100
MUTATION_RATE = 0.7
CROSSOVER_RATE = 0.3

def initialize_population(frams_lib, size):
    """Create initial population of random creatures."""
    population = []
    for _ in range(size):
        # Get simplest creature in f0 encoding
        genotype = frams_lib.getSimplest('0')
        
        # Mutate it a few times for diversity
        for _ in range(randint(1, 3)):
            genotype = frams_lib.mutate([genotype])[0]
        
        population.append(genotype)
    
    return population

def evaluate_population(frams_lib, population):
    """Evaluate all creatures in population."""
    fitnesses = frams_lib.evaluate(population)
    return fitnesses

def select_parent(population, fitnesses, tournament_size=3):
    """Tournament selection: pick best of random sample."""
    indices = [randint(0, len(population) - 1) for _ in range(tournament_size)]
    best_idx = max(indices, key=lambda i: fitnesses[i] if fitnesses[i] is not None else -999999)
    return population[best_idx]

def create_offspring(frams_lib, parent1, parent2):
    """Create a child from two parents."""
    if random() < CROSSOVER_RATE:
        # Crossover
        child = frams_lib.crossOver(parent1, parent2)
    else:
        # Mutation
        child = choice([parent1, parent2])
        child = frams_lib.mutate([child])[0]
    
    return child

def run_evolution(frams_lib):
    """Main evolutionary loop."""
    print("Initializing population...")
    population = initialize_population(frams_lib, POPULATION_SIZE)
    
    best_fitness_overall = None
    best_genotype_overall = None
    
    for generation in range(GENERATIONS):
        print(f"Generation {generation + 1}/{GENERATIONS}")
        
        # Evaluate
        fitnesses = evaluate_population(frams_lib, population)
        
        # Track best
        for genotype, fitness in zip(population, fitnesses):
            if fitness is not None:
                if best_fitness_overall is None or fitness > best_fitness_overall:
                    best_fitness_overall = fitness
                    best_genotype_overall = genotype
                    print(f"  New best: {best_fitness_overall:.2f}")
        
        # Create next generation
        next_population = []
        for _ in range(POPULATION_SIZE):
            # Select two parents
            parent1 = select_parent(population, fitnesses)
            parent2 = select_parent(population, fitnesses)
            
            # Create offspring
            child = create_offspring(frams_lib, parent1, parent2)
            next_population.append(child)
        
        population = next_population
        
        # Optional: check progress every 10 generations
        if (generation + 1) % 10 == 0:
            valid_count = sum(1 for f in fitnesses if f is not None)
            print(f"  Valid solutions: {valid_count}/{POPULATION_SIZE}")
    
    print(f"\nFinal result: {best_fitness_overall}")
    return best_fitness_overall, best_genotype_overall

def main():
    parser = argparse.ArgumentParser(description='GECCO Competition Algorithm')
    parser.add_argument('-path', required=True, help='Path to Framsticks library')
    parser.add_argument('-sim', default='eval-allcriteria.sim', help='Simulation file')
    parser.add_argument('-opt', default='COGpath', help='Optimization criteria')
    args = parser.parse_args()
    
    # Initialize competition library
    try:
        frams_lib = FramsticksLibCompetition(args.path)
    except Exception as e:
        print(f"Error initializing Framsticks: {e}")
        sys.exit(1)
    
    # Run algorithm
    try:
        best_fitness, best_genotype = run_evolution(frams_lib)
        print(f"Algorithm complete. Best fitness: {best_fitness}")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error during evolution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # CRITICAL: Always call end() when done
        try:
            frams_lib.end()
        except SystemExit:
            pass  # end() calls sys.exit()

if __name__ == '__main__':
    main()
```

---

## ✅ Step 4: Test Your Algorithm

### Test 1: Syntax Check
```bash
python my_algorithm.py --help
```
Expected: Argument help is displayed.

### Test 2: Local Run (with path)
```bash
python my_algorithm.py -path C:\Framsticks

# Expected output:
# Initializing population...
# Generation 1/100
#   Valid solutions: 45/50
# Generation 2/100
#   New best: 25.3
# ...
# Final result: 42.7
# Saved '<base64>.results' (myteam)
```

### Test 3: Time/Evaluation Limits
Verify that:
- [ ] Algorithm stops after 1 hour
- [ ] Algorithm stops after 100k evaluations
- [ ] Results file is created with format: `<base64_team_id>.results`
- [ ] `print()` statements show progress

### Test 4: Clean Environment
Create a fresh directory with **only**:
- Your algorithm file
- requirements.txt
- README.txt

Then run:
```bash
pip install -r requirements.txt
python my_algorithm.py -path C:\Framsticks
```

This ensures no hidden dependencies exist.

---

## 📦 Step 5: Prepare Submission

### 1. Create requirements.txt
```
deap==1.4.1
numpy==1.24.0
```

(Adjust versions based on what you installed)

### 2. Create README.txt
```
GECCO Competition Algorithm - MyTeam

INSTALLATION:
1. Install Python 3.8 or later
2. pip install -r requirements.txt
3. Download Framsticks from https://framsticks.com/download.html
4. Extract Framsticks to a directory (e.g., C:\Framsticks)

RUNNING THE ALGORITHM:
python my_algorithm.py -path <path_to_framsticks>

Example (Windows):
python my_algorithm.py -path "C:\Framsticks"

Example (Linux):
python my_algorithm.py -path "/home/user/Framsticks"

OUTPUT:
- Console output shows generation progress
- Results saved to: <base64_team_id>.results

TIME LIMITS:
- Maximum 100,000 evaluations
- Maximum 1 hour runtime (excluding evaluation time)
- Algorithm will automatically stop when limits are reached

ALGORITHM DESCRIPTION:
This algorithm uses a simple evolutionary strategy:
1. Initialize population with random mutated creatures
2. Evaluate fitness using tournament selection
3. Create offspring through crossover and mutation
4. Repeat for fixed generations or until time limit
5. Return best solution found

The algorithm uses f0 genetic encoding (simple linear creatures)
which provides a good balance between search space and efficiency.
```

### 3. Create algorithm_description.md
```
# Algorithm Description: MyTeam Evolution

## Overview
A straightforward evolutionary algorithm optimizing Framsticks creatures
for center-of-gravity movement patterns.

## Strategy
1. **Initialization**: Start with simplest creatures, mutate for diversity
2. **Evaluation**: Batch evaluate population using FramsticksLibCompetition
3. **Selection**: Tournament selection (pick best of random sample)
4. **Variation**: Crossover + mutation for offspring creation
5. **Termination**: Continue until generation limit or resource exhaustion

## Key Parameters
- Population size: 50
- Generations: 100
- Mutation rate: 70%
- Crossover rate: 30%
- Tournament size: 3
- Genetic encoding: f0

## Computational Complexity
- Time: O(generations × population × evaluation)
- Space: O(population) genotypes in memory
- Evaluations: ~5,000 per generation (50 pop × 100 gen)

## Advantages
- Simple, easy to understand and modify
- Works with all Framsticks encodings
- Good convergence on simple fitness landscapes

## Limitations
- May converge prematurely on complex landscapes
- No adaptive parameter control
- No constraint-aware selection

## Future Improvements
- Adaptive mutation rates (self-adaptive ES)
- Multi-objective optimization (for multiple criteria)
- Constraint handling (penalty functions)
- Island model (multiple populations)
```

### 4. Organize Files
```
submission/
├── my_algorithm.py
├── requirements.txt
├── README.txt
└── algorithm_description.md
```

### 5. Zip and Send
```bash
# Create zip file
zip -r my_team_algorithm.zip submission/

# Send to:
# maciej.komosinski@cs.put.poznan.pl
# Subject: GECCO 2026 Algorithm Submission - MyTeam
```

---

## 🎯 Step 6: Optimize Your Algorithm

### Easy Wins
1. **Increase population size** (if time permits)
   ```python
   POPULATION_SIZE = 100  # More diversity
   GENERATIONS = 50       # Fewer generations
   ```

2. **Add elitism** (keep best solution)
   ```python
   # Keep best 2 individuals
   best_indices = sorted(range(len(fitnesses)), 
                         key=lambda i: fitnesses[i] if fitnesses[i] is not None else -999999)[-2:]
   next_population[:2] = [population[i] for i in best_indices]
   ```

3. **Adaptive mutation rates**
   ```python
   if generation < GENERATIONS / 2:
       mutation_rate = 0.8  # Explore early
   else:
       mutation_rate = 0.3  # Exploit late
   ```

4. **Early stopping**
   ```python
   if no improvement for 20 generations:
       break  # Then call frams_lib.end()
   ```

### Advanced Techniques
1. **Multi-strategy approach**: Try different encodings (f0 vs f1)
2. **Fitness shaping**: Combine multiple objectives
3. **Adaptive crossover**: Adjust crossover/mutation based on fitness
4. **Constraint handling**: Penalize solutions violating complexity limits

---

## 🚀 Step 7: Final Checklist

Before submission, verify:

- [ ] Algorithm uses `FramsticksLibCompetition` (not `FramsticksLib`)
- [ ] Calls `.end()` when complete
- [ ] Works in clean environment (separate directory)
- [ ] No hardcoded paths (uses command-line `-path` argument)
- [ ] requirements.txt lists all dependencies
- [ ] README has clear installation steps
- [ ] Algorithm description explains the strategy
- [ ] Code has basic comments
- [ ] Handles None fitness values (invalid solutions)
- [ ] No internet required
- [ ] No GPU or parallel processing
- [ ] Respects time and evaluation limits
- [ ] All files included in zip
- [ ] Email deadline: June 15, 2026

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'FramsticksLibCompetition'"
- Ensure you're in the framspy directory
- Or copy `FramsticksLibCompetition.py` to your algorithm's directory
- Or add framspy to Python path: `sys.path.append('/path/to/framspy')`

### "frams_lib.evaluate() returns None for all genotypes"
- Framsticks library not found or not working
- Run `python frams-test.py <path>` to verify
- Check that `.sim` files are in Framsticks/data/

### "Algorithm times out before finishing"
- Reduce `POPULATION_SIZE` or `GENERATIONS`
- Increase generation interval for progress checks
- Use fewer evaluations per generation

### "Results file not created"
- Did you call `.end()`? (Must happen in code)
- Is `COMPETITOR_ID` alphanumeric only?
- Did the program reach the `end()` statement?

### "fitness values are always None"
- Genotypes may be malformed
- Try: `genotype = frams_lib.getSimplest('0')` without mutation first
- Check Framsticks installation (run frams-test.py)

---

## 📚 Next Steps

1. **Baseline**: Get the simple algorithm working first
2. **Test**: Run locally with all settings
3. **Improve**: Adjust parameters based on results
4. **Optimize**: Implement advanced techniques
5. **Submit**: Early (avoid last-minute issues)

Good luck! 🎉

---

## 🔗 References

- **Official Competition**: https://www.framsticks.com/gecco-competition
- **Framsticks Download**: https://framsticks.com/download.html
- **DEAP Documentation**: https://deap.readthedocs.io/
- **Contact**: support@framsticks.com
