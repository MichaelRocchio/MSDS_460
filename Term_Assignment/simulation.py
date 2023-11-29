import simpy
import random

# Constants
SIMULATION_TIME = 8 * 60  # Simulate for 8 hours (in minutes)
ARRIVAL_RATE = 5          # Customer arrives every 5 minutes, on average
RUSHED_THRESHOLD = 3      # Threshold for a 'rushed' customer's tolerance in minutes

# Define customer behavior
class Customer:
    def __init__(self, env, name, customer_type):
        self.env = env
        self.name = name
        self.customer_type = customer_type
        self.arrival_time = env.now

    def order(self):
        # Implement the ordering process here
        yield self.env.timeout(random.randint(1, 5))  # Random service time between 1 and 5 minutes

# Burger Shop environment
def burger_shop(env):
    while True:
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_RATE))  # Customer arrival based on an exponential distribution

        customer_type = 'rushed' if random.random() < 0.5 else 'relaxed'  # 50% chance for each customer type
        customer = Customer(env, f'Customer {env.now}', customer_type)
        env.process(customer.order())

        print(f'{env.now}: {customer.name} ({customer.customer_type}) has arrived.')

# Run the simulation
env = simpy.Environment()
env.process(burger_shop(env))
env.run(until=SIMULATION_TIME)
