from flask import Flask, render_template, request, jsonify
from chatRequests import ChatRequest
from werkzeug.utils import secure_filename
import os
import atexit
import shutil

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['DELETE_ON_CLOSE'] = False

if app.config['DELETE_ON_CLOSE']:
    def clear_file_contents():
        directory_name = os.path.abspath(app.config['UPLOAD_FOLDER'])
        if not os.path.isdir(directory_name):
            raise ValueError(f"{directory_name} is not a valid directory path.")

        # Iterate over the directory and remove each file and subdirectory
        for root, dirs, files in os.walk(directory_name, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                shutil.rmtree(dir_path)

    atexit.register(clear_file_contents)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

chatRequest = ChatRequest(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    
    print(user_input)
    response = chatRequest.makeChatRequest(user_input)
    #print(f"\n\n{response}\n\n")
    return jsonify({'response': response})


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        chatRequest.addFileMessage(filename)
        return f'File successfully uploaded: {filename}'
    
@app.route('/files', methods=['GET'])
def get_files():
    files = chatRequest.getFiles()
    return jsonify(files)

@app.route('/delete-file', methods=['DELETE'])
def delete_file():
    data = request.get_json()
    filename = data.get('filename')

    if filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            os.remove(file_path)
            if not chatRequest.removeFileMessage(filename):
                return jsonify({'message': f'Error removing {filename} from messages'}), 500
            return jsonify({'message': f'File {filename} deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to delete file {filename}', 'exception': str(e)}), 500
    else:
        return jsonify({'error': 'No filename provided in request'}), 400

@app.route('/prompt-suggestion', methods=['GET'])
def prompt_suggestion():
    prompt_suggestion = chatRequest.getPromptSuggestion()
    response_data = {"response": f"{prompt_suggestion}"}
    return jsonify(response_data), 200

@app.route('/set-report', methods=['POST'])
def set_showReport():
    showReport = request.json.get('showReport')
    chatRequest.setShowReport(showReport)
    response_data = {"showReport": showReport}
    return jsonify(response_data), 200

@app.route('/get-report', methods=['GET'])
def get_showReport():
    showReport = chatRequest.getShowReport()
    response_data = {"showReport": showReport}
    return jsonify(response_data), 200
    

    
if __name__ == '__main__':
    app.run(debug=True)


