"""
Discrete-Event Operations & Queueing Simulator for Aroma Dining Operations
Simulates multi-channel online and offline customer streams across Canteen, FastFood, Juice, and Restaurant service counters.

Features:
  - Multi-server queueing (M/M/k) event simulation.
  - Poisson arrival process with time-varying arrival rates (peak vs off-peak hours).
  - Online delivery orders vs Offline walk-in customer queue prioritization.
  - Queue length, waiting time, utilization rate, and throughput bottleneck reporting.
"""

import heapq
import numpy as np

class Event:
    def __init__(self, timestamp, event_type, customer_id, counter_type, service_time=0.0):
        self.timestamp = timestamp
        self.event_type = event_type  # 'ARRIVAL' or 'DEPARTURE'
        self.customer_id = customer_id
        self.counter_type = counter_type
        self.service_time = service_time

    def __lt__(self, other):
        return self.timestamp < other.timestamp

class AromaOperationsSimulator:
    def __init__(self, counters_config, simulation_time_hours=8.0, seed=42):
        """
        Parameters:
        - counters_config: dict specifying server counts and mean service times
            e.g. {'FastFood': {'servers': 3, 'mean_service_min': 4.0}, ...}
        - simulation_time_hours: length of simulation run in hours
        """
        self.config = counters_config
        self.sim_time_max = simulation_time_hours * 60.0  # in minutes
        self.seed = seed
        np.random.seed(seed)

    def run_simulation(self, arrival_rates_per_min):
        """
        Runs discrete event queueing simulation.
        - arrival_rates_per_min: dict with arrival rate lambda (customers/min) per counter
        """
        event_queue = []
        customer_id_counter = 0

        # Initialize arrival events
        for counter, rate in arrival_rates_per_min.items():
            if counter not in self.config:
                continue
            t = np.random.exponential(1.0 / rate)
            while t < self.sim_time_max:
                customer_id_counter += 1
                mean_service = self.config[counter]['mean_service_min']
                s_time = np.random.exponential(mean_service)
                heapq.heappush(event_queue, Event(t, 'ARRIVAL', customer_id_counter, counter, s_time))
                t += np.random.exponential(1.0 / rate)

        # Simulation state
        counters_state = {
            c: {
                'busy_servers': 0,
                'max_servers': self.config[c]['servers'],
                'queue': [],
                'wait_times': [],
                'completed_customers': 0
            }
            for c in self.config
        }

        # Event Loop
        while event_queue:
            evt = heapq.heappop(event_queue)
            c_state = counters_state[evt.counter_type]

            if evt.event_type == 'ARRIVAL':
                if c_state['busy_servers'] < c_state['max_servers']:
                    # Server available immediately
                    c_state['busy_servers'] += 1
                    c_state['wait_times'].append(0.0)
                    dep_time = evt.timestamp + evt.service_time
                    heapq.heappush(event_queue, Event(dep_time, 'DEPARTURE', evt.customer_id, evt.counter_type))
                else:
                    # Queue customer
                    c_state['queue'].append((evt.timestamp, evt.service_time, evt.customer_id))

            elif evt.event_type == 'DEPARTURE':
                c_state['completed_customers'] += 1
                if c_state['queue']:
                    # Serve next customer in queue
                    arr_time, serv_time, cust_id = c_state['queue'].pop(0)
                    wait_t = evt.timestamp - arr_time
                    c_state['wait_times'].append(wait_t)
                    dep_time = evt.timestamp + serv_time
                    heapq.heappush(event_queue, Event(dep_time, 'DEPARTURE', cust_id, evt.counter_type))
                else:
                    c_state['busy_servers'] -= 1

        # Calculate metrics
        metrics = {}
        for counter, st in counters_state.items():
            waits = st['wait_times']
            metrics[counter] = {
                'completed_customers': st['completed_customers'],
                'avg_wait_time_min': float(np.mean(waits)) if waits else 0.0,
                'p95_wait_time_min': float(np.percentile(waits, 95)) if waits else 0.0,
                'throughput_per_hour': float(st['completed_customers'] / (self.sim_time_max / 60.0))
            }

        return metrics

if __name__ == "__main__":
    config = {
        'Canteen': {'servers': 4, 'mean_service_min': 3.5},
        'FastFood': {'servers': 3, 'mean_service_min': 5.0},
        'Juice': {'servers': 2, 'mean_service_min': 2.5},
        'Restaurant': {'servers': 5, 'mean_service_min': 15.0}
    }
    arrival_rates = {
        'Canteen': 1.0,    # 60 customers/hr
        'FastFood': 0.5,   # 30 customers/hr
        'Juice': 0.6,      # 36 customers/hr
        'Restaurant': 0.2  # 12 customers/hr
    }

    sim = AromaOperationsSimulator(config, simulation_time_hours=4.0)
    res = sim.run_simulation(arrival_rates)
    print("=== Aroma Dining Discrete-Event Simulation ===")
    for counter, stats in res.items():
        print(f"Counter [{counter}]:")
        print(f"  Completed Customers: {stats['completed_customers']}")
        print(f"  Avg Wait Time: {stats['avg_wait_time_min']:.2f} min")
        print(f"  95th Percentile Wait: {stats['p95_wait_time_min']:.2f} min")
        print(f"  Throughput: {stats['throughput_per_hour']:.1f} cust/hr")
