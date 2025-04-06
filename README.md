# GrabOrgan

**GrabOrgan** is a microservice architecture developed by SMU ESD for organ matching and delivery. This project leverages Cloud Firestore, RabbitMQ, Kong (with decK), and a Node-based frontend.

---

## Setting up Your Environment

### 1. Set Up Cloud Firestore on Firebase

1. **Enable Firestore API** on your Google Cloud project.
2. Generate a **private key JSON file** and rename it to `*_Key.json`.
3. Place the `*_Key.json` file into a `secrets` directory within the respective atomic service directory.
4. When running locally, set the environment variable:
   - **Windows:**  
     `set <SERVICE>_DB_KEY=secrets/<filename>.json`
   - **Mac/Linux:**  
     `export <SERVICE>_DB_KEY=secrets/<filename>.json`

---

### 2. Unzip `secrets.zip` or build your own Firestore for each service

1. Place the unzipped `secrets` directory in the root (e.g. `GrabOrgan/secrets`).
2. Verify the folder structure. A common unzip bug may create a duplicate folder (e.g. `secrets/recipient/recipient.json/recipient.json`).  
   - If found, remove the duplicate so that each key is located at, for example, `secrets/recipient/recipient_Key.json`.

---

### 3. Set Up the `.env` File

Create a `.env` file in the root directory with your Azure connection string:

```env
AZURE_CONNECTION_STRING=<YOUR-CONNECTION-STRING-FROM-AZURE>
```

### 4. Build Docker Containers

From the root directory (GrabOrgan), run:
```bash
docker compose up -d --build
```

### 5. Set Up RabbitMQ Configuration

Once the RabbitMQ container is running, perform the following steps:
1.	Change directory to the RabbitMQ setup folder:
```bash
cd common/rabbitmq
```
2.	Create a virtual environment:
```bash
python3 -m venv venv
```
3.	Activate the virtual environment:
```bash
source venv/bin/activate
```
4.	Install dependencies:
```bash
python -m pip install --no-cache-dir -r requirements.txt
```
5.	Run the AMQP setup script:
```bash
python amqp_setup.py
```
### If successful, you should see output similar to:

    Setting up AMQP...
    Connecting to AMQP broker at localhost:5672...
    Connected
    Open channel
    Declaring exchange: request_organ_exchange (direct)
    Declaring exchange: test_compatibility_exchange (direct)
    Declaring exchange: test_result_exchange (direct)
    Declaring exchange: activity_log_exchange (topic)
    Declaring exchange: error_handling_exchange (topic)
    Declaring exchange: order_exchange (direct)
    Declaring exchange: notification_status_exchange (topic)
    Declaring exchange: notification_acknowledge_exchange (topic)
    Declaring exchange: driver_match_exchange (direct)
    Creating queue: match_request_queue
    Binding queue: match_request_queue to exchange: request_organ_exchange with routing key: match.request
    Creating queue: test_compatibility_queue
    Binding queue: test_compatibility_queue to exchange: test_compatibility_exchange with routing key: test.compatibility
    Creating queue: match_test_result_queue
    Binding queue: match_test_result_queue to exchange: test_result_exchange with routing key: test.result
    Creating queue: order_queue
    Binding queue: order_queue to exchange: order_exchange with routing key: order.organ
    Creating queue: activity_log_queue
    Binding queue: activity_log_queue to exchange: activity_log_exchange with routing key: *.info
    Creating queue: error_queue
    Binding queue: error_queue to exchange: error_handling_exchange with routing key: *.error
    Creating queue: noti_delivery_status_queue
    Binding queue: noti_delivery_status_queue to exchange: notification_status_exchange with routing key: *.status
    Creating queue: noti_acknowledgement_queue
    Binding queue: noti_acknowledgement_queue to exchange: notification_acknowledge_exchange with routing key: *.acknowledge
    Creating queue: driver_match_request_queue
    Binding queue: driver_match_request_queue to exchange: driver_match_exchange with routing key: driver.request
    ✅ AMQP Setup Complete!

### 6. Load Kong Configuration
The compose.yaml includes a deck-sync service that automatically loads the kong-data/kong.yaml file into Kong. To manually sync the configuration, run:
```
docker run --rm \
    -v "$(pwd)/kong-data:/deck" \
    kong/deck:latest \
    sync --state /deck/kong.yaml --kong-addr http://localhost:8001
```
    To dump your current Kong configuration into kong.yaml:
```
deck dump --output-file kong.yaml --kong-addr http://localhost:8001
```

| Note: Even with a global CORS plugin configuration in Kong, if your routes define a methods list, ensure OPTIONS is included (or remove the methods field to allow all methods).

### 7. Install Frontend Dependencies
From the root directory (GrabOrgan), navigate to the frontend folder and install dependencies:
```
cd fe
npm install
```
### 8. Start the Frontend Server
Start your frontend development server:
```
npm run dev
```