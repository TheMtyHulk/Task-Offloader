import numpy as np
import torch
import random
from collections import deque
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import time
from datetime import datetime
from PSOxMCT import Task_Assignment_Calc

pso_param={}
# edge_task_ids=[ ]
# assignment_to_edge={}

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.learning_rate = 0.001
        self.epsilon = 1.0  # Exploration factor
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.995

        # Neural networks (Q-network and target network)
        self.q_network = DQN(state_size, action_size)
        self.target_network = DQN(state_size, action_size)
        self.optimizer = torch.optim.Adam(self.q_network.parameters(), lr=self.learning_rate)

        self.update_target_network()

    def update_target_network(self):
        """ Update target network weights """
        self.target_network.load_state_dict(self.q_network.state_dict())

    def select_action(self, state):
        """ Non-deterministic action selection with epsilon-greedy approach """
        if np.random.rand() <= self.epsilon:
            return random.choice([0, 1])  # Randomly select action for exploration
        state = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        q_values = self.q_network(state)
        return torch.argmax(q_values).item()  # Choose best action based on Q-values

    def train(self):
        """ Train the agent """
        if len(self.memory) < 32:
            return
        batch = random.sample(self.memory, 32)

        for state, action, reward, next_state, done in batch:
            state = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            next_state = torch.tensor(next_state, dtype=torch.float32).unsqueeze(0)

            # Compute target for the current state
            target = reward
            if not done:
                next_q_values = self.target_network(next_state)
                target += self.gamma * torch.max(next_q_values).item()

            # Compute predicted Q-value for the chosen action
            q_values = self.q_network(state)
            q_value = q_values[0][action]

            # Compute loss (difference between predicted and target)
            loss = (q_value - target) ** 2

            # Backpropagation
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        # Reduce epsilon for less exploration over time
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# Define the Q-Network
class DQN(torch.nn.Module):
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__()
        self.fc1 = torch.nn.Linear(state_size, 128)
        self.fc2 = torch.nn.Linear(128, 128)
        self.fc3 = torch.nn.Linear(128, action_size)

    def forward(self, state):
        x = torch.relu(self.fc1(state))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)



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
            # break
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

def edge_Task_Allotment(assignment:dict) -> dict:
    pass


if __name__ == '__main__':
    # Simulation setup
    state_size = 3  # [task_size, edge_computation_power, cloud_computation_power]
    action_size = 2  # 0 = Edge, 1 = Cloud
    task_count = 0
    # Initialize DQN agent
    agent = DQNAgent(state_size, action_size)
    
    db=connect_To_DB()
    tasks_cluster = db['tasks']
    
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
                tasks_cluster.update_one({'_id': undone_tasks[i]}, {'$set': {'assigned_to': 'Edge' if action == 0 else 'Cloud'}}) 
                
                if action == 0:
                    # edge_task_ids.append(undone_tasks[i])
                    pso_param[undone_tasks[i]] = task_size.get(undone_tasks[i])
                    
                print(f"Task {undone_tasks[i]}: Allocated to {'Edge' if action == 0 else 'Cloud'}")

            t=Task_Assignment_Calc(3,pso_param)
            dist=t.get_distribution()
            
            # for key,val in dist.items():
            #     if val in assignment_to_edge:
            #         assignment_to_edge['E'+str(val)].append(key)
            #     else:
            #         assignment_to_edge['E'+str(val)]=[key]
            #     assignment_to_edge['E'+str(val)]=[key]
            # undone_tasks.clear()
                
    except KeyboardInterrupt:
        print("Server stopped.")




















'''
# Simulation setup
state_size = 3  # [task_size, edge_computation_power, cloud_computation_power]
action_size = 2  # 0 = Edge, 1 = Cloud

# Initialize DQN agent
agent = DQNAgent(state_size, action_size)

# Simulation loop: run for a number of tasks
num_tasks = 50  # You can adjust the number of tasks
for task_num in range(num_tasks):
    # Dynamically generate task parameters (task size, edge computation power, cloud computation power)
    task_size = random.uniform(0.1, 1.0)  # Task size between 0.1 and 1.0
    edge_computation_power = random.uniform(0.2, 1.0)  # Edge computation power between 0.2 and 1.0
    cloud_computation_power = random.uniform(0.2, 1.0)  # Cloud computation power between 0.2 and 1.0

    # Current state: [task_size, edge_computation_power, cloud_computation_power]
    state = [task_size, edge_computation_power, cloud_computation_power]

    # Select action with epsilon-greedy approach
    action = agent.select_action(state)

    # Calculate reward based on computation power and task size
    if action == 0:  # Edge
        reward = edge_computation_power * task_size  # Positive reward for higher computational cost
    else:  # Cloud
        reward = cloud_computation_power * task_size  # Positive reward for higher computational cost

    # The next state: simulate next task (dynamically generated)
    next_task_size = random.uniform(0.1, 1.0)
    next_edge_computation_power = random.uniform(0.2, 1.0)
    next_cloud_computation_power = random.uniform(0.2, 1.0)
    next_state = [next_task_size, next_edge_computation_power, next_cloud_computation_power]

    # Done flag (whether the task is done)
    done = True  # For this example, we consider each task completion as done

    # Store experience in memory
    agent.memory.append((state, action, reward, next_state, done))

    # Train the agent using experiences
    agent.train()

    # Update the target network periodically
    if task_num % 10 == 0:
        agent.update_target_network()

    print(f"Task {task_num + 1}: Allocated to {'Edge' if action == 0 else 'Cloud'} with reward {reward:.2f}")
    
    '''