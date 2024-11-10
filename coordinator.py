from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc
from concurrent import futures
from datetime import datetime
from pymongo import MongoClient
import os
import grpc
import time
from algos import PSOxMCT
worker_set=set()

'''
what do i want to do?
make the coordinator and the edge server communicate
make the edge server do the task 
make the coordinator assign the task to the edge server
make the coordinator assign the task to edge server using the algorithm[pso]
'''



class CoordinatorService(coordinator_pb2_grpc.CoordinatorServiceServicer):
    def __init__(self):
        
        #this is the dictionary that will hold the tasks should look like
        # self.tasks = {
        #     "worker1": ["task1", "task2"],
        #     "worker2": ["task3"]
        # }
        
        #initialize the mongo client and connections
        client = MongoClient(os.getenv('MONGO_URL'))
        self.db = client['taskmaster']
        self.db_tasks=self.db['tasks']
        self.files=self.db_db["fs.files"]
        
        #this holds the tasks that are not done
        self.undone_tasks={}
        self.assigned_tasks={}
        
    #search for the tasks that undone tasks if so make a dict of it and return true
    def get_Undone_Tasks(self):

        for task in self.db_tasks.find({"picked_at": None, "assigned_at": None}):
            file_length=self.files.find_one({"_id":task.get('_id')}).get('length')
            self.undone_tasks[task.get('_id')]=round(file_length/1024/1024,2)
            
        if not self.undone_tasks:
            '''
            no task is left to be done so return false
            '''
            return False
        return True
    
    def get_Task_assignment(self):
        pass
            
    def HeartbeatStream(self, request_iterator, context):
        for request in request_iterator:
            worker_set.add(request.workerId)
            print(f"Received heartbeat from worker {request.workerId}")
            # tasks = self.tasks.get(request.workerId, [])
            if self.get_Undone_Tasks():
                task_id = self.undone_tasks.pop(0)
                self.tasks.find_one_and_update(
                    {"_id": task_id},
                    {"$set": {"picked_at": datetime.now().strftime('%H:%M:%S')}}
                )
                response = coordinator_pb2.TaskResponse(
                    ack="Acknowledged",
                    taskId=str(task_id),
                    workerId=request.workerId
                )
            else:
                response = coordinator_pb2.TaskResponse(
                    ack="Acknowledged",
                    taskId="",
                    workerId=request.workerId
                )
            yield response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    coordinator_pb2_grpc.add_CoordinatorServiceServicer_to_server(CoordinatorService(), server)
    server.add_insecure_port('localhost:50051')
    server.start()
    print("Server started, listening on port 50051.")
    try:
        while True:
            time.sleep(86400)  # Keep the server running for 24 hours
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
    
    