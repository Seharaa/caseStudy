"""
Call Center Simulation using SimPy
Author: S. M. P. S. Siriwardhana

Description:
This simulation models a customer service call center using SimPy.
It compares three scenarios:
1. Baseline: 5 agents, 10 calls/hour
2. More Agents: 7 agents, 10 calls/hour
3. Higher Load: 5 agents, 12 calls/hour

Outputs:
- Average wait time
- Agent utilization
- Queue length
- Throughput
"""

import simpy
import random
import statistics

RANDOM_SEED = 42
SIM_HOURS = 8
MEAN_SERVICE_MINUTES = 5

class CallCenter:
    def __init__(self, env, num_agents):
        self.env = env
        self.agent = simpy.Resource(env, capacity=num_agents)
        self.total_busy_time = 0
        self.last_event_time = 0
        self.busy_times = []

    def serve(self, customer_id):
        service_time = random.expovariate(1.0 / MEAN_SERVICE_MINUTES)
        yield self.env.timeout(service_time)

def customer(env, customer_id, call_center, wait_times):
    arrival_time = env.now
    with call_center.agent.request() as request:
        yield request
        wait = env.now - arrival_time
        wait_times.append(wait)
        start_busy = env.now
        yield env.process(call_center.serve(customer_id))
        end_busy = env.now
        call_center.busy_times.append((start_busy, end_busy))

def setup(env, call_center, arrival_rate_per_hour, wait_times):
    customer_id = 0
    while env.now < SIM_HOURS * 60:
        inter_arrival = random.expovariate(arrival_rate_per_hour / 60.0)
        yield env.timeout(inter_arrival)
        env.process(customer(env, customer_id, call_center, wait_times))
        customer_id += 1

def run_scenario(num_agents, arrival_rate_per_hour, replications=30):
    all_results = []
    for r in range(replications):
        random.seed(RANDOM_SEED + r)
        env = simpy.Environment()
        call_center = CallCenter(env, num_agents)
        wait_times = []
        env.process(setup(env, call_center, arrival_rate_per_hour, wait_times))
        env.run(until=SIM_HOURS * 60)

        # Compute metrics
        avg_wait = statistics.mean(wait_times) if wait_times else 0.0
        num_served = len(wait_times)
        total_busy_time = sum(end - start for start, end in call_center.busy_times)
        utilization = total_busy_time / (num_agents * SIM_HOURS * 60)
        avg_queue_len = sum(wait_times) / SIM_HOURS if wait_times else 0

        all_results.append({
            'avg_wait': avg_wait,
            'utilization': utilization,
            'num_served': num_served,
            'avg_queue_len': avg_queue_len
        })
    # Aggregate results
    agg = {}
    for key in ['avg_wait', 'utilization', 'num_served', 'avg_queue_len']:
        vals = [res[key] for res in all_results]
        agg[key+'_mean'] = statistics.mean(vals)
        agg[key+'_stdev'] = statistics.pstdev(vals)
    return agg

if __name__ == "__main__":
    scenarios = {
        'Baseline (5 agents, 10/hr)': (5, 10),
        'More Agents (7 agents, 10/hr)': (7, 10),
        'Higher Load (5 agents, 12/hr)': (5, 12)
    }

    for name, (agents, rate) in scenarios.items():
        result = run_scenario(agents, rate)
        print(f"\n{name}")
        print(f"  Avg wait: {result['avg_wait_mean']:.2f} min (stdev {result['avg_wait_stdev']:.2f})")
        print(f"  Utilization: {result['utilization_mean']:.2f}")
        print(f"  Customers served: {result['num_served_mean']:.0f}")
        print(f"  Avg queue length (approx): {result['avg_queue_len_mean']:.2f}")
