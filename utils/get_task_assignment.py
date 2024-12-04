def get_Task_Assignment_From_Queue(EDGE_ID,c):
    tasks =[]
    c.execute("SELECT TASK_ID FROM TASK_QUEUE WHERE EDGE=?", (EDGE_ID,))
    loc_db_tasks = c.fetchall()
    
    if loc_db_tasks:
        
        for t in loc_db_tasks:
            tasks.append(t[0])
        print(",".join(tasks))
        
        for t in tasks:    
            c.execute("DELETE FROM TASK_QUEUE WHERE TASK_ID=?", (t,))
        c.connection.commit()
        
        return ",".join(tasks)
    
    return None