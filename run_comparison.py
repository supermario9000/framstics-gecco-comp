#!/usr/bin/env python3
"""
Compare the baseline DEAP algorithm (FramsticksEvolution.py) against the
SouperTeam adaptive algorithm (algorithm.py) using FramsticksLibCompetition.

Both algorithms are run in separate subprocesses so they each get a fresh
Framsticks library instance (the native library can only be loaded once per
process).

Usage:
    python -u run_comparison.py -path /path/to/framsticks [-generations 20] [-popsize 50]
"""

import argparse
import os
import sys
import subprocess
import re
import threading
import time


def parse_args():
    parser = argparse.ArgumentParser(description="Compare baseline vs SouperTeam algorithm.")
    parser.add_argument("-path", required=True, help="Path to Framsticks library.")
    parser.add_argument("-sim", default="eval-allcriteria.sim;deterministic.sim;recording-body-coords.sim",
                        help="Sim file(s) separated by semicolons.")
    parser.add_argument("-genformat", default="1", help="Genetic format. Default: 1")
    parser.add_argument("-popsize", type=int, default=50, help="Population size. Default: 50")
    parser.add_argument("-generations", type=int, default=20,
                        help="Generations for baseline. Default: 20")
    parser.add_argument("-timeout", type=int, default=3600,
                        help="Max seconds per algorithm run. Default: 3600 (1h)")
    return parser.parse_args()


def extract_best_fitness(output_text):
    """Extract best fitness from output using multiple strategies.

    Tries in order:
    1. FramsticksLibCompetition.end() line: "best solution = <value>"
    2. SouperTeam algorithm output: "Best fitness: <value>" or "Best: <value>"
    3. DEAP generation table: the 'max' column from the last row
    """
    # Strategy 1: competition .end() output
    match = re.search(r"best solution\s*=\s*([\d.eE+\-]+|None)", output_text)
    if match and match.group(1) != "None":
        return float(match.group(1))

    # Strategy 2: SouperTeam progress lines like "Best: 1.2345" or "Best fitness: 1.2345"
    best_val = None
    for m in re.finditer(r"Best(?:\s+fitness)?:\s*([\d.eE+\-]+)", output_text):
        val = float(m.group(1))
        if best_val is None or val > best_val:
            best_val = val
    if best_val is not None:
        return best_val

    # Strategy 3: DEAP table rows — columns are: gen, nevals, avg, stddev, min, max
    max_from_table = None
    for m in re.finditer(r"^\d+\s+\d+\s+[\d.eE+\-]+\s+[\d.eE+\-]+\s+[\d.eE+\-]+\s+([\d.eE+\-]+)", output_text, re.MULTILINE):
        val = float(m.group(1))
        if max_from_table is None or val > max_from_table:
            max_from_table = val
    if max_from_table is not None:
        return max_from_table

    return None


def run_with_progress(cmd, label, timeout):
    """Run a subprocess with a live progress bar showing elapsed time."""
    print("=" * 60)
    print(f"RUNNING {label}")
    print("Command:", " ".join(cmd))
    print("=" * 60)

    cwd = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, cwd=cwd)

    output_lines = []
    stop_event = threading.Event()

    def reader(stream, dest):
        for line in stream:
            dest.append(line)
        stream.close()

    stdout_lines = []
    stderr_lines = []
    t_out = threading.Thread(target=reader, args=(proc.stdout, stdout_lines), daemon=True)
    t_err = threading.Thread(target=reader, args=(proc.stderr, stderr_lines), daemon=True)
    t_out.start()
    t_err.start()

    spinner = ['|', '/', '-', '\\']
    start = time.time()
    idx = 0
    try:
        while proc.poll() is None:
            elapsed = time.time() - start
            if elapsed > timeout:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"\n  [TIMEOUT] Killed after {timeout}s")
                break
            bar_len = 30
            filled = int(bar_len * min(elapsed / timeout, 1.0))
            bar = '#' * filled + '-' * (bar_len - filled)
            pct = min(elapsed / timeout * 100, 100.0)
            spin = spinner[idx % len(spinner)]
            print(f"\r  {spin} [{bar}] {pct:5.1f}%  {elapsed:.0f}s / {timeout}s", end="", flush=True)
            idx += 1
            time.sleep(0.3)
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait(timeout=5)
        print("\n  [INTERRUPTED]")

    t_out.join(timeout=2)
    t_err.join(timeout=2)

    elapsed = time.time() - start
    print(f"\r  Done [{('#' * 30)}] 100.0%  {elapsed:.1f}s elapsed          ")
    print()

    stdout_text = "".join(stdout_lines)
    stderr_text = "".join(stderr_lines)
    print(stdout_text)
    if stderr_text:
        print("[stderr]", stderr_text)

    return stdout_text + stderr_text, proc.returncode


def run_baseline(args):
    """Run FramsticksEvolution.py (DEAP eaSimple) via subprocess."""
    cmd = [
        sys.executable, "-u", "FramsticksEvolution.py",
        "-path", args.path,
        "-sim", args.sim,
        "-opt", "COGpath",
        "-genformat", args.genformat,
        "-popsize", str(args.popsize),
        "-generations", str(args.generations),
    ]
    return run_with_progress(cmd, "BASELINE (FramsticksEvolution.py / DEAP eaSimple)", args.timeout)


def run_souper(args):
    """Run algorithm.py (SouperTeam adaptive) via subprocess."""
    cmd = [
        sys.executable, "-u", "algorithm.py",
        "-path", args.path,
        "-sim", args.sim,
        "-genformat", args.genformat,
        "-popsize", str(args.popsize),
    ]
    return run_with_progress(cmd, "SOUPERTEAM (algorithm.py / Adaptive Evolution)", args.timeout)


def main():
    args = parse_args()

    if not os.path.isdir(args.path):
        print(f"Error: '{args.path}' is not a valid directory.")
        sys.exit(1)

    baseline_output, baseline_rc = run_baseline(args)
    souper_output, souper_rc = run_souper(args)

    baseline_best = extract_best_fitness(baseline_output)
    souper_best = extract_best_fitness(souper_output)

    def status_label(rc):
        if rc == -15 or rc == -9:
            return "KILLED (timeout)"
        elif rc == 0:
            return "OK"
        elif rc is None:
            return "UNKNOWN"
        else:
            return f"exit code {rc}"

    print("\n" + "=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)
    print(f"  Baseline (DEAP eaSimple)  : {baseline_best}  [{status_label(baseline_rc)}]")
    print(f"  SouperTeam (Adaptive EA)  : {souper_best}  [{status_label(souper_rc)}]")

    if baseline_rc in (-15, -9) or souper_rc in (-15, -9):
        print(f"\n  Note: One or both runs were killed by timeout ({args.timeout}s).")
        print(f"  Increase -timeout for a fair comparison.")

    if baseline_best is not None and souper_best is not None:
        if souper_best > baseline_best:
            diff = souper_best - baseline_best
            pct = (diff / abs(baseline_best) * 100) if baseline_best != 0 else float('inf')
            print(f"\n  >>> SouperTeam wins by {diff:.4f} ({pct:.1f}% improvement)")
        elif baseline_best > souper_best:
            diff = baseline_best - souper_best
            pct = (diff / abs(souper_best) * 100) if souper_best != 0 else float('inf')
            print(f"\n  >>> Baseline wins by {diff:.4f} ({pct:.1f}% better)")
        else:
            print(f"\n  >>> Tie (both {baseline_best})")
    else:
        print("\n  Could not parse fitness from one or both runs.")
        print("  Check the output above for errors.")
    print("=" * 60)


if __name__ == "__main__":
    main()
