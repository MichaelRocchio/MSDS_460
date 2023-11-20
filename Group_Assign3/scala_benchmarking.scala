import spark.implicits._
import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._
import java.io.{BufferedWriter, FileWriter, File}

val datasetSmall = spark.read.option("header", "true").csv("data/dataset_small.csv")
val datasetMedium = spark.read.option("header", "true").csv("data/dataset_medium.csv")
val datasetLarge = spark.read.option("header", "true").csv("data/dataset_large.csv")
val joinDataset = spark.read.option("header", "true").csv("data/join_dataset.csv")

def sortDataset(dataset: DataFrame): DataFrame = {
    dataset.orderBy($"Value".desc)
}

def filterDataset(dataset: DataFrame): DataFrame = {
    dataset.filter($"Category".isin("A", "B"))
}

def aggregateDataset(dataset: DataFrame): DataFrame = {
    dataset.groupBy($"Category").agg(mean($"Value").as("AverageValue"))
}

def joinDatasets(dataset1: DataFrame, dataset2: DataFrame): DataFrame = {
    dataset1.join(dataset2, "ID")
}

def benchmarkTask(taskName: String, size: String, task: => DataFrame): String = {
    val startTime = System.nanoTime()
    task.count()
    val endTime = System.nanoTime()
    val duration = (endTime - startTime) / 1e9d
    s"$taskName\t$size\t$duration\tScala\n"
}

val benchmarkResults = Seq(("Small", datasetSmall), ("Medium", datasetMedium), ("Large", datasetLarge)).flatMap { case (size, dataset) =>
  Seq(
    benchmarkTask("Sort", size, sortDataset(dataset)),
    benchmarkTask("Filter", size, filterDataset(dataset)),
    benchmarkTask("Aggregate", size, aggregateDataset(dataset)),
    benchmarkTask("Join", size, joinDatasets(dataset, joinDataset))
  )
}

val benchmarkResultsDF = spark.createDataFrame(
  benchmarkResults.map { result =>
    val Array(task, size, time, language) = result.split("\t")
    (task, size, time.toDouble, language)
  }
).toDF("Task", "Size", "Time", "Language")


benchmarkResultsDF.repartition(1).write.mode("overwrite").option("header", "true").csv("data/benchmark_results_scala")

import java.io.File

val folderName = "data/benchmark_results_scala"
val fileName = "data/benchmark_results_scala.csv"
new File(folderName).listFiles().find(_.getName.endsWith(".csv")).foreach { csvFile =>
  csvFile.renameTo(new File(fileName))
  }
def deleteFolder(folder: File): Unit = {
  if (folder.isDirectory) {
    val files = folder.listFiles()
    if (files != null) {
      files.foreach(deleteFolder)
    }
  }
  folder.delete()
}

deleteFolder(new File(folderName))
