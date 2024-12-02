import grpc
import time
from proto_buffs import coordinator_pb2
from proto_buffs import coordinator_pb2_grpc
from gridfs import GridFS
from pymongo import MongoClient
import os
import logging
from bson import ObjectId
from image_processing.process_img import process_img  
from image_processing.process_vedio import process_video
import datetime
from bson import ObjectId
import jwt
from dotenv import load_dotenv
from grpc import ssl_channel_credentials
import psutil


def get_Computation_Power():
    # Get the CPU usage percentage
    cpu_usage = psutil.cpu_percent()
    # Get the memory usage percentage
    memory_usage = psutil.virtual_memory().percent
    avg_util=(cpu_usage+memory_usage)/2
    computation_power=(100-avg_util)/100
    computation_power=round(computation_power,2)

    return computation_power

def compute(task_id, db):
    try:
        fs = GridFS(db)
        filee = fs.find_one({"_id": ObjectId(task_id)})
        tasks=db['tasks']
        if not filee:
            raise Exception("File not found in GridFS with the provided task_id")

        # Create a directory for saving the file if it does not exist
        save_dir = 'working_files'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    
        #adjusting the file name to avoid overwriting 
        filename, file_extension = os.path.splitext(filee.filename)
        
        new_filename=task_id+file_extension
        
        file_path = os.path.join(save_dir, filename+file_extension)
        
        
        # Save the file to the directory
        with open(file_path, "wb") as f:
            f.write(filee.read())
            logging.info("file saved successfully")
        # if os.path.exists(file_path):

        if file_extension==".jpg" or file_extension==".png" or file_extension==".jpeg":
            tasks.update_one({"_id":ObjectId(task_id)}, {"$set": {"started_at": datetime.datetime.now()}})
            
            compute_img(file_path,new_filename,filename,file_extension,task_id,fs)  
            # print(file_path,new_filename,filename,file_extension,task_id,fs)
            tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed_at": datetime.datetime.now()}})
            
            logging.info(f"File {filee.filename} has been successfully saved ")
            
        elif file_extension==".mp4" or file_extension==".avi" or file_extension==".mov":
            tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"started_at": datetime.datetime.now()}})
            compute_video(file_path,new_filename,filename,file_extension,task_id,fs)
            tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed_at": datetime.datetime.now()}})
            logging.info(f"File {filee.filename} has been successfully saved ")
        else:
            logging.error("File format not supported")
            
        # print(f"File {filee.filename} has been successfully saved to {file_path}")
        
        return 

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def compute_img(file_path,new_filename,filename,file_extension,task_id,fs):
    # Process the image (this function should save the computed image to a new file path)
    computed_file_path = process_img(file_path, new_filename, filename, file_extension, task_id)
    
    # Find the old file by its task_id
    old_file = fs.find_one({"_id": ObjectId(task_id)})
    if old_file:
        # Retrieve the old file's metadata
        old_file_id = old_file._id
        old_metadata = old_file.metadata if old_file.metadata else {}
        old_content_type = old_file.contentType if old_file.contentType else {}

        # Delete the old file
        fs.delete(old_file_id)

        # Upload the computed file with the same _id and metadata
        with open(computed_file_path, "rb") as f:
            fs.put(f, _id=old_file_id, filename=filename, metadata=old_metadata,contentType=old_content_type)

    
    # print("File replaced successfully with the computed image.")
    logging.info("File replaced successfully with the computed image.")
    # Delete the computed file
    print(computed_file_path)
    print(file_path)
    # os.remove(computed_file_path)
    # os.remove(file_path)
    return


def compute_video(file_path,new_filename,filename,file_extension,task_id,fs):
    computed_file_path = process_video(file_path, new_filename, filename, file_extension, task_id)
    
    # Find the old file by its task_id
    old_file = fs.find_one({"_id": ObjectId(task_id)})
    if old_file:
        # Retrieve the old file's metadata
        old_file_id = old_file._id
        old_metadata = old_file.metadata if old_file.metadata else {}
        old_content_type = old_file.contentType if old_file.contentType else {}

        # Delete the old file
        fs.delete(old_file_id)

        # Upload the computed file with the same _id and metadata
        with open(computed_file_path, "rb") as f:
            fs.put(f, _id=old_file_id, filename=filename, metadata=old_metadata, contentType=old_content_type)

    
    # print("File replaced successfully with the computed image.")
    logging.info("File replaced successfully with the computed image.")
    # Delete the computed file
    os.remove(computed_file_path)
    os.remove(file_path)
    return


def generate_jwt(edge_id):
    SECRET_KEY=os.getenv('JWT_SECRET')
    payload = {
        'edgeId': edge_id, 
        'exp': datetime.datetime.now() + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(payload,SECRET_KEY, algorithm='HS256')
    return token

def run_worker(edge_id):
    try:
        with open('openssl-keys/server.crt', 'rb') as f:
            certificate_chain = f.read()
    except FileNotFoundError:
        print("Certificate file not found.")
        return
    
    credentials = grpc.ssl_channel_credentials(certificate_chain)
    channel = grpc.secure_channel('127.0.0.1:50051',credentials)
    stub = coordinator_pb2_grpc.CoordinatorServiceStub(channel)

    def heartbeat_stream():
        last_time_comp_pow_sent=0
        while True:
            current_time = time.time()
            
            if current_time - last_time_comp_pow_sent >= 60:
                pow = get_Computation_Power()
                yield coordinator_pb2.HeartbeatRequest(edgeId=edge_id, computation_power=pow)
                last_time_comp_pow_sent = current_time
                
            else:
                yield coordinator_pb2.HeartbeatRequest(edgeId=edge_id)
            
            time.sleep(5)  # Send heartbeat every 5 seconds
    
    token = generate_jwt(edge_id)
    metadata = [('authorization', token)]
    try:
        for response in stub.HeartbeatStream(heartbeat_stream(), metadata=metadata):
            if response.taskId:
                # print(f"Worker {worker_id} received task: {response.taskId}")
                client = MongoClient(os.getenv('MONGO_URL'))
                
                for task_id in response.taskId.split(","):
                   
                    compute(task_id, client['taskmaster'])
                   
                # Process the task here
            else:
                print(f"edge {edge_id} received no task.",response.ack)
    except grpc.RpcError as e:
        print(f"edge {edge_id} encountered an error: {e}")
    except KeyboardInterrupt:
        print(f"edge {edge_id} stopped.")
        
if __name__ == '__main__':
    load_dotenv()
    #set base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    edge_id = "E1"  # Replace with a unique worker ID
    run_worker(edge_id)
    
    
    
    

