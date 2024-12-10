def upload_allotment_to_queue(dist:dict,conn) -> dict:
    
    if not dist:
        return
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS task_queue (TASK_ID STRING PRIMARY KEY, EDGE STRING)''')
    
    EDGE_POOL=[i[0] for i in c.execute("SELECT * FROM WORKER_POOL").fetchall()]
    
    if not EDGE_POOL:
        print("No edge devices available. Please add edge devices to the pool.")
        return
    
    # Create a mapping from matrix-produced values to actual edge device IDs
    edge_mapping = {i: EDGE_POOL[i] for i in range(len(EDGE_POOL))}
    
    for key, val in dist.items():
        if c.execute("SELECT * FROM task_queue WHERE TASK_ID=?", (str(key),)).fetchone():
            continue
        if val not in edge_mapping:
            val = 0  # Default to the first available edge device if the value is not in the mapping
        actual_edge_id = edge_mapping[val]
        c.execute("INSERT INTO task_queue (TASK_ID, EDGE) VALUES (?, ?)", (str(key), str(actual_edge_id)))
    conn.commit()
    
    return