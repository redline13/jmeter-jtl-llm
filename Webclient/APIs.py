import os
import requests
import random
from openai import OpenAI
from enum import Enum
from dotenv import load_dotenv
load_dotenv()
import json
import datetime


defaultConfig = {
            "model": "gpt-4o",
            "max_tokens" : 4000,
            "n" : 1,
            "stop" : None,
            "temperature" : 0.2,
            "top_p" : 1.0,
            "presence_penalty" : 0.0,
            "frequency_penalty" : 0.0
}

def getPrompts(filepath):
    prompts = {
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
                                            # {{fileName}}_path = "{os.path.abspath(filepath)}/{{fileName}}.extension"
                                            # {{fileName1}}_path = "{os.path.abspath(filepath)}/{{fileName1}}.extension"
                                            # {{fileName2}}_path = "{os.path.abspath(filepath)}/{{fileName2}}.extension"
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
                                                    # file{#}_path = "Users/mikebugden/Desktop/FordAPITest/results{#}.jtl"
                                                    # file1_path = "/Users/mikebugden/Desktop/FordAPITest/results1.jtl"
                                                    # file2_path = "/Users/mikebugden/Desktop/FordAPITest/results2.jtl"
                                                    
                                                    # Example Input and Output:
                                                    # - Input: "can you create me a graph that compares latency times for file1"
                                                    # - Output: " ```python {some python code that creates an interactable html graph} ``` 
                                                """,
                "generateGraphInteractiveMain" :    """
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
                                                    # {{fileName}}_path = "{os.path.abspath(filepath)}/{{fileName}}.extension"
                                                    # {{fileName1}}_path = "{os.path.abspath(filepath)}/{{fileName1}}.extension"
                                                    # {{fileName2}}_path = "{os.path.abspath(filepath)}/{{fileName2}}.extension"
                                                    # All extensions will be spreadsheet files such as csv, jtl, or others
                                                    # When comparing multiple files with time stamps, make sure you normalize the timeStamps, and start all graphs at the same time or point, usually x=0.
                                                    
                                                    # Example Input and Output:
                                                    # - Input: "can you create me a graph that compares latency times for testFile1.csv"
                                                    # - Output: " ```python {{some python code that creates an interactable html graph}} ``` 
                                                """,
                "AssistantInstructions":    f"""
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
                                                    # You will be given files as file IDs for the assistant:
                                                    # "{{fileName.extension}}: {{rawFileContents}}"
                                                    # Any number of data files provided will be located at the following directories
                                                    # {{fileName}}_path = "{os.path.abspath(filepath)}/{{fileName}}.extension"
                                                    # {{fileName1}}_path = "{os.path.abspath(filepath)}/{{fileName1}}.extension"
                                                    # {{fileName2}}_path = "{os.path.abspath(filepath)}/{{fileName2}}.extension"
                                                    # When comparing multiple files with time stamps, make sure you normalize the timeStamps, and start all graphs at the same time or point, usually at time x=0.
                                                    # This means that when files have a time axis, they must all start at x=0
                                                    
                                                    # Example Input and Output:
                                                    # - Input: "can you create me a graph that compares latency times for testFile1.csv"
                                                    # - Output: "```python {{some python code that creates an interactable html graph}} ```
                                                    # - **Fully completed example output**: 
                                                    
                                                    
                                                    # Please make sure that I get a text response as an output and not anything else. The output should be exclusively text in the format as I have described.
                                                    # Do not generate anything but output text and never execute any code yourself, only ensure the code provided works without errors.
                                                """,

                "promptSuggestion" : """
                                    Generate a random example prompt for an AI graphing system that demonstrates its capabilities. 
                                    Include details such as the type of data, the graph type, and any specific features or instructions for generating a useful graph.

                                    
                                    # Examples:
                                    # Show me a graph that compares latency times for {insertFileName}
                                    # Show me a graph of jmeter threads per second for {insertFileName}
                                    # Create a pie chart of Response Codes for {insertFileName(s)}
                                    # Show me a Bar Graph of Response Codes for {insertFileName(s)}
                                    # Show me a Scatter Plot of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                    # Show me a Line Graph of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                    # Show me a Histogram of {Insert relavent Column names and axis configuration} for {insertFileNames
                                    # Show me a Bubble Chart of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                    # Show me a Heat Map of {Insert relavent Column names and axis configuration} for {insertFileNames}
                                    # Show me a Discrete Bar Chart of {Insert relavent Column names and axis configuration} for {insertFileNames
                                    # Show me {Insert Any graph type supported by plotly} of {Insert relavent Column names and axis configuration} for {insertFileNames}


                                    # You will be given a list of file names and columns in the file as a user message: "fileData: [{"filename": [{list of columns in file}]}, {"filename2": [{list of columns in file}]} ]"
                                    # Feel free to plot multiple files on the same graph.
                                    # Note If you have time on an axis with multiple files, you should specify the graphs should utilize a normalized time format. And that all of the graphs should start at the same time when appropriate.
                                    This will ensure that graphs with results taken multiple days or even weeks at a time, will be compared against eachother on timing related graphs.
                                    **Keep it below 300 characters**
                                    **Never repeat prompts, always generate unique prompts**
                                    # already provided and non-unique prompts will be provided to by the user message "Provided Prompts: [{array of provided prompts}]"
                                    """


    }

    return prompts

#projectDir = os.getcwd()
#print(projectDir)

uploadFilePath = os.getcwd() + "/uploads/"
def getFileListString():
    fileString = f"""
    # Files:
    # The data files provided are located at the following directories"

    """

    for file in getFiles():
        filePath = os.path.join(uploadFilePath, file)
        fileTempString = f"# {file} = \"{filePath}\"\n"
        fileString += fileTempString


    return fileString

def getFiles(fullPath=False):
        if fullPath:
            return [os.path.join(uploadFilePath, file) for file in os.listdir(uploadFilePath)]
        return os.listdir(uploadFilePath)



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



class ChatThreads(object):
    def __init__(self, app, client, thread_id=None):
        
        self.app = app
        self.client = client

        if thread_id is None: 
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
        else:
            self.thread_id = thread_id

        name = str(random.randint(0, 999999))
        self.assistant = self.client.beta.assistants.create(
            name=name,
            instructions=getPrompts(self.app.config['UPLOAD_FOLDER'])["AssistantInstructions"],
            model="gpt-4o",
            temperature=defaultConfig["temperature"],
            top_p=defaultConfig["top_p"],
        )

        self.updateFileMessages()
 

    def getLatestResposne(self, run_id):
        # Get latest message from chat thread
        thread_messages = self.client.beta.threads.messages.list(self.thread_id, run_id=run_id)
        print(thread_messages)
        response = thread_messages.data[0].content[0].text.value

        return response

    def updateFileMessages(self):
        
        file_paths = self.getFiles(fullPath=True)
        if not (len(file_paths) > 0):
            print("No files found in the specified directory.")
            return

        fileIds = []
        files = self.client.files.list()

        for path in file_paths:
            foundFile = False

            filename = os.path.basename(path)
            for uploadedFile in files.data:
                if uploadedFile.filename == filename:
                    fileIds.append(uploadedFile.id)
                    foundFile = True

            if not foundFile:
                file = self.client.files.create(
                    file=open(path, "rb"),
                    purpose='assistants'
                )
                fileIds.append(file.id)
        
        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        

        self.assistant = self.client.beta.assistants.update(
            assistant_id=self.assistant.id,
            tool_resources={
                "code_interpreter": {"file_ids": fileIds}
            }
        )
        
        print("Files updated successfully")

    def addUserMessage(self, role, content):
        thread_message = self.client.beta.threads.messages.create(
            self.thread_id,
            role=role,
            content=content,
        )
        print("message added successfully")
        return thread_message


    def changeThread(self, thread_id):
        self.thread_id = thread_id

    def deleteThread(self):
        response = self.client.beta.threads.delete(self.thread_id)
        self.changeThread("")
        return response.deleted
    
    def runThread(self):
        print("begining run process")
        startTime = datetime.datetime.now()
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread_id,
            assistant_id=self.assistant.id,
        )
        endTime = datetime.datetime.now()
        elapsed_time = endTime - startTime
        elapsed_seconds = elapsed_time.total_seconds()

        # Print the elapsed time to the first decimal place
        print(f"Elapsed run time: {elapsed_seconds} seconds")

        if run.status == 'completed': 
            print("Thread ran successfully")
            return run
        else:
            return False
        
    
    def getFiles(self, fullPath=False):
        if fullPath:
            return [os.path.join(self.app.config['UPLOAD_FOLDER'], file) for file in os.listdir(self.app.config['UPLOAD_FOLDER'])]
        return os.listdir(self.app.config['UPLOAD_FOLDER'])
    
    def getResponse(self):
        run = self.runThread()
        latestResponse = self.getLatestResposne(run_id=run.id)
        return latestResponse
    
    def convert_file_to_txt(self, file_path):
        txt_path = file_path.rsplit('.', 1)[0] + ".txt"
        txt_path = txt_path.replace("uploads", "txtFiles")
        with open(file_path, 'r') as input_file:
            content = input_file.read()
        with open(txt_path, 'w') as txt_file:
            txt_file.write(content)
        return txt_path




class OpenAI_API(object):
    def __init__(self, app):
        
        self.app = app

        filePath = self.app.config['UPLOAD_FOLDER']

        self.prompts = getPrompts(filePath)
        
        self.client = OpenAI(
            api_key=os.getenv('openAI_apikey'),
        )

        self.genConfig = defaultConfig

        #self.chatThread = ChatThreads(self.app, self.client)
    
    def basicRequest(self, chatHistory, genConfig=None):
        completion = self.chatCompletion(chatHistory, genConfig)
        #operate on the completion

        return completion.choices[0].message.content
    
    def chatCompletion(self, chatHistory, genConfig=None):
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

        #return completion.choices[0].message.content
        return completion
    
    def AssistantRunRequest(self):
        return self.chatThread.getResponse()
    
if __name__ == "__main__":
    # prompts = getPrompts("")
    # sysString = prompts["generateGraphInteractiveTest"]
    # fileString = getFileListString()
    # finalString = sysString + fileString
    # print(finalString)
    print(uploadFilePath)
