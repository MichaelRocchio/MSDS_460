CREATE TABLE dataset_small (
    ID INT,
    Date DATE,
    Category VARCHAR(1),
    Value FLOAT
);

CREATE TABLE dataset_medium (
    ID INT,
    Date DATE,
    Category VARCHAR(1),
    Value FLOAT
);

CREATE TABLE dataset_large (
    ID INT,
    Date DATE,
    Category VARCHAR(1),
    Value FLOAT
);

CREATE TABLE join_dataset (
    ID INT,
    JoinValue FLOAT
);

COPY dataset_small FROM '/Users/michaelrocchio/git/MSDS_460_Group/Group_Assign3/data/dataset_small.csv' DELIMITER ',' CSV HEADER;
COPY dataset_medium FROM '/Users/michaelrocchio/git/MSDS_460_Group/Group_Assign3/data/dataset_medium.csv' DELIMITER ',' CSV HEADER;
COPY dataset_large FROM '/Users/michaelrocchio/git/MSDS_460_Group/Group_Assign3/data/dataset_large.csv' DELIMITER ',' CSV HEADER;
COPY join_dataset FROM '/Users/michaelrocchio/git/MSDS_460_Group/Group_Assign3/data/join_dataset.csv' DELIMITER ',' CSV HEADER;


CREATE TABLE benchmark_results
(
    task_name TEXT,
    dataset_size TEXT,
    execution_time DOUBLE PRECISION,
    language TEXT
);


DO $$
DECLARE
    start_time TIMESTAMP;
BEGIN

    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Sort', 'Small', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM dataset_small
    ORDER BY "value" DESC;
    

    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Filter', 'Small', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM dataset_small
    WHERE "category" IN ('A', 'B');
    

    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Aggregate', 'Small', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM (
        SELECT "category", AVG("value") AS "AverageValue"
        FROM dataset_small
        GROUP BY "category"
    ) AS aggregated_small;
    
    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Join', 'Small', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM (
        SELECT * FROM dataset_small s
        JOIN join_dataset j ON s."id" = j."id"
    ) AS joined_small;
END $$;

DO $$
DECLARE
    start_time TIMESTAMP;
BEGIN

    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Sort', 'Medium', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM dataset_medium
    ORDER BY "value" DESC;
    
    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Filter', 'Medium', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM dataset_medium
    WHERE "category" IN ('A', 'B');
    
    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Aggregate', 'Medium', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM (
        SELECT "category", AVG("value") AS "AverageValue"
        FROM dataset_medium
        GROUP BY "category"
    ) AS aggregated_medium;
    
    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Join', 'Medium', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM (
        SELECT * FROM dataset_medium s
        JOIN join_dataset j ON s."id" = j."id"
    ) AS joined_medium;
END $$;

DO $$
DECLARE
    start_time TIMESTAMP;
BEGIN

    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Sort', 'Large', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM dataset_large
    ORDER BY "value" DESC;
    
    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Filter', 'Large', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM dataset_large
    WHERE "category" IN ('A', 'B');
    
    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Aggregate', 'Large', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM (
        SELECT "category", AVG("value") AS "AverageValue"
        FROM dataset_large
        GROUP BY "category"
    ) AS aggregated_large;
    
    start_time := clock_timestamp();
    INSERT INTO benchmark_results (task_name, dataset_size, execution_time, language)
    SELECT 'Join', 'Large', extract(epoch from (SELECT clock_timestamp() - start_time)), 'PostgreSQL'
    FROM (
        SELECT * FROM dataset_large s
        JOIN join_dataset j ON s."id" = j."id"
    ) AS joined_large;
END $$;

CREATE TABLE final_benchmark_results AS
Select     task_name, 
    dataset_size, 
    execution_time, 
    language
    From (
    SELECT DISTINCT 
        task_name, 
        dataset_size, 
        execution_time, 
        language,
        CASE dataset_size
            WHEN 'Small' THEN 1
            WHEN 'Medium' THEN 2
            WHEN 'Large' THEN 3
        END AS size_order
    FROM benchmark_results
    ORDER BY size_order) AS ordered_results; 