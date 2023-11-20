import time
import pandas as pd

dataset_small = pd.read_csv("data/dataset_small.csv")
dataset_medium = pd.read_csv("data/dataset_medium.csv")
dataset_large = pd.read_csv("data/dataset_large.csv")
secondary_dataset = pd.read_csv("data/join_dataset.csv")

def sort_dataset(dataset):
    return dataset.sort_values(by='Value', ascending=False)

def filter_dataset(dataset):
    return dataset[dataset['Category'].isin(['A', 'B'])]

def aggregate_dataset(dataset):
    return dataset.groupby('Category')['Value'].mean()

def join_datasets(main_dataset, secondary_dataset):
    return pd.merge(main_dataset, secondary_dataset, on='ID')
    
def benchmark_task(task_function, dataset, dataset2=None):
    start_time = time.time()
    try:
        result = task_function(dataset)
    except:
        result = task_function(dataset, dataset2)
    end_time = time.time()
    return end_time - start_time

execution_time = benchmark_task(sort_dataset, dataset_small)
results = []
for dataset, size in zip([dataset_small, dataset_medium, dataset_large], ['Small', 'Medium', 'Large']):
    results.append({'Task': 'Sort', 'Size': size, 'Time': benchmark_task(sort_dataset, dataset)})
    results.append({'Task': 'Filter', 'Size': size, 'Time': benchmark_task(filter_dataset, dataset)})
    results.append({'Task': 'Aggregate', 'Size': size, 'Time': benchmark_task(aggregate_dataset, dataset)})
    results.append({'Task': 'Join', 'Size': size, 'Time': benchmark_task(join_datasets, dataset, secondary_dataset)})


benchmark_results = pd.DataFrame(results)
benchmark_results['Language'] = 'Python'
benchmark_results.to_csv("data/benchmark_results_python.csv", header=True, index=False)