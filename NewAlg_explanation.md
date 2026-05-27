# Explanation of `NewAlg.py`

`NewAlg.py` is an **evolutionary optimizer** for the Framsticks GECCO competition.

In plain terms, it tries to automatically discover a good Framsticks creature design by repeatedly:

1. Creating candidate creatures.
2. Simulating/evaluating them.
3. Keeping the better ones.
4. Mutating/crossing them to create new candidates.
5. Repeating until the evaluation or time budget runs out.

You can think of it like artificial breeding: good creatures are more likely to become parents, but the algorithm also keeps experimenting so it does not get stuck too early.

---

# Very Short Genetic Algorithm Primer

A genetic algorithm usually has these concepts:

- **Genotype**  
  The encoded “DNA” of a solution. Here it is a Framsticks genotype string.

- **Individual**  
  One candidate solution. Here: a genotype plus its fitness score.

- **Fitness**  
  How good a candidate is. Framsticks evaluates the creature and returns a number.

- **Population**  
  The current group of candidate solutions.

- **Mutation**  
  Randomly changing one genotype to create a similar but different child.

- **Crossover**  
  Combining two parent genotypes to produce a child.

- **Selection**  
  Choosing which candidates survive or reproduce.

- **Elitism**  
  Always keeping some of the best candidates.

- **Diversity / novelty**  
  Preferring some candidates that are different from the current population, not only those with high fitness.

This file implements all of those, plus an archive of good solutions, adaptive mutation depth, local improvement bursts, and restarts.

---

# Constants at the Top

```python
COMPETITOR_ID = "SouperTeam"
DEFAULT_GENETIC_FORMAT = "1"
DEFAULT_SIM = "eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim"
MAX_EVALUATIONS = 100_000
EVALUATION_SAFETY_MARGIN = 150
MAX_ALGORITHM_TIME = 3600
TIME_SAFETY_MARGIN = 45
```

These define competition/run settings.

- **`COMPETITOR_ID`**  
  The team name submitted to Framsticks.

- **`DEFAULT_GENETIC_FORMAT`**  
  The Framsticks genotype encoding format.

- **`DEFAULT_SIM`**  
  Simulation config files used by Framsticks.

- **`MAX_EVALUATIONS`**  
  The competition budget: at most 100,000 evaluations.

- **`EVALUATION_SAFETY_MARGIN`**  
  Stops slightly before 100,000 to avoid accidentally exceeding the limit.

- **`MAX_ALGORITHM_TIME`**  
  One hour.

- **`TIME_SAFETY_MARGIN`**  
  Stops 45 seconds early to avoid timing out.

---

# `Individual`

```python
@dataclass
class Individual:
    genotype: str
    fitness: float | None = None
    birth: int = 0
```

An `Individual` represents one creature candidate.

It stores:

- **`genotype`**  
  The Framsticks genotype string.

- **`fitness`**  
  The evaluation score. Higher is better. `None` means invalid or unevaluated/failed.

- **`birth`**  
  The generation in which this individual was created.

This class is just a lightweight container.

---

# `Archive`

The `Archive` class stores the best genotypes found so far.

```python
class Archive:
```

It has:

- **`items`**  
  A list of `(genotype, fitness)` pairs.

- **`seen`**  
  A set of genotypes already in the archive.

- **`max_size`**  
  Maximum number of archived genotypes.

## Why have an archive?

The normal population changes over time. A really good solution could theoretically disappear if not protected. The archive prevents that by keeping the best discoveries separately.

## `add`

```python
def add(self, genotype, fitness):
```

Adds a genotype to the archive if it has a valid fitness.

If the genotype is already known, it updates it only if the new fitness is better.

Then it sorts archive items from best to worst and trims the archive to `max_size`.

## `best`

```python
def best(self):
```

Returns the best archived `(genotype, fitness)` pair, or `(None, None)` if empty.

## `sample`

```python
def sample(self, pressure=2.5):
```

Samples a genotype from the archive, biased toward better ones.

The archive is sorted best-first. This line:

```python
r = random.random() ** pressure
```

makes smaller indexes more likely, so better archived candidates are selected more often.

---

# `HybridOptimizer`

This is the main evolutionary algorithm.

```python
class HybridOptimizer:
```

It manages:

- The current population.
- Evaluation budget.
- Time budget.
- Best-so-far solution.
- Mutation/crossover.
- Survivor selection.
- Restarts.
- Local improvement.

---

# Initialization

```python
def __init__(self, frams_lib, args):
```

Important fields:

- **`self.frams_lib`**  
  Interface to Framsticks. This performs mutation, crossover, evaluation, constraint checks, etc.

- **`self.pop_size`**  
  Number of individuals kept in the population.

- **`self.elite_count`**  
  Number of top individuals always preserved.

- **`self.archive`**  
  Long-term memory of best genotypes.

- **`self.population`**  
  Current generation’s individuals.

- **`self.evaluated_cache`**  
  Maps genotype to fitness, so the same genotype is not evaluated twice.

- **`self.generated`**  
  Tracks generated genotypes to avoid duplicates.

- **`self.generation`**  
  Current generation number.

- **`self.best_fitness` / `self.best_genotype`**  
  Best result found so far.

- **`self.mutation_depth`**  
  How many mutations can be chained. This increases during stagnation.

- **`self.has_structural_constraints`**  
  Checks whether limits like max parts/joints/neurons are active.

---

# Budget Management

```python
def evaluations_used(self):
def remaining_evaluations(self):
def time_left(self):
def should_stop(self):
```

These methods stop the algorithm when:

- It is close to using all 100,000 evaluations.
- It is close to the 1-hour time limit.

This is important for competitions where exceeding limits can invalidate results.

---

# Constraint Checking

```python
def constraints_ok(self, genotype):
```

This checks whether a genotype is allowed.

It rejects:

- Empty genotypes.
- Framsticks invalid genotypes.
- Genotypes longer than `max_numgenochars`.
- Genotypes violating structural constraints like max parts, joints, neurons, or neural connections.

If no structural constraints are active, it skips the expensive structural check.

---

# Remembering the Best Candidate

```python
def remember_best(self, genotype, fitness):
```

Whenever a genotype is evaluated, this method:

1. Adds it to the archive.
2. Checks if it beats the global best.
3. If yes, updates:
   - `self.best_fitness`
   - `self.best_genotype`
   - `self.last_improvement_generation`

This lets the algorithm know when it last made progress.

---

# Evaluation

```python
def evaluate_candidates(self, genotypes, birth):
```

This is one of the most important methods.

It receives genotype strings, filters them, evaluates new valid ones, caches results, and returns `Individual` objects.

The process:

1. Skip genotypes already in `evaluated_cache`.
2. Reject genotypes that violate constraints.
3. Stop adding candidates if the remaining evaluation budget is almost exhausted.
4. Evaluate candidates in chunks using:

```python
fitnesses = self.frams_lib.evaluate(chunk)
```

5. Cache each fitness.
6. Update best-so-far and archive.
7. Return a list of `Individual` objects.

The cache matters because simulations are expensive. Evaluating the same genotype twice wastes budget.

---

# Mutation

```python
def mutate_depth(self, genotype, depth):
```

This applies mutation multiple times in a row.

Example:

- Depth `1`: mutate once.
- Depth `3`: mutate, then mutate the result, then mutate again.

Higher depth means bigger changes.

If Framsticks returns an invalid genotype, it increments `invalid_offspring` and stops.

---

# Crossover

```python
def crossover(self, left, right):
```

This combines two parent genotypes using Framsticks:

```python
child = self.frams_lib.crossOver(left, right)
```

If crossover fails, it returns one of the parents instead.

So crossover is used as another way to create new children, but with a fallback.

---

# Genotype Distance and Novelty

```python
def genotype_distance(self, a, b):
def novelty(self, genotype, reference):
```

These estimate how different one genotype is from others.

`genotype_distance` compares sampled characters from two genotype strings. It is not a perfect biological/structural distance, but it is a cheap approximation.

`novelty` compares a genotype against up to 6 existing individuals and returns the average distance.

Why this matters:

If the algorithm only keeps the highest-fitness individuals, the population may become too similar. Then it can get stuck. Novelty helps preserve variety.

---

# Parent Selection

There are two parent-selection methods.

## Tournament Selection

```python
def tournament_parent(self):
```

This randomly samples several individuals and picks the best among them.

Example:

If tournament size is 7, it randomly chooses 7 individuals from the population and selects the one with the highest fitness.

This creates selection pressure: better individuals are more likely to reproduce.

## Rank Parent Selection

```python
def rank_parent(self):
```

This sorts valid individuals by fitness and samples with bias toward better ones.

This is used as the second parent during crossover.

---

# Creating the Initial Population

```python
def make_seed_population(self):
```

The algorithm starts from Framsticks’ simplest valid genotype:

```python
simplest = self.frams_lib.getSimplest(self.args.genformat)
```

Then it repeatedly mutates it by random depths:

```python
depths = [1, 2, 3, 4, 6, 8, 11, 15]
```

This creates an initial population with some variety instead of starting with many identical copies.

The method returns up to `pop_size` seed genotypes.

---

# Generating Offspring

```python
def generate_offspring(self, count):
```

This creates new genotype strings for the next generation.

Each child is created by one of three strategies.

## 1. Mutate an archived elite

```python
if roll < self.args.archive_mutation_rate and self.archive.items:
```

This chooses a good genotype from the archive and mutates it.

Purpose:

- Exploit already-good solutions.
- Search around proven candidates.

## 2. Crossover two parents

```python
elif roll < self.args.archive_mutation_rate + self.args.crossover_rate
```

This chooses two parents and crosses them over.

Then it often mutates the child afterward:

```python
if random.random() < self.args.post_crossover_mutation_rate:
```

Purpose:

- Combine traits from two good candidates.
- Still introduce variation afterward.

## 3. Mutate a population parent

```python
else:
```

This picks a parent from the current population and mutates it.

Sometimes it does a deeper “random walk” mutation:

```python
if random.random() < self.args.random_walk_rate:
```

Purpose:

- Continue normal evolutionary search.
- Occasionally make larger exploratory jumps.

---

# Adaptive Mutation Depth

Inside `generate_offspring`:

```python
stagnation = self.generation - self.last_improvement_generation
self.mutation_depth = min(
    self.args.max_mutation_depth,
    1 + stagnation // self.args.depth_step
)
```

If the algorithm has not improved for many generations, it increases mutation depth.

Meaning:

- If things are improving, make smaller changes.
- If stuck, make larger changes.

This is similar to saying: “If local tweaks are not working, try bigger jumps.”

---

# Duplicate Avoidance

```python
if child in self.generated or child in self.evaluated_cache:
    self.duplicate_offspring += 1
    continue
```

The algorithm avoids wasting time on repeated genotypes.

This is especially important when the population converges and mutation/crossover often produces already-seen candidates.

---

# Survivor Selection

```python
def survivor_selection(self, candidates):
```

This decides who survives into the next population.

The candidates are usually:

```python
current population + newly evaluated offspring
```

The method:

1. Separates valid and invalid individuals.
2. Sorts valid individuals by fitness.
3. Keeps strict elites:

```python
selected = valid[:self.elite_count]
```

4. Fills the rest of the population using both fitness and novelty:

```python
ind.fitness + self.args.novelty_weight * abs(ind.fitness) * self.novelty(...)
```

So candidates are preferred if they are:

- High fitness.
- Somewhat different from already-selected survivors.

This prevents the population from becoming too homogeneous.

---

# Local Improvement Burst

```python
def local_improvement_burst(self):
```

Every few generations, the algorithm spends extra evaluations around the best archived genotypes.

It takes top archive items:

```python
bases = [item[0] for item in self.archive.items[: min(8, len(self.archive.items))]]
```

Then creates nearby mutations, usually shallow ones:

```python
depth = random.choice([1, 1, 2, 2, 3, self.mutation_depth])
```

Purpose:

- Fine-tune the best solutions.
- Search the neighborhood of known strong candidates.

This is more exploitative than normal offspring generation.

---

# Restart Logic

```python
def restart_if_needed(self):
```

If no improvement occurs for too many generations:

```python
if stagnation < self.args.restart_after:
    return
```

then the algorithm partially restarts.

It keeps elites from the archive:

```python
keep = [Individual(g, f, self.generation) for g, f in self.archive.items[: self.elite_count]]
```

Then fills the rest with fresh mutations from:

- The simplest genotype.
- Top archive genotypes.

Purpose:

- Escape stagnation.
- Avoid spending the rest of the run in a bad local optimum.
- Keep the best discoveries instead of throwing everything away.

---

# Main Evolution Loop

```python
def run(self):
```

This is the core algorithm.

The flow is:

## 1. Create initial population

```python
seed_genotypes = self.make_seed_population()
self.population = self.evaluate_candidates(seed_genotypes, 0)
self.population = self.survivor_selection(self.population)
```

## 2. Repeat until budget/time limit

```python
while not self.should_stop():
```

Each generation:

1. Increment generation counter.
2. Decide how many offspring to evaluate.
3. Generate offspring genotypes.
4. Evaluate offspring.
5. Combine old population and offspring.
6. Occasionally run local improvement.
7. Select survivors.
8. Restart if stuck.
9. Print status.

At the end:

```python
print("Best fitness:", self.best_fitness)
print("Best genotype:", self.best_genotype)
```

---

# Command-Line Arguments

```python
def parse_arguments():
```

This defines many tunable parameters.

Important ones:

- **`-path`**  
  Path to the Framsticks library. Required.

- **`-popsize`**  
  Number of individuals in the population. Default: `80`.

- **`-batch_size`**  
  Number of new offspring evaluated per generation. Default: `30`.

- **`-tournament`**  
  Tournament size for parent selection. Default: `7`.

- **`-elite_fraction`**  
  Fraction of population kept as strict elites. Default: `0.18`.

- **`-archive_size`**  
  Number of best genotypes remembered. Default: `80`.

- **`-crossover_rate`**  
  Probability of making a child through crossover. Default: `0.22`.

- **`-archive_mutation_rate`**  
  Probability of mutating an archived elite. Default: `0.28`.

- **`-random_walk_rate`**  
  Probability of deeper exploratory mutation. Default: `0.16`.

- **`-restart_after`**  
  Number of stagnant generations before restart. Default: `45`.

- **`-local_every`**  
  Run local improvement every N generations. Default: `5`.

- **Constraint args**  
  These restrict maximum parts, joints, neurons, connections, or genotype length.

---

# Program Entry Point

```python
def main():
```

This:

1. Parses CLI arguments.
2. Configures the Framsticks competition wrapper.
3. Creates `FramsticksLibCompetition`.
4. Creates `HybridOptimizer`.
5. Runs the optimizer.
6. Cleans up Framsticks at the end.

Important lines:

```python
FramsticksLibCompetition.SIMPLE_FITNESS_FORMAT = True
FramsticksLibCompetition.DETERMINISTIC = False
```

The first means `evaluate` returns simple fitness values.

The second means the evaluation is not forced to be deterministic by the wrapper, although the simulation config includes deterministic settings.

---

# Big Picture: What Kind of Algorithm Is This?

This is not a minimal genetic algorithm. It is a **hybrid evolutionary algorithm**.

It combines:

- **Standard genetic algorithm ideas**
  - Population
  - Mutation
  - Crossover
  - Fitness-based selection

- **Elitist search**
  - Best individuals are always preserved.

- **Archive-based search**
  - Best-ever genotypes are remembered and reused.

- **Adaptive mutation**
  - Mutation becomes stronger when progress stalls.

- **Novelty preservation**
  - Some diversity is encouraged during survivor selection.

- **Local search**
  - Periodically mutates the best genotypes to improve them.

- **Restart strategy**
  - If stuck, rebuilds the population while preserving top archived genotypes.

So the optimizer tries to balance two competing goals:

- **Exploitation**  
  Improve already-good solutions.

- **Exploration**  
  Search new areas of the genotype space.

Good evolutionary algorithms need both.

---

# Simplified Pseudocode

```text
start with simple Framsticks genotype
mutate it many ways to create initial population
evaluate population

while time and evaluation budget remain:
    create new children using:
        - mutation of archive elites
        - crossover of selected parents
        - mutation of selected population parents

    evaluate children

    combine old population + children

    sometimes:
        locally improve best archived genotypes

    select next population:
        - always keep best elites
        - fill remaining slots using fitness + diversity

    if no improvement for many generations:
        partially restart population

print best genotype found
```

---

# Most Important Things to Understand

- **The genotype string is the creature’s DNA.**
- **Framsticks evaluates a genotype and returns its fitness.**
- **Higher fitness is better.**
- **The algorithm does not know how to design a good creature directly.**
- **Instead, it searches by repeatedly modifying and selecting genotypes.**
- **The archive protects the best solutions found so far.**
- **Mutation depth increases when the search gets stuck.**
- **Novelty helps keep the population diverse.**
- **Restarts help escape local optima.**
