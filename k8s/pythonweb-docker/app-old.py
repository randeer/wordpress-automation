from flask import Flask, render_template, request
import mysql.connector
import subprocess
import threading

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'docker.lala-1992.xyz',
    'user': 'root',
    'password': 'rashmikamanawadu',
    'database': 'k8sautomation'
}

# Maximum length for email column
MAX_EMAIL_LENGTH = 50  # Adjust this value based on your column definition

def validate_input_length(data):
    for key, value in data.items():
        if len(value) > MAX_EMAIL_LENGTH:
            return f'Error: {key} is too long. Maximum length is {MAX_EMAIL_LENGTH} characters.'
    return None

def user_account_exists(useraccount, cursor):
    # Check if the useraccount already exists in the database
    query = "SELECT COUNT(*) FROM k8sautomationtable WHERE useraccount = %s"
    cursor.execute(query, (useraccount,))
    result = cursor.fetchone()
    return result[0] > 0

def run_ansible_playbook(useraccount, useremail, domainname):
    playbook_path = 'k8s.yaml'  # Replace with the actual path to your Ansible playbook

    ansible_command = [
        'ansible-playbook',
        playbook_path,
        '--extra-vars',
        f'useraccount={useraccount} useremail={useremail} domainname={domainname}'
    ]

    try:
        subprocess.run(ansible_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error running Ansible playbook: {e}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Get form data
    username = request.form['username']
    useraccount = request.form['useraccount']
    email = request.form['email']
    domainname = request.form['domainname']

    # Validate input length
    validation_error = validate_input_length({'username': username, 'useraccount': useraccount, 'email': email, 'domainname': domainname})
    if validation_error:
        return validation_error

    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if useraccount already exists
        if user_account_exists(useraccount, cursor):
            conn.close()
            return f'Error: User account "{useraccount}" already exists. Redirecting back to the form in 5 seconds...<script>setTimeout(function(){{window.location.href = "/";}}, 5000);</script>'

        # Insert data into the database
        insert_query = "INSERT INTO k8sautomationtable (username, useraccount, email, domainname) VALUES (%s, %s, %s, %s)"
        data = (username, useraccount, email, domainname)
        cursor.execute(insert_query, data)

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        # Run Ansible playbook in a separate thread
        ansible_thread = threading.Thread(target=run_ansible_playbook, args=(useraccount, email, domainname))
        ansible_thread.start()

        # Forward the user to the success page
        return 'Form submitted successfully! Redirecting to the success page...<script>setTimeout(function(){{window.location.href = "/success";}}, 60000);</script>'
    except mysql.connector.Error as err:
        return f'Database error: {err}'

@app.route('/success')
def success():
    return 'Your request has been processed successfully. You will be redirected to your domain page shortly.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
