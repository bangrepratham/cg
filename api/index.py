from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import re
import subprocess
import tempfile
import os
import uuid
import signal
import threading
import time

app = Flask(__name__)

# Configure API key
genai.configure(api_key="AIzaSyBJYfcyuitqMbccuP4NOIE0h_vmOPU2Y8U")

# Initialize the model
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Dictionary to store running processes
running_processes = {}

# Maximum execution time in seconds
MAX_EXECUTION_TIME = 10

@app.route('/')
def index():
    return send_file('chat.html')

@app.route('/generate', methods=['POST'])
def generate_code():
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        enhanced_prompt = f"""
        Generate clean, well-documented code based on this request: "{prompt}"
        
        Please provide only the code without explanations before or after.
        Include helpful comments within the code to explain key parts.
        Use best practices and efficient algorithms.
        """
        response = model.generate_content([enhanced_prompt])
        code = extract_code_from_response(response.text)
        return jsonify({"code": code})
    
    except Exception as e:
        print(f"Error generating code: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'unknown')
    use_gemini = data.get('useGemini', False)
    
    if not code:
        return jsonify({"error": "Code is required"}), 400
    
    execution_id = str(uuid.uuid4())
    
    try:
        if use_gemini:
            output = simulate_execution_with_gemini(code, language, execution_id)
            return jsonify({"output": output})
        
        if language == 'python':
            output = execute_python(code, execution_id)
        elif language in ['javascript', 'nodejs']:
            output = execute_javascript(code, execution_id)
        elif language == 'php':
            output = execute_php(code, execution_id)
        elif language == 'ruby':
            output = execute_ruby(code, execution_id)
        elif language in ['cpp', 'c++', 'c']:
            output = execute_cpp(code, execution_id)
        elif language == 'java':
            output = execute_java(code, execution_id)
        elif language in ['bash', 'shell']:
            output = execute_bash(code, execution_id)
        else:
            output = simulate_execution_with_gemini(code, language, execution_id)
        
        return jsonify({"output": output})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if execution_id in running_processes:
            try:
                os.killpg(os.getpgid(running_processes[execution_id].pid), signal.SIGTERM)
            except:
                pass
            del running_processes[execution_id]

def extract_code_from_response(text):
    code_blocks = re.findall(r'```(?:\w+)?\s*([\s\S]*?)```', text)
    if code_blocks:
        return code_blocks[0].strip()
    return text.strip()

def execute_with_timeout(func, execution_id, *args, **kwargs):
    result = ["", "Execution timed out"]
    def target():
        nonlocal result
        try:
            result[0] = func(*args, **kwargs)
            result[1] = None
        except Exception as e:
            result[1] = str(e)
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(MAX_EXECUTION_TIME)
    if thread.is_alive():
        if execution_id in running_processes:
            try:
                os.killpg(os.getpgid(running_processes[execution_id].pid), signal.SIGTERM)
            except:
                pass
            del running_processes[execution_id]
        return "Execution timed out after {} seconds".format(MAX_EXECUTION_TIME)
    if result[1]:
        return "Error: " + result[1]
    return result[0]

def simulate_execution_with_gemini(code, language, execution_id):
    """
    Use Gemini to simulate code execution for any language.
    Updated: Analyze the generated code (displayed under "Here's the code you requested:")
    and execute it, returning only the output prefixed with "result:".
    """
    try:
        prompt = f"""
        For givencode: Please analyze the following {language} code, which is the code displayed under "Here's the code you requested:".
        Then, execute this code in its appropriate runtime environment and return only the output.
        Do not include any explanations or commentary.
        The output must be prefixed with "result:" immediately followed by the actual output.
        If the code does not produce any output, simply return "result:".
        
        ```{language}
        {code}
        ```
        """
        response = model.generate_content([prompt])
        output = re.sub(r'```(?:\w+)?\s*([\s\S]*?)```', r'\1', response.text).strip()
        if not output.lower().startswith("result:"):
            output = "result: " + output
        return output
    except Exception as e:
        return f"Simulation Error: {str(e)}"

def execute_python(code, execution_id):
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
        f.write(code)
        temp_file = f.name
    try:
        process = subprocess.Popen(
            ['python', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        running_processes[execution_id] = process
        def run_process():
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(stderr)
            return stdout
        result = execute_with_timeout(run_process, execution_id)
        return result
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def execute_javascript(code, execution_id):
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as f:
        f.write(code)
        temp_file = f.name
    try:
        process = subprocess.Popen(
            ['node', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        running_processes[execution_id] = process
        def run_process():
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(stderr)
            return stdout
        return execute_with_timeout(run_process, execution_id)
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def execute_php(code, execution_id):
    with tempfile.NamedTemporaryFile(suffix='.php', mode='w', delete=False) as f:
        f.write(code)
        temp_file = f.name
    try:
        process = subprocess.Popen(
            ['php', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        running_processes[execution_id] = process
        def run_process():
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(stderr)
            return stdout
        return execute_with_timeout(run_process, execution_id)
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def execute_ruby(code, execution_id):
    with tempfile.NamedTemporaryFile(suffix='.rb', mode='w', delete=False) as f:
        f.write(code)
        temp_file = f.name
    try:
        process = subprocess.Popen(
            ['ruby', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        running_processes[execution_id] = process
        def run_process():
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(stderr)
            return stdout
        return execute_with_timeout(run_process, execution_id)
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def execute_cpp(code, execution_id):
    with tempfile.NamedTemporaryFile(suffix='.cpp', mode='w', delete=False) as f:
        f.write(code)
        cpp_file = f.name
    exec_file = tempfile.NamedTemporaryFile(delete=False).name
    try:
        compile_process = subprocess.Popen(
            ['g++', cpp_file, '-o', exec_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        compile_stdout, compile_stderr = compile_process.communicate()
        if compile_process.returncode != 0:
            return "Compilation Error: " + compile_stderr
        process = subprocess.Popen(
            [exec_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        running_processes[execution_id] = process
        def run_process():
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(stderr)
            return stdout
        return execute_with_timeout(run_process, execution_id)
    finally:
        try:
            os.unlink(cpp_file)
            os.unlink(exec_file)
        except:
            pass

def execute_java(code, execution_id):
    match = re.search(r'public\s+class\s+(\w+)', code)
    if not match:
        return "Error: Could not find a public class in the Java code"
    class_name = match.group(1)
    with tempfile.TemporaryDirectory() as temp_dir:
        java_file = os.path.join(temp_dir, class_name + ".java")
        with open(java_file, 'w') as f:
            f.write(code)
        try:
            compile_process = subprocess.Popen(
                ['javac', java_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            compile_stdout, compile_stderr = compile_process.communicate()
            if compile_process.returncode != 0:
                return "Compilation Error: " + compile_stderr
            process = subprocess.Popen(
                ['java', '-cp', temp_dir, class_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
            running_processes[execution_id] = process
            def run_process():
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    raise Exception(stderr)
                return stdout
            return execute_with_timeout(run_process, execution_id)
        except Exception as e:
            return f"Error: {str(e)}"

def execute_bash(code, execution_id):
    with tempfile.NamedTemporaryFile(suffix='.sh', mode='w', delete=False) as f:
        f.write(code)
        temp_file = f.name
    try:
        os.chmod(temp_file, 0o755)
        process = subprocess.Popen(
            ['bash', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        running_processes[execution_id] = process
        def run_process():
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(stderr)
            return stdout
        return execute_with_timeout(run_process, execution_id)
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
