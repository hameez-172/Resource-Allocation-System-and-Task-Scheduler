import streamlit as st
import networkx as nx
import pandas as pd
import plotly.express as px
import io

# --- 1. Dataset Parsing Logic ---
def parse_jobshop_data(content):
    """Taillard format (.txt) ko dictionary mein convert karne ke liye"""
    lines = content.strip().split('\n')
    try:
        header = lines[0].split()
        if not header: return None
    except:
        return None

    tasks_input = {}
    job_count = 0
    
    # Dataset parsing logic for Taillard format
    for line in lines:
        clean_line = line.strip()
        # Skip empty lines or header info
        if not clean_line or clean_line.startswith('[') or clean_line.startswith('source'):
            continue
            
        parts = clean_line.split()
        if len(parts) < 2: continue
        
        job_count += 1
        job_id = f"Job_{job_count}"
        
        # Numbers ko pairs mein read karna (Machine_ID, Duration)
        for j in range(0, len(parts), 2):
            if j+1 >= len(parts): break
            
            task_num = (j // 2) + 1
            task_id = f"{job_id}_T{task_num}"
            machine_id = f"M{parts[j]}"
            duration = int(parts[j+1])
            
            # [cite_start]Dependency logic [cite: 14, 15]
            dependencies = [f"{job_id}_T{task_num-1}"] if task_num > 1 else []
                
            tasks_input[task_id] = {
                'duration': duration, 
                'dependencies': dependencies,
                'machine': machine_id
            }
    return tasks_input

# --- 2. Core Scheduling Algorithm (Discrete Math) ---
def task_scheduler(tasks_data, machines_list):
    G = nx.DiGraph()
    for t_id, info in tasks_data.items():
        G.add_node(t_id, duration=info['duration'], machine=info.get('machine', 'M1'))
        for dep in info['dependencies']:
            if dep in tasks_data:
                G.add_edge(dep, t_id)

    if not nx.is_directed_acyclic_graph(G):
        return None, None

    # [cite_start]Critical Path Analysis (Graph Theory) [cite: 1, 7]
    critical_path = nx.dag_longest_path(G, weight='duration')
    
    machine_free_time = {m: 0 for m in machines_list}
    task_finish_time = {}
    schedule = []
    completed_tasks = set()

    # [cite_start]Priority Rule: Shortest Job First [cite: 16]
    while len(completed_tasks) < len(tasks_data):
        ready_tasks = [
            n for n in G.nodes() 
            if n not in completed_tasks and all(d in completed_tasks for d in G.predecessors(n))
        ]
        if not ready_tasks: break
        
        ready_tasks.sort(key=lambda x: tasks_data[x]['duration'])

        for task_id in ready_tasks:
            target_machine = tasks_data[task_id].get('machine', machines_list[0])
            if target_machine not in machine_free_time:
                machine_free_time[target_machine] = 0
            
            # [cite_start]Start time calculation [cite: 17, 18]
            dep_finish_times = [task_finish_time[d] for d in G.predecessors(task_id)]
            start_time = max([machine_free_time[target_machine]] + dep_finish_times)
            end_time = start_time + tasks_data[task_id]['duration']
            
            machine_free_time[target_machine] = end_time
            task_finish_time[task_id] = end_time
            completed_tasks.add(task_id)
            
            schedule.append({
                "Machine": target_machine,
                "Task": task_id,
                "Start": start_time,
                "Finish": end_time,
                "Is_Critical": task_id in critical_path
            })
    return schedule, critical_path

# --- 3. Streamlit UI --- 
st.set_page_config(page_title="JobShop Pro Optimizer", layout="wide")
st.title("⚙️ JobShop Resource Optimizer")
[cite_start]st.markdown("Yeh system **Job Shop Scheduling (JSSP)** ke algorithms par mabni hai. [cite: 1, 7]")

# Sidebar for File Upload
st.sidebar.header("Data Source")
uploaded_file = st.sidebar.file_uploader("Taillard Dataset (.txt) upload karein", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    tasks_input = parse_jobshop_data(content)
    
    if tasks_input:
        machines = sorted(list(set([info['machine'] for info in tasks_input.values()])))
        st.sidebar.success(f"Loaded {len(tasks_input)} tasks on {len(machines)} machines.")

        if st.button("Generate Optimized Schedule"):
            result, cp = task_scheduler(tasks_input, machines)
            
            if result:
                df = pd.DataFrame(result)
                makespan = df['Finish'].max()
                
                m1, m2 = st.columns(2)
                m1.metric("Total Makespan (Completion Time)", f"{makespan} units")
                m2.metric("Critical Tasks Count", len(cp))

                st.subheader("Timeline Visualization (Gantt Chart)")
                fig = px.timeline(df, x_start="Start", x_end="Finish", y="Machine", 
                                  color="Is_Critical", 
                                  color_discrete_map={True: "red", False: "blue"},
                                  hover_data=["Task"])
                fig.layout.xaxis.type = 'linear'
                for d in fig.data:
                    filt = df[df['Is_Critical'] == (d.name == 'True')]
                    d.x = filt['Finish'] - filt['Start']
                    d.base = filt['Start']
                
                st.plotly_chart(fig, use_container_width=True)

                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Schedule CSV", csv, "job_schedule.csv", "text/csv")
            else:
                st.error("Algorithm failed. Please check for circular dependencies.")
    else:
        st.error("File format sahi nahi hai.")
else:
    st.info("Sidebar se .txt file upload karein.")
