"""Run and compare the repository example algorithm with a custom competition algorithm.

Usage: python -u compare_algorithms.py -path PATH_TO_LIB -opt vertpos -popsize 20 -generations 5 ...
"""
from FramsticksLib import FramsticksLib
from FramsticksEvolution import parseArguments, prepareToolbox
from deap import tools, algorithms
import numpy as np
import competition_algorithm


def make_stats():
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    filter_feasible_for_function = lambda function, fitness_criteria: function(list(filter(lambda v: all(x != -999999.0 for x in v), fitness_criteria)))
    stats.register("avg", lambda fitness_criteria: filter_feasible_for_function(np.mean, fitness_criteria))
    stats.register("stddev", lambda fitness_criteria: filter_feasible_for_function(np.std, fitness_criteria))
    stats.register("min", lambda fitness_criteria: filter_feasible_for_function(np.min, fitness_criteria))
    stats.register("max", lambda fitness_criteria: filter_feasible_for_function(np.max, fitness_criteria))
    return stats


def summarize_hof(hof):
    if len(hof) == 0:
        return "(empty)"
    lines = []
    for ind in hof:
        lines.append(f"fitness={ind.fitness.values}\tgenotype={ind[0]}")
    return "\n".join(lines)


def main():
    parsed_args = parseArguments()
    OPTIMIZATION_CRITERIA = parsed_args.opt.split(",")

    framsLib = FramsticksLib(parsed_args.path, parsed_args.lib, parsed_args.sim)
    toolbox = prepareToolbox(framsLib, OPTIMIZATION_CRITERIA, parsed_args.tournament, '1' if parsed_args.genformat is None else parsed_args.genformat, parsed_args.initialgenotype)

    # create identical initial population then clone for independent runs
    initial_pop = toolbox.population(n=parsed_args.popsize)
    pop_example = [tools.clone(ind) for ind in initial_pop]
    pop_custom = [tools.clone(ind) for ind in initial_pop]

    # stats and hof for each run
    stats1 = make_stats()
    stats2 = make_stats()
    hof1 = tools.HallOfFame(parsed_args.hof_size)
    hof2 = tools.HallOfFame(parsed_args.hof_size)

    print("Running example algorithm (eaSimple)...")
    pop1, log1 = algorithms.eaSimple(pop_example, toolbox, cxpb=parsed_args.pxov, mutpb=parsed_args.pmut, ngen=parsed_args.generations, stats=stats1, halloffame=hof1, verbose=True)

    print("Running custom competition algorithm...")
    pop2, log2 = competition_algorithm.run(pop_custom, toolbox, parsed_args, stats2, hof2)

    print("\n=== Comparison summary ===")
    print("Example algorithm Hall of Fame:")
    print(summarize_hof(hof1))
    print("\nCustom algorithm Hall of Fame:")
    print(summarize_hof(hof2))

    # quick numeric comparison (best max per run)
    def best_value(hof):
        if len(hof) == 0:
            return None
        return max(ind.fitness.values[0] for ind in hof)

    best1 = best_value(hof1)
    best2 = best_value(hof2)
    print(f"\nBest fitness (example): {best1}")
    print(f"Best fitness (custom):  {best2}")


if __name__ == "__main__":
    main()
