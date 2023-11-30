
PERCENT_SUBSCRIBERS = 0.10  # Percentage of customers who are subscribers
PREMIUM_MEMBERSHIP_PRICE = 20  # Adjustable premium membership price
NUM_CUSTOMERS = 1000  # Total number of unique customers in the customer base


customer_ids = range(1, NUM_CUSTOMERS + 1)
is_subscriber = np.random.rand(NUM_CUSTOMERS) < PERCENT_SUBSCRIBERS
price_tolerance = np.random.normal(20, 5, NUM_CUSTOMERS)  # Normal dist with mean 20 and std 5
customer_base_df = pd.DataFrame({
    'CustomerID': customer_ids, 
    'IsSubscriber': is_subscriber,
    'PriceTolerance': price_tolerance
})
customer_base_df.to_csv('customer_base.csv', index=False)
customer_base_df


DAYS_IN_SIMULATION = 30
SIMULATION_TIME_PER_DAY = 8 * 60  # 8 hours per day in minutes
ARRIVAL_RATE = 2  # Average time between arrivals
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

for day in range(1, DAYS_IN_SIMULATION + 1):
    env = simpy.Environment()
    regular_queue = simpy.Resource(env, capacity=1)
    premium_queue = simpy.Resource(env, capacity=1)
    env.process(burger_shop(env, regular_queue, premium_queue, day, customer_base_df, PREMIUM_MEMBERSHIP_PRICE))
    env.run(until=SIMULATION_TIME_PER_DAY)

df = pd.DataFrame(customer_records)

df['wait_time'] = df['departure_time'] - df['arrival_time']
df