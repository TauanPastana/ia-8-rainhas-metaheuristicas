import argparse
import csv
import math
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean, pstdev

N = 8

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass
class RunResult:
    algorithm: str
    run_id: int
    time_seconds: float
    iterations: int
    best_solution: str
    final_conflicts: int
    success: int
    final_fitness: float


def count_conflicts(board):
    conflicts = 0
    for i in range(N):
        for j in range(i + 1, N):
            same_row = board[i] == board[j]
            same_diag = abs(board[i] - board[j]) == abs(i - j)
            if same_row or same_diag:
                conflicts += 1
    return conflicts


def fitness_from_conflicts(conflicts):
    return 1 / (1 + conflicts)


def random_board():
    return [random.randint(0, N - 1) for _ in range(N)]


def board_to_binary(board):
    bits = []
    for row in board:
        bits.extend(int(b) for b in format(row, "03b"))
    return bits


def binary_to_board(bits):
    board = []
    for i in range(0, len(bits), 3):
        chunk = bits[i:i + 3]
        if len(chunk) < 3:
            chunk = chunk + [0] * (3 - len(chunk))
        row = int("".join(str(b) for b in chunk), 2) % N
        board.append(row)
    return board[:N]


def board_to_str(board):
    return "[" + ", ".join(map(str, board)) + "]"


def unique_top_solutions(results, top_k=5):
    seen = set()
    top = []
    for r in sorted(results, key=lambda x: (x["final_conflicts"], x["time_seconds"])):
        s = r["best_solution"]
        if s not in seen:
            seen.add(s)
            top.append(r)
        if len(top) == top_k:
            break
    return top


def greedy_randomized_construction(rcl_size):
    board = [-1] * N
    for col in range(N):
        candidates = []
        for row in range(N):
            board[col] = row
            conflicts = 0
            for prev_col in range(col):
                if board[prev_col] == row or abs(board[prev_col] - row) == abs(prev_col - col):
                    conflicts += 1
            candidates.append((conflicts, row))
        candidates.sort(key=lambda x: x[0])
        rcl = candidates[:max(1, min(rcl_size, len(candidates)))]
        board[col] = random.choice(rcl)[1]
    return board


def local_search(board):
    current = board[:]
    current_conflicts = count_conflicts(current)
    improved = True

    while improved:
        improved = False
        best_board = current[:]
        best_conflicts = current_conflicts

        for col in range(N):
            original = current[col]
            for row in range(N):
                if row == original:
                    continue
                candidate = current[:]
                candidate[col] = row
                c = count_conflicts(candidate)
                if c < best_conflicts:
                    best_conflicts = c
                    best_board = candidate[:]
                    improved = True

        current = best_board
        current_conflicts = best_conflicts

    return current


def grasp(max_iterations=200, rcl_size=3):
    start = time.perf_counter()
    best_board = None
    best_conflicts = math.inf
    iterations_used = 0

    for it in range(max_iterations):
        iterations_used = it + 1
        candidate = greedy_randomized_construction(rcl_size)
        candidate = local_search(candidate)
        conflicts = count_conflicts(candidate)

        if conflicts < best_conflicts:
            best_conflicts = conflicts
            best_board = candidate[:]

        if best_conflicts == 0:
            break

    elapsed = time.perf_counter() - start
    final_fitness = fitness_from_conflicts(best_conflicts)
    return {
        "algorithm": "GRASP",
        "time_seconds": elapsed,
        "iterations": iterations_used,
        "best_solution": best_board,
        "final_conflicts": best_conflicts,
        "final_fitness": fitness_from_conflicts(best_conflicts),
        "success": int(best_conflicts == 0),
    }


def random_binary_individual():
    return board_to_binary(random_board())


def roulette_select(population, fitnesses):
    total = sum(fitnesses)
    if total == 0:
        return random.choice(population)
    pick = random.uniform(0, total)
    acc = 0
    for individual, fit in zip(population, fitnesses):
        acc += fit
        if acc >= pick:
            return individual
    return population[-1]


def one_point_crossover(p1, p2):
    point = random.randint(1, len(p1) - 1)
    return p1[:point] + p2[point:]


def mutate(individual, mutation_rate):
    mutated = individual[:]
    for i in range(len(mutated)):
        if random.random() < mutation_rate:
            mutated[i] = 1 - mutated[i]
    return mutated


def genetic_algorithm(pop_size=20, crossover_rate=0.80, mutation_rate=0.03, max_generations=1000):
    start = time.perf_counter()
    population = [random_binary_individual() for _ in range(pop_size)]
    best_solution = None
    best_conflicts = math.inf
    generations_used = 0

    for gen in range(max_generations):
        generations_used = gen + 1
        decoded = [binary_to_board(ind) for ind in population]
        conflicts_list = [count_conflicts(board) for board in decoded]
        fitnesses = [fitness_from_conflicts(c) for c in conflicts_list]

        best_idx = min(range(len(conflicts_list)), key=lambda i: conflicts_list[i])
        if conflicts_list[best_idx] < best_conflicts:
            best_conflicts = conflicts_list[best_idx]
            best_solution = decoded[best_idx][:]

        if best_conflicts == 0:
            break

        elite_count = max(1, pop_size // 5)
        elite_indices = sorted(range(pop_size), key=lambda i: conflicts_list[i])[:elite_count]
        new_population = [population[i][:] for i in elite_indices]

        while len(new_population) < pop_size:
            parent1 = roulette_select(population, fitnesses)
            parent2 = roulette_select(population, fitnesses)
            child = parent1[:]
            if random.random() < crossover_rate:
                child = one_point_crossover(parent1, parent2)
            child = mutate(child, mutation_rate)
            new_population.append(child)

        population = new_population

    elapsed = time.perf_counter() - start
    
    return {
        "algorithm": "GA",
        "time_seconds": elapsed,
        "iterations": generations_used,
        "best_solution": best_solution,
        "final_conflicts": best_conflicts,
        "final_fitness": fitness_from_conflicts(best_conflicts),
        "success": int(best_conflicts == 0),
    }


def run_experiments(runs, grasp_iterations, rcl_size, pop_size, crossover_rate, mutation_rate, max_generations):
    results = []
    for i in range(1, runs + 1):
        r = grasp(grasp_iterations, rcl_size)
        results.append(RunResult(
            algorithm=r["algorithm"],
            run_id=i,
            time_seconds=r["time_seconds"],
            iterations=r["iterations"],
            best_solution=board_to_str(r["best_solution"]),
            final_conflicts=r["final_conflicts"],
            final_fitness=r["final_fitness"],
            success=r["success"]
        ))

    for i in range(1, runs + 1):
        r = genetic_algorithm(pop_size, crossover_rate, mutation_rate, max_generations)
        results.append(RunResult(
            algorithm=r["algorithm"],
            run_id=i,
            time_seconds=r["time_seconds"],
            iterations=r["iterations"],
            best_solution=board_to_str(r["best_solution"]),
            final_conflicts=r["final_conflicts"],
            final_fitness=r["final_fitness"],
            success=r["success"]
        ))

    return results


def summarize(results):
    summary = []
    for alg in sorted(set(r.algorithm for r in results)):
        alg_results = [r for r in results if r.algorithm == alg]
        times = [r.time_seconds for r in alg_results]
        iters = [r.iterations for r in alg_results]
        conflicts = [r.final_conflicts for r in alg_results]
        success_rate = sum(r.success for r in alg_results) / len(alg_results)
        summary.append({
            "algorithm": alg,
            "runs": len(alg_results),
            "mean_time_seconds": mean(times),
            "std_time_seconds": pstdev(times) if len(times) > 1 else 0.0,
            "mean_iterations": mean(iters),
            "std_iterations": pstdev(iters) if len(iters) > 1 else 0.0,
            "success_rate": success_rate,
            "mean_final_conflicts": mean(conflicts),
            "best_conflicts": min(conflicts),
            "worst_conflicts": max(conflicts),
        })
    return summary


def save_results_csv(results, filename="results.csv"):
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    return path


def save_summary_csv(summary, filename="summary.csv"):
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        for row in summary:
            writer.writerow(row)
    return path


def save_top_solutions_by_algorithm_csv(results, filename="top_solutions_by_algorithm.csv", top_k=5):
    path = OUTPUT_DIR / filename

    rows = []
    algorithms = sorted(set(r.algorithm for r in results))

    for alg in algorithms:
        alg_results = [r.__dict__ for r in results if r.algorithm == alg]
        top = unique_top_solutions(alg_results, top_k=top_k)
        rows.extend(top)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
    "algorithm",
    "run_id",
    "time_seconds",
    "iterations",
    "best_solution",
    "final_conflicts",
    "final_fitness",
    "success",
],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return path


def parse_args():
    parser = argparse.ArgumentParser(description="8 Queens metaheuristics: GRASP and Genetic Algorithm")
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--grasp-iterations", type=int, default=200)
    parser.add_argument("--rcl-size", type=int, default=3)
    parser.add_argument("--population", type=int, default=20)
    parser.add_argument("--crossover-rate", type=float, default=0.80)
    parser.add_argument("--mutation-rate", type=float, default=0.03)
    parser.add_argument("--max-generations", type=int, default=1000)
    return parser.parse_args()


def main():
    args = parse_args()

    results = run_experiments(
        runs=args.runs,
        grasp_iterations=args.grasp_iterations,
        rcl_size=args.rcl_size,
        pop_size=args.population,
        crossover_rate=args.crossover_rate,
        mutation_rate=args.mutation_rate,
        max_generations=args.max_generations,
    )

    summary = summarize(results)

    results_path = save_results_csv(results)
    summary_path = save_summary_csv(summary)
    top_path = save_top_solutions_by_algorithm_csv(results)

    print("Saved:", results_path)
    print("Saved:", summary_path)
    print("Saved:", top_path)

    for row in summary:
        print(row)


if __name__ == "__main__":
    main()