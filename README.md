# StockTracker

StockTracker is a lightweight, self-hosted web application for tracking your stock portfolio performance. Built with Python and Flask, it provides real-time insights into your holdings, transaction history, and overall wealth growth, along with push notifications for market updates.

## Features

*   **Portfolio Dashboard:** View total portfolio value, unrealized P/L, daily changes, and lifetime growth.
*   **Asset Allocation:** Visual breakdown of your portfolio using interactive charts.
*   **Transaction Management:** Buy and sell stocks to track your history and realized gains.
*   **Real-time Data:** Fetches stock prices and news using Yahoo Finance data.
*   **User System:** Secure registration and login with password hashing.
*   **Notifications:** Integration with [Pushover](https://pushover.net/) for market alerts (Open, Close, Hourly, etc.).
*   **Data Export:** Export your holdings and transaction history to CSV.
*   **Privacy Focused:** All data is stored locally in JSON files; no external database required.

## Prerequisites

*   Python 3.8 or higher
*   pip (Python package manager)
*   OpenSSL (for generating a self-signed certificate for HTTPS)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd StockTracker
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Environment Variables:**
    Create a `.env` file in the root directory of the project. You can copy the structure below:

    ```ini
    # .env
    SECRET_KEY=your_secure_random_string_here
    CRON_SECRET=your_custom_cron_secret_string
    PUSHOVER_APP_TOKEN=your_pushover_app_token_here
    ```

    *   `SECRET_KEY`: Used by Flask to sign session cookies. Make this long and random.
    *   `CRON_SECRET`: A password you define to protect the automated notification endpoint.
    *   `PUSHOVER_APP_TOKEN`: (Optional) Your application token from Pushover if you want notifications.

2.  **Data Directory:**
    The application will automatically create a `data/` folder to store user and portfolio data in JSON format.

## Running the Application

### Development (HTTP)
To run the server locally for testing over HTTP:

```bash
python app.py
```
The app will be accessible at `http://localhost:5000`.

### Production (HTTPS)
For a production environment, it is highly recommended to use HTTPS. You can use **Hypercorn** to serve the application over HTTPS.

1.  **Generate a Self-Signed Certificate:**
    First, create a self-signed SSL certificate using OpenSSL. This will create `cert.pem` and `key.pem` files.
    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    ```
    *(Note: Your browser will warn you that this certificate is not trusted. This is expected for a self-signed certificate.)*

2.  **Run the Hypercorn Server:**
    Use the following command to start the server with your new certificate.
    ```bash
    hypercorn --certfile cert.pem --keyfile key.pem --bind "0.0.0.0:8000" wsgi:app
    ```
    And if you havented added Hypercorn to path do the command below
    ```bash
    python -m hypercorn --cert-file cert.pem --keyfile key.pem --bind "0.0.0.0:8000" wsgi:app
    ```
    The application will be available at `https://localhost:8000`.

### Production (HTTPS) with Certbot
Use this if you own a domain name (e.g., `example.com`) and want a trusted certificate.

1.  **Port Forwarding:** Ensure **Port 80** is forwarded on your router to this machine. Certbot needs Port 80 to verify you own the domain.
2.  **Install Certbot:** Download and install Certbot for Windows from [certbot.eff.org](https://certbot.eff.org/instructions?ws=other&os=windows).
3.  **Generate Certificate:** Open PowerShell as Administrator and run:
    ```bash
    certbot certonly --standalone
    ```
    Follow the prompts. Certbot will temporarily spin up a server on Port 80 to verify your domain.
4.  **Run Hypercorn:** Once successful, point Hypercorn to the generated files (usually in `C:\Certbot\live\yourdomain.com\`):
    ```bash
    hypercorn --cert-file "C:\Certbot\live\yourdomain.com\fullchain.pem" --key-file "C:\Certbot\live\yourdomain.com\privkey.pem" --bind "0.0.0.0:8000" wsgi:app
    ```
    *Note: You must keep Port 80 open/forwarded so Certbot can automatically renew the certificate every 60 days.*

### Alternative Production Servers (HTTP)
If you are running behind a reverse proxy that handles HTTPS for you, you can use Waitress or Gunicorn.

**Windows (Waitress):**
```bash
waitress-serve --host 0.0.0.0 --port 8000 wsgi:app
```
And if you havented added Waitress to path do the command below
```bash
python -m waitress-serve --host 0.0.0.0 --port 8000 wsgi:app
```

**Linux/macOS (Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## Setting up Notifications (Cron Job)

To receive periodic portfolio updates via Pushover, you need to trigger the `/cron/trigger` endpoint.

**Endpoint:** `GET /cron/trigger?secret=<YOUR_CRON_SECRET>`

### Linux/Mac (Crontab)
To trigger the job every 30 minutes:

1.  Open your crontab:
    ```bash
    crontab -e
    ```

2.  Add the following line (replace with your actual domain and secret):
    ```cron
    */30 * * * * curl "https://your-domain.com/cron/trigger?secret=your_custom_cron_secret_string"
    ```
##CronJobs.org
You can use cronjobs.org for free to set up a cronjob

1. Sign up
2. Add a cronjob
3. set duration to every 30 minutes
4. set url to "https://your-domain.com/cron/trigger?secret=your_custom_cron_secret_string"
    
### Windows (Task Scheduler)
You can use Windows Task Scheduler to make a periodic web request. A simple way is to use PowerShell.

1.  Open Task Scheduler.
2.  Create a new Basic Task.
3.  Set the trigger to run every 30 minutes.
4.  For the action, choose "Start a program" and enter `powershell`.
5.  In "Add arguments", paste the following (replace with your URL and secret):
    ```powershell
    -Command "Invoke-WebRequest -Uri https://localhost:8000/cron/trigger?secret=your_custom_cron_secret_string"
    ```

## Security Notes

*   **Secrets:** Never commit your `.env` or `*.pem` files to version control. They are already added to `.gitignore`.
*   **Port Forwarding:** If you are exposing this to the internet via port forwarding, ensure you have set strong values for `SECRET_KEY` and `CRON_SECRET`.
*   **HTTPS:** For a real production deployment, consider using a certificate from a trusted authority like [Let's Encrypt](https://letsencrypt.org/) instead of a self-signed one.

## Project Structure

*   `app.py`: Main application entry point.
*   `wsgi.py`: WSGI entry point for Gunicorn.
*   `routes.py`: URL route definitions and logic.
*   `models.py`: Data handling (JSON read/write).
*   `utils.py`: Helper functions for stock data fetching and notifications.
*   `config.py`: Configuration loading.
*   `templates_html.py`: HTML templates stored as Python strings.
