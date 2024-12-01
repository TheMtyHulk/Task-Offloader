from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc
from concurrent import futures
from datetime import datetime
import os
import grpc
import time
import sqlite3
import threading
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
    def add_Worker_To_Pool(self, EDGE_ID):
        temp = self.c.execute("SELECT * FROM WORKER_POOL WHERE EDGE_ID=:edge_id", {"edge_id": EDGE_ID})
        
        # if worker already in pool, update timestamp
        if temp.fetchone():
            self.c.execute(
                "UPDATE WORKER_POOL SET TIMESTAMP=:timestamp WHERE EDGE_ID=:edge_id",
                {"timestamp": datetime.now(), "edge_id": EDGE_ID}
            )
            self.c.connection.commit()
            return
        
        self.c.execute(
            "INSERT INTO WORKER_POOL (EDGE_ID, TIMESTAMP) VALUES (:edge_id, :timestamp)",
            {"edge_id": EDGE_ID, "timestamp": datetime.now()}
        )
        self.c.connection.commit()
        return
    
    def HeartbeatStream(self, request_iterator, context):
        for request in request_iterator:
            
            #add edge device to worker pool
            if request.edgeId :
                self.add_Worker_To_Pool(request.edgeId)
            
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
          

class JWTAuthInterceptor(grpc.ServerInterceptor):
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get('authorization')
        if not token:
            context = handler_call_details.invocation_metadata
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Authorization token is missing')
        try:
            jwt.decode(token, self.secret_key, algorithms=['HS256'])
            print(f"Authentication successful for token: {token}")
            logging.info(f"Authentication successful for token: {token}")
        except jwt.ExpiredSignatureError:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Token has expired')
        except jwt.InvalidTokenError:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid token')
        return continuation(handler_call_details)


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
    
    