import socket
from datetime import datetime
import select
import network
import game

MAX_MSG_LENGTH = 2048
HOST_IP = "0.0.0.0"
HOST_PORT = 7755
ACTIVE_CONNECTIONS = 5
UPDATE_DELTA = 1000
WORLD_STEP = 0.001

s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s_socket.bind((HOST_IP, HOST_PORT))
s_socket.listen(ACTIVE_CONNECTIONS)

sockets = [s_socket,]
clients = {}

def main_loop():
  now = datetime.now()
  last = now

  world = game.World()

  while True:
    writable_sockets = network.get_writable(clients)
    readable, writable, errors = select.select(sockets, writable_sockets, sockets, 0.005)

    for socket in writable:
      if clients.has_key(socket):
        client = clients[socket]
        if len(client.output_buffer) > 0:
          sent_length = socket.send(client.output_buffer)
          client.output_buffer = client.output_buffer[sent_length:]

    for socket in readable:
      if clients.has_key(socket):
        client = clients[socket]
        client.input_buffer = client.input_buffer + socket.recv(MAX_MSG_LENGTH)
      else:
        print "New Connection"
        new_socket = socket.accept()[0]
        new_client = network.ConnectedClient(new_socket, game.Player(world, len(clients)))
        new_client.output_buffer += world.handshake()
        clients[new_socket] = new_client
        sockets.append(new_socket)

    for socket in errors:
      # Error Handling
      client[socket].close()

    for client in clients.values():
      client.update()

    now = datetime.now()
    delta_time = now - last
    delta = delta_time.microseconds

    if delta >= UPDATE_DELTA:
      world.update(WORLD_STEP * (delta / UPDATE_DELTA))
      for client in clients.values():
        client.send()
      last += delta_time

if __name__ == "__main__":
    main_loop()