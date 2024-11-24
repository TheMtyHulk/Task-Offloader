from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc
from concurrent import futures
from datetime import datetime
import os
import grpc
import time
import sqlite3
import threading

worker_set=set()



class CoordinatorService(coordinator_pb2_grpc.CoordinatorServiceServicer):
    def __init__(self):

        conn = sqlite3.connect('queue.db', check_same_thread=False)
        self.c = conn.cursor()
        #create worker pool and task queue tables if not exist
        self.c.execute('''CREATE TABLE IF NOT EXISTS WORKER_POOL (EDGE_ID STRING PRIMARY KEY, TIMESTAMP DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS TASK_QUEUE (TASK_ID STRING PRIMARY KEY, EDGE STRING)''')

        # self.start_periodic_task()


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
    
    
    #add edge device to worker pool
    def add_Worker_To_Pool(self,EDGE_ID):
        temp=self.c.execute("SELECT * FROM WORKER_POOL WHERE EDGE_ID=?", (EDGE_ID,))
        
        # if worker already in pool, update timestamp
        if temp.fetchone():
            self.c.execute("UPDATE WORKER_POOL SET TIMESTAMP=? WHERE EDGE_ID=?", (datetime.now(),EDGE_ID))
            self.c.connection.commit()
            return
        
        self.c.execute("INSERT INTO WORKER_POOL (EDGE_ID) VALUES (?)", (EDGE_ID,datetime.now()))
        self.c.connection.commit()
        return
    
    def HeartbeatStream(self, request_iterator, context):
        for request in request_iterator:
            
            # if request.edgeId not in worker_set:
                # worker_set.add(request.edgeId)
            if request.edgeId :
                self.add_worker_to_pool(request.edgeId)
            
            print(f"Received heartbeat from edge {request.edgeId}")
            # tasks = self.tasks.get(request.workerId, [])
            tasks=self.get_Task_Assignment_From_Queue(request.edgeId)
            
            if tasks:
                response = coordinator_pb2.TaskResponse(
                    ack="Acknowledged",
                    taskId=tasks,
                    edgeId=request.edgeId
                )
            else:
                response = coordinator_pb2.TaskResponse(
                    ack="Acknowledged",
                    taskId="",
                    edgeId=request.edgeId
                )
            yield response
          

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    coordinator_pb2_grpc.add_CoordinatorServiceServicer_to_server(CoordinatorService(), server)
    server.add_insecure_port('localhost:50051')
    server.start()
    # server.wa
    print("Server started, listening on port 50051.")
    # try:
    #     while True:
    #         time.sleep(86400)  # Keep the server running for 24 hours
    # except KeyboardInterrupt:
    #     server.stop(0)
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
    
    