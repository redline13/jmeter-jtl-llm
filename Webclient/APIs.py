import os
import requests
from dotenv import load_dotenv
load_dotenv()
import json

from enum import Enum

class LLM(Enum):
    GPT = 1
    Gemini = 2


class Redline_API(object):
    def __init__(self):
        self.redlineAPIKEY = os.getenv('redline_apikey')
        self.statsDownloadURL = "https://www.redline13.com/Api/StatsDownloadUrls?loadTestId="
        self.metricsDownloadURL = "https://www.redline13.com/Api/Metrics?filter=.&loadTestId="

    def httpRequest(self, id):
        client = requests.Session()

        url = f"{self.metricsDownloadURL}{id}"

        headers = {
            "X-Redline-Auth": self.redlineAPIKEY
        }

        try:
            response = client.get(url, headers=headers)
            response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.exceptions.RequestException as err:
            print(f"Error sending GET request: {err}")
            return None

        try:
            body = response.content
        except Exception as err:
            print(f"Error reading response body: {err}")
            return None

        if response.status_code != 200:
            print("Response status:", response.status_code)
            print(body.decode('utf-8'))

        return body.decode('utf-8')


class LLMBase(object):
    """
    A base class to provide standard operations for LLM APIs. Methods and
    members shared between LLM platforms will be listed here
    
    Methods:
    generateReport(self, content) -> string
        Generate a word report in html from selected LLM.
    
    generateGraphConfigs(self, csvFile) -> string (array of dictionaries)
        Generate a graph coniguration for GraphService
    """
    def __init__(self, app):
        self.app = app

        filePath = self.app.config['UPLOAD_FOLDER']

        self.prompts = {
            "graphReport" :     f"""
                                    # Context:
                                    # You are a Data Analyst and Performance Engineer. Your primary task is to create written reports. You will never write any text that is not a written report. Follow these steps for every request:
                                    Determine the type of report the user needs to best display the information requested. Load and analyze the data from the provided files.
                                    
                                    Tasks:
                                    1. **Load Data** load the data from the provided files, the files will be given in the provided formats.
                                    2. **Report creation**: Act like a performance engineer and write a detailed summary from the given raw performance results
                                    You need to identify the anomalies, standard deviations number of errors, and number of transactions. Help me identifying potential bottlenecks as well.
                                    2. **No Graphs**: The user will often ask to create graphs or change existing graphs. Never mention or create graphs at any time, only give data in a written report format.
                                    
                                    # Files:
                                        # You will be given files in this format as a user message:
                                        # "{{fileName.extension}}: {{rawFileContents}}"
                                        # Any number of data files provided will be located at the following directories
                                        # {{fileName}}_path = "{os.path.abspath(self.app.config['UPLOAD_FOLDER'])}/{{fileName}}.extension"
                                        # {{fileName1}}_path = "{os.path.abspath(self.app.config['UPLOAD_FOLDER'])}/{{fileName1}}.extension"
                                        # {{fileName2}}_path = "{os.path.abspath(self.app.config['UPLOAD_FOLDER'])}/{{fileName2}}.extension"
                                        # All extensions will be spreadsheet files such as csv, jtl, or others
                                        # Only load files requested by the user.
                                    
                                    Example:
                                    # ### Summary Report
                                    # data to provide the user.
                                    # Keep it to roughly 500-1000 characters
                                """,
            "generateGraphInteractive" :    """
                                                # Context:
                                                # You are a Data Analysis and Visualization Assistant. Your primary task is to help users create charts and diagrams from their data using Python. Follow these steps for every request:

                                                # Task:
                                                1. **Understand the Request**: Determine the type of graph or diagram the user needs to best display the information requested.
                                                2. **Data Preparation**: Load the data from the provided files. files will be given as previous chat messages starting with the file identifier example: (file1: {fileData})
                                                3. **Graph Creation**: Generate the requested graph using Python libraries such as plotly, pandas and more.
                                                4. **Graphing Code Generation**: Save the generated graph an interactable html graph such as plot_html = fig.to_html(full_html=False). Then you must print(plot_html)
                                                5. **Message Formatting**: Never write plt.show() as this will cause errors for my program, only print the results to fig.to_html().
                                                6. **User Interaction**: You are to simply be an assistant that provides graphs. Never tell the user the process for which you make these graphs.
                                                The python code block should be the ONLY text provided.

                                                # Constraints:
                                                # - Use Python standard libraries only, this includes plotly, seaborn, and pandas and others as needed.
                                                # - Ensure the functions are robust and handle edge cases gracefully.
                                                # = Make sure to print your html results
                                                # - You may use any form of graph besides a boxplot. Boxplots cause errors and are bad for visualization

                                                # Files:
                                                # Any data files provided should be located at the following directories
                                                # file{#}_path = "Users/mikebugden/Desktop/FordAPITest/results{#}.csv"
                                                # file1_path = "/Users/mikebugden/Desktop/FordAPITest/results1.csv"
                                                # file2_path = "/Users/mikebugden/Desktop/FordAPITest/results2.csv"
                                                
                                                # Example Input and Output:
                                                # - Input: "can you create me a graph that compares latency times for file1"
                                                # - Output: " ```python {some python code that creates an interactable html graph} ``` 
                                            """,

            "generatedGraphInteractiveDynamicFiles":    f"""
                                                # Context:
                                                # You are a Data Analysis and Visualization Assistant. Your primary task is to help users create charts and diagrams from their data using Python. Follow these steps for every request:

                                                # Task:
                                                1. **Understand the Request**: Determine the type of graph or diagram the user needs to best display the information requested.
                                                2. **Data Preparation**: Load the data from the provided files. files will be given as previous chat messages starting with the file identifier example: (file1: {{fileData}})
                                                3. **Graph Creation**: Generate the requested graph using Python libraries such as plotly, pandas and more.
                                                4. **Graphing Code Generation**: Save the generated graph an interactable html graph such as plot_html = fig.to_html(full_html=False). Then you must print(plot_html)
                                                5. **Message Formatting**: Never write plt.show() as this will cause errors for my program, only print the results to fig.to_html().
                                                6. **User Interaction**: You are to simply be an assistant that provides graphs. Never tell the user the process for which you make these graphs.
                                                The python code block should be the ONLY text provided.

                                                # Constraints:
                                                # - Use Python standard libraries only, this includes plotly, seaborn, and pandas and others as needed.
                                                # - Ensure the functions are robust and handle edge cases gracefully.
                                                # = Make sure to print your html results

                                                # Files:
                                                # You will be given files in this format as a user message:
                                                # "{{fileName.extension}}: {{rawFileContents}}"
                                                # Any number of data files provided will be located at the following directories
                                                # {{fileName}}_path = "{os.path.abspath(self.app.config['UPLOAD_FOLDER'])}/{{fileName}}.extension"
                                                # {{fileName1}}_path = "{os.path.abspath(self.app.config['UPLOAD_FOLDER'])}/{{fileName1}}.extension"
                                                # {{fileName2}}_path = "{os.path.abspath(self.app.config['UPLOAD_FOLDER'])}/{{fileName2}}.extension"
                                                # All extensions will be spreadsheet files such as csv, jtl, or others
                                                
                                                # Example Input and Output:
                                                # - Input: "can you create me a graph that compares latency times for testFile1.csv"
                                                # - Output: " ```python {{some python code that creates an interactable html graph}} ``` 
                                            """,

            "promptSuggestion" : """
                                Generate a random example prompt for an AI graphing system that demonstrates its capabilities. 
                                Include details such as the type of data, the graph type, and any specific features or instructions for generating a useful graph.

                                
                                # Examples:
                                # Show me a graph that compares latency times for {insertFileName}
                                # Show me a graph of jmeter threads per second for {insertFileName}
                                # Create a pie chart of Response Codes for {insertFileNames}
                                # Show me a Bar Graph of Response Codes for {insertFileNames}
                                # Show me a Scatter Plot of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                # Show me a Line Graph of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                # Show me a Histogram of {Insert relavent Column names and axis configuration} for {insertFileNames
                                # Show me a Bubble Chart of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                # Show me a Heat Map of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                # Show me a Discrete Bar Chart of {Insert relavent Column names and axis configuration} for {insertFileNames
                                # Show me {Insert Any graph type supported by plotly} of {Insert relavent Column names and axis configuration} for {insertFileNames}


                                # You will be given a list of file names and columns in the file as a user message: "fileData: [{"filename": [{list of columns in file}]}, {"filename2": [{list of columns in file}]} ]"
                                # Feel free to plot multiple files on the same graph. Make sure all files are plotted together.
                                # Note If you have time on an axis with multiple files, you should specify the graphs should utilize a normalized time format. And that all of the graphs should start at the same time when appropriate.
                                This will ensure that graphs with results taken multiple days or even weeks at a time, will be compared against eachother on timing related graphs.
                                **Keep it below 300 characters**
                                **Never repeat prompts, always generate unique prompts**
                                # already provided and non-unique prompts will be provided to by the user message "Provided Prompts: [{array of provided prompts}]"
                                """


        }


    """
    Generate a word report in html from selected LLM.

    Parameters:
    content - Raw data (as string) to send to LLM for analysis

    Returns:
    string: Response from LLM.
    """
    def generateReport(self, content):
        pass


    """
    Generates a graphConfig array from dataframe and selected LLM.

    Parameters:
    csvFile - DataFrame: converts to string when send to LLM

    Returns:
    string: Response from LLM.
    """
    def generateGraphConfigs(self, csvFile):
        """
        Generate a graph configuration from given csvFile and given LLM platform
        """
        pass


    """
    Generates a graphConfig array from dataframe and selected LLM.

    Parameters:
    csvFile - DataFrame: converts to string when send to LLM

    Returns:
    string: Response from LLM.
    """
    def basicRequest(self, msgs):
        """
        Generate a response from a prewritten set of messages
        """
        pass


from openai import OpenAI

class OpenAI_API(LLMBase):
    def __init__(self, app):
        
        super().__init__(app)
        
        self.client = OpenAI(
            api_key=os.getenv('openAI_apikey_redline'),
        )
        self.genConfig = {
            "model": "gpt-4o",
            "max_tokens" : 4000,
            "n" : 1,
            "stop" : None,
            "temperature" : 0.2,
            "top_p" : 1.0,
            "presence_penalty" : 0.0,
            "frequency_penalty" : 0.0
        }
    
    def basicRequest(self, chatHistory, genConfig=None):
        if genConfig == None:
            genConfig = self.genConfig

        completion = self.client.chat.completions.create(
            messages=chatHistory,
            model=genConfig["model"],
            max_tokens=genConfig["max_tokens"],
            n=genConfig["n"],
            stop=genConfig["stop"],
            temperature=genConfig["temperature"],
            top_p=genConfig["top_p"],
            presence_penalty=genConfig["presence_penalty"],
            frequency_penalty=genConfig["frequency_penalty"]
        )

        return completion.choices[0].message.content


import google.generativeai as genai
class Gemini_API(LLMBase):
    def __init__(self, app):

        super().__init__(app)

        genai.configure(api_key=os.getenv('google_apikey'))

        self.model = genai.GenerativeModel('gemini-pro')
        
        self.prompt = "Act like a performance engineer and write a detailed summary from the given raw performance " \
                            "results without a title. You need to identify the anomalies, standard deviations, " \
                            "minimum and maximum response time, " \
                            "number of errors, and number of transactions. " \
                            "Help me identifying potential bottlenecks as well." \
                            "Only generate answers from data provided" \
                            "Build a report from the data formatted in html"  
        
        self.genConfig = genai.types.GenerationConfig(
            # Only one candidate for now.
            candidate_count=1,
            temperature=0.0,
            max_output_tokens=4000)

    """
    Get a list of all models.

    Parameters: #
    Returns:
    string: A list of all avalible models.
    """
    def getModels(self):
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)

    def generateReport(self, content):
        fullPrompt = self.prompts["report"] + content

        generation_config = self.genConfig

        response = self.model.generate_content(fullPrompt,
            generation_config=generation_config)
            #stop_sequences=['x'],
        response.candidates

        if response.candidates[0].finish_reason.name != "STOP":
            return response.candidates
        return response.candidates[0].content.parts[0].text

    def generateGraphConfigs(self, csvFile):
        fullPrompt = self.prompts["graph"] + str(csvFile)

        generation_config = self.genConfig

        response = self.model.generate_content(fullPrompt,
            generation_config=generation_config)
            #stop_sequences=['x'],
        response.candidates

        if response.candidates[0].finish_reason.name != "STOP":
            return response.candidates
        return response.candidates[0].content.parts[0].text
    
    def basicRequest(self, msgs):
        print("You are calling a function that is not setup!")
        pass