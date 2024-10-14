import coordinator_pb2
import coordinator_pb2_grpc
from concurrent import futures
from datetime import datetime
from pymongo import MongoClient
import os
import grpc
import time

worker_set=set()

class CoordinatorService(coordinator_pb2_grpc.CoordinatorServiceServicer):
    def __init__(self):
        # self.tasks = {
        #     "worker1": ["task1", "task2"],
        #     "worker2": ["task3"]
        # }
        client = MongoClient(os.getenv('MONGO_URL'))
        self.db = client['taskmaster']
        self.tasks=self.db['tasks']
        self.undone_tasks=[]
        
        for task in self.tasks.find({"picked_at": None}):
            self.undone_tasks.append(task.get('_id'))
            
            
    def HeartbeatStream(self, request_iterator, context):
        for request in request_iterator:
            worker_set.add(request.workerId)
            print(f"Received heartbeat from worker {request.workerId}")
            # tasks = self.tasks.get(request.workerId, [])
            if self.undone_tasks:
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
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started, listening on port 50051.")
    try:
        while True:
            time.sleep(86400)  # Keep the server running for 24 hours
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
    
    