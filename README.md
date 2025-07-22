# Multithreaded TCP Server with SSL Support

This repository contains a simple multithreaded TCP server implemented in Python. It is designed to demonstrate robust client handling, SSL/TLS support, and operation as a background service. The server listens for incoming secure connections, echoes received messages back to clients, and handles each client connection in a separate thread.

The application is containerized using Docker, providing a consistent and isolated environment for development and deployment. This README.md guides you through setting up and running the server, both for local development/testing and as a persistent Linux service using systemd.


## 1. Project Overview

## ✅ Linux Daemon Support

This server is designed and tested to run as a persistent Linux background service using:

- `systemd` (preferred for production setups)
- Docker (containerized deployment)
- Manual daemonization (for quick tests)

A complete systemd configuration is provided below, allowing the server to be started, stopped, and enabled at boot like any traditional Linux service.

➡️ If you're looking for persistent, production-grade deployment, jump to the “Running as a Linux Daemon” section.
A pre-configured systemd service file is available under the deploy/ directory for quick setup.

This server provides an exact string-matching service against a file (e.g., 200k.txt). It is multithreaded to handle multiple client connections concurrently and uses SSL/TLS for secure communication. Key features include:

* Secure communication via SSL/TLS
* Concurrent client handling using Python's threading module
* Configurable string search (re-read file on each query or use a cached set)
* Containerized with Docker for easy deployment
* Designed for persistent operation as a systemd service on Linux

## 2. Project Structure

The project has the following structure:
├── server.py             # The core multithreaded TCP server application with SSL support  
├── client.py             # Example client to connect to and query the server  
├── config.ini            # Configuration file for the server (SSL, file paths, etc.)  
├── requirements.txt      # Python dependencies for the server and client  
├── cert.pem              # SSL certificate file  
├── key.pem               # SSL private key file  
├── 200k.txt              # Example data file for string searching  
├── Dockerfile            # Docker instructions to build the server image  
├── README.md             # This documentation file  
├── benchmarks.py         # Benchmarking the algorithm's speed and performance  
└── tests/  
    ├── test_client_server.py   # Tests client connection and requests to the server  
    ├── test_config.py          # Tests ThreadedServer's ability to load configuration from config.ini  
    ├── test_integration.py     # Tests overall system integration  
    └── test_search.py          # Tests the string search method in ThreadedServer  
    └── test_benchmarks.py      # Tests the performance of the algorithm

      
## 3. Prerequisites

To build and run this application, you will need:

Docker Desktop (for macOS/Windows development and testing) – Download it from Docker's official website.
A Linux Server or VM (for production deployment as a daemon/service) – This server should have Docker Engine installed.


## Generate SSL Certificates
Run the following command to generate a self-signed SSL certificate and private key.
This is used for ssl.wrap_socket():

bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

This command will generate a self-signed SSL certificate and private key.
It creates the following two files in the current directory:
key.pem — your private key
cert.pem — your self-signed certificate


## 4. Getting Started (Local Development/Testing with Docker)

This section explains how to quickly get the server running on your local machine using Docker Desktop.

# config.ini
[DEFAULT]
ssl_enabled = True             # IMPORTANT: Set to True for SSL/TLS connections
linuxpath = /app/200k.txt      # Path to your 200k.txt inside the Docker container
reread_on_query = False        # Set to True to re-read the file on every query, False to cache

Build the Docker Image
Navigate to the project's root directory (where the Dockerfile is located) and build the Docker image.
This process may take a few minutes on the first run as it downloads base images and installs dependencies.

Bash
## Build docker image
docker buildx build -t my-tcp-server .
docker run -d -p 44445:44445 --name tcp_server_container tcp-server
docker ps

connect to the server using python client.py "your_search_query"
## example
python client.py "hello"

## result should be
"STRING EXISTS" or "STRING NOT FOUND" from the server.


## Running as a Linux Daemon (Systemd Service)

**Overview:**

This section provides comprehensive instructions on how to run the server as a robust background service (daemon) on Linux systems that utilize systemd.
systemd is the modern and standard init system used by most contemporary Linux distributions (e.g., Ubuntu 16.04+, Debian 8+, CentOS 7+, Fedora 22+, RHEL 7+).

**Prerequisites:**

Before proceeding, please ensure the following conditions are met:

1.  Linux Environment: You are working on a Linux distribution that uses systemd. You can verify this by running systemctl --version. If it returns a version number, systemd is in use.

2.  Python Project Files: Ensure that your project files are correctly placed on the Linux system.
Recommended Locations: For custom applications, common best practices for installation directories include:
/opt/your_project_name/ – for optional or third-party software not managed by the system package manager.
/usr/local/your_project_name/ – for locally compiled software or machine-specific applications not managed by the system package manager.

Note: This guide uses /path/to/your/project as a placeholder. Be sure to replace this with the actual absolute path to your project directory.

3.  Python 3 Installed: A compatible version of Python 3 must be installed on your system. You can verify this by running which python3 or which python. Common paths include /usr/bin/python3 or /usr/local/bin/python3.

4.  Sudo Privileges: Ensure you have sudo privileges on the Linux machine to perform system-level operations such as creating users, placing service files, and managing services.

5.  Robust Python Script: The Python script (e.g., deploy/tcp_string_server.py) should be designed to run continuously and handle errors gracefully. It should ideally include:
Logging: Output should be directed to log files (using Python’s logging module) or to standard output/error streams, which systemd can capture.
Absolute Paths: All file paths used within the script should be absolute (e.g., /var/log/my_app.log instead of my_app.log).

------------------------------------------------------------------------------------------------------------------------------------------------------
**Steps for Installation:**

Follow these steps carefully to set up your project as a `systemd` service.

Ensure your Python project files are organized and accessible.

1.  **Place Your Project Files:**
    Copy or deploy your entire project (e.g., `deploy/tcp_string_server.py` and any supporting modules, configuration files, etc.) to the project directory on the Linux server.

    * **Example:** As the project is named `Algorithmic_task`, you might place it in `/opt/Algorithmic_task/`.
    * **Verification:** Navigate to the chosen directory and confirm all your project files are present.

    ```bash
    # Example: If your project files are in a local directory, copy them:
    # sudo cp -r /home/youruser/my_local_project_dir /opt/my_awesome_app

    # Verify the contents of the project directory
    ls -l /path/to/your/project

------------------------------------------------------------------------------------------------------------------------------------------------------
### Step 2: Create a Dedicated System User and Group (Highly Recommended)

Running services as the `root` user is a significant security risk. Creating a dedicated, unprivileged system user and group provides isolation and limits potential damage if your service were compromised.

1.  **Create the User and Group:**
    Execute the following command to create a new system user and group for your service. Choose a descriptive name.

    ```bash
    sudo adduser \
        --system \
        --no-create-home \
        --group \
        your_username_for_service
    ```
    * `adduser`: Command to add a user.
    * `--system`: Creates a "system" user. System users typically have no login shell, no home directory, and are intended for running services rather than interactive logins.
    * `--no-create-home`: Prevents the creation of a home directory for this user, as it's not needed for a service user.
    * `--group`: Creates a group with the same name as the user. This simplifies permission management.
    * `your_username_for_service`: **Replace this placeholder** with your desired username (e.g., `myprojectuser`, `awesomeapp`).

    **Example:**
    ```bash
    sudo adduser --system --no-create-home --group myprojectuser
    ```

### Step 3: Set Correct Permissions for Your Project Directory

The service user needs appropriate permissions to read and execute the Python script and any other files the project interacts with (e.g., data files, configuration files).

1.  **Change Ownership:**
    Change the ownership of your entire project directory (and its contents) to the newly created service user and group.

    ```bash
    sudo chown -R your_username_for_service:your_groupname_for_service /path/to/your/project
    ```
    * `-R`: Recursive, applies the ownership change to all files and subdirectories within the specified path.
    * `your_username_for_service:your_groupname_for_service`: **Replace these placeholders** with the user and group you created in Step 2.
    * `/path/to/your/project`: **Replace this placeholder** with the actual absolute path to your project directory.

    **Example:**
    ```bash
    sudo chown -R myprojectuser:myprojectuser /opt/my_awesome_app
    ```
    **Make Python Script Executable:**
    Ensure your main Python script (the one `ExecStart` will call) has execute permissions.

    ```bash
    sudo chmod +x /path/to/your/project/my_service_script.py
    ```
    * `+x`: Adds execute permission for the owner, group, and others.
    * `/path/to/your/project/my_service_script.py`: **Replace this placeholder** with the actual absolute path to your main Python script.

2.  **Make Python Script Executable:**
    Ensure your main Python script (the one `ExecStart` will call) has execute permissions.

    ```bash
    sudo chmod +x /path/to/your/project/my_service_script.py
    ```
    * `+x`: Adds execute permission for the owner, group, and others.
    * `/path/to/your/project/my_service_script.py`: **Replace this placeholder** with the actual absolute path to your main Python script.

  The `systemd` service unit file defines how `systemd` manages your application.

  **Create the Service File:**
    Open a new file for editing in the `/etc/systemd/system/` directory. The filename should be descriptive and end with `.service`.

    ```bash
    sudo nano /etc/systemd/system/your_project_name.service
    ```
    * `your_project_name.service`: **Replace this placeholder** with a unique and descriptive name for your service (e.g., `my_awesome_app.service`). Avoid spaces in the name.
    * `nano`: A simple command-line text editor. You can use `vim` or `gedit` if you prefer.

#### Using systemd  
1. Step 1: Create the systemd Service File
   Open a terminal on your Linux server
   Create and edit the service file with: 

   ```bash  
   sudo nano /etc/systemd/system/tcp_string_server.service 

2. Step 2: Configure the Service
   Copy and paste the following configuration, making sure to:
   Replace /path/to/Algorithmic_task with your actual project directory path
   Verify /usr/bin/python3 is your correct Python 3 path (check with which python3)

   [Unit]  
   Description=TCP String Search Server  
   After=network.target  

   [Service]  
   User=root  
   WorkingDirectory=/path/to/Algorithmic_task  ## path to the project
   ExecStart=/usr/bin/python3 /path/to/Algorithmic_task/server.py  
   Restart=always  
   StandardOutput=syslog  
   StandardError=syslog  

   [Install]  
   WantedBy=multi-user.target  

3. Step 3: Reload systemd to recognize the new service:
   sudo systemctl daemon-reload

4. Step 4: Start the Service
   sudo systemctl start tcp_string_server

5. Enable the service to start on boot:
   sudo systemctl enable tcp_string_server 

6. Step 4: Verify the Service
   Check the service status:
   sudo systemctl status tcp_string_server

7. View live logs:
   sudo journalctl -u tcp_string_server -f



## Method 2: Using Docker (Alternative Containerized Approach)

If you prefer containerization, follow these steps:

1. Build the Docker image:
   docker build -t tcp_string_server .

2. Run the container in detached mode:
   docker run -d --name tcp_server -p 44445:44445 tcp_string_server

3. Verify it's running:
   docker ps 

4. View container logs:
   docker logs tcp_server 


## Method 3: Manual Daemonization (Quick Testing)
For temporary testing without systemd:

1. Navigate to your project directory:
   cd /path/to/Algorithmic_task

2. Run the server in the background:
   nohup python3 server.py > server.log 2>&1 &

3. Verify it's running:
   `ps aux | grep server.py

4. View the output:
   tail -f server.log


## NOTE
For production environments, systemd is strongly recommended for better process management
The Docker method provides isolation and easier deployment
The manual method is suitable only for quick testing as it lacks proper service management


## To stop the service:
systemd: sudo systemctl stop tcp_string_server
Docker: docker stop tcp_server
Manual: pkill -f "python3 server.py"

------------------------------------------------------------------------------------------------------------------------

**Common Service Management Commands:**

Once your service is set up, these commands will help you manage it.

* **Stop the service:**
    ```bash
    sudo systemctl stop your_project_name.service
    ```
    This will immediately stop the running instance of your service.

* **Restart the service:**
    ```bash
    sudo systemctl restart your_project_name.service
    ```
    This stops and then starts the service. Useful after making changes to your Python code.

* **Disable the service (prevent it from starting on boot):**
    ```bash
    sudo systemctl disable your_project_name.service
    ```
    This removes the symbolic link that enables auto-start. The service will no longer start at boot, but you can still start it manually.

* **Remove the service (if you no longer need it):**
    1.  Stop the service:
        ```bash
        sudo systemctl stop your_project_name.service
        ```
    2.  Disable the service:
        ```bash
        sudo systemctl disable your_project_name.service
        ```
    3.  Delete the service unit file:
        ```bash
        sudo rm /etc/systemd/system/your_project_name.service
        ```
    4.  Reload systemd:
        ```bash
        sudo systemctl daemon-reload
        ```
    5.  (Optional) Remove the dedicated user and group if no other services use them:
        ```bash
        sudo deluser your_username_for_service
        sudo delgroup your_groupname_for_service
        ```
    6.  (Optional) Remove your project files.

* **Check if the service is enabled (will start on boot):**
    ```bash
    sudo systemctl is-enabled your_project_name.service
    ```
    Returns `enabled` or `disabled`.

------------------------------------------------------------------------------------------------------------------------

**Troubleshooting Tips:**

* **"Failed to start" or "Active: inactive (dead)" Status:**
    * Check `sudo journalctl -u your_project_name.service -f` immediately after attempting to start the service. Look for error messages (e.g., Python tracebacks, permission denied).
    * Verify all paths in your `.service` file are absolute and correct (e.g., `ExecStart`, `WorkingDirectory`).
    * Ensure the `User` and `Group` specified in the service file exist and have correct permissions on the `WorkingDirectory` and any files your script accesses (logs, data, config).
    * Check the syntax of your `.service` file carefully for typos.

* **"Permission Denied" Errors:**
    * Double-check ownership and permissions of your project directory (`chown -R`, `chmod +x`).
    * Ensure your service user has write access to any log files or data directories your script tries to create or modify.

* **Service Starts but Does Nothing / No Logs:**
    * Verify your Python script is actually performing the expected actions and has proper logging configured.
    * If using `print()` statements for debugging, ensure `StandardOutput=syslog` (or a direct log file) is correctly set in your service file.
    * Check `WorkingDirectory` in the service file. If your script uses relative paths, this needs to be correct.

* **Python Interpreter Path:**
    * Sometimes Python is installed in a non-standard location. Use `which python3` to find the correct absolute path (e.g., `/usr/bin/python3`, `/usr/local/bin/python3`, or even within a virtual environment, though running virtual environments directly as systemd services has extra considerations).






