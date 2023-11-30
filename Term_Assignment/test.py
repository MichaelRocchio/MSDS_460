import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import random
import sys
import simpy
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from tqdm import tqdm  # Import tqdm


menu_df = pd.read_csv('menu.csv')

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

customer_base_df=pd.read_csv("customer_base.csv")
try:
    menu_df['Gross Profit Per Item']=pd.to_numeric(menu_df['Gross Profit Per Item'].str.replace('$',''))
except:
    pass

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

DAYS_IN_SIMULATION = 365
SIMULATION_TIME_PER_DAY = 8 * 60  # 8 hours per day in minutes
ARRIVAL_RATE = 1  # Average time between arrivals
MAX_QUEUE_LENGTH_REGULAR = 5  # Maximum queue length before regular customers start balking
MAX_QUEUE_LENGTH_IMPATIENT = 3  # Maximum queue length for impatient customers
RENEGING_TIME_REGULAR = 8  # Time after which a regular customer may renege
RENEGING_TIME_IMPATIENT = 3  # Time for impatient customers
IMPATIENCE_PROBABILITY = 0.15  # Probability that a customer is impatient on a given visit

customer_records = []

def choose_items(menu, num_items):
    chosen_items = random.choices(menu['ID'], weights=menu['Popularity'], k=num_items)
    return chosen_items

class Customer:
    def __init__(self, env, customer_id, queue, queue_name, day, is_subscriber, is_impatient):
        self.env = env
        self.customer_id = customer_id
        self.queue = queue
        self.queue_name = queue_name
        self.day = day
        self.is_subscriber = is_subscriber
        self.is_impatient = is_impatient

    def order(self):
        num_items_ordered = max(1, min(8, int(np.random.normal(3, 1))))
        ordered_items = choose_items(menu_df, num_items_ordered)
        total_prep_time = sum(menu_df[menu_df['ID'].isin(ordered_items)]['Prep_Time'])
        max_queue_length = MAX_QUEUE_LENGTH_IMPATIENT if self.is_impatient else MAX_QUEUE_LENGTH_REGULAR
        reneging_time = RENEGING_TIME_IMPATIENT if self.is_impatient else RENEGING_TIME_REGULAR

        record = {
            'customer_id': self.customer_id,
            'is_subscriber': self.is_subscriber,
            'is_impatient': self.is_impatient,
            'queue_name': self.queue_name,
            'day': self.day,
            'arrival_time': self.env.now,
            'num_items_ordered': num_items_ordered
        }

        for i in range(1, 8):
            record[f'item{i}'] = ordered_items[i - 1] if i <= len(ordered_items) else None

        with self.queue.request() as request:
            if len(self.queue.queue) > max_queue_length:
                record['action'] = 'balked'
                customer_records.append(record)
                return

            yield request | self.env.timeout(reneging_time)
            yield self.env.timeout(total_prep_time)

            record['departure_time'] = self.env.now
            record['action'] = 'served'
            customer_records.append(record)

def burger_shop(env, regular_queue, premium_queue, day, customer_base, premium_price):
    while True:
        arrival_interval = random.expovariate(1.0 / ARRIVAL_RATE)
        yield env.timeout(arrival_interval)

        selected_customer = customer_base.sample(1).iloc[0]
        customer_id = selected_customer['CustomerID']
        price_tolerance = selected_customer['PriceTolerance']
        is_subscriber = selected_customer['IsSubscriber'] or (price_tolerance >= premium_price)

        is_impatient = random.random() < IMPATIENCE_PROBABILITY
        queue = premium_queue if is_subscriber else regular_queue
        queue_name = 'premium_queue' if is_subscriber else 'regular_queue'

        customer = Customer(env, customer_id, queue, queue_name, day, is_subscriber, is_impatient)
        env.process(customer.order())



def calculate_profit(row, menu):
    total_profit = 0.0
    for i in range(1, 8): 
        item_id = row[f'item{i}']
        if item_id!=0:
            profit = menu.loc[menu['ID'] == item_id, 'Gross Profit Per Item'].values[0]
            total_profit += profit
    return total_profit



def burger_shop(env, regular_queue, premium_queue, day, customer_base, premium_price):
    while True:
        arrival_interval = random.expovariate(1.0 / ARRIVAL_RATE)
        yield env.timeout(arrival_interval)

        selected_customer = customer_base.sample(1).iloc[0]
        customer_id = selected_customer['CustomerID']
        is_impatient = random.random() < IMPATIENCE_PROBABILITY
        price_tolerance = selected_customer['PriceTolerance']
        is_subscriber = selected_customer['IsSubscriber'] or (price_tolerance >= premium_price)

        queue = premium_queue if is_subscriber else regular_queue
        queue_name = 'premium_queue' if is_subscriber else 'regular_queue'

        customer = Customer(env, customer_id, queue, queue_name, day, is_subscriber, is_impatient)
        env.process(customer.order())

def run_simulation_for_price(premium_price, customer_base_df):
    global customer_records
    customer_records = []

    for day in range(1, DAYS_IN_SIMULATION + 1):
        env = simpy.Environment()
        regular_queue = simpy.Resource(env, capacity=1)
        premium_queue = simpy.Resource(env, capacity=1)
        env.process(burger_shop(env, regular_queue, premium_queue, day, customer_base_df, premium_price))
        env.run(until=SIMULATION_TIME_PER_DAY)

    simulation_df = pd.DataFrame(customer_records)
    for i in range(1, 8):
        simulation_df[f'item{i}'] = simulation_df[f'item{i}'].fillna(0).astype(int)
    simulation_df['profit'] = simulation_df.apply(lambda row: calculate_profit(row, menu_df), axis=1)
    profit_per_subscriber = premium_price
    sub_profit = simulation_df[simulation_df['is_subscriber']]['customer_id'].nunique() * profit_per_subscriber
    food_profit=simulation_df['profit'].sum()
    total_profit=sub_profit+food_profit
    return total_profit

def optimize_membership_price(customer_base_df):
    def objective_function(price):
        return -run_simulation_for_price(price[0], customer_base_df)

    bounds = [(5.00, 50.00)] 

    initial_guess = [18.00]

    result = minimize(objective_function, initial_guess, bounds=bounds)

    return result, result.x[0]

def run_simulation_for_price(premium_price, customer_base_df):
    global customer_records
    customer_records = []

    for day in range(1, DAYS_IN_SIMULATION + 1):
        env = simpy.Environment()
        regular_queue = simpy.Resource(env, capacity=1)
        premium_queue = simpy.Resource(env, capacity=1)
        env.process(burger_shop(env, regular_queue, premium_queue, day, customer_base_df, premium_price))
        env.run(until=SIMULATION_TIME_PER_DAY)

    simulation_df = pd.DataFrame(customer_records)
    for i in range(1, 8):
        simulation_df[f'item{i}'] = simulation_df[f'item{i}'].fillna(0).astype(int)
    simulation_df['profit'] = simulation_df.apply(lambda row: calculate_profit(row, menu_df), axis=1)
    profit_per_subscriber = premium_price
    sub_profit = simulation_df[simulation_df['is_subscriber']]['customer_id'].nunique() * profit_per_subscriber
    food_profit=simulation_df['profit'].sum()
    total_profit=sub_profit+food_profit
    simulation_df['wait_time'] = simulation_df['departure_time'] - simulation_df['arrival_time']
    return total_profit

def run_simulation_for_dataset(premium_price, customer_base_df):
    global customer_records
    customer_records = []

    for day in range(1, DAYS_IN_SIMULATION + 1):
        env = simpy.Environment()
        regular_queue = simpy.Resource(env, capacity=1)
        premium_queue = simpy.Resource(env, capacity=1)
        env.process(burger_shop(env, regular_queue, premium_queue, day, customer_base_df, premium_price))
        env.run(until=SIMULATION_TIME_PER_DAY)

    simulation_df = pd.DataFrame(customer_records)
    for i in range(1, 8):
        simulation_df[f'item{i}'] = simulation_df[f'item{i}'].fillna(0).astype(int)
    simulation_df['profit'] = simulation_df.apply(lambda row: calculate_profit(row, menu_df), axis=1)
    profit_per_subscriber = premium_price
    sub_profit = simulation_df[simulation_df['is_subscriber']]['customer_id'].nunique() * profit_per_subscriber
    food_profit=simulation_df['profit'].sum()
    total_profit=sub_profit+food_profit
    simulation_df['wait_time'] = simulation_df['departure_time'] - simulation_df['arrival_time']
    return simulation_df


np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

def simulation_wrapper(price):
    global customer_base_df  # Access the global variable
    return run_simulation_for_price(price, customer_base_df)

def parallel_profit_calculation(start_price, end_price, num_processes=150):
    prices = np.arange(start_price, end_price + 0.01, 0.01)
    future_to_price = {}

    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        for price in prices:
            future = executor.submit(simulation_wrapper, price)
            future_to_price[future] = price

        results = []

        # Wrap the as_completed with tqdm for progress display
        for future in tqdm(as_completed(future_to_price), total=len(prices), desc="Simulations"):
            price = future_to_price[future]
            profit = future.result()
            results.append((price, profit))

    results.sort(key=lambda x: x[0])  # Sort results based on price
    return pd.DataFrame(results, columns=['price', 'profit'])

# Example usage
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

sim_df1 = parallel_profit_calculation(5.00, 25.00)
sim_df1.to_csv("full_calc.csv")
print(sim_df1)

optimal_price0 = sim_df2[sim_df2['profit']==sim_df2['profit'].max()]['price'].values[0]
final_sim_df=run_simulation_for_dataset(optimal_price0, customer_base_df)
for i in range(1, 8):
    final_sim_df[f'item{i}'] = final_sim_df[f'item{i}'].fillna(0).astype(int)
final_sim_df['profit'] = final_sim_df.apply(lambda row: calculate_profit(row, menu_df), axis=1)
final_sim_df.to_csv("final_sim_df.csv")




# Setting plot style
sns.set(style="whitegrid")

# Plotting Profit Distribution
plt.figure(figsize=(20, 12))
sns.histplot(final_sim_df['profit'], bins=30, kde=True)
plt.title('Distribution of Profits Per Order')
plt.xlabel('Profit ($)')
plt.ylabel('Frequency')
plt.savefig('graphs/profit.png', dpi=1200)

# Plotting Wait Time Distribution
plt.figure(figsize=(20, 12))
sns.histplot(final_sim_df['wait_time'], bins=30, kde=True, color='orange')
plt.title('Distribution of Wait Times')
plt.xlabel('Wait Time (minutes)')
plt.ylabel('Frequency')
plt.savefig('graphs/wait_time.png', dpi=1200)


# Plotting Number of Items Ordered
plt.figure(figsize=(20, 12))
sns.countplot(x='num_items_ordered', data=final_sim_df, palette='viridis')
plt.title('Number of Items Ordered Per Order')
plt.xlabel('Number of Items')
plt.ylabel('Count')
plt.savefig('graphs/items_ordered.png', dpi=1200)

# Subscriber vs Non-Subscriber Counts
plt.figure(figsize=(20, 12))
sns.countplot(x='is_subscriber', data=final_sim_df, palette='pastel')
plt.title('Optimal Subscriber vs Non-Subscriber Counts')
plt.xlabel('Is Subscriber')
plt.ylabel('Count')
plt.savefig('graphs/subscriber.png', dpi=1200)

plt.figure(figsize=(24, 12))
plt.plot(sim_df1['price'], sim_df1['profit'], marker='o', color='b', label='Profit at different prices')
plt.axvline(x=optimal_price, color='r', linestyle='--', label=f'Optimal Price: ${optimal_price}')
plt.text(optimal_price, max(profits), f'${optimal_price}', color='red', ha='right')
plt.xlabel('Premium Subscription Price ($)')
plt.ylabel('Total Profit ($)')
plt.title('Profit vs. Premium Subscription Price')
plt.legend()
plt.show()
plt.savefig('graphs/optimization.png', dpi=1200)