# Task Offloading System

This project is a task offloading system that allows users to upload tasks (files) and distribute them for processing across edge and cloud resources. The system uses a combination of Deep Q-Network (DQN) and Particle Swarm Optimization (PSO) algorithms to optimize task assignments.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [License](#license)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/task-offloading-system.git
    cd task-offloading-system
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    - Create a `.env` file in the root directory and add the following:
        ```
        MONGO_URL=your_mongo_connection_string
        ```

5. Compile the protobuf files:
    ```sh
    python -m grpc_tools.protoc --proto_path=proto_buffs coordinator.proto --python_out=proto_buffs --grpc_python_out=proto_buffs
    ```

## Usage

1. Start the coordinator server:
    ```sh
    python coordinator.py
    ```

2. Start the DQN initialization script:
    ```sh
    python offloader.py
    ```

3. Start the edge worker:
    ```sh
    python Edge.py
    ```

4. Start the Node.js server:
    ```sh
    cd Node
    npm install
    npm start
    ```

5. Open your browser and navigate to `http://localhost:5002` to access the web interface.


## Project Structure
```
├── algos/
│   ├── DQN.py
│   ├── PSOxMCT.py
├── image_processing/
│   ├── process_img.py
│   ├── process_video.py
├── Node/
│   ├── .env
│   ├── app.js
│   ├── controllers/
│   ├── views/
│   └── package.json
├── proto_buffs/
│   ├── coordinator.proto
│   ├── coordinator_pb2.py
│   ├── coordinator_pb2_grpc.py
├── coordinator.py
├── offloader.py
├── Edge.py
├── requirements.txt
├── scheduler.py
└── LICENSE
```
## API Endpoints

### File Management

- `GET /files`: Retrieve all files.
- `GET /files/:filename`: Retrieve a file by its filename.
- `POST /upload`: Upload files.
- `POST /files/del/:id`: Delete a file by its ID.

### Task Management

- `GET /computed_at/:id`: Get the `computed_at` value of a file by its ID.
- `GET /computed_at`: Get the `computed_at` value of all files.
- `POST /schedule-tasks`: Schedule tasks for processing.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
