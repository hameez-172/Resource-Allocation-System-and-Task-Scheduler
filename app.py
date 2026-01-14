import streamlit as st
import networkx as nx
import pandas as pd
import plotly.express as px
import io

# --- 1. Dataset Parsing Logic ---
def parse_jobshop_data(content):
    lines = content.strip().split('\n')
    tasks_input = {}
    job_count = 0
    
    for line in lines:
        clean_line = line.strip()
        # Skip empty lines, headers, or source tags 
        if not clean_line or "[" in clean_line or "source" in clean_line:
            continue
            
        parts = clean_line.split()
        # Kam az kam 2 numbers (Machine ID aur Duration) hone chahiye
        if len(parts) < 2: continue
        
        job_count += 1
        job_id = f"Job_{job_count}"
        
        for j in range(0, len(parts), 2):
            if j+1 >= len(parts): break
            try:
                task_num = (j // 2) + 1
                task_id = f"{job_id}_T{task_num}"
                machine_id = f"M{parts[j]}"
                # Yahan error aa raha tha, try-except handle karega 
                duration = int(parts[j+1])
                
                dependencies = [f"{job_id}_T{task_num-1}"] if task_num > 1 else []
                tasks_input[task_id] = {
                    'duration': duration, 
                    'dependencies': dependencies,
                    'machine': machine_id
                }
            except ValueError:
                continue # Agar koi part number nahi hai toh use skip kar dein
    return tasks_input

# --- 2. Core Scheduling Algorithm (Discrete Math) ---
def task_scheduler(tasks_data, machines_list):
    G = nx.DiGraph()
    for t_id, info in tasks_data.items():
        G.add_node(t_id, duration=info['duration'], machine=info['machine'])
        for dep in info['dependencies']:
            if dep in tasks_data:
                G.add_edge(dep, t_id)

    if not nx.is_directed_acyclic_graph(G): return None, None

    critical_path = nx.dag_longest_path(G, weight='duration')
    machine_free_time = {m: 0 for m in machines_list}
    task_finish_time = {}
    schedule = []
    completed_tasks = set()

    # Priority Rule: Shortest Job First 
    while len(completed_tasks) < len(tasks_data):
        ready_tasks = [n for n in G.nodes() if n not in completed_tasks and all(d in completed_tasks for d in G.predecessors(n))]
        if not ready_tasks: break
        ready_tasks.sort(key=lambda x: tasks_data[x]['duration'])

        for task_id in ready_tasks:
            target_machine = tasks_data[task_id]['machine']
            dep_finish = [task_finish_time[d] for d in G.predecessors(task_id)]
            start_time = max([machine_free_time.get(target_machine, 0)] + dep_finish)
            end_time = start_time + tasks_data[task_id]['duration']
            machine_free_time[target_machine] = end_time
            task_finish_time[task_id] = end_time
            completed_tasks.add(task_id)
            schedule.append({"Machine": target_machine, "Task": task_id, "Start": start_time, "Finish": end_time, "Is_Critical": task_id in critical_path})
    return schedule, critical_path

# --- 3. Streamlit UI (Viva Optimized) --- 
st.set_page_config(page_title="JobShop Pro Optimizer", layout="wide")
st.title("⚙️ JobShop Resource Optimizer")

# Viva ke liye 2 datasets
small_data = "5 5\n1 2 2 4 3 1 4 2 5 3\n2 3 1 1 4 4 3 2 5 2"
large_data = "100 100\n11 2 87 56 13 85 49 18 67 25 59 81 2 83 0 46 41 80 73 4 50 32 80 97 10 21 92 47 21 87 78 30 96 58 46 50 27 30 30 45 30 24 38 39 73 24 81 51 45 72 98 6 90 54 39 78 22 90 45 91 93 2 96 80 46 29 85 43 36 50 19 10 50 28 73 25 94 40 23 86 39 40 1 48 89 72 39 42 18 67 28 37 84 39 51 28 28 57 93"

dataset_choice = st.sidebar.selectbox("Viva Datasets Selection:", ["Small 5x5 Case", "Large 100x100 Case", "Upload Your Kaggle File"])

if dataset_choice == "Small 5x5 Case":
    tasks_input = parse_jobshop_data(small_data)
elif dataset_choice == "Large 100x100 Case":
    tasks_input = parse_jobshop_data(large_data)
else:
    uploaded_file = st.sidebar.file_uploader("Upload .txt", type=["txt"])
    tasks_input = parse_jobshop_data(uploaded_file.getvalue().decode("utf-8")) if uploaded_file else None

if tasks_input:
    machines = sorted(list(set([info['machine'] for info in tasks_input.values()])))
    if st.button("Calculate Optimal Schedule"):
        result, cp = task_scheduler(tasks_input, machines)
        if result:
            df = pd.DataFrame(result)
            st.metric("Total Makespan", f"{df['Finish'].max()} units")
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Machine", color="Is_Critical", color_discrete_map={True: "red", False: "blue"})
            fig.layout.xaxis.type = 'linear'
            for d in fig.data:
                filt = df[df['Is_Critical'] == (d.name == 'True')]
                d.x = filt['Finish'] - filt['Start']
                d.base = filt['Start']
            st.plotly_chart(fig, use_container_width=True)
