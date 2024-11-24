import subprocess
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


if os.path.exists('queue.db'):
    os.remove('queue.db')

if not os.path.exists('queue.db'):
    open('queue.db', 'w').close()

# Path to the virtual environment's Python interpreter
venv_python = os.path.join('venv', 'Scripts', 'python.exe')  # Use 'Scripts' on Windows

# Start the subprocesses
logging.info("Starting subprocesses...")
process2 = subprocess.Popen([venv_python, 'coordinator.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(15)
process1 = subprocess.Popen([venv_python, 'offloader.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)



try:
    while True:
        # Check if the subprocesses are still running
        if process1.poll() is not None:
            logging.error("Process 1 has terminated unexpectedly.")
            break
        if process2.poll() is not None:
            logging.error("Process 2 has terminated unexpectedly.")
            break

        # Optionally, read the output from the subprocesses
        stdout1 = process1.stdout.readline()
        if stdout1:
            logging.info(f"Process 1 output: {stdout1.decode().strip()}")
        
        stdout2 = process2.stdout.readline()
        if stdout2:
            logging.info(f"Process 2 output: {stdout2.decode().strip()}")

        # Sleep for a while before checking again
        time.sleep(1)

except KeyboardInterrupt:
    logging.info("Terminating subprocesses...")
    process1.terminate()
    process2.terminate()
    process1.wait()
    process2.wait()
    logging.info("Subprocesses terminated.")