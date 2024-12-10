from algos.DQN import DQNAgent
import os
from pymongo import MongoClient
import time
from datetime import datetime
from algos import PSOxMCT as pso
from dotenv import load_dotenv
import sqlite3
import threading
from bson import ObjectId

from utils.offloader.upload_allotment_to_queue import upload_allotment_to_queue
pso_param={}

NO_OF_EDGE_DEVICES = 3
edge_computation_power = 0.2



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
        for f in files.find({'_id':ObjectId(ud)}):
            # estimated_task_times(round(file.get('length')/1024/1024,2))
            file_length_mb = round(f.get('length') / 1024 / 1024, 2)
            # file_lengths[ud] = max(0.1, min(file_length_mb, 1.0))
            file_lengths[ud] = file_length_mb
    return file_lengths

def periodic_Worker_Pool_Check(conn, tasks_cluster):
    c = conn.cursor()
    while True:
        # print("Executing periodic task")
        edges = []
        row = c.execute("SELECT * FROM WORKER_POOL").fetchall()

        for r in row:
            edges.append(r[0])
            # Delete worker from pool if idle for more than 5 minutes
            timestamp = datetime.strptime(r[1], '%Y-%m-%d %H:%M:%S.%f')
            if (datetime.now() - timestamp).seconds > 180:
                c.execute("DELETE FROM WORKER_POOL WHERE EDGE_ID=?", (r[0],))
                conn.commit()
                print(f"Worker {r[0]} removed from pool due to inactivity.")
                # Delete tasks assigned to the worker
                task_ids = c.execute("SELECT TASK_ID FROM TASK_QUEUE WHERE EDGE=?", (r[0],)).fetchall()
                if not task_ids:
                    continue
                # Reset the task status
                for t in task_ids:
                    tasks_cluster.update_one({'_id': ObjectId(t[0])}, {'$set': {'started_at': None}})
                    tasks_cluster.update_one({'_id': ObjectId(t[0])}, {'$set': {'completed_at': None}})
                    tasks_cluster.update_one({'_id': ObjectId(t[0])}, {'$set': {'picked_at': None}})
                    tasks_cluster.update_one({'_id': ObjectId(t[0])}, {'$set': {'assigned_to': None}})
                    c.execute("DELETE FROM TASK_QUEUE WHERE TASK_ID=?", (t[0],))
                    conn.commit()
                c.execute("DELETE FROM COMPUTATION_POWER WHERE EDGE_ID=?", (r[0],))
                conn.commit()

        print("Worker pool updated.")
        
        global NO_OF_EDGE_DEVICES
        NO_OF_EDGE_DEVICES = len(edges)
        
        sums = 0
        comps = c.execute("SELECT POWER FROM COMPUTATION_POWER").fetchall()
        for i in comps:
            sums += i[0]
        
        global edge_computation_power
        if NO_OF_EDGE_DEVICES != 0:
            edge_computation_power = round(sums / NO_OF_EDGE_DEVICES, 2)
        
        time.sleep(15)

def get_New_Queue_conn(check_same_thrd=False):
    conn = sqlite3.connect('queue.db', check_same_thread=check_same_thrd)
    return conn
   

def start_Periodic_Worker_Pool_Check(tasks_cluster):
    thread = threading.Thread(target=periodic_Worker_Pool_Check,args=(get_New_Queue_conn(),tasks_cluster,))
    thread.daemon = True  # Daemonize thread to exit when the main program exits
    thread.start()


if __name__ == '__main__':
   
    state_size = 3  # [task_size, edge_computation_power, cloud_computation_power]
    action_size = 2  # 0 = Edge, 1 = Cloud
    task_count = 0
    # Initialize DQN agent
    agent = DQNAgent(state_size, action_size)
    
    # if os.path.exists('queue.db'):
    
    cloud_computation_power = 1.0
    
    db=connect_To_DB()
    tasks_cluster = db['tasks']
    
    if not os.path.exists('queue.db'):
        open('queue.db', 'w').close()
    
    conn = get_New_Queue_conn()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS TASK_QUEUE (TASK_ID STRING PRIMARY KEY, EDGE STRING)''')
    c.execute('''CREATE TABLE IF NOT EXISTS WORKER_POOL (EDGE_ID STRING PRIMARY KEY, TIMESTAMP DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    #start the periodic worker pool check thread
    time.sleep(2)
    start_Periodic_Worker_Pool_Check(tasks_cluster)
    time.sleep(2)

    
    undone_tasks=[]
    try:
        while True:
            print('using computation power',edge_computation_power)
            for task in tasks_cluster.find({"picked_at": None}):
                undone_tasks.append(task.get('_id'))
            print("no of edge dev",NO_OF_EDGE_DEVICES)
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
                
                tasks_cluster.update_one({'_id': ObjectId(undone_tasks[i])}, {'$set': {'picked_at': datetime.now()}})
                tasks_cluster.update_one({'_id': ObjectId(undone_tasks[i])}, {'$set': {'assigned_to': 'Edge' if action == 0 else 'cloud'}}) 
               
                if NO_OF_EDGE_DEVICES != 0:
                    if action == 0:
                        pso_param[undone_tasks[i]] = task_size.get(undone_tasks[i])
                elif NO_OF_EDGE_DEVICES==0:
                    if action == 0:
                        tasks_cluster.update_one({'_id': ObjectId(undone_tasks[i])}, {'$set': {'assigned_to': 'cloud'}}) 
                    continue
                print(f"Task {undone_tasks[i]}: Allocated to {'Edge' if action == 0 else 'Cloud'}")
            
            # get pso distribution
            if NO_OF_EDGE_DEVICES != 0:
                
                print('NO_OF_EDGE_DEVICES: ',NO_OF_EDGE_DEVICES)
                t=pso.Task_Assignment_Calc(NO_OF_EDGE_DEVICES,pso_param)
                dist=t.get_distribution()
                
                #upload the distribution to the local file queue i.e. sqlite
                #
                for i in dist:
                    print(f"Task {i} is assigned to {dist[i]}")
                    #
                upload_allotment_to_queue(dist,conn)
                pso_param.clear()
                
    
            
            #never delete this shit
            undone_tasks.clear()

                
    except KeyboardInterrupt:
        print("offloader stopped.")
