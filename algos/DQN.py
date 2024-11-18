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