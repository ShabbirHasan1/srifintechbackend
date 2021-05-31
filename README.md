# Srifintechbackend
ip = [167.71.231.30](http://167.71.231.30/) 
#### refrences 
- https://tinyurl.com/69h7cbxw 
- https://www.youtube.com/watch?v=US9BkvzuIxw


### 1. Login into the vps using ssh key 

### 2.  Configuring user and SSH details 
         :~# adduser username
         :~# usermod -aG sudo username
         
         :~# ufw allow OpenSSH
         :~# ufw enable
         :~# ufw allow 8080
         :~# mkdir -p /home/username/.ssh
         :~# cp ~/.ssh/authorized_keys /home/username/.ssh/
         :~# chown -R username:username /home/username/.ssh
         :~# chmod 755 /home/username
         :~# su username
        
### 3. Setup and Installations
         
         :~$ sudo apt-get update
         :~$ sudo apt-get install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx
         :~$ sudo -H pip3 install --upgrade pip
         :~$ sudo -H pip3 install virtualenv

         
         :~$ sudo ufw allow 'Nginx Full'
         
         check if Nginx is working by visiting IP n if success >
         :~$ sudo systemctl stop nginx
         
         :~$ git clone 'repo url'
         :~$ cd srifintechbackend/
         :~$ virtualenv deploy
         :~$ source deploy/bin/activate
         :~$ pip install -r requirements.txt
         :~$ pip install django gunicorn psycopg2
         :~$ deactivate

### 3.  Gunicorn service setup 

       :~$ sudo nano /etc/systemd/system/gunicorn.service
       
       add following code in the file and save
>   [Unit]
>    Description=gunicorn daemon
>    After=network.target

>   [Service]
>   User=username
>	Group=username
>	WorkingDirectory=/home/username/srifintechbackend
>	ExecStart=/home/username/srifintechbackend/deploy/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/username/srifintechbackend/srifintechbackend.sock >srifintechbackend.wsgi:application

>[Install]
WantedBy=multi-user.target

     :~$ sudo systemctl start gunicorn
     :~$ sudo systemctl enable gunicorn
     
     check status command - 
    :~$  sudo systemctl status gunicorn
     
     active >
     ctrl + c 
    
   :~$  sudo systemctl daemon-reload
   :~$ sudo systemctl restart gunicorn

## Configure Nginx to Proxy Pass to Gunicorn
	:~$ sudo nano /etc/nginx/sites-available/srifintechbackend
	add following code in the file and save
> server {
    listen 80;
    server_name 167.71.231.30;

>    location = /favicon.ico { access_log off; log_not_found off; }
>    location /static/ {
>        root /home/username/srifintechbackend;
>    }

>    location / {
>       include proxy_params;
>       proxy_pass http://unix:/home/username/srifintechbackend/srifintechbackend.sock;
>   }
>}

    :~$ sudo ln -s /etc/nginx/sites-available/srifintechbackend /etc/nginx/sites-enabled


     Test your Nginx configuration for syntax errors by typing:
     :~$ sudo nginx -t
     
     :~$ sudo systemctl restart nginx
     :~$ sudo ufw delete allow 8080
     :~$ sudo ufw allow 'Nginx Full'




