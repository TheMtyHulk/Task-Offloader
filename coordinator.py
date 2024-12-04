from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc
from concurrent import futures
from datetime import datetime
import os
import grpc
import time
import sqlite3
from utils.auth_interceptor import JWTAuthInterceptor
from utils.update_computaion_pow import update_Computation_Power
from utils.get_task_assignment import get_Task_Assignment_From_Queue
from utils.add_worker_to_pool import add_Worker_To_Pool
from dotenv import load_dotenv
import jwt
import logging

worker_set=set()



class CoordinatorService(coordinator_pb2_grpc.CoordinatorServiceServicer):
    def __init__(self):

        conn = sqlite3.connect('queue.db', check_same_thread=False)
        self.c = conn.cursor()
        #create worker pool and task queue tables if not exist
        self.c.execute('''CREATE TABLE IF NOT EXISTS WORKER_POOL (EDGE_ID STRING PRIMARY KEY, TIMESTAMP DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS TASK_QUEUE (TASK_ID STRING PRIMARY KEY, EDGE STRING)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS COMPUTATION_POWER(EDGE STRING PRIMARY KEY, POWER REAL)''')
       
        self.c.connection.commit()


        
    def HeartbeatStream(self, request_iterator, context):
        for request in request_iterator:
            
            #add edge device to worker pool
            if request.edgeId :
                add_Worker_To_Pool(request.edgeId,self.c)
            if request.computation_power:
                update_Computation_Power(request.edgeId,request.computation_power,self.c)
             
            print(f"Received heartbeat from edge {request.edgeId}")
            # tasks = self.tasks.get(request.workerId, [])
            tasks=get_Task_Assignment_From_Queue(request.edgeId,self.c)
            
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
    load_dotenv()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), interceptors=[JWTAuthInterceptor(os.getenv('JWT_SECRET'))])
    coordinator_pb2_grpc.add_CoordinatorServiceServicer_to_server(CoordinatorService(), server)
    
    #load SSL/TLS certificate
    try:
        with open('openssl-keys/server.crt', 'rb') as f:
            certificate_chain = f.read()
        with open('openssl-keys/server.key', 'rb') as f:
            private_key = f.read()
    except FileNotFoundError:
        print("Certificate and/or private key file not found")
        return
    
    server_credentials = grpc.ssl_server_credentials([(private_key, certificate_chain,)])
    server.add_secure_port('[::]:50051', server_credentials)
    server.start()
    # server.wa
    print("Server started, listening on port 50051.")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
    
    