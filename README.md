# Sales_Agent

## Project Setup Instructions for Sales_Agent

This README provides a step-by-step guide to set up the project in the `Sales_Agent` directory. Follow the instructions carefully to create a virtual environment, install dependencies, and configure necessary API keys.

### Prerequisites

- Ensure that **Python** is installed on your system. You can check this by running:
  ```bash
  python --version
  ```

- Install **pip** if it's not already installed:
  ```bash
  python -m ensurepip --upgrade
  ```

### Step 1: Create a Virtual Environment

1. **Navigate to the Sales_Agent directory**:
   ```bash
   cd path/to/Sales_Agent
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```
   This command creates a new directory named `venv` within the `Sales_Agent` folder, containing a self-contained Python environment.

3. **Activate the virtual environment**:
   - On **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - On **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

### Step 2: Install Dependencies

Once the virtual environment is activated, install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```

### Step 3: Create and Configure the `.env` File

1. **Create a `.env` file** in the `Sales_Agent` directory:
   ```bash
   touch .env
   ```

2. **Open the `.env` file**  and add the following lines, replacing placeholders with your actual API keys and Gmail app password:
   ```plaintext
   GROQ_API_KEY=your_groq_api_key_here
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   password="your_gmail_app_password_here"
   ```

### Step 4: Obtain Gmail App Password

To create an app password for your Gmail account:

1. Go to your Google Account settings.
2. Navigate to **Security**.
3. Under "Signing in to Google," select **App passwords**.
4. Follow the prompts to generate an app password.
5. Copy this password and paste it into your `.env` file under `password`.

### Step 5: Enable Google Sheets API and Obtain Credentials

1. **Enable Google Sheets API**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Navigate to **APIs & Services > Library**.
   - In the search bar, type "Google Sheets API" and select it from the results.
   - Click on **Enable** to enable the Google Sheets API for your project [1][2].

2. **Create OAuth Credentials**:
   - Still in the Google Cloud Console, go to **APIs & Services > Credentials**.
   - Click on **Create Credentials**, then select **OAuth client ID**.
   - Configure the consent screen if prompted, providing necessary details like Application Name (e.g., `SpreadsheetConnector`).
   - Choose application type as **Desktop app**, then click **Create**.
   - Download the credentials JSON file and rename it to `credentials.json`.

3. Place `credentials.json` in the `Sales_Agent` directory.

### Step 6: Update Sender Email in `app.py`

1. Open `app.py` .
2. Locate the `sender_details` dictionary (on line 122).
3. Change the `sender_email` value to your own Gmail address.

### Step 7: Run the Application

With everything set up, you can now run your application:

```bash
streamlit run app.py
```

The app will launch on your localhost.

### Additional Notes

- If you choose to switch to another LLM, ensure you provide the corresponding API key in the `.env` file.

By following these steps, you should have a fully functional setup for your Sales_Agent project!

