from algos.DQN import DQNAgent
import os
from pymongo import MongoClient
import time
from datetime import datetime
from algos import PSOxMCT as pso
from dotenv import load_dotenv
import sqlite3
import threading

pso_param={}

def connect_To_DB():
    load_dotenv()
    #set base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    #load the env file
    mongo_uri = os.getenv('MONGO_URL')
    #establish connection to the database if connection fails retry 5 times
    for i in range(5):
        try:
            client = MongoClient(mongo_uri)
            return client['taskmaster']
           
        except:
            print("Connection failed. Retrying...")
            time.sleep(3)
    return None
    

def get_Task_Size(undone_tasks, files) -> dict:
    file_lengths = {}
    for ud in undone_tasks:
        for f in files.find({'_id': ud}):
            # estimated_task_times(round(file.get('length')/1024/1024,2))
            file_length_mb = round(f.get('length') / 1024 / 1024, 2)
            # file_lengths[ud] = max(0.1, min(file_length_mb, 1.0))
            file_lengths[ud] = file_length_mb
    return file_lengths

def upload_allotment_to_queue(dist:dict,conn) -> dict:
    
    if not dist:
        return
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS task_queue (TASK_ID STRING PRIMARY KEY, EDGE STRING)''')
    
    for key, val in dist.items():
        if c.execute("SELECT * FROM task_queue WHERE TASK_ID=?", (str(key),)).fetchone():
            continue
        c.execute("INSERT INTO task_queue (TASK_ID, EDGE) VALUES (?, ?)", (str(key), 'E'+str(val)))
    conn.commit()
    return
 
def periodic_Worker_Pool_Check(conn,tasks_cluster):
    c=conn.cursor()
    while True:
        # print("Executing periodic task")
        row=c.execute("SELECT * FROM WORKER_POOL")
        
        for r in row:
            #delete worker from pool if idle for more than 5 minutes
            if (datetime.now()-datetime.strptime(r[1], '%Y-%m-%d %H:%M:%S')).seconds > 300:
                c.execute("DELETE FROM WORKER_POOL WHERE EDGE_ID=?", (r[0],))
                conn.commit()
            task_ids = c.execute("SELECT TASK_ID FROM TASK_QUEUE WHERE EDGE=?", (r[0],)).fetchall()
            if not task_ids:
                continue
            # task_ids = [t[0] for t in task_ids]
            for t in task_ids:
                
                tasks_cluster.update_one({'_id': t[0]}, {'$set': {'started_at': None}})
                tasks_cluster.update_one({'_id': t[0]}, {'$set': {'completed_at': None}})
                tasks_cluster.update_one({'_id': t[0]}, {'$set': {'completed_by': None}})
                tasks_cluster.update_one({'_id': t[0]}, {'$set': {'computed_at': None}})
                c.execute("DELETE FROM TASK_QUEUE WHERE TASK_ID=?", (t[0],))
                conn.commit()
                
            print(f"Worker {r[0]} removed from pool due to inactivity.")
        # Your periodic task code here
        
        time.sleep(60)  # Execute every 60 seconds

def start_Periodic_Worker_Pool_Check(conn,tasks_cluster):
    thread = threading.Thread(target=periodic_Worker_Pool_Check,args=(conn,tasks_cluster,))
    thread.daemon = True  # Daemonize thread to exit when the main program exits
    thread.start()

if __name__ == '__main__':
   
    state_size = 3  # [task_size, edge_computation_power, cloud_computation_power]
    action_size = 2  # 0 = Edge, 1 = Cloud
    task_count = 0
    # Initialize DQN agent
    agent = DQNAgent(state_size, action_size)
    
    # if os.path.exists('queue.db'):
    #     os.remove('queue.db')
    
    db=connect_To_DB()
    tasks_cluster = db['tasks']
    
    if not os.path.exists('queue.db'):
        open('queue.db', 'w').close()
    
    conn = sqlite3.connect('queue.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS TASK_QUEUE (TASK_ID STRING PRIMARY KEY, EDGE STRING)''')
    c.execute('''CREATE TABLE IF NOT EXISTS WORKER_POOL (EDGE_ID STRING PRIMARY KEY, TIMESTAMP DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    #start the periodic worker pool check thread
    start_Periodic_Worker_Pool_Check(conn,tasks_cluster)
    
    edge_computation_power = 0.2
    cloud_computation_power = 1.0
    
    undone_tasks=[]
    try:
        while True:
            for task in tasks_cluster.find({"picked_at": None}):
                undone_tasks.append(task.get('_id'))
            
            if not undone_tasks:
                print("no tasks to offload")
                time.sleep(5)
                continue
            
            # Get task size
            task_size=get_Task_Size(undone_tasks,db['fs.files'])
            
            for i in range(len(undone_tasks)):
                current_task_size = task_size.get(undone_tasks[i])
                if current_task_size is None:
                    # print(f"Skipping task {undone_tasks[i]} due to missing size information.")
                    continue
                
                state = [current_task_size, edge_computation_power, cloud_computation_power]
                action = agent.select_action(state)
                if action == 0:  # Edge
                    reward = -edge_computation_power * current_task_size  # Reward depends on edge computation power and task size
                else:  # Cloud
                    reward = -cloud_computation_power * current_task_size  # Reward depends on cloud computation power and task size
                    
                if i < len(undone_tasks) - 1:
                    
                    next_task_size = task_size.get(undone_tasks[i + 1])
                    next_state = [next_task_size, edge_computation_power, cloud_computation_power]
                    done = True
                    agent.memory.append((state, action, reward, next_state, done))
                
                agent.train()
                task_count += 1
                
                if task_count % 10 == 0:
                    agent.update_target_network()
                
                tasks_cluster.update_one({'_id': undone_tasks[i]}, {'$set': {'picked_at': datetime.now().strftime('%H:%M:%S')}})
                tasks_cluster.update_one({'_id': undone_tasks[i]}, {'$set': {'computed_at': 'Edge' if action == 0 else 'cloud'}}) 
                
                if action == 0:
                    # edge_task_ids.append(undone_tasks[i])
                    pso_param[undone_tasks[i]] = task_size.get(undone_tasks[i])
                    
                print(f"Task {undone_tasks[i]}: Allocated to {'Edge' if action == 0 else 'Cloud'}")
            
            # get pso distribution
            t=pso.Task_Assignment_Calc(3,pso_param)
            dist=t.get_distribution()
            
            #upload the distribution to the local file queue i.e. sqlite
            #
            for i in dist:
                print(f"Task {i} is assigned to {dist[i]}")
                #
            upload_allotment_to_queue(dist,conn)
    
            
            #never delete this shit
            undone_tasks.clear()

                
    except KeyboardInterrupt:
        print("offloader stopped.")
