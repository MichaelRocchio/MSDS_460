import pandas as pd
import pulp

df = pd.read_excel("data.xlsx")
df['predecessorTaskIDs'].fillna("", inplace=True)
df = df[['taskID', 'task', 'predecessorTaskIDs', 'bestCaseHours', 'expectedHours', 'worstCaseHours']]


def solve_project_plan(df, case="expected"):
    # LP Model
    lp_problem = pulp.LpProblem("Project_Planning", pulp.LpMinimize)
    
    # Decision vars
    start_times = pulp.LpVariable.dicts("start_time", df["taskID"], 0, None)
    
    # Objective function
    project_end = pulp.LpVariable("project_end", 0, None)
    lp_problem += project_end, "Minimize_Project_Duration"
    
    # adding constraints
    for index, row in df.iterrows():
        task = row["taskID"]
        
        # duration of cases
        if case == "best":
            duration = row["bestCaseHours"]
        elif case == "worst":
            duration = row["worstCaseHours"]
        else:
            duration = row["expectedHours"]
        
        predecessors = [pred.strip() for pred in row["predecessorTaskIDs"].split(",") if pred.strip()]
        
        # task duration constraint
        lp_problem += start_times[task] + duration <= project_end
        
        # task dependencies constraints
        for predecessor in predecessors:
            lp_problem += start_times[task] >= start_times[predecessor] + duration

    # Solver
    lp_problem.solve()
    
    # output prep
    results = {
        "status": pulp.LpStatus[lp_problem.status],
        "optimal_duration": project_end.varValue,
        "task_start_times": {task: var.varValue for task, var in start_times.items()}
    }
    
    return results

cases = ["best", "expected", "worst"]
for case in cases:
    result = solve_project_plan(df, case)
    print(f"Results for {case} case:")
    print(f"Optimal project duration: {result['optimal_duration']} hours")
    print("Start times for tasks:")
    for task, start_time in result["task_start_times"].items():
        print(f"Task {task}: {start_time} hours")
    print("\n")cd