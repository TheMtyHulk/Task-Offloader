import sqlite3
import os


base_dir = os.path.dirname(os.path.abspath(__file__))

def update_Computation_Power(EDGE_ID, pow,c):
    pow=round(pow,2)
    # Check if the EDGE_ID already exists in the table
    temp = c.execute("SELECT * FROM COMPUTATION_POWER WHERE EDGE=:edge_id", {"edge_id": EDGE_ID})
    
    if temp.fetchone():
        # If EDGE_ID exists, update the computation power
        c.execute(
            "UPDATE COMPUTATION_POWER SET POWER=:power WHERE EDGE=:edge_id",
            {"power": pow, "edge_id": EDGE_ID}
        )
    else:
        # If EDGE_ID does not exist, insert a new record
        c.execute(
            "INSERT INTO COMPUTATION_POWER (EDGE, POWER) VALUES (:edge_id, :power)",
            {"edge_id": EDGE_ID, "power": pow}
        )
    
    # Commit the transaction
    c.connection.commit()