# Simple-web-APP  
The algorithm is like this. 
Run the main file main.py from the application directory, then open the html file in the browser (localhost - 127.0.0.1, port-3000) . 
After on the page for sending messages, for example, enter data into the form, they get into the web application, which sends it further for processing, using socket (UDP protocol), Socket server. The Socket server translates the received byte string into a dictionary and saves it as a json file data.json in the storage folder.

Additionally you can upload app from dockerhub(https://hub.docker.com/repository/docker/alexeygoryachev/web_app/general)  
docker push alexeygoryachev/web_app:tagname
