import argparse
import math
import os
import random
import sys
from dataclasses import dataclass
from time import perf_counter

from FramsticksLibCompetition import FramsticksLibCompetition


COMPETITOR_ID = "SouperTeam"
DEFAULT_GENETIC_FORMAT = "1"
DEFAULT_SIM = "eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim"
MAX_EVALUATIONS = 100_000
EVALUATION_SAFETY_MARGIN = 150
MAX_ALGORITHM_TIME = 3600
TIME_SAFETY_MARGIN = 45


@dataclass
class Individual:
    genotype: str
    fitness: float | None = None
    birth: int = 0


class Archive:
    def __init__(self, max_size):
        self.max_size = max_size
        self.items = []
        self.seen = set()

    def add(self, genotype, fitness):
        if fitness is None:
            return
        if genotype in self.seen:
            for i, current in enumerate(self.items):
                if current[0] == genotype and fitness > current[1]:
                    self.items[i] = (genotype, fitness)
                    break
        else:
            self.items.append((genotype, fitness))
            self.seen.add(genotype)
        self.items.sort(key=lambda item: item[1], reverse=True)
        while len(self.items) > self.max_size:
            removed = self.items.pop()
            self.seen.discard(removed[0])

    def best(self):
        return self.items[0] if self.items else (None, None)

    def sample(self, pressure=2.5):
        if not self.items:
            return None
        r = random.random() ** pressure
        index = min(len(self.items) - 1, int(r * len(self.items)))
        return self.items[index][0]


class HybridOptimizer:
    def __init__(self, frams_lib, args):
        self.frams_lib = frams_lib
        self.args = args
        self.pop_size = args.popsize
        self.elite_count = max(3, int(self.pop_size * args.elite_fraction))
        self.archive = Archive(args.archive_size)
        self.population = []
        self.evaluated_cache = {}
        self.generated = set()
        self.generation = 0
        self.start_time = perf_counter()
        self.last_improvement_generation = 0
        self.best_fitness = None
        self.best_genotype = None
        self.mutation_depth = 1
        self.invalid_offspring = 0
        self.duplicate_offspring = 0
        self.has_structural_constraints = any(
            value is not None
            for value in (
                self.args.max_numparts,
                self.args.max_numjoints,
                self.args.max_numneurons,
                self.args.max_numconnections,
            )
        )

    def evaluations_used(self):
        return getattr(self.frams_lib, "_evaluation_count", 0)

    def remaining_evaluations(self):
        return MAX_EVALUATIONS - EVALUATION_SAFETY_MARGIN - self.evaluations_used()

    def time_left(self):
        return MAX_ALGORITHM_TIME - TIME_SAFETY_MARGIN - (perf_counter() - self.start_time)

    def should_stop(self):
        return self.remaining_evaluations() <= 0 or self.time_left() <= 0

    def constraints_ok(self, genotype):
        if not genotype or genotype == self.frams_lib.GENOTYPE_INVALID:
            return False
        if self.args.max_numgenochars is not None and len(genotype) > self.args.max_numgenochars:
            return False
        if not self.has_structural_constraints:
            return True
        return self.frams_lib.satisfiesConstraints(
            genotype,
            self.args.max_numparts,
            self.args.max_numjoints,
            self.args.max_numneurons,
            self.args.max_numconnections,
            self.args.max_numgenochars,
        )

    def remember_best(self, genotype, fitness):
        if fitness is None:
            return False
        self.archive.add(genotype, fitness)
        if self.best_fitness is None or fitness > self.best_fitness:
            self.best_fitness = fitness
            self.best_genotype = genotype
            self.last_improvement_generation = self.generation
            return True
        return False

    def evaluate_candidates(self, genotypes, birth):
        unique = []
        for genotype in genotypes:
            if genotype in self.evaluated_cache:
                continue
            if not self.constraints_ok(genotype):
                self.evaluated_cache[genotype] = None
                continue
            unique.append(genotype)
            if len(unique) >= self.remaining_evaluations():
                break
        if unique:
            total = len(unique)
            chunk_size = max(1, self.args.eval_chunk)
            for start in range(0, total, chunk_size):
                chunk = unique[start : start + chunk_size]
                print(
                    f"\nEvaluating candidates {start + 1}-{start + len(chunk)}/{total} at generation {self.generation}...",
                    flush=True,
                )
                fitnesses = self.frams_lib.evaluate(chunk)
                for genotype, fitness in zip(chunk, fitnesses):
                    self.evaluated_cache[genotype] = fitness
                    self.remember_best(genotype, fitness)
        individuals = []
        for genotype in genotypes:
            if genotype in self.evaluated_cache:
                individuals.append(Individual(genotype, self.evaluated_cache[genotype], birth))
        return individuals

    def mutate_depth(self, genotype, depth):
        child = genotype
        for _ in range(depth):
            mutated = self.frams_lib.mutate([child])[0]
            if not mutated or mutated == self.frams_lib.GENOTYPE_INVALID:
                self.invalid_offspring += 1
                break
            child = mutated
        return child

    def crossover(self, left, right):
        child = self.frams_lib.crossOver(left, right)
        if not child or child == self.frams_lib.GENOTYPE_INVALID:
            self.invalid_offspring += 1
            return random.choice([left, right])
        return child

    def genotype_distance(self, a, b):
        if a == b:
            return 0.0
        la = len(a)
        lb = len(b)
        if la == 0 or lb == 0:
            return 1.0
        sample = min(80, la, lb)
        stride_a = max(1, la // sample)
        stride_b = max(1, lb // sample)
        aa = a[::stride_a][:sample]
        bb = b[::stride_b][:sample]
        matches = sum(1 for x, y in zip(aa, bb) if x == y)
        return 1.0 - matches / max(len(aa), len(bb), 1)

    def novelty(self, genotype, reference):
        if not reference:
            return 1.0
        sample = random.sample(reference, min(len(reference), 6))
        return sum(self.genotype_distance(genotype, other.genotype) for other in sample) / len(sample)

    def selectable(self):
        valid = [ind for ind in self.population if ind.fitness is not None]
        return valid if valid else self.population

    def tournament_parent(self):
        candidates = random.sample(self.selectable(), min(len(self.selectable()), self.args.tournament))
        return max(candidates, key=lambda ind: -math.inf if ind.fitness is None else ind.fitness)

    def rank_parent(self):
        valid = sorted(self.selectable(), key=lambda ind: -math.inf if ind.fitness is None else ind.fitness)
        if not valid:
            return random.choice(self.population)
        r = random.random() ** 2.0
        return valid[min(len(valid) - 1, int(r * len(valid)))]

    def make_seed_population(self):
        simplest = self.frams_lib.getSimplest(self.args.genformat)
        seeds = [simplest]
        frontier = [simplest]
        depths = [1, 2, 3, 4, 6, 8, 11, 15]
        while len(seeds) < self.pop_size * 2 and not self.should_stop():
            base = random.choice(frontier[-max(1, min(len(frontier), 20)):])
            depth = random.choice(depths)
            genotype = self.mutate_depth(base, depth)
            if genotype not in seeds and self.constraints_ok(genotype):
                seeds.append(genotype)
                frontier.append(genotype)
        return seeds[:self.pop_size]

    def generate_offspring(self, count):
        offspring = []
        attempts = 0
        max_attempts = count * self.args.attempt_factor
        last_progress_time = perf_counter()
        stagnation = self.generation - self.last_improvement_generation
        self.mutation_depth = min(self.args.max_mutation_depth, 1 + stagnation // self.args.depth_step)
        while len(offspring) < count and attempts < max_attempts and not self.should_stop():
            attempts += 1
            roll = random.random()
            if roll < self.args.archive_mutation_rate and self.archive.items:
                base = self.archive.sample()
                depth = random.randint(1, max(1, self.mutation_depth + 2))
                child = self.mutate_depth(base, depth)
            elif roll < self.args.archive_mutation_rate + self.args.crossover_rate and len(self.selectable()) >= 2:
                p1 = self.tournament_parent().genotype
                p2 = self.rank_parent().genotype
                child = self.crossover(p1, p2)
                if random.random() < self.args.post_crossover_mutation_rate:
                    child = self.mutate_depth(child, random.randint(1, max(1, self.mutation_depth)))
            else:
                parent = self.tournament_parent().genotype
                if random.random() < self.args.random_walk_rate:
                    depth = random.randint(self.mutation_depth, self.args.max_mutation_depth + 3)
                else:
                    depth = random.randint(1, max(1, self.mutation_depth))
                child = self.mutate_depth(parent, depth)
            if child in self.generated or child in self.evaluated_cache:
                self.duplicate_offspring += 1
                continue
            if self.constraints_ok(child):
                self.generated.add(child)
                offspring.append(child)
            now = perf_counter()
            if now - last_progress_time >= self.args.progress_seconds:
                print(
                    f"\rGenerating generation {self.generation}: {len(offspring)}/{count} offspring "
                    f"after {attempts}/{max_attempts} attempts...",
                    end="",
                    flush=True,
                )
                last_progress_time = now
        print(
            f"\rGenerated {len(offspring)}/{count} offspring for generation {self.generation} "
            f"after {attempts}/{max_attempts} attempts.{' ' * 20}",
            flush=True,
        )
        return offspring

    def survivor_selection(self, candidates):
        valid = [ind for ind in candidates if ind.fitness is not None]
        invalid = [ind for ind in candidates if ind.fitness is None]
        valid.sort(key=lambda ind: ind.fitness, reverse=True)
        selected = valid[:self.elite_count]
        pool = valid[self.elite_count:]
        while len(selected) < self.pop_size and pool:
            sample_size = min(len(pool), max(10, self.pop_size // 3))
            sample = random.sample(pool, sample_size)
            best = max(
                sample,
                key=lambda ind: ind.fitness + self.args.novelty_weight * abs(ind.fitness) * self.novelty(ind.genotype, selected),
            )
            selected.append(best)
            pool.remove(best)
        if len(selected) < self.pop_size:
            selected.extend(invalid[: self.pop_size - len(selected)])
        return selected[:self.pop_size]

    def local_improvement_burst(self):
        if not self.archive.items or self.remaining_evaluations() <= 0:
            return []
        budget = min(self.args.local_burst, self.remaining_evaluations())
        candidates = []
        bases = [item[0] for item in self.archive.items[: min(8, len(self.archive.items))]]
        while len(candidates) < budget and bases:
            base = random.choice(bases)
            depth = random.choice([1, 1, 2, 2, 3, self.mutation_depth])
            child = self.mutate_depth(base, max(1, depth))
            if child not in self.generated and child not in self.evaluated_cache and self.constraints_ok(child):
                self.generated.add(child)
                candidates.append(child)
        return self.evaluate_candidates(candidates, self.generation)

    def restart_if_needed(self):
        stagnation = self.generation - self.last_improvement_generation
        if stagnation < self.args.restart_after:
            return
        keep = [Individual(g, f, self.generation) for g, f in self.archive.items[: self.elite_count]]
        fresh_count = max(0, self.pop_size - len(keep))
        fresh = []
        simplest = self.frams_lib.getSimplest(self.args.genformat)
        sources = [simplest] + [g for g, _ in self.archive.items[:10]]
        attempts = 0
        while len(fresh) < fresh_count and attempts < fresh_count * 30 and not self.should_stop():
            attempts += 1
            source = random.choice(sources)
            depth = random.randint(2, self.args.max_mutation_depth + 6)
            child = self.mutate_depth(source, depth)
            if child not in self.generated and child not in self.evaluated_cache and self.constraints_ok(child):
                self.generated.add(child)
                fresh.append(child)
        evaluated = self.evaluate_candidates(fresh, self.generation)
        self.population = self.survivor_selection(keep + evaluated + self.population)
        self.last_improvement_generation = self.generation

    def print_status(self, final=False):
        elapsed = perf_counter() - self.start_time
        used = self.evaluations_used()
        pct = min(100.0, 100.0 * used / max(1, MAX_EVALUATIONS - EVALUATION_SAFETY_MARGIN))
        best = "None" if self.best_fitness is None else f"{self.best_fitness:.6g}"
        end = "\n" if final else ""
        print(
            f"\rGen {self.generation:5d} | evals {used:6d} ({pct:5.1f}%) | best {best} | "
            f"depth {self.mutation_depth} | cache {len(self.evaluated_cache)} | time {elapsed:6.1f}s",
            end=end,
            flush=True,
        )

    def run(self):
        print("Creating initial population...", flush=True)
        seed_genotypes = self.make_seed_population()
        self.generated.update(seed_genotypes)
        self.population = self.evaluate_candidates(seed_genotypes, 0)
        self.population = self.survivor_selection(self.population)
        self.print_status()
        while not self.should_stop():
            self.generation += 1
            batch_size = min(self.args.batch_size, self.remaining_evaluations())
            if batch_size <= 0:
                break
            print(f"\nStarting generation {self.generation} with batch size {batch_size}.", flush=True)
            offspring_genotypes = self.generate_offspring(batch_size)
            if not offspring_genotypes:
                self.restart_if_needed()
                if not self.population:
                    break
                continue
            offspring = self.evaluate_candidates(offspring_genotypes, self.generation)
            candidates = self.population + offspring
            if self.generation % self.args.local_every == 0:
                candidates.extend(self.local_improvement_burst())
            self.population = self.survivor_selection(candidates)
            self.restart_if_needed()
            if self.generation % self.args.status_every == 0:
                self.print_status()
        self.print_status(final=True)
        print("Best fitness:", self.best_fitness)
        print("Best genotype:", self.best_genotype)


def existing_directory(path):
    if os.path.isdir(path):
        return path
    raise NotADirectoryError(path)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Hybrid adaptive Framsticks optimizer for GECCO COG trajectory competition.")
    parser.add_argument("-path", type=existing_directory, required=True, help="Path to Framsticks library without trailing slash.")
    parser.add_argument("-lib", required=False, help="Library name. If omitted, the platform default is used.")
    parser.add_argument("-sim", required=False, default=DEFAULT_SIM, help="Semicolon-separated Framsticks simulation settings files.")
    parser.add_argument("-genformat", required=False, default=DEFAULT_GENETIC_FORMAT, help="Genetic format. Default: 1.")
    parser.add_argument("-popsize", type=int, default=80, help="Population size.")
    parser.add_argument("-batch_size", type=int, default=30, help="Offspring evaluations per generation.")
    parser.add_argument("-eval_chunk", type=int, default=10, help="Number of candidates evaluated before printing progress again.")
    parser.add_argument("-attempt_factor", type=int, default=8, help="Maximum offspring generation attempts per requested offspring.")
    parser.add_argument("-progress_seconds", type=float, default=5.0, help="Seconds between offspring generation progress messages.")
    parser.add_argument("-tournament", type=int, default=7, help="Tournament size.")
    parser.add_argument("-elite_fraction", type=float, default=0.18, help="Fraction of population preserved as strict elites.")
    parser.add_argument("-archive_size", type=int, default=80, help="Number of best genotypes retained in archive.")
    parser.add_argument("-crossover_rate", type=float, default=0.22, help="Probability of crossover offspring.")
    parser.add_argument("-archive_mutation_rate", type=float, default=0.28, help="Probability of mutating an archived elite.")
    parser.add_argument("-post_crossover_mutation_rate", type=float, default=0.72, help="Probability of mutating after crossover.")
    parser.add_argument("-random_walk_rate", type=float, default=0.16, help="Probability of deeper exploratory mutation.")
    parser.add_argument("-max_mutation_depth", type=int, default=8, help="Maximum adaptive mutation chain depth.")
    parser.add_argument("-depth_step", type=int, default=12, help="Stagnant generations needed to increase mutation depth.")
    parser.add_argument("-restart_after", type=int, default=45, help="Generations without improvement before restart.")
    parser.add_argument("-local_every", type=int, default=5, help="Run elite local improvement every N generations.")
    parser.add_argument("-local_burst", type=int, default=35, help="Extra elite-neighborhood evaluations during local improvement.")
    parser.add_argument("-novelty_weight", type=float, default=0.015, help="Small diversity bonus in survivor selection.")
    parser.add_argument("-status_every", type=int, default=1, help="Print status every N generations.")
    parser.add_argument("-max_numparts", type=int, default=None, help="Maximum number of Parts.")
    parser.add_argument("-max_numjoints", type=int, default=None, help="Maximum number of Joints.")
    parser.add_argument("-max_numneurons", type=int, default=None, help="Maximum number of Neurons.")
    parser.add_argument("-max_numconnections", type=int, default=None, help="Maximum number of neural connections.")
    parser.add_argument("-max_numgenochars", type=int, default=None, help="Maximum genotype length.")
    return parser.parse_args()


def main():
    args = parse_arguments()
    FramsticksLibCompetition.COMPETITOR_ID = COMPETITOR_ID
    FramsticksLibCompetition.SIMPLE_FITNESS_FORMAT = True
    FramsticksLibCompetition.DETERMINISTIC = False
    frams_lib = FramsticksLibCompetition(args.path, args.lib, args.sim)
    try:
        optimizer = HybridOptimizer(frams_lib, args)
        optimizer.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        try:
            frams_lib.end()
        except SystemExit:
            pass


if __name__ == "__main__":
    main()
