import numpy as np
from deap import tools

def run(pop, toolbox, parsed_args, stats, hof):
    """Simple example competition algorithm runner.

    This is a template you can edit. It follows a generational GA similar
    to DEAP's `eaSimple` so it can be compared fairly with the example.
    """
    pop = [tools.clone(ind) for ind in pop]
    log = []
    ngen = parsed_args.generations
    cxpb = parsed_args.pxov
    mutpb = parsed_args.pmut

    for gen in range(1, ngen + 1):
        # Selection
        offspring = toolbox.select(pop, len(pop))
        offspring = [tools.clone(ind) for ind in offspring]

        # Crossover
        for i in range(1, len(offspring), 2):
            if np.random.random() < cxpb:
                offspring[i-1], offspring[i] = toolbox.mate(offspring[i-1], offspring[i])
                try:
                    del offspring[i-1].fitness.values
                    del offspring[i].fitness.values
                except Exception:
                    pass

        # Mutation
        for i in range(len(offspring)):
            if np.random.random() < mutpb:
                offspring[i], = toolbox.mutate(offspring[i])
                try:
                    del offspring[i].fitness.values
                except Exception:
                    pass

        # Evaluate invalid individuals
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        if invalid:
            fitnesses = list(map(toolbox.evaluate, invalid))
            for ind, fit in zip(invalid, fitnesses):
                ind.fitness.values = tuple(fit)

        # Replace population
        pop[:] = offspring

        # Update Hall of Fame and statistics
        hof.update(pop)
        if stats is not None:
            record = stats.compile(pop)
            log.append(record)
            print(f"[competition_algorithm] Gen {gen}: {record}")

    return pop, log
