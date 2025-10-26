# ==============================
# Bank Queue Simulation - Multiple Runs Version
# Author: K.D.H.P.Kothalawala
# ==============================

import simpy
import random
import statistics

# === Function to Get Simulation Parameters ===
def get_simulation_parameters():
    """Let user choose manual or random simulation setup."""
    print("Welcome to Bank Queue Simulation\n")
    choice = input("Do you want to use Random parameters or Manual input? (R/M): ").strip().lower()

    if choice == 'm':
        # --- Manual Input Mode ---
        num_tellers = int(input("Enter number of tellers: "))
        mean_interarrival = float(input("Enter mean interarrival time (minutes): "))
        mean_service_time = float(input("Enter mean service time (minutes): "))
        sim_time = float(input("Enter total simulation time (minutes): "))
        num_runs = int(input("Enter number of simulation runs: "))
    else:
        # --- Random Mode (Auto-generate realistic values) ---
        num_tellers = random.choice([2, 3, 4])
        mean_interarrival = round(random.uniform(0.8, 1.5), 2)
        mean_service_time = round(random.uniform(1.5, 2.5), 2)
        sim_time = 480  # fixed 8 hours
        num_runs = 10   # default number of runs
        print("\n--- Random Parameters Selected ---")
        print(f"Number of tellers: {num_tellers}")
        print(f"Mean interarrival time: {mean_interarrival} minutes")
        print(f"Mean service time: {mean_service_time} minutes")
        print(f"Simulation time: {sim_time} minutes")
        print(f"Number of simulation runs: {num_runs}\n")

    return num_tellers, mean_interarrival, mean_service_time, sim_time, num_runs


# === Customer Process ===
def customer(env, name, bank, mean_service_time, waiting_times, service_times, verbose=False):
    """A customer arrives, waits for a teller, gets served, then leaves."""
    arrival_time = env.now
    if verbose:
        print(f"{name} arrives at {arrival_time:.2f}")

    with bank.request() as request:
        yield request  # Wait for a teller
        wait = env.now - arrival_time
        waiting_times.append(wait)
        if verbose:
            print(f"{name} starts service at {env.now:.2f} (Waited {wait:.2f} mins)")

        # Service process
        service_time = random.expovariate(1.0 / mean_service_time)
        service_times.append(service_time)
        yield env.timeout(service_time)
        if verbose:
            print(f"{name} leaves at {env.now:.2f}")


# === Customer Arrival Process ===
def customer_arrivals(env, bank, mean_interarrival, mean_service_time, waiting_times, service_times, verbose=False):
    """Generate customers arriving randomly."""
    customer_id = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / mean_interarrival))
        customer_id += 1
        env.process(customer(env, f"Customer_{customer_id}", bank, mean_service_time, waiting_times, service_times, verbose))


# === Run a Single Simulation ===
def run_single_simulation(num_tellers, mean_interarrival, mean_service_time, sim_time, run_number=1, verbose=False):
    """Run one simulation and return statistics."""
    if verbose:
        print(f"\n--- Simulation Run {run_number} ---")
    
    env = simpy.Environment()
    bank = simpy.Resource(env, capacity=num_tellers)

    # Data lists
    waiting_times = []
    service_times = []

    env.process(customer_arrivals(env, bank, mean_interarrival, mean_service_time, waiting_times, service_times, verbose))
    env.run(until=sim_time)

    # Calculate statistics
    stats = {
        'run_number': run_number,
        'customers_served': len(waiting_times),
        'avg_waiting_time': statistics.mean(waiting_times) if waiting_times else 0,
        'max_waiting_time': max(waiting_times) if waiting_times else 0,
        'avg_service_time': statistics.mean(service_times) if service_times else 0,
        'waiting_times': waiting_times,
        'service_times': service_times
    }
    
    if verbose and waiting_times:
        print(f"Run {run_number} - Customers: {len(waiting_times)}, Avg Wait: {stats['avg_waiting_time']:.2f} mins")
    
    return stats


# === Run Multiple Simulations ===
def run_multiple_simulations(num_tellers, mean_interarrival, mean_service_time, sim_time, num_runs):
    """Run multiple simulations and return aggregated results."""
    print(f"\n=== Running {num_runs} Simulations ===")
    
    all_stats = []
    
    for run in range(1, num_runs + 1):
        # Use different random seed for each run but show first run details
        verbose = (run == 1)  # Show details only for first run
        stats = run_single_simulation(num_tellers, mean_interarrival, mean_service_time, sim_time, run, verbose)
        all_stats.append(stats)
    
    return all_stats


# === Calculate Overall Statistics ===
def calculate_overall_statistics(all_stats):
    """Calculate overall statistics from all simulation runs."""
    if not all_stats:
        return None
    
    # Extract metrics across all runs
    avg_waiting_times = [stats['avg_waiting_time'] for stats in all_stats if stats['customers_served'] > 0]
    max_waiting_times = [stats['max_waiting_time'] for stats in all_stats if stats['customers_served'] > 0]
    customers_served = [stats['customers_served'] for stats in all_stats]
    avg_service_times = [stats['avg_service_time'] for stats in all_stats if stats['customers_served'] > 0]
    
    # Flatten all waiting times for overall statistics
    all_waiting_times = []
    all_service_times = []
    for stats in all_stats:
        all_waiting_times.extend(stats['waiting_times'])
        all_service_times.extend(stats['service_times'])
    
    overall_stats = {
        'total_runs': len(all_stats),
        'total_customers_served': sum(customers_served),
        'avg_customers_per_run': statistics.mean(customers_served),
        
        # Across-run averages
        'mean_avg_waiting_time': statistics.mean(avg_waiting_times) if avg_waiting_times else 0,
        'std_avg_waiting_time': statistics.stdev(avg_waiting_times) if len(avg_waiting_times) > 1 else 0,
        
        'mean_max_waiting_time': statistics.mean(max_waiting_times) if max_waiting_times else 0,
        'mean_avg_service_time': statistics.mean(avg_service_times) if avg_service_times else 0,
        
        # Overall statistics (all customers across all runs)
        'overall_avg_waiting_time': statistics.mean(all_waiting_times) if all_waiting_times else 0,
        'overall_max_waiting_time': max(all_waiting_times) if all_waiting_times else 0,
        'overall_avg_service_time': statistics.mean(all_service_times) if all_service_times else 0,
        
        # Confidence intervals (simplified)
        'waiting_time_95ci_low': statistics.mean(avg_waiting_times) - 1.96 * statistics.stdev(avg_waiting_times) / (len(avg_waiting_times) ** 0.5) if len(avg_waiting_times) > 1 else 0,
        'waiting_time_95ci_high': statistics.mean(avg_waiting_times) + 1.96 * statistics.stdev(avg_waiting_times) / (len(avg_waiting_times) ** 0.5) if len(avg_waiting_times) > 1 else 0
    }
    
    return overall_stats


# === Display Results ===
def display_results(all_stats, overall_stats, num_tellers):
    """Display detailed results from all simulations."""
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS - {overall_stats['total_runs']} Simulation Runs")
    print(f"{'='*60}")
    print(f"Number of tellers: {num_tellers}")
    print(f"Total customers served: {overall_stats['total_customers_served']}")
    print(f"Average customers per run: {overall_stats['avg_customers_per_run']:.1f}")
    
    print(f"\n--- Waiting Time Statistics ---")
    print(f"Average waiting time (across runs): {overall_stats['mean_avg_waiting_time']:.2f} ± {overall_stats['std_avg_waiting_time']:.2f} minutes")
    print(f"95% Confidence Interval: [{overall_stats['waiting_time_95ci_low']:.2f}, {overall_stats['waiting_time_95ci_high']:.2f}] minutes")
    print(f"Average maximum waiting time: {overall_stats['mean_max_waiting_time']:.2f} minutes")
    print(f"Overall average waiting time (all customers): {overall_stats['overall_avg_waiting_time']:.2f} minutes")
    print(f"Overall maximum waiting time: {overall_stats['overall_max_waiting_time']:.2f} minutes")
    
    print(f"\n--- Service Time Statistics ---")
    print(f"Average service time: {overall_stats['mean_avg_service_time']:.2f} minutes")
    print(f"Overall average service time: {overall_stats['overall_avg_service_time']:.2f} minutes")
    
    # Show individual run results
    print(f"\n--- Individual Run Results ---")
    for stats in all_stats:
        if stats['customers_served'] > 0:
            print(f"Run {stats['run_number']:2d}: {stats['customers_served']:3d} customers, "
                  f"Avg wait: {stats['avg_waiting_time']:6.2f} mins, "
                  f"Max wait: {stats['max_waiting_time']:6.2f} mins")
        else:
            print(f"Run {stats['run_number']:2d}: No customers served")


# === Main Program ===
if __name__ == "__main__":
    # Step 1: Get parameters
    num_tellers, mean_interarrival, mean_service_time, sim_time, num_runs = get_simulation_parameters()

    # Step 2: Run multiple simulations
    print(f"\n=== Bank Queue Simulation - {num_runs} Runs ===")
    
    # Run all simulations
    all_stats = run_multiple_simulations(num_tellers, mean_interarrival, mean_service_time, sim_time, num_runs)
    
    # Calculate overall statistics
    overall_stats = calculate_overall_statistics(all_stats)
    
    # Display results
    display_results(all_stats, overall_stats, num_tellers)
    
    print(f"\n{'='*60}")
    print("Simulation Complete!")
    print(f"{'='*60}")