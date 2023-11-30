from flask import Flask, render_template, request, jsonify
import pymysql
import os
import subprocess
import shutil
import random

app = Flask(__name__)

# MySQL configurations
db_host = "172.17.0.2"
db_user = "root"
db_password = "rashmikamanawadu"
db_name = "wordpress1"

# Create a connection to the MySQL database
connection = pymysql.connect(host=db_host, user=db_user, password=db_password, db=db_name, cursorclass=pymysql.cursors.DictCursor)

# Ansible playbook variables
ansible_playbook_path = "/home/randeer/myapp/python-web/configure_mysql.yml"

# Terraform variables
terraform_path = "/usr/bin/terraform"  # Update with the actual path

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    username = request.form['username']
    mobile = request.form['mobile']
    domain = request.form['domain']
    email = request.form['email']

    # Check if the username already exists
    with connection.cursor() as cursor:
        select_sql = "SELECT * FROM your_table_name WHERE username = %s"
        cursor.execute(select_sql, (username,))
        result = cursor.fetchone()

    if result:
        return jsonify({"message": "Username already exists. Choose a different username."})
    
    # Generate a random 4-digit number higher than 1000
    new_port = random.randint(1001, 9999)

    # Check if the generated port already exists in the dockerhostport table
    with connection.cursor() as cursor:
        select_port_sql = "SELECT * FROM dockerhostport WHERE portno = %s"
        cursor.execute(select_port_sql, (new_port,))
        existing_port = cursor.fetchone()

        # Keep generating a new port until a unique one is found
        while existing_port:
            new_port = random.randint(1001, 9999)
            cursor.execute(select_port_sql, (new_port,))
            existing_port = cursor.fetchone()

    # Insert the new port into the dockerhostport table
    with connection.cursor() as cursor:
        insert_port_sql = "INSERT INTO dockerhostport (portno) VALUES (%s)"
        cursor.execute(insert_port_sql, (new_port,))
        connection.commit()

    # Insert data into MySQL database
    with connection.cursor() as cursor:
        insert_sql = "INSERT INTO your_table_name (name, username, mobile, domain) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_sql, (name, username, mobile, domain))
        connection.commit()

    # Create a directory with the username
    user_directory = os.path.join("/home/randeer/myapp/python-web/users", username)
    os.makedirs(user_directory)

    # Run Ansible playbook to configure MySQL with dynamic values
    subprocess.run(['ansible-playbook', ansible_playbook_path,
                    '-e', f'mysql_db_name=wordpress_{username}',
                    '-e', f'mysql_db_user=wordpressuser{username}',
                    '-e', f'mysql_db_password=wordpresspassword{username}',
                    '-e', f'userfolder={username}',
                    '-e', f'wordpress_name=test{username}',
                    '-e', f'wordpress_domain={domain}',
                    '-e', f'useremail={email}',
                    '-e', f'wordpress_port={new_port}'])

    # Copy main.tf to the user's directory
    main_tf_source = os.path.join("/home/randeer/myapp/python-web", "main.tf")
    main_tf_destination = os.path.join(user_directory, "main.tf")
    
    # Modify the main.tf file with dynamic values
    with open(main_tf_source, 'r') as file:
        data = file.read()

    data = data.replace('my_httpd', username)  # Replace 'my_httpd' with the username
    data = data.replace('4444', str(hash(username) % (10 ** 4) + 10000))  # Use a hash of the username for the external port
    
    with open(main_tf_destination, 'w') as file:
        file.write(data)

    # Run Terraform to create Docker container
    subprocess.run([terraform_path, 'init'], cwd=user_directory)
    subprocess.run([terraform_path, 'apply', '--auto-approve'], cwd=user_directory)

    # Get Docker container host ports
   # docker_command = f'docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}" | awk \'NR>1 {{split($3, ports, "->"); gsub("[^0-9]", "", ports[1]); printf("%s,", ports[1])}}\' | sed \'s/,$//\' | awk -F, \'{{for(i=1;i<=NF;i++) {{sub(/^0+/, "", $i); if($i) printf("%s%s",sep,$i); sep=","}} print ""}}\''
    docker_command = 'docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}" | awk \'NR>1 {split($3, ports, "->"); gsub("[^0-9]", "", ports[1]); printf("%s,", ports[1])}\' | sed \'s/,$//\' | awk -F, \'{for(i=1;i<=NF;i++) {sub(/^0+/, "", $i); if($i) printf("%s%s",sep,$i); sep=","} print ""}\''

    try:
        docker_output = subprocess.check_output(docker_command, shell=True, text=True)
        docker_ports_array = docker_output.strip().split(',')
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to get Docker container ports: {e.output}"})

    return f"Data submitted successfully: {name}, {username}, {mobile}, {domain}\nDocker Ports Array: {docker_ports_array}"

if __name__ == '__main__':
    app.run(port=9999, debug=True)
