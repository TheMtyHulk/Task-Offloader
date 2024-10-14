import os
import gridfs
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime

class scheduler:
    def __init__(self):
        client = MongoClient(os.getenv('MONGO_URL'))
        self.db = client['taskmaster']
        # self.schedule("tasks")
    
    def schedule(self, directory):
        db = self.db
        tasks = db['tasks']
        fs=gridfs.GridFS(db)
        for name in os.listdir(directory):
            uuid=str(uuid4())
            if not name.endswith('.pdf'):
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
        print("All PDF files have been uploaded to MongoDB and tasks have been scheduled.")
s=scheduler()
s.schedule("tasks")