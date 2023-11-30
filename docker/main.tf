terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

# Specify the Docker provider
provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# Define the MySQL container
resource "docker_container" "mysql" {
  name  = "wordpress_mysql"
  image = "mysql:latest"
  ports {
    internal = 3306
    external = 3306
  }
  volumes {
    container_path = "/var/lib/mysql"
    read_only = false
    host_path = "/home/randeer/myapp/sql"
  }
  env = [
    "MYSQL_ROOT_PASSWORD=rashmikamanawadu",
    "MYSQL_DATABASE=wordpress",
    "MYSQL_USER=rashmika",
    "MYSQL_PASSWORD=manawadu",
  ]
}

# Define the WordPress volume for data
resource "docker_volume" "wordpress_data" {
  name = "wordpress_data"
}

# Define the WordPress container
resource "docker_container" "wordpress" {
  name  = "wordpress_app"
  image = "wordpress:latest"
  ports {
    internal = 80
    external = 8080
  }
  volumes {
    host_path = "/home/randeer/myapp/html"
    container_path = "/var/www/html"
    read_only = false
  }
  depends_on = [docker_container.mysql]

  env = [
    "WORDPRESS_DB_HOST=wordpress_mysql",
    "WORDPRESS_DB_NAME=wordpress",
    "WORDPRESS_DB_USER=rashmika",
    "WORDPRESS_DB_PASSWORD=manawadu",
  ]
}


