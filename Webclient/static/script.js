document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('file-input').addEventListener('change', uploadFile);
    document.getElementById('user-input').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    suggestionsElement = document.getElementById('suggestions')
    suggestionsElement.checked = false;
    showSuggestions(suggestionsElement.checked);
    suggestionsElement.addEventListener('change', function(event) {
        showSuggestions(suggestionsElement.checked)
    });

    reportCheckboxElement = document.getElementById('report');
    (async () => {
        const shouldCheck = await getShowReport();
        reportCheckboxElement.checked = shouldCheck;
        reportCheckboxElement.addEventListener('change', function(event) {
            setShowReport(reportCheckboxElement.checked);
        });
    })();
    
    updateFiles();
    //addSuggestedPrompts();
});

async function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === "") return;
    // Display user message
    addMessage(userInput, 'user');

    // Clear input
    document.getElementById('user-input').value = "";

    // Call Flask server
    const response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userInput })
    });
    
    const data = await response.json();
    const botResponse = data.response;
    // Display bot response
    addMessage(botResponse, 'bot');
}

async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a file to upload.');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const result = await response.text();
    updateFiles();
}

async function updateFiles() {
    const response = await fetch('/files');
    const files = await response.json();

    const filesDiv = document.getElementById('files');
    filesDiv.innerHTML = '';
    if (files.length === 0) {
        filesDiv.textContent = 'No files found.';
        return;
    }
    filesDiv.classList.remove('hidden');
    
    files.forEach(file => {
        const fileButton = document.createElement('button');

        fileButton.addEventListener('mouseenter', () => {
            fileButton.textContent = 'Remove File';
        });
        fileButton.addEventListener('mouseleave', () => {
            fileButton.textContent = `${file}`;
        });
        fileButton.addEventListener('click', () => {
            deleteFile(file);
        });

        fileButton.textContent = `${file}`;
        fileButton.classList.add('file-item');
        //fileButton.addEventListener('click', () => deleteFile(file));
        filesDiv.appendChild(fileButton);
    });
}

async function deleteFile(filename) {
    const response = await fetch('/delete-file', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filename: filename })
    });

    const result = await response.text();
    updateFiles();
}

function addMessage(text, sender) {
    const isInteractive = true;
    const chatBox = document.getElementById('chat-box');
    const message = document.createElement('div');
    message.classList.add('message', sender);

    if (isInteractive && sender !== 'user') {
        setInnerHTML(message, text);
    } else {
        message.textContent = text;
    }

    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function setInnerHTML(elm, html) {
    elm.innerHTML = html;
    
    Array.from(elm.querySelectorAll("script")).forEach(oldScriptEl => {
        const newScriptEl = document.createElement("script");
        
        Array.from(oldScriptEl.attributes).forEach(attr => {
            newScriptEl.setAttribute(attr.name, attr.value);
        });
        
        const scriptText = document.createTextNode(oldScriptEl.innerHTML);
        newScriptEl.appendChild(scriptText);
        
        oldScriptEl.parentNode.replaceChild(newScriptEl, oldScriptEl);
    });
}

async function addSuggestedPrompts() {
    const suggestedPrompts = document.getElementById('suggested-prompts-additions');
    var suggestedPromptsCount = suggestedPrompts.children.length;

    while (suggestedPromptsCount < 3) {
        const response = await fetch('/prompt-suggestion');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        if (suggestedPrompts.children.length < 3) {
            addSuggestedPrompt(data.response);
        }
        suggestedPromptsCount = suggestedPrompts.children.length;
    }
}

function addSuggestedPrompt(prompt) {
    const suggestedPrompts = document.getElementById('suggested-prompts-additions');
    const suggestedPrompt = document.createElement('button');
    suggestedPrompt.addEventListener('mouseenter', () => {
        suggestedPrompt.textContent = 'Select Prompt';
    });
    suggestedPrompt.addEventListener('mouseleave', () => {
        suggestedPrompt.textContent = `${prompt}`;
    });
    suggestedPrompt.addEventListener('click', () => {
        suggestedPrompt.textContent = `${prompt}`;
        selectSuggestedPrompt(suggestedPrompt);
    });
    suggestedPrompt.classList.add('suggested-prompt');
    suggestedPrompt.textContent = prompt;
    suggestedPrompts.appendChild(suggestedPrompt);
}

function selectSuggestedPrompt(suggestedPrompt) {
    suggestedPromptText = suggestedPrompt.textContent;
    suggestedPrompt.remove();
    document.getElementById('user-input').value = suggestedPromptText;
    sendMessage();
    addSuggestedPrompts();
}

async function showSuggestions(isChecked) {
    //code to show/hide suggestions
    const checked = isChecked
    //if box is not checked, hide the suggested-prompts div
    const element = document.getElementById('suggested-prompts')
    if (!checked) {
        //console.log('hidden');
        element.style.display = 'none';
        element.classList.add('hidden');
    } else {
        //console.log('unhidden');
        element.style.display = 'block';
        element.classList.remove('hidden');
        addSuggestedPrompts();
    }
}

async function setShowReport(isChecked) { 
    const response = await fetch('/set-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ showReport: isChecked })
    });
}

async function getShowReport() {
    const response = await fetch('/get-report');
    const data = await response.json();
    console.log(data.showReport);
    return data.showReport;
}