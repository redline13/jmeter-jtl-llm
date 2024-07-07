# JMeter JTL LLM Analyzer

A powerful tool for analyzing JMeter JTL files with the help of Language Model (LLM) technology. Upload your JTL files, ask insightful questions, and generate informative graphs effortlessly.

## Setup

1. **Install Python:**
   - Ensure you have Python 3.10 or 3.11 installed on your system.

2. **Clone the Repository:**
   ```sh
   git clone https://github.com/your-username/jmeter-jtl-llm.git
   cd jmeter-jtl-llm

3. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt

4. **Set Up Environment Variables:**

   - Create a `.env` file in the `/WebClient` directory of the project.
   - Add the necessary environment variables to the `.env` file. For example:

    ```env
    openAI_apikey_redline=https://platform.openai.com/api-keys <--- WebServer implementation only requires this
    redline_apikey=https://www.redline13.com/Account/apikey
    google_apikey=https://aistudio.google.com/app/apikey
    ```


## Usage

5. **Startup:**
   - To start the application, Run:
    
    ```sh
    python Webclient/app.py
