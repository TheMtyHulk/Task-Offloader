import numpy as np
from pymongo import MongoClient
import os

class Task_Assignment_Calc:
    def __init__(self,num_vms,undonetasks:dict) -> None:
        
        self.num_vms = num_vms
        # client = MongoClient(os.getenv('MONGO_URL'))
        # self.db = client['taskmaster']
        # self.tasks=self.db['tasks']
        # files=self.db["fs.files"]

        self.undonetasks=undonetasks
        
        # for task in self.tasks.find({"picked_at": None}):
        #    self.undonetasks.append(task.get('_id'))
           
        self.num_tasks = len(self.undonetasks)
        
        estimated_task_times=[]
        
        for ud in self.undonetasks.values():
            # for file in files.find({'_id':ud}):
                estimated_task_times.append(ud)
                
        estimated_task_times=np.array(estimated_task_times)
        
        self.initial_distribution, initial_time = self.pso_task_scheduling(self.num_tasks, estimated_task_times, num_vms)
        actual_task_times = np.random.rand(self.num_tasks) * 8  # Actual times, for example
        adjusted_distribution, adjusted_time = self.adjust_scheduling(self.initial_distribution, actual_task_times, num_vms)
        self.adjusted_distribution=adjusted_distribution        
        # return adjusted_distribution
  
    # def estimate_task_times(self,num_tasks):
    #     return np.random.rand(num_tasks) * 10  # Random estimates between 0 and 10

    def initialize_particles(self,num_particles, num_tasks, num_vms):
        particles = np.zeros((num_particles, num_tasks, num_vms))
        for i in range(num_particles):
            for task_id in range(num_tasks):
                vm_id = np.random.randint(0, num_vms)
                particles[i, task_id, vm_id] = 1
        return particles

    def calculate_completion_time(self,particle, task_times):
        completion_times = np.sum(particle * task_times[:, None], axis=0)
        return np.max(completion_times)

    def update_particles(self,particles, velocities, global_best, personal_bests, task_times, w=0.5, c1=1.0, c2=1.5):
        num_particles = particles.shape[0]
        for i in range(num_particles):
            r1, r2 = np.random.rand(), np.random.rand()
            velocities[i] = w * velocities[i] + c1 * r1 * (personal_bests[i] - particles[i]) + c2 * r2 * (global_best - particles[i])
            particles[i] += velocities[i]
            particles[i] = np.clip(particles[i], 0, 1)
            # Ensure each task is assigned to exactly one VM
            for task_id in range(particles.shape[1]):
                assigned_vm = np.argmax(particles[i, task_id])
                particles[i, task_id] = 0
                particles[i, task_id, assigned_vm] = 1
        return particles, velocities

    def pso_task_scheduling(self,num_tasks, task_times, num_vms, num_particles=45, num_iterations=500):
        particles = self.initialize_particles(num_particles, num_tasks, num_vms)
        velocities = np.zeros_like(particles)
        personal_bests = np.copy(particles)
        personal_best_times = np.array([self.calculate_completion_time(p, task_times) for p in personal_bests])
        global_best = personal_bests[np.argmin(personal_best_times)]
        global_best_time = np.min(personal_best_times)

        for _ in range(num_iterations):
            for i, particle in enumerate(particles):
                completion_time = self.calculate_completion_time(particle, task_times)
                if completion_time < personal_best_times[i]:
                    personal_bests[i] = particle
                    personal_best_times[i] = completion_time
                    if completion_time < global_best_time:
                        global_best = particle
                        global_best_time = completion_time

            particles, velocities =self.update_particles(particles, velocities, global_best, personal_bests, task_times)

        # Convert global_best to the desired output format
        task_distribution = np.argmax(global_best, axis=1)
        adjusted_distribution = np.zeros((num_tasks, num_vms), dtype=int)
        for task_id, vm_id in enumerate(task_distribution):
            adjusted_distribution[task_id, vm_id] = 1

        return adjusted_distribution, global_best_time

    def adjust_scheduling(self,best_distribution, actual_task_times, num_vms):
        num_tasks = len(actual_task_times)
        adjusted_distribution, adjusted_time = self.pso_task_scheduling(num_tasks, actual_task_times, num_vms)
        return adjusted_distribution, adjusted_time

    def get_distribution(self)->dict:
        dist = {}
        distribution = self.adjusted_distribution
        _id=[x for x in self.undonetasks.keys()]
        for task_index, row in enumerate(distribution):
            for vm_index, assigned in enumerate(row):
                if assigned == 1:
                    task_id = _id[task_index]
                    dist[task_id] = vm_index
                    break  # Move to the next task after finding the assigned VM
        
        
        return dist
        

    # Main execution flow
    # num_tasks = 15

# num_vms = 5

# estimated_task_times = estimate_task_times(num_tasks)

# num_tasks = len(estimated_task_times)

# T=Task_Assignment_Calc(num_vms=5,)

# for task_assignment in T.get_distribution():
#     print(task_assignment)
# dictofdist,adjusted_dist,undonetasks=T.get_distribution()

# print(dictofdist)
# print(adjusted_dist)
# print(undonetasks)
# print("Adjusted Completion Time:", adjusted_time)