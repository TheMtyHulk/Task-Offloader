from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc
from concurrent import futures
from datetime import datetime
import os
import grpc
import time
import sqlite3

worker_set=set()



class CoordinatorService(coordinator_pb2_grpc.CoordinatorServiceServicer):
    def __init__(self):

        conn = sqlite3.connect('queue.db', check_same_thread=False)
        self.c = conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS WORKER_POOL (EDGE_ID STRING PRIMARY KEY)''')



    def get_Task_Assignment_From_Queue(self,EDGE_ID):
        tasks =[]
        self.c.execute("SELECT TASK_ID FROM TASK_QUEUE WHERE EDGE=?", (EDGE_ID,))
        loc_db_tasks = self.c.fetchall()
        
        if loc_db_tasks:
            
            for t in loc_db_tasks:
                tasks.append(t[0])
            print(",".join(tasks))
            
            for t in tasks:    
                self.c.execute("DELETE FROM TASK_QUEUE WHERE TASK_ID=?", (t,))
            self.c.connection.commit()
            
            return ",".join(tasks)
        
        return None
    
    def add_worker_to_pool(self,EDGE_ID):
        self.c.execute("INSERT INTO WORKER_POOL (EDGE_ID) VALUES (?)", (EDGE_ID,))
        self.c.connection.commit()
        return
    
    def HeartbeatStream(self, request_iterator, context):
        for request in request_iterator:
            
            if request.workerId not in worker_set:
                worker_set.add(request.workerId)
                self.add_worker_to_pool(request.workerId)
            
            print(f"Received heartbeat from worker {request.workerId}")
            # tasks = self.tasks.get(request.workerId, [])
            tasks=self.get_Task_Assignment_From_Queue(request.workerId)
            
            if tasks:
                response = coordinator_pb2.TaskResponse(
                    ack="Acknowledged",
                    taskId=tasks,
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
    
    