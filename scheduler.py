import os
import gridfs
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv

class scheduler:
    
    def __init__(self):
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URL')
        client = MongoClient(mongo_uri)
        
        self.db = client['taskmaster']
        # self.schedule("tasks")
    
    def schedule(self, directory):
        db = self.db
        tasks = db['tasks']
        fs=gridfs.GridFS(db)
        for name in os.listdir(directory):
            uuid=str(uuid4())
            if not name.endswith('.jpg') and not name.endswith('.jpeg') and not name.endswith('.png'):
                continue
            with open(os.path.join(directory, name), 'rb') as f:
                fs.put(f, filename=name,_id=uuid)
            tasks.create_index("scheduled_at")
            tasks.insert_one({
				"_id": uuid,
				"command": name,
				"scheduled_at": datetime.now().strftime('%H:%M:%S'),
				"picked_at": None,
				"started_at": None,
				"completed_at": None,
				"completed_by": None,
                "assigned_to":None
			})
        print("All images have been uploaded to MongoDB and tasks have been scheduled.")
s=scheduler()
s.schedule("tasks/images")