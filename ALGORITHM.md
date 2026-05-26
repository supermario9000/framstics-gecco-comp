# SouperTeam — Why `algorithm.py` Beats the Example

This document explains, in concrete scientific and mathematical terms, why
[algorithm.py](algorithm.py) (an adaptive multi-strategy evolutionary
algorithm, hereafter **AMS-EA**) is expected to outperform the example
baseline [FramsticksEvolution.py](FramsticksEvolution.py) (DEAP's
`eaSimple` with fixed parameters, hereafter **eaSimple**) on the GECCO
Framsticks COG-trajectory task.

The argument is organized around eight independent improvements. Each one
is grounded in a known result from the evolutionary computation
literature, and each one targets a specific failure mode of `eaSimple` on
this problem.

---

## 1. Strong (μ + λ) elitism vs. generational replacement

**Baseline.** `eaSimple` performs *generational* replacement
([FramsticksEvolution.py:232](FramsticksEvolution.py#L232)):

```python
pop[:] = offspring
```

The offspring population *fully replaces* the parents. The best individual
ever found in a generation can be lost in the next one if crossover and
mutation degrade it. The Hall-of-Fame is only *recorded*, not re-injected.

**AMS-EA.** We use (μ + λ) elitist replacement
([algorithm.py:404-420](algorithm.py#L404-L420)): the union of parents and
offspring is sorted by fitness and the top `μ` survive. In addition, the
top 15% of the population is guaranteed to survive every generation
([algorithm.py:36](algorithm.py#L36)).

**Why it matters.** Rudolph (1994) proved that an elitist EA on a finite
discrete search space converges with probability 1 to the global optimum,
while non-elitist EAs do not have this guarantee. On a noisy /
deceptive landscape such as COG-path fitness, losing the incumbent best
to a single bad mutation can erase tens of thousands of evaluations of
progress. Strong elitism makes the best-so-far a monotonically
non-decreasing sequence:

    f*(t+1) ≥ f*(t)   for all generations t

This is not true for `eaSimple`.

---

## 2. Adaptive operator rates from observed success

**Baseline.** `pmut = 0.9` and `pxov = 0.2` are fixed at the command line
and never updated ([FramsticksEvolution.py:146-147](FramsticksEvolution.py#L146-L147)).
These were chosen *a priori* and stay constant across all 10 settings of
the competition, even though the fitness landscapes are different.

**AMS-EA.** Operator rates are updated online using a credit-assignment
rule
([algorithm.py:229-251](algorithm.py#L229-L251)). For each operator
*op ∈ {mutation, crossover}* we maintain trial and success counters; an
offspring counts as a success if its fitness exceeds the *population
median*. Every 20 trials we update:

    s = successes / trials
    if s > τ_high:  rate ← min(rate_max, rate + 0.02)
    if s < τ_low:   rate ← max(rate_min, rate − 0.02)

with `τ_high = 0.25, τ_low = 0.10` for mutation, and bounds
`[0.40, 0.95]` so the rate never collapses or saturates.

**Why it matters.** This is a form of **Adaptive Operator Selection
(AOS)**, well studied since Davis (1989) and formalized by Fialho et al.
(2010). On problems where the relative usefulness of mutation vs.
crossover varies during the run (typical: exploration early, exploitation
late), adaptive rates dominate any fixed schedule chosen blindly. The
median-based reward avoids the bias of *generational best* rewards (which
over-credit lucky improvements).

---

## 3. Stagnation detection and partial restart

**Baseline.** `eaSimple` has *no* restart mechanism. If the population
converges to a local optimum at generation 3, it will keep mutating around
that optimum for all remaining generations. The diversity, measured by
e.g. genotype Hamming distance, collapses monotonically.

**AMS-EA.** When the best fitness has not improved for
`STAGNATION_WINDOW = 15` generations
([algorithm.py:46](algorithm.py#L46)), we trigger a *partial restart*
([algorithm.py:260-287](algorithm.py#L260-L287)):

1. Keep the elite (top 15%) — preserves what we know.
2. Add up to 5 mutated copies of Hall-of-Fame members — explores the
   neighborhood of historically good basins.
3. Refill the rest (~40% of the population) from a fresh, diverse seeding
   — re-injects exploration entropy.

**Why it matters.** This implements **Random Immigrants** (Grefenstette
1992) combined with **CHC-style restart** (Eshelman 1991). Mathematically,
it raises the mixing time of the underlying Markov chain on the genotype
space, lower-bounding the probability of escaping any basin of attraction
within a finite horizon. On a 100k-evaluation budget with many local
optima, this is the difference between exploring one basin or several.

---

## 4. Hall-of-Fame *re-injection* (not just recording)

**Baseline.** DEAP's `HallOfFame` is a passive log: it tracks the best-N
ever seen but never feeds them back to the population
([FramsticksEvolution.py:210, 233](FramsticksEvolution.py#L210)).

**AMS-EA.** Every 10 generations we replace the worst current individual
with a *mutated* Hall-of-Fame member
([algorithm.py:422-428](algorithm.py#L422-L428)). During restarts we seed
up to 5 mutated HoF members
([algorithm.py:273-278](algorithm.py#L273-L278)).

**Why it matters.** This makes the search non-Markovian in a useful way:
historically good regions can be re-visited even after the population has
drifted away from them. It is a finite-memory approximation of the
*archive-based* methods (NSGA-II archives, MAP-Elites grids) that
consistently outperform memoryless EAs.

---

## 5. Budget-aware evaluation accounting

**Baseline.** `eaSimple` is parameterized in *generations*
([FramsticksEvolution.py:144](FramsticksEvolution.py#L144), default 5).
The actual evaluation count is `popsize × (generations + 1)`. If the user
mis-sizes the run, the algorithm either stops far short of the 100,000
budget (wasting evaluations) or, worse, exceeds the wall-clock and gets
killed mid-generation.

**AMS-EA.** The main loop conditions on remaining evaluations, not
generations ([algorithm.py:207-211, 329-334](algorithm.py#L207-L211)):

    budget_remaining = MAX_EVALUATIONS − SAFETY_MARGIN − total_evaluations

The batch size shrinks gracefully as the budget is exhausted
([algorithm.py:331-336](algorithm.py#L331-L336)), and a 500-evaluation
safety margin ensures we never trigger the simulator's hard kill mid-run.

**Why it matters.** The competition normalizes scores across runs of
identical budget. An algorithm that uses 98,000 of 100,000 evaluations
always weakly dominates one that stops at 50,000. Budget-aware sizing
guarantees we extract every evaluation we are entitled to.

---

## 6. Diverse initialization

**Baseline.** Every individual is the *same* simplest genotype produced by
`getSimplest()` ([FramsticksEvolution.py:66, 119](FramsticksEvolution.py#L66)).
The initial population has zero diversity — all 50 individuals are
identical. The first generation of mutations is the only source of
variation.

**AMS-EA.** We seed each individual by applying a *random number* of
mutations (drawn from `{1,2,3,4,5,6}`) to the simplest genotype
([algorithm.py:120-134](algorithm.py#L120-L134)). The expected pairwise
Hamming distance of the initial population is therefore strictly positive,
covering multiple complexity levels simultaneously.

**Why it matters.** Population diversity at *t = 0* dominates the
asymptotic behavior of any EA with finite restart probability. Starting
from 50 clones means the first 1-2 generations are spent recovering
diversity that should have been there from the start — a pure waste of
the evaluation budget.

---

## 7. Hybrid tournament + rank-based selection

**Baseline.** Pure tournament selection with fixed `tournsize = 5`
([FramsticksEvolution.py:126](FramsticksEvolution.py#L126)). Tournament
selection has constant selection pressure regardless of the fitness
distribution: if all individuals are nearly equal, the winner is
essentially random (good); if one is dramatically better, it dominates
every tournament it enters (bad — premature convergence).

**AMS-EA.** We mix two selection schemes with a 70/30 split
([algorithm.py:355-361](algorithm.py#L355-L361)): tournament-5 (high
pressure, good for exploitation) and linear-ranking (low pressure,
diversity-preserving). Linear ranking assigns selection probability

    p_i = rank_i / Σ rank

so even the worst feasible individual has a non-zero chance of being
selected — preserving genetic material that may recombine into a future
breakthrough.

**Why it matters.** Goldberg & Deb (1991) showed that no single selection
scheme is universally best. A blend reduces variance across landscapes,
which directly improves the *averaged* score across the 10 competition
settings.

---

## 8. Multi-mutation depth under stagnation

**Baseline.** A single `mutate()` call per offspring
([FramsticksEvolution.py:61](FramsticksEvolution.py#L61)). The expected
phenotypic step size is fixed for the entire run.

**AMS-EA.** When stagnation is detected, the mutation depth scales up to 4
sequential mutations per offspring
([algorithm.py:253-258, 137-146](algorithm.py#L253-L258)):

    depth = min(MAX_MUTATION_DEPTH, 1 + gens_without_improvement / (W/2))

This corresponds to taking a larger step in genotype space when the local
gradient information has been exhausted.

**Why it matters.** This is a discrete analogue of **CMA-ES step-size
control** (Hansen 2001): when progress stalls, increase the search radius;
when progress resumes, contract again. The single-mutation baseline cannot
escape local optima that require a coordinated multi-gene change.

---

## Combined effect on the competition objective

The competition score is

    score = (1/10) Σ_s normalize_s( mean over 20 reruns of best fitness )

To win, an algorithm must produce *high mean best-fitness with low
variance* across heterogeneous settings. The eight features above attack
this objective from complementary directions:

| Improvement                  | Reduces variance | Raises mean |
|------------------------------|:----------------:|:-----------:|
| 1. Elitism                   | ✅               | ✅          |
| 2. Adaptive rates            |                  | ✅          |
| 3. Stagnation restart        | ✅               | ✅          |
| 4. HoF re-injection          |                  | ✅          |
| 5. Budget awareness          | ✅               | ✅          |
| 6. Diverse init              | ✅               |             |
| 7. Hybrid selection          | ✅               | ✅          |
| 8. Multi-mutation depth      |                  | ✅          |

None of these features are present in `eaSimple`. Each one is a small,
well-understood improvement; together they form an algorithm whose
expected score under the competition's normalization scheme strictly
dominates the baseline in the limit of repeated trials.

---

## References

- Rudolph, G. (1994). *Convergence analysis of canonical genetic
  algorithms.* IEEE Trans. Neural Networks 5(1).
- Davis, L. (1989). *Adapting operator probabilities in genetic
  algorithms.* ICGA-89.
- Fialho, Á., Da Costa, L., Schoenauer, M., Sebag, M. (2010).
  *Analyzing bandit-based adaptive operator selection mechanisms.*
  Annals of Mathematics and AI 60.
- Grefenstette, J. J. (1992). *Genetic algorithms for changing
  environments.* PPSN II.
- Eshelman, L. J. (1991). *The CHC adaptive search algorithm.* FOGA-1.
- Goldberg, D. E., Deb, K. (1991). *A comparative analysis of selection
  schemes used in genetic algorithms.* FOGA-1.
- Hansen, N., Ostermeier, A. (2001). *Completely derandomized
  self-adaptation in evolution strategies.* Evol. Comput. 9(2).
