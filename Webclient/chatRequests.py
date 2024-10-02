import pandas as pd
import random
import subprocess
import sys
import os
import threading
import asyncio

from APIs import Redline_API, OpenAI_API, getFileListString


class ChatRequest(object):
    
    def __init__(self, app):
        
        self.config = {
            "retryOnError": True,
            "retryAttemptsMax" : 5,
            "showReport" : False,
        }

        self.app = app

        self.messages = []

        self.retryAttempts = 0

        self.hasReset = False

        self.generatedPromptSuggestions = []

        self.chatAPI = OpenAI_API(self.app)

        self.setMessages()

    def setSystemMessage(self):
        systemMessage = self.chatAPI.prompts["generateGraphInteractiveMain"] + getFileListString()
        if len(self.messages) == 0:
            self.addMessage("system", systemMessage)
            return True
        elif self.messages[0]["role"] == "system":
            self.messages[0]["content"] = systemMessage
            return True
        else:
            print("Error updating prompt with file changes")
            return False
        return False

    def setMessages(self):
        self.messages = []
        self.setSystemMessage()
        #self.addMessage("system", startingPrompt)
        files = self.getFiles()
        #uncomment this return for assistant
        #return
        for file in files:
            self.addFileMessage(file)

    def addFileMessage(self, file_name):
        file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], file_name)
        file_contents = self.createPandasDataFrame(file_path)
        self.addMessage("user", f"{file_name}: {str(file_contents)}")
        self.setSystemMessage()
        #self.chatAPI.chatThread.
        #Messages()

    def createPandasDataFrame(self, file_path):
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() in ['.xls', '.xlsx']:
            file_contents = pd.read_excel(file_path)
        else:
            file_contents = pd.read_csv(file_path)
        return file_contents

    def removeFileMessage(self, file_name):
        for message in self.messages:
            if message["role"] == "user" and message["content"].find(file_name) == 0:
                self.messages.remove(message)
                self.setSystemMessage()
                #self.chatAPI.chatThread.updateFileMessages()
                return True
        return False

    def addMessage(self, role, content):
        if role not in ["system", "user", "assistant"]:
            print(f"Error adding message to message history, unknown \"role\":\"{role}\"\n")
            return False
        
        messageAddition = {"role": role, "content": content}
        self.messages.append(messageAddition)
        #comment out this return for assistant
        return True

        if role == "user" and content.find("file_name") < 0:
            self.chatAPI.chatThread.addUserMessage(role, content)

        return True
    
    def makeChatRequest(self, content):
        if content == "showMessages":
            return str(self.messages)
        if not self.addMessage("user", content):
            return "Error creating message"
        #assistants call
        #response = self.chatAPI.AssistantRunRequest()
        #normal call
        response = self.chatAPI.basicRequest(self.messages)
        if not self.addMessage("assistant", response):
            return "Error creating message"
        
        if self.config["retryOnError"]: 
            self.retryAttempts = 0
            self.hasReset = False
            graphResponse = self.getGraphResponse(response)
        else:
            graphResponse = self.parseResponseInteractive(response)
        if graphResponse == None:
            return f"graphResponse is None.   Attempts: {self.retryAttempts}   self.messages: {self.messages}"

        #Second message must be reworked due to new file submission
        finalResponse = graphResponse
        if self.config["showReport"]:
            secondResponse = self.generateGraphReport(content)
            finalResponse += secondResponse
        
        return finalResponse

    #Tries to get a html string of saved graph from a response
    def getGraphResponse(self, response):
        self.retryAttempts += 1
        try:
            graphResponse = self.parseResponseInteractive(response, True)#self.parseGraphResponse(response)
            return graphResponse
        
        except Exception as e:
            """
            if self.retryAttempts > self.config["retryAttemptsMax"] and not self.hasReset:
                originalUserMsg = self.messages[len(self.messages) - (2*self.retryAttempts)]['content']
                self.setMessages()

                if not self.addMessage("user", originalUserMsg):
                    return "Error creating message"
                response = self.chatAPI.basicRequest(self.messages)
                if not self.addMessage("assistant", response):
                    return "Error creating message"
                
                self.hasReset = True
                self.getGraphResponse(response)
            """
            if self.retryAttempts > (self.config["retryAttemptsMax"]):
                return None

            #print(f"output of e:{e.__str__()}")
            originalUserMsg = self.messages[len(self.messages) - (2*self.retryAttempts)]['content']
            latestCodeBlock = self.messages[len(self.messages) - 1]['content']
            #f"Here is the code: {latestCodeBlock}. \nError in your latest attempt of generated code: {e.__str__()}\n Please try to fix this error in your code and complete the request: {originalUserMsg}"
            fullMsg = f"Here is your provided code: {latestCodeBlock}. \nError in your latest attempt of generated code: {e.__str__()}. Please try to fix errors in your code and complete the request: {originalUserMsg}"
            if not self.addMessage("user", fullMsg):
                return "Error creating message"
            newResponse = self.chatAPI.basicRequest(self.messages)
            if not self.addMessage("assistant", newResponse):
                return "Error creating message"
            
            print(f"Error occoured: Retrying {self.retryAttempts}")
            return self.getGraphResponse(newResponse)
    
    #Takes a OpenAI response, replaces code block with html for interactive graph
    def parseResponseInteractive(self, response, tmpFile=False):
        
        try:
            start = response.find("```python")
            pyStart = response.find("import", start)
            end = response.find("```", pyStart)

            #print(f"start: {start}, pyStart: {pyStart}, end: {end}")
            if start != -1 and pyStart != -1:
                if end != -1:
                    code_block = response[pyStart:end]
                    stringToReplace = response[start:end+3]
                else:
                    code_block = response[pyStart:]
                    stringToReplace = response[start:]
                #print(f"\n\n\ncodeblock:\n{code_block}\n\n\n")
                
                import matplotlib
                matplotlib.use('Agg')
                ###
                if tmpFile:
                    random_name = str(random.randint(100000, 999999))
                    file_name = os.path.join("generatedCodeFiles", f"{random_name}.py")
                    with open(file_name, "w") as code_file:
                        code_file.write(code_block)
                else:
                    file_name = os.path.join("generatedCodeFiles", "generated_code.py")
                    with open(file_name, "w") as code_file:
                        code_file.write(code_block)
                try:
                    html_str = ""
                    python_executable = sys.executable
                    result = subprocess.run([python_executable, file_name], check=True, capture_output=True, text=True)
                    print("Generated script ran successfully")
                    html_str = result.stdout
                    
                except subprocess.CalledProcessError as e:
                    print("Error running script")
                    #print(e.stderr)
                    raise ValueError(f"{e.stderr}")
                
                finally:
                    if os.path.exists(file_name) and tmpFile:
                        os.remove(file_name)

                ###
                response = response.replace(stringToReplace, html_str)

                return response
            return response
        except Exception as e:
            print(f"error getting code block from ChatRequest.parseReponse() : {e}")
            raise ValueError(f"{e}")
        
    def getPromptSuggestion(self):
        def generateContent():
            fileData = []
            filePaths = self.getFiles(True)

            for filepath in filePaths:
                try:
                    df = self.createPandasDataFrame(filepath)
                    columns_list = df.columns.tolist()
                    filename = os.path.basename(filepath)
                    file_dict = {filename: columns_list}
                    fileData.append(file_dict)

                except FileNotFoundError:
                    print(f"File '{filename}' not found. Skipping...")

            messagesHistory = [
                {"role": "system", "content": self.chatAPI.prompts["promptSuggestion"]},
                {"role": "user", "content": f"fileData: {str(fileData)}"},
                {"role": "user", "content": f"Provided Prompts: {str(self.generatedPromptSuggestions)}"},
            ]
            
            genConfig = {
                "model": "gpt-4o-mini",
                "max_tokens" : 4000,
                "n" : 1,
                "stop" : None,
                "temperature" : 0.8,
                "top_p" : 1.0,
                "presence_penalty" : 0.9,
                "frequency_penalty" : 0.9
            }

            return messagesHistory, genConfig
        
        mh, gc = generateContent()
        response = self.chatAPI.basicRequest(mh, gc)
        self.generatedPromptSuggestions.append(response)
        if len(self.generatedPromptSuggestions) > 20:
            self.generatedPromptSuggestions = []
        return response
    
    def generateGraphReport(self, content):
        def generateContent():
            #fileData = []
            filePaths = self.getFiles(True)

            messagesHistory = [
                {"role": "system", "content": self.chatAPI.prompts["graphReport"]},
            ]

            for filepath in filePaths:
                try:
                    df = pd.read_csv(filepath) 
                    filename = os.path.basename(filepath)
                    messagesHistory.append({"role": "user", "content": f"{filename}: {str(df)}"})

                except FileNotFoundError:
                    print(f"File '{filename}' not found. Skipping...")

            messagesHistory.append({"role": "user", "content": content})
            
            genConfig = {
            "model": "gpt-4o",
            "max_tokens" : 4000,
            "n" : 1,
            "stop" : None,
            "temperature" : 0.6,
            "top_p" : 1.0,
            "presence_penalty" : 0.0,
            "frequency_penalty" : 0.0
            }

            return messagesHistory, genConfig

        mh, gc = generateContent()
        response = self.chatAPI.basicRequest(mh, gc)
        return response
    
    async def generateBaselineGraphs(self, filename):
        graphRequests = [
            f"Can you show me a graph of JMeter threads per second for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of Average JMeter Thread Elapsed Time for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of Sampled HTTP Requests per Second for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of Request Average Response Time for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of KB Per Request per Second for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of Sampled Errors per Second for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of Error Average Response Time for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of KB Per Error per Second for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of Sampled Errors per Second for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
            f"Can you show me a graph of Sampled Errors per Second for {filename}. Ensure the title of the graph is the name of the requested graph with the filename. Make sure x axis is timeStamp",
        ]
        
        async def handleRequest(request):
            #print("req started")
            messages = list(self.messages)
            messages.append({"role": "user", "content": request})
            response = self.chatAPI.basicRequest(messages)
            #print("req finished")
            if not self.config["retryOnError"]:
                try:
                    graphResponse = self.parseResponseInteractive(response, True)
                    return graphResponse
                except Exception as e:
                    return f"Error generating graph report. No retry attempts"

            i = 0
            successful = False
            while i < self.config["retryAttemptsMax"] and not successful:
                try:
                    graphResponse = self.parseResponseInteractive(response, True)
                    successful = True
                    return graphResponse
                except Exception as e:
                    fullMsg = f"Here is your provided code: {response}. \nError in your latest attempt of generated code: {e.__str__()}. Please try to fix errors in your code and complete the request: {request}"
                    messages.append({"role": "user", "content": fullMsg})
                    response = self.chatAPI.basicRequest(messages)
            if not successful:
                numRetries = self.config["retryAttemptsMax"]
                return f"Error generating graph report. maxRetryAttempts: {numRetries}"
            
        tasks = []
        for request in graphRequests:
            task = asyncio.create_task(handleRequest(request))
            tasks.append(task)
            print("added task")
        print("gathering")
        res = await asyncio.gather(*tasks)
        return res

        
    def setShowReport(self, showReport):
        self.config["showReport"] = showReport

    def getShowReport(self):
        return self.config["showReport"]
    
    def getFiles(self, fullPath=False):
        if fullPath:
            return [os.path.join(self.app.config['UPLOAD_FOLDER'], file) for file in os.listdir(self.app.config['UPLOAD_FOLDER'])]
        return os.listdir(self.app.config['UPLOAD_FOLDER'])
        
