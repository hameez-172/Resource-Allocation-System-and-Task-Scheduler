import streamlit as st
import networkx as nx
import pandas as pd
import plotly.express as px
import io

# --- 1. Dataset Parsing Logic ---
def parse_jobshop_data(content):
    """Taillard format (.txt) ko dictionary mein convert karne ke liye"""
    lines = content.strip().split('\n')
    # Metadata nikalna (Jobs aur Machines ki tadaad)
    try:
        header = lines[0].split()
        num_jobs = int(header[0])
    except:
        return None

    tasks_input = {}
    # Line 1 ke baad se har line ek Job hai
    for i, line in enumerate(lines[1:]):
        if "}"
            duration = int(parts[j+1])
            
            # Dependency: Job ka har task pichle task par depend karta hai
            dependencies = []
            if j > 0:
                dependencies = [f"{job_id}_T{j//2}"]
                
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

    # Critical Path Analysis
    critical_path = nx.dag_longest_path(G, weight='duration')
    
    machine_free_time = {m: 0 for m in machines_list}
    task_finish_time = {}
    schedule = []
    completed_tasks = set()

    # [cite_start]Shortest Job First rule based on DAG [cite: 14, 15, 16]
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
    # Parsing
    content = uploaded_file.getvalue().decode("utf-8")
    tasks_input = parse_jobshop_data(content)
    
    if tasks_input:
        machines = list(set([info['machine'] for info in tasks_input.values()]))
        st.sidebar.success(f"Loaded {len(tasks_input)} tasks on {len(machines)} machines.")

        if st.button("Generate Optimized Schedule"):
            result, cp = task_scheduler(tasks_input, machines)
            
            if result:
                df = pd.DataFrame(result)
                
                # Metrics
                makespan = df['Finish'].max()
                m1, m2 = st.columns(2)
                m1.metric("Total Makespan (Completion Time)", f"{makespan} units")
                m2.metric("Critical Tasks Count", len(cp))

                # Gantt Chart
                st.subheader("Timeline Visualization (Gantt Chart)")
                fig = px.timeline(df, x_start="Start", x_end="Finish", y="Machine", 
                                  color="Is_Critical", 
                                  color_discrete_map={True: "red", False: "blue"},
                                  hover_data=["Task"])
                fig.layout.xaxis.type = 'linear'
                # Fix for Plotly linear timeline
                for d in fig.data:
                    filt = df[df['Is_Critical'] == (d.name == 'True')]
                    d.x = filt['Finish'] - filt['Start']
                    d.base = filt['Start']
                
                st.plotly_chart(fig, use_container_width=True)

                # Export
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Schedule CSV", csv, "job_schedule.csv", "text/csv")
            else:
                st.error("Algorithm failed. Please check data for circular dependencies.")
    else:
        st.error("File format sahi nahi hai. Taillard format use karein.")
else:
    st.info("Baraye maharbani sidebar se apna dataset (.txt file) upload karein.")