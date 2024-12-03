import azure.functions as func
import datetime, json, logging, os, time
from pymongo import MongoClient
from gridfs import GridFS
from image_processing.process_img import process_img
from image_processing.process_vedio import process_video
from bson import ObjectId

app = func.FunctionApp()

@app.timer_trigger(schedule="*/10 * * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def TimerTriggerFunction(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')
    
    # Current UTC time
    current_utc_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Get the connection string from the environment variable
    connection_string = os.getenv('MONGO_CONNECTION_STRING')
    
    if not connection_string:
        logging.error('MONGO_CONNECTION_STRING is not set.')
        return
    
    # Retry 5 times to connect to MongoDB
    for i in range(5):
        try:
            client = MongoClient(connection_string)
            print("Connected to MongoDB")
            break
        except:
            logging.error('Failed to connect to MongoDB. Retrying...')
            time.sleep(5)
    
    # Get the database and collection
    try:
        tasks = client['taskmaster']['tasks']
        
        for task in tasks.find({'assigned_to': "cloud", 'started_at': None}):
            tasks.update_one({"_id": task['_id']}, {"$set": {"started_at": datetime.datetime.now()}})
            compute(str(task.get('_id')), client['taskmaster'])  # Convert ObjectId to string
            # logging.info(task)
            
        
        logging.info('Python timer trigger function executed.')
    except Exception as e:
        logging.error(f'An error occurred: {e}')

def compute(task_id, db):
    try:
        fs = GridFS(db)
        filee = fs.find_one({"_id": ObjectId(task_id)})  # Convert task_id back to ObjectId
        tasks = db['tasks']
        if not filee:
            raise Exception("File not found in GridFS with the provided task_id")
        # Create a directory for saving the file if it does not exist
        save_dir = 'working_files'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
        # Adjusting the file name to avoid overwriting 
        filename, file_extension = os.path.splitext(filee.filename)
        
        new_filename = str(task_id) + file_extension  # Ensure task_id is a string
        
        file_path = os.path.join(save_dir, filename + file_extension)
        
        # Save the file to the directory
        with open(file_path, "wb") as f:
            f.write(filee.read())
            
        if file_extension in [".jpg", ".png", ".jpeg"]:
            compute_img(file_path, new_filename, filename, file_extension, task_id, fs)
        elif file_extension in [".mp4", ".avi", ".mov"]:
            compute_video(file_path, new_filename, filename, file_extension, task_id, fs)
        else:
            logging.error("File format not supported")
        
        tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed_at": datetime.datetime.now()}})
        logging.info(f"File {filee.filename} has been successfully saved ")
        
        return task_id
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None
 
 
def compute_img(file_path,new_filename,filename,file_extension,task_id,fs):
    # Process the image (this function should save the computed image to a new file path)
    computed_file_path = process_img(file_path, new_filename, filename, file_extension, task_id)
    print(computed_file_path)
    # Find the old file by its task_id
    old_file = fs.find_one({"_id": ObjectId(task_id)})
    if old_file:
        # Retrieve the old file's metadata
        old_file_id = old_file._id
        old_metadata = old_file.metadata if old_file.metadata else {}
        old_content_type = old_file.contentType if old_file.contentType else {}

        # Delete the old file
        fs.delete(ObjectId(old_file_id))

        # Upload the computed file with the same _id and metadata
        with open(computed_file_path, "rb") as f:
            fs.put(f, _id=ObjectId(old_file_id), filename=filename+file_extension, metadata=old_metadata,contentType=old_content_type)

    
    # print("File replaced successfully with the computed image.")
    logging.info("File replaced successfully with the computed image.")
    # Delete the computed file
    os.remove(computed_file_path)
    os.remove(file_path)
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
        fs.delete(ObjectId(old_file_id))

        # Upload the computed file with the same _id and metadata
        with open(computed_file_path, "rb") as f:
            fs.put(f, _id=ObjectId(old_file_id), filename=filename+file_extension, metadata=old_metadata,contentType=old_content_type)

    
    # print("File replaced successfully with the computed image.")
    logging.info("File replaced successfully with the computed image.")
    # Delete the computed file
    os.remove(computed_file_path)
    os.remove(file_path)
    return
