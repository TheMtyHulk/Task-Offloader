from datetime import datetime

def add_Worker_To_Pool(EDGE_ID,c):
    temp = c.execute("SELECT * FROM WORKER_POOL WHERE EDGE_ID=:edge_id", {"edge_id": EDGE_ID})
    
    # if worker already in pool, update timestamp
    if temp.fetchone():
        c.execute(
            "UPDATE WORKER_POOL SET TIMESTAMP=:timestamp WHERE EDGE_ID=:edge_id",
            {"timestamp": datetime.now(), "edge_id": EDGE_ID}
        )
        c.connection.commit()
        return
    
    c.execute(
        "INSERT INTO WORKER_POOL (EDGE_ID, TIMESTAMP) VALUES (:edge_id, :timestamp)",
        {"edge_id": EDGE_ID, "timestamp": datetime.now()}
    )
    c.connection.commit()
    return