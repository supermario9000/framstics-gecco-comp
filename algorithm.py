from deap import tools
import numpy as np

def run(pop, toolbox, parsed_args, stats, hof):
    log = []
    ngen = parsed_args.generations
    cxpb = parsed_args.pxov
    mutpb = parsed_args.pmut
    for gen in range(1, ngen + 1):
        # Selection
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation
        for i in range(1, len(offspring), 2):
            if np.random.random() < cxpb:
                offspring[i-1], offspring[i] = toolbox.mate(offspring[i-1], offspring[i])
                del offspring[i-1].fitness.values
                del offspring[i].fitness.values
        for i in range(len(offspring)):
            if np.random.random() < mutpb:
                offspring[i], = toolbox.mutate(offspring[i])
                del offspring[i].fitness.values

        # Evaluate invalid individuals
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid)
        for ind, fit in zip(invalid, fitnesses):
            ind.fitness.values = tuple(fit)

        # Replace population and update hall of fame/statistics
        pop[:] = offspring
        hof.update(pop)
        if stats is not None:
            record = stats.compile(pop)
            log.append(record)
            print(f"Gen {gen}: {record}")
    return pop, log