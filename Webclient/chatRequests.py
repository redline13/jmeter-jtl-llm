import pandas as pd
import random
import subprocess
import sys
import os

from APIs import Redline_API, OpenAI_API, Gemini_API, LLM

csvFile1 = "/Users/mikebugden/Desktop/FordAPITest/results1.csv"
csvFile2 = "/Users/mikebugden/Desktop/FordAPITest/results2.csv"

class ChatRequest(object):
    
    def __init__(self, app, LLM_type=LLM.GPT):
        
        self.config = {
            "retryOnError": True,
            "retryAttemptsMax" : 5,
            "showReport" : False,
        }

        self.app = app

        self.LLM = LLM_type

        self.messages = []

        self.chatAPI = None

        self.retryAttempts = 0

        self.hasReset = False

        self.generatedPromptSuggestions = []

        if (self.LLM == LLM.Gemini):
            self.chatAPI = Gemini_API(self.app)
        elif (self.LLM == LLM.GPT):
            self.chatAPI = OpenAI_API(self.app)

        self.setMessages()

    def setMessages(self):
        self.messages = []
        startingPrompt = self.chatAPI.prompts["generatedGraphInteractiveDynamicFiles"]
        self.addMessage("system", startingPrompt)
        files = self.getFiles()
        
        for file in files:
            self.addFileMessage(file)

    def addFileMessage(self, file_name):
        file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], file_name)
        file_contents = pd.read_csv(file_path)
        self.addMessage("user", f"{file_name}: {str(file_contents)}")
    
    def getFiles(self, fullPath=False):
        if fullPath:
            return [os.path.join(self.app.config['UPLOAD_FOLDER'], file) for file in os.listdir(self.app.config['UPLOAD_FOLDER'])]
        return os.listdir(self.app.config['UPLOAD_FOLDER'])

    def removeFileMessage(self, file_name):
        for message in self.messages:
            if message["role"] == "user" and message["content"].find(file_name) == 0:
                self.messages.remove(message)
                return True
        return False

    def addMessage(self, role, content):
        """
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user", "content": "Where was it played?"}
        """
        if role not in ["system", "user", "assistant"]:
            print(f"Error adding message to message history, unknown \"role\":\"{role}\"\n")
            return False
        
        messageAddition = {"role": role, "content": content}
        self.messages.append(messageAddition)
        return True
    
    def makeChatRequest(self, content):
        if not self.addMessage("user", content):
            return "Error creating message"
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
            graphResponse = self.parseResponseInteractive(response)#self.parseGraphResponse(response)
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
    def parseResponseInteractive(self, response):
        
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
                with open("generated_code.py", "w") as code_file:
                    code_file.write(code_block)
                try:
                    html_str = ""
                    python_executable = sys.executable
                    result = subprocess.run([python_executable, "generated_code.py"], check=True, capture_output=True, text=True)
                    print("Generated script ran successfully")
                    html_str = result.stdout
                    
                except subprocess.CalledProcessError as e:
                    print("Error running script")
                    #print(e.stderr)
                    raise ValueError(f"{e.stderr}")
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
                    df = pd.read_csv(filepath) 
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
            "model": "gpt-4o",
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
            fileData = []
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
    
    def setShowReport(self, showReport):
        self.config["showReport"] = showReport

    def getShowReport(self):
        return self.config["showReport"]

    
    """
    #Takes a OpenAI response, replaces code block with html display for saved image
    def parseResponseImg(self, response):
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
                with open("generated_code.py", "w") as code_file:
                    code_file.write(code_block)
                try:
                    python_executable = sys.executable
                    result = subprocess.run([python_executable, "generated_code.py"], check=True, capture_output=True, text=True)
                    print("Generated script ran successfully")
                    print(result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Error running script")
                    #print(e.stderr)
                    raise ValueError(f"{e.stderr}")
                ###

                imgString = ""
                imgCount = code_block.count(".savefig(")
                #print(f"\n\nIMAGECOUNT : {imgCount}\n\n")
                #for i in range(imgCount):
                    #/Users/mikebugden/Desktop/RedlineLLM/WebClient/WebGraphs/myPNGFile1.png
                    #imgString += f"<img src=\"/static/WebGraphs/myPNGFile{i+1}.png?rand={random.randint(1, 999999)}\" alt=\"Image\">"
                imgString += f"<img src=\"/static/WebGraphs/myPNGFile.png?rand={random.randint(1, 999999)}\" alt=\"Image\">"

                response = response.replace(stringToReplace, imgString)

                return response

        except Exception as e:
            print(f"error getting code block from ChatRequest.parseReponse() : {e}")
            raise ValueError(f"{e}")
    """

        
