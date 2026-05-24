#!/usr/bin/env python3
"""
SouperTeam GECCO Competition Algorithm
Adaptive Multi-Strategy Evolutionary Optimization for Framsticks COG Trajectory.

Improvements over baseline FramsticksEvolution.py (DEAP eaSimple):
1. Strong elitism - top individuals always survive
2. Adaptive mutation intensity - applies multiple mutations when stagnating
3. Stagnation detection with partial population restart
4. Hall-of-fame seeding - best-ever solutions re-enter population
5. Budget-aware generation sizing
6. Diverse initialization with varied mutation depths
7. Rank-based selection pressure scaling
8. Operator success tracking with adaptive rates
"""

import sys
import os
import argparse
import random
import math
from time import perf_counter

import numpy as np

from FramsticksLibCompetition import FramsticksLibCompetition


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPETITOR_ID = "SouperTeam"

POPULATION_SIZE = 60
ELITE_FRACTION = 0.15          # top 15% always survive
TOURNAMENT_SIZE = 5
INITIAL_MUTATION_RATE = 0.85
INITIAL_CROSSOVER_RATE = 0.30
MIN_MUTATION_RATE = 0.40
MAX_MUTATION_RATE = 0.95
MIN_CROSSOVER_RATE = 0.10
MAX_CROSSOVER_RATE = 0.50

# Stagnation detection
STAGNATION_WINDOW = 15         # generations without improvement before restart
RESTART_FRACTION = 0.40        # fraction of population to restart

# Multi-mutation: when stagnating, apply mutation multiple times
MAX_MUTATION_DEPTH = 4         # max consecutive mutations on one individual

# Budget
MAX_EVALUATIONS = 100_000
SAFETY_MARGIN = 500            # stop this many evals before hard limit

# Initialization diversity
INIT_MUTATION_DEPTHS = [1, 2, 3, 4, 5, 6]  # varied complexity for initial pop

# Genetic format
DEFAULT_GENETIC_FORMAT = "1"   # f1 encoding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def evaluate_batch(frams_lib, genotypes):
    """Evaluate a list of genotypes. Returns list of (genotype, fitness) tuples."""
    fitnesses = frams_lib.evaluate(genotypes)
    return list(zip(genotypes, fitnesses))


def is_valid(fitness):
    """Check if a fitness value is valid (not None)."""
    return fitness is not None


def tournament_select(population, fitnesses, k, tournament_size):
    """Select k individuals via tournament selection. Only considers valid fitnesses."""
    selected = []
    valid_indices = [i for i, f in enumerate(fitnesses) if is_valid(f)]
    if not valid_indices:
        # fallback: random selection from entire population
        return [population[random.randint(0, len(population) - 1)] for _ in range(k)]

    for _ in range(k):
        candidates = random.choices(valid_indices, k=tournament_size)
        best = max(candidates, key=lambda i: fitnesses[i])
        selected.append(population[best])
    return selected


def rank_based_select(population, fitnesses, k):
    """Rank-based selection with linear ranking pressure."""
    indexed = [(i, f) for i, f in enumerate(fitnesses) if is_valid(f)]
    if not indexed:
        return [population[random.randint(0, len(population) - 1)] for _ in range(k)]

    indexed.sort(key=lambda x: x[1])
    n = len(indexed)
    # Linear ranking: probability proportional to rank
    weights = [i + 1 for i in range(n)]
    total = sum(weights)
    probs = [w / total for w in weights]

    selected = []
    for _ in range(k):
        r = random.random()
        cumulative = 0.0
        for j, (idx, _) in enumerate(indexed):
            cumulative += probs[j]
            if r <= cumulative:
                selected.append(population[idx])
                break
        else:
            selected.append(population[indexed[-1][0]])
    return selected


def create_diverse_population(frams_lib, size, genetic_format):
    """Create a diverse initial population with varied mutation depths."""
    population = []
    simplest = frams_lib.getSimplest(genetic_format)

    for i in range(size):
        genotype = simplest
        depth = random.choice(INIT_MUTATION_DEPTHS)
        for _ in range(depth):
            mutated = frams_lib.mutate([genotype])[0]
            if mutated is not None:
                genotype = mutated
        population.append(genotype)

    return population


def apply_mutations(frams_lib, genotype, depth=1):
    """Apply mutation multiple times to a genotype for stronger exploration."""
    result = genotype
    for _ in range(depth):
        mutated = frams_lib.mutate([result])[0]
        if mutated is not None:
            result = mutated
        else:
            break
    return result


# ---------------------------------------------------------------------------
# Main Algorithm
# ---------------------------------------------------------------------------

class AdaptiveEvolution:
    """Adaptive Multi-Strategy Evolutionary Algorithm."""

    def __init__(self, frams_lib, genetic_format=DEFAULT_GENETIC_FORMAT,
                 population_size=POPULATION_SIZE):
        self.frams_lib = frams_lib
        self.genetic_format = genetic_format
        self.pop_size = population_size
        self.elite_count = max(2, int(self.pop_size * ELITE_FRACTION))

        # Adaptive parameters
        self.mutation_rate = INITIAL_MUTATION_RATE
        self.crossover_rate = INITIAL_CROSSOVER_RATE
        self.mutation_depth = 1

        # Tracking
        self.best_fitness = None
        self.best_genotype = None
        self.generations_without_improvement = 0
        self.total_evaluations = 0
        self.generation = 0

        # Operator success tracking
        self.mutation_successes = 0
        self.mutation_trials = 0
        self.crossover_successes = 0
        self.crossover_trials = 0

        # Hall of fame (archive of best-ever solutions)
        self.hall_of_fame = []
        self.hof_max_size = 20

        self.start_time = perf_counter()

    def _budget_remaining(self):
        return MAX_EVALUATIONS - SAFETY_MARGIN - self.total_evaluations

    def _should_stop(self):
        return self._budget_remaining() <= 0

    def _update_best(self, genotype, fitness):
        if fitness is not None and (self.best_fitness is None or fitness > self.best_fitness):
            self.best_fitness = fitness
            self.best_genotype = genotype
            self.generations_without_improvement = 0
            self._update_hof(genotype, fitness)
            return True
        return False

    def _update_hof(self, genotype, fitness):
        """Maintain hall of fame of best-ever solutions."""
        self.hall_of_fame.append((genotype, fitness))
        self.hall_of_fame.sort(key=lambda x: x[1], reverse=True)
        if len(self.hall_of_fame) > self.hof_max_size:
            self.hall_of_fame = self.hall_of_fame[:self.hof_max_size]

    def _adapt_parameters(self):
        """Adapt mutation/crossover rates based on operator success."""
        # Adapt mutation rate
        if self.mutation_trials > 20:
            success_rate = self.mutation_successes / self.mutation_trials
            if success_rate > 0.25:
                # Mutations are working well, increase slightly
                self.mutation_rate = min(MAX_MUTATION_RATE, self.mutation_rate + 0.02)
            elif success_rate < 0.10:
                # Mutations rarely improve, decrease
                self.mutation_rate = max(MIN_MUTATION_RATE, self.mutation_rate - 0.02)
            self.mutation_successes = 0
            self.mutation_trials = 0

        # Adapt crossover rate
        if self.crossover_trials > 20:
            success_rate = self.crossover_successes / self.crossover_trials
            if success_rate > 0.20:
                self.crossover_rate = min(MAX_CROSSOVER_RATE, self.crossover_rate + 0.02)
            elif success_rate < 0.05:
                self.crossover_rate = max(MIN_CROSSOVER_RATE, self.crossover_rate - 0.02)
            self.crossover_successes = 0
            self.crossover_trials = 0

        # Adapt mutation depth based on stagnation
        if self.generations_without_improvement > STAGNATION_WINDOW // 2:
            self.mutation_depth = min(MAX_MUTATION_DEPTH,
                                     1 + self.generations_without_improvement // (STAGNATION_WINDOW // 2))
        else:
            self.mutation_depth = 1

    def _partial_restart(self, population, fitnesses):
        """Restart a fraction of the population when stagnating."""
        print(f"  [Restart] Stagnation detected after {self.generations_without_improvement} gens. "
              f"Restarting {int(RESTART_FRACTION * 100)}% of population.")

        # Keep elites
        sorted_indices = sorted(
            [i for i, f in enumerate(fitnesses) if is_valid(f)],
            key=lambda i: fitnesses[i], reverse=True
        )
        keep_count = self.elite_count
        new_pop = [population[i] for i in sorted_indices[:keep_count]]

        # Seed some from hall of fame with extra mutations
        hof_seed_count = min(5, len(self.hall_of_fame))
        for i in range(hof_seed_count):
            geno = self.hall_of_fame[i][0]
            mutated = apply_mutations(self.frams_lib, geno, depth=random.randint(2, 4))
            new_pop.append(mutated)

        # Fill rest with fresh random individuals
        fill_count = self.pop_size - len(new_pop)
        fresh = create_diverse_population(self.frams_lib, fill_count, self.genetic_format)
        new_pop.extend(fresh)

        self.generations_without_improvement = 0
        self.mutation_depth = 1
        return new_pop

    def _create_offspring(self, parents, parent_fitnesses):
        """Create one offspring using adaptive operators."""
        if random.random() < self.crossover_rate and len(parents) >= 2:
            # Crossover
            p1 = random.choice(parents)
            p2 = random.choice(parents)
            child = self.frams_lib.crossOver(p1, p2)
            self.crossover_trials += 1
            if child is None:
                child = apply_mutations(self.frams_lib, p1, self.mutation_depth)
            operator = "crossover"
        else:
            # Mutation
            parent = random.choice(parents)
            child = apply_mutations(self.frams_lib, parent, self.mutation_depth)
            self.mutation_trials += 1
            operator = "mutation"

        return child, operator

    def run(self):
        """Main evolutionary loop."""
        print(f"Initializing population (size={self.pop_size}, format=f{self.genetic_format})...")
        population = create_diverse_population(self.frams_lib, self.pop_size, self.genetic_format)

        # Initial evaluation
        if self._should_stop():
            return
        results = evaluate_batch(self.frams_lib, population)
        self.total_evaluations += len(population)
        fitnesses = [f for _, f in results]

        for geno, fit in results:
            if is_valid(fit):
                self._update_best(geno, fit)

        print(f"  Initial best: {self.best_fitness}")

        # Main loop
        while not self._should_stop():
            self.generation += 1
            budget = self._budget_remaining()
            if budget < self.pop_size:
                # Not enough budget for full generation, do smaller batch
                batch_size = max(1, budget)
            else:
                batch_size = self.pop_size

            # Check for stagnation restart
            if self.generations_without_improvement >= STAGNATION_WINDOW:
                population = self._partial_restart(population, fitnesses)
                # Re-evaluate the new population
                eval_count = min(len(population), self._budget_remaining())
                if eval_count <= 0:
                    break
                results = evaluate_batch(self.frams_lib, population[:eval_count])
                self.total_evaluations += eval_count
                fitnesses = [f for _, f in results]
                # Pad with None if not all evaluated
                fitnesses.extend([None] * (len(population) - eval_count))
                for geno, fit in results:
                    if is_valid(fit):
                        self._update_best(geno, fit)
                continue

            # Selection: combine tournament and rank-based
            if random.random() < 0.7:
                selected_parents = tournament_select(
                    population, fitnesses, batch_size, TOURNAMENT_SIZE)
            else:
                selected_parents = rank_based_select(
                    population, fitnesses, batch_size)

            # Create offspring
            offspring = []
            operators_used = []
            for _ in range(batch_size):
                if self._should_stop():
                    break
                child, operator = self._create_offspring(selected_parents, fitnesses)
                if child is not None:
                    offspring.append(child)
                    operators_used.append(operator)

            if not offspring or self._should_stop():
                break

            # Evaluate offspring
            eval_count = min(len(offspring), self._budget_remaining())
            if eval_count <= 0:
                break
            offspring = offspring[:eval_count]
            operators_used = operators_used[:eval_count]

            results = evaluate_batch(self.frams_lib, offspring)
            self.total_evaluations += len(offspring)
            offspring_fitnesses = [f for _, f in results]

            # Track operator success
            for i, (geno, fit) in enumerate(results):
                if is_valid(fit):
                    self._update_best(geno, fit)
                    # Check if offspring is better than population median
                    valid_parent_fits = [f for f in fitnesses if is_valid(f)]
                    if valid_parent_fits:
                        median_fit = np.median(valid_parent_fits)
                        if fit > median_fit:
                            if operators_used[i] == "mutation":
                                self.mutation_successes += 1
                            else:
                                self.crossover_successes += 1

            # Elitist replacement: keep elite from current pop + best offspring
            # Merge current population and offspring
            all_genotypes = list(population) + offspring
            all_fitnesses = list(fitnesses) + offspring_fitnesses

            # Sort by fitness (valid ones first, then by value descending)
            indexed = list(range(len(all_genotypes)))
            indexed.sort(key=lambda i: all_fitnesses[i] if is_valid(all_fitnesses[i]) else -1e18,
                         reverse=True)

            # New population: top pop_size individuals
            new_pop = []
            new_fit = []
            for idx in indexed[:self.pop_size]:
                new_pop.append(all_genotypes[idx])
                new_fit.append(all_fitnesses[idx])

            population = new_pop
            fitnesses = new_fit

            # Occasionally inject hall-of-fame individual (every 10 gens)
            if self.generation % 10 == 0 and self.hall_of_fame:
                hof_geno = self.hall_of_fame[0][0]
                # Replace worst individual with mutated HoF member
                mutated_hof = apply_mutations(self.frams_lib, hof_geno, depth=random.randint(1, 2))
                population[-1] = mutated_hof
                fitnesses[-1] = None  # will be evaluated next generation

            self.generations_without_improvement += 1
            self._adapt_parameters()

            # Progress report every 10 generations
            if self.generation % 10 == 0:
                valid_count = sum(1 for f in fitnesses if is_valid(f))
                elapsed = perf_counter() - self.start_time
                print(f"  Gen {self.generation:4d} | Best: {self.best_fitness:.4f} | "
                      f"Evals: {self.total_evaluations:6d} | "
                      f"Valid: {valid_count}/{self.pop_size} | "
                      f"MutRate: {self.mutation_rate:.2f} | "
                      f"MutDepth: {self.mutation_depth} | "
                      f"Stag: {self.generations_without_improvement} | "
                      f"Time: {elapsed:.1f}s")

        print(f"\n{'='*60}")
        print(f"Algorithm complete.")
        print(f"  Generations: {self.generation}")
        print(f"  Total evaluations: {self.total_evaluations}")
        print(f"  Best fitness: {self.best_fitness}")
        print(f"  Best genotype: {self.best_genotype}")
        print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='SouperTeam GECCO Competition Algorithm. '
                    'Run with "python -u %s" to disable output buffering.' % sys.argv[0])
    parser.add_argument('-path', type=str, required=True,
                        help='Path to Framsticks library without trailing slash.')
    parser.add_argument('-lib', required=False,
                        help='Library name. If not given, platform default is assumed.')
    parser.add_argument('-sim', required=False, default="eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim",
                        help='The .sim file(s) with settings. Separate multiple with semicolons.')
    parser.add_argument('-genformat', required=False, default=DEFAULT_GENETIC_FORMAT,
                        help='Genetic format (0, 1, 4, 9, B). Default: 1')
    parser.add_argument('-popsize', type=int, default=POPULATION_SIZE,
                        help=f'Population size. Default: {POPULATION_SIZE}')
    parser.add_argument('-max_numparts', type=int, default=None,
                        help='Maximum number of Parts. Default: no limit')
    parser.add_argument('-max_numjoints', type=int, default=None,
                        help='Maximum number of Joints. Default: no limit')
    parser.add_argument('-max_numneurons', type=int, default=None,
                        help='Maximum number of Neurons. Default: no limit')
    parser.add_argument('-max_numconnections', type=int, default=None,
                        help='Maximum number of Neural connections. Default: no limit')
    parser.add_argument('-max_numgenochars', type=int, default=None,
                        help='Maximum number of characters in genotype. Default: no limit')
    return parser.parse_args()


def ensure_dir(path):
    if os.path.isdir(path):
        return path
    raise NotADirectoryError(path)


def main():
    parsed_args = parse_arguments()
    ensure_dir(parsed_args.path)

    print(f"SouperTeam GECCO Competition Algorithm")
    print(f"Arguments: {vars(parsed_args)}")
    print(f"-" * 60)

    # Set competitor ID before instantiation
    FramsticksLibCompetition.COMPETITOR_ID = COMPETITOR_ID
    FramsticksLibCompetition.SIMPLE_FITNESS_FORMAT = True

    # Initialize the competition library
    frams_lib = FramsticksLibCompetition(
        parsed_args.path,
        parsed_args.lib,
        parsed_args.sim
    )

    # Run the algorithm
    try:
        algo = AdaptiveEvolution(
            frams_lib,
            genetic_format=parsed_args.genformat,
            population_size=parsed_args.popsize
        )
        algo.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Error during evolution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # CRITICAL: Always call end() when done
        try:
            frams_lib.end()
        except SystemExit:
            pass


if __name__ == "__main__":
    main()
