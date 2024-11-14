import grpc
import time
from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc


def run_worker(worker_id):
    channel = grpc.insecure_channel('localhost:50051')
    stub = coordinator_pb2_grpc.CoordinatorServiceStub(channel)

    def heartbeat_stream():
        while True:
            yield coordinator_pb2.HeartbeatRequest(workerId=worker_id)
            time.sleep(5)  # Send heartbeat every 5 seconds

    try:
        for response in stub.HeartbeatStream(heartbeat_stream()):
            if response.taskId:
                # print(f"Worker {worker_id} received task: {response.taskId}")
                print(response.taskId.split(","))
                # Process the task here
            else:
                print(f"Worker {worker_id} received no task.",response.ack)
    except grpc.RpcError as e:
        print(f"Worker {worker_id} encountered an error: {e}")
    except KeyboardInterrupt:
        print(f"Worker {worker_id} stopped.")
        
if __name__ == '__main__':
    worker_id = "E1"  # Replace with a unique worker ID
    run_worker(worker_id)