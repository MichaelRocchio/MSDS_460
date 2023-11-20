library(dplyr)
library(microbenchmark)

dataset_small <- read.csv("data/dataset_small.csv")
dataset_medium <- read.csv("data/dataset_medium.csv")
dataset_large <- read.csv("data/dataset_large.csv")
join_dataset <- read.csv("data/join_dataset.csv")


sort_dataset <- function(dataset) {
  dataset %>% arrange(desc(Value))
}

filter_dataset <- function(dataset) {
  dataset %>% filter(Category %in% c('A', 'B'))
}

aggregate_dataset <- function(dataset) {
  dataset %>% group_by(Category) %>% summarize(Avg_Value = mean(Value))
}

join_datasets <- function(main_dataset, secondary_dataset) {
  inner_join(main_dataset, secondary_dataset, by = "ID")
}
benchmark_task <- function(task_function, dataset, secondary_dataset = NULL) {
  if (!is.null(secondary_dataset)) {
    timing <- microbenchmark(task_function(dataset, secondary_dataset), times = 10L)
  } else {
    timing <- microbenchmark(task_function(dataset), times = 10L)
  }
  return(summary(timing)$median)  
}

results <- list()
for (dataset in list(dataset_small, dataset_medium, dataset_large)) {
  size <- ifelse(nrow(dataset) == nrow(dataset_small), "Small",
                 ifelse(nrow(dataset) == nrow(dataset_medium), "Medium", "Large"))
  
  results <- c(results, list(list("Task" = "Sort", "Size" = size, 
                                  "Time" = benchmark_task(sort_dataset, dataset))))
  results <- c(results, list(list("Task" = "Filter", "Size" = size, 
                                  "Time" = benchmark_task(filter_dataset, dataset))))
  results <- c(results, list(list("Task" = "Aggregate", "Size" = size, 
                                  "Time" = benchmark_task(aggregate_dataset, dataset))))
  results <- c(results, list(list("Task" = "Join", "Size" = size, 
                                  "Time" = benchmark_task(join_datasets, dataset, join_dataset))))
}
benchmark_results <- do.call(rbind.data.frame, results)
benchmark_results$Language <- "R"
write.csv(benchmark_results, "data/benchmark_results_R.csv", row.names = FALSE)