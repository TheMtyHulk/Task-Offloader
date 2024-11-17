import grpc
import time
from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc
from gridfs import GridFS
from pymongo import MongoClient
import os

def compute(tasks_list):
    print("Computing tasks")
    for task in tasks_list:
        print(task)
    return "Task completed"

def run_worker(edge_id):
    channel = grpc.insecure_channel('localhost:50051')
    stub = coordinator_pb2_grpc.CoordinatorServiceStub(channel)

    def heartbeat_stream():
        while True:
            yield coordinator_pb2.HeartbeatRequest(edgeId=edge_id)
            time.sleep(5)  # Send heartbeat every 5 seconds

    try:
        for response in stub.HeartbeatStream(heartbeat_stream()):
            if response.taskId:
                # print(f"Worker {worker_id} received task: {response.taskId}")
               
                compute(response.taskId.split(","))
                # Process the task here
            else:
                print(f"edge {edge_id} received no task.",response.ack)
    except grpc.RpcError as e:
        print(f"edge {edge_id} encountered an error: {e}")
    except KeyboardInterrupt:
        print(f"edge {edge_id} stopped.")
        
if __name__ == '__main__':
    edge_id = "E1"  # Replace with a unique worker ID
    run_worker(edge_id)