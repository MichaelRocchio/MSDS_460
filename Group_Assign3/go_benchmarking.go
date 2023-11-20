package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

type Data struct {
	ID       int
	Date     string
	Category string
	Value    float64
}

type JoinData struct {
	ID                int
	Additional_Column float64
}

func readCSVData(filePath string) ([]Data, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	_, err = reader.Read()
	if err != nil {
		return nil, err
	}

	var data []Data
	for {
		record, err := reader.Read()
		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}

		id, _ := strconv.Atoi(record[0])
		value, _ := strconv.ParseFloat(record[3], 64)

		data = append(data, Data{
			ID:       id,
			Date:     record[1],
			Category: record[2],
			Value:    value,
		})
	}

	return data, nil
}

func readJoinCSVData(filePath string) ([]JoinData, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	_, err = reader.Read() // Skip header
	if err != nil {
		return nil, err
	}

	var data []JoinData
	for {
		record, err := reader.Read()
		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}

		id, _ := strconv.Atoi(record[0])
		additionalColumn, _ := strconv.ParseFloat(record[1], 64)

		data = append(data, JoinData{
			ID:                id,
			Additional_Column: additionalColumn,
		})
	}

	return data, nil
}

func joinData(mainData []Data, joinData []JoinData) []map[string]interface{} {
	joinMap := make(map[int]JoinData)
	for _, jd := range joinData {
		joinMap[jd.ID] = jd
	}

	var joinedData []map[string]interface{}
	for _, md := range mainData {
		if jd, ok := joinMap[md.ID]; ok {
			joinedRow := map[string]interface{}{
				"ID":                md.ID,
				"Date":              md.Date,
				"Category":          md.Category,
				"Value":             md.Value,
				"Additional_Column": jd.Additional_Column,
			}
			joinedData = append(joinedData, joinedRow)
		}
	}

	return joinedData
}

func saveBenchmarkResultsToCSV(data [][]string, filePath string) error {
	file, err := os.Create(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	headers := []string{"Task", "Size", "Time", "Language"}
	if err := writer.Write(headers); err != nil {
		return err
	}

	for _, row := range data {
		if err := writer.Write(row); err != nil {
			return err
		}
	}

	return nil
}

func benchmark(task string, f func()) float64 {
	start := time.Now()
	f()
	elapsed := time.Since(start)
	return elapsed.Seconds()
}

func main() {
	// Load datasets
	datasetSmall, err := readCSVData("data/dataset_small.csv")
	if err != nil {
		panic(err)
	}
	joinDataset, err := readJoinCSVData("data/join_dataset.csv")
	if err != nil {
		panic(err)
	}
	datasetMedium, err := readCSVData("data/dataset_medium.csv")
	if err != nil {
		panic(err)
	}
	datasetLarge, err := readCSVData("data/dataset_large.csv")
	if err != nil {
		panic(err)
	}

	tasks := map[string]func(){
		"Sort Small": func() {
			sort.Slice(datasetSmall, func(i, j int) bool { return datasetSmall[i].Value < datasetSmall[j].Value })
		},
		"Filter Small": func() {
			for _, d := range datasetSmall {
				if d.Value > 50 {
				}
			}
		},
		"Aggregate Small": func() {
			var sum float64
			for _, d := range datasetSmall {
				sum += d.Value
			}
		},
		"Join Small": func() {
			joinData(datasetSmall, joinDataset)
		},
		"Sort Medium": func() {
			sort.Slice(datasetMedium, func(i, j int) bool { return datasetMedium[i].Value < datasetMedium[j].Value })
		},
		"Filter Medium": func() {
			for _, d := range datasetMedium {
				if d.Value > 50 {
				}
			}
		},
		"Aggregate Medium": func() {
			var sum float64
			for _, d := range datasetMedium {
				sum += d.Value
			}
		},
		"Join Medium": func() {
			joinData(datasetMedium, joinDataset)
		},
		"Sort Large": func() {
			sort.Slice(datasetLarge, func(i, j int) bool { return datasetLarge[i].Value < datasetLarge[j].Value })
		},
		"Filter Large": func() {
			for _, d := range datasetLarge {
				if d.Value > 50 {
				}
			}
		},
		"Aggregate Large": func() {
			var sum float64
			for _, d := range datasetLarge {
				sum += d.Value
			}
		},
		"Join Large": func() {
			joinData(datasetLarge, joinDataset)
		},
	}

	var benchmarkResults [][]string
	for taskName, taskFunc := range tasks {
		timeTaken := benchmark(taskName, taskFunc)
		parts := strings.Split(taskName, " ")
		task := parts[0]
		size := parts[1]
		benchmarkResults = append(benchmarkResults, []string{task, size, fmt.Sprintf("%.6f", timeTaken), "Go"})
	}

	if err := saveBenchmarkResultsToCSV(benchmarkResults, "data/benchmark_results_go.csv"); err != nil {
		fmt.Println("Error saving benchmark results:", err)
	}
}
