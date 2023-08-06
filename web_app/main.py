import json
import mimetypes
import pathlib
import socket
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer, BaseHTTPRequestHandler


#данные для запуска сокет сервера
HOST = '127.0.0.1'
PORT = 5000

#данные для запуска http сервера через контейнер 
HOST_http = '0.0.0.0'
PORT_http = 3000


#реализация класса http сервера
class HttpHandler(BaseHTTPRequestHandler):
    
    #метод обработки GET запросов
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)
    
    #метод обработки html ответов
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


    #метод обработки статических ресурсов
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())
    
    #метод обработки POST запросов
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        self.send_to_socket_server(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
        

    #метод обработки отправки сообщений сокет серверу
    def send_to_socket_server(self, data_dict):
        try:
            message = json.dumps(data_dict)
            socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_client.sendto(message.encode(), (HOST, PORT))
        except ConnectionRefusedError:
            print('Socket server is not running')
        finally:
            socket_client.close()


#функция обработки сокет сервером полученых сообщений 
def handle_message(data):
    message = json.loads(data.decode())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    data_dict = {timestamp: message}
    with open('storage/data.json', 'r+', encoding='utf-8') as file:
        data = json.load(file)
        data.update(data_dict)
        file.seek(0)
        json.dump(data, file, indent=4, ensure_ascii=False)


#функция реализации сокет сервера
def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((HOST, PORT))
        print(f'Socket server started on {HOST}:{PORT}')
        try:
            while True:
                data, addr = server_socket.recvfrom(1024)
                handle_message(data)
                if not data:
                    break
        except KeyboardInterrupt:
            print(f'Destroy server') 

#функция реализации http сервера
def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (HOST_http, PORT_http)
    http = server_class(server_address, handler_class)
    print(f'Http server started on {HOST_http}:{PORT_http}')
    try:
        http.serve_forever()   
    except KeyboardInterrupt:
        print(f'Server stopped')
    finally:
        http.server_close()


if __name__ == '__main__':
    #проброс volumes, создание внешней папки для хранения полученных данных в файле data.json
    storage = pathlib.Path().joinpath('storage')
    file_storage = storage / 'data.json'
    if not file_storage.exists():
        with open(file_storage, 'w', encoding='utf-8') as fd:
            json.dump({}, fd, ensure_ascii=False)
    
    #запуск в потоках http сервер и сокет сервер
    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            executor.submit(run_http_server, HTTPServer, HttpHandler)
            executor.submit(run_socket_server)
        except KeyboardInterrupt:
            print(f'Server stopped')
            sys.exit(0)
