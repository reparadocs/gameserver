import socket
from datetime import datetime
import select
import time
import json
import numpy
import random
import math

MAX_MSG_LENGTH = 2048

s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s_socket.bind(("0.0.0.0", 7755))
s_socket.listen(5)

sockets = [s_socket,]
clients = {}

start = time.clock()
now = start
last = now - 1

def normalize(vector):
  length = math.sqrt(vector[0]*vector[0] + vector[1]*vector[1])
  return numpy.array([vector[0] / length, vector[1] / length])

class Rectangle:
  def __init__(self, center, size):
    self.center = center
    self.width = size[0]
    self.height = size[1]

  def contains(self, point):
    x_val = abs(point[0] - self.center[0])
    y_val = abs(point[1] - self.center[1])
    if x_val < self.width / 2 and y_val < self.height / 2:
      return True
    return False

def pack(command):
  return json.dumps(command) + '\n'

def unpack(message):
  return json.loads(message)

class World:
  pad_speed = 150.0
  ball_speed = 80.0
  screen_size = numpy.array([640.0, 400.0])
  left_pos = numpy.array([32.0, 200.0])
  right_pos = numpy.array([618.0, 200.0])
  ball_pos = numpy.array([320.0, 200.0])
  direction = numpy.array([-1.0,0.0])
  pad_size = numpy.array([8.0, 32.0])

  def update(self, delta):
    left_rect = Rectangle(self.left_pos, self.pad_size)
    right_rect = Rectangle(self.right_pos, self.pad_size)
    self.ball_pos = self.ball_pos + self.direction * self.ball_speed * delta


    if (self.ball_pos[1] < 0 and self.direction[1] < 0) or (self.ball_pos[1] > self.screen_size[1] and self.direction[1] > 0):
      self.direction[1] = -self.direction[1]

    if (left_rect.contains(self.ball_pos) and self.direction[0] < 0) or (right_rect.contains(self.ball_pos) and self.direction[0] > 0):
      self.direction[0] = -self.direction[0]
      self.ball_speed *= 1.1
      self.direction[1] = random.random()*2.0 - 1
      self.direction = normalize(self.direction)

    if (self.ball_pos[0] < 0 or self.ball_pos[0] > self.screen_size[0]):
      print "Reset!"
      self.ball_pos = self.screen_size * 0.5
      self.ball_speed = 80
      self.direction = numpy.array([-1, 0])

  def move_action(self, player, direction, delta):
    if player == 'left':
      self.left_pos[1] += self.pad_speed * delta * direction
    else:
      self.right_pos[1] += self.pad_speed * delta * direction

class Player:
  def __init__(self, world, pk):
    self.world = world
    self.id = pk

  def process_command(self, command):
    if "action" in command:
      side = 'left'
      if self.id == 0:
        side = 'right'
      c_act = command["action"]
      if c_act == "up":
        self.world.move_action(side, -1, command["delta"])
      if c_act == "down":
        self.world.move_action(side, 1, command["delta"])

  def output(self):
    rtn = ""
    rtn += pack({"object":"ball", "pos_x":self.world.ball_pos[0], "pos_y":self.world.ball_pos[1]})
    rtn += pack({"object":"right", "pos_x":self.world.right_pos[0], "pos_y":self.world.right_pos[1]})
    rtn += pack({"object":"left", "pos_x":self.world.left_pos[0], "pos_y":self.world.left_pos[1]})
    return rtn

class ConnectedClient:
  output_buffer = ""
  input_buffer = ""
  socket_id = -1
  entity = None

  def __init__(self, socket_id, entity):
    global sockets
    global clients

    self.entity = entity
    self.socket_id = socket_id

    clients[socket_id] = self
    sockets.append(socket_id)

  def update(self):
    while True:
      command = self.input_buffer.partition("\n")
      if (command[1] == ""):
        break
      if self.entity:
        self.entity.process_command(unpack(command[0]))
      self.input_buffer = command[2]

  def send(self):
    if self.entity:
      output_msg = self.entity.output()
      self.output_buffer += output_msg

def get_writeable():
  writeable_sockets = []
  for client in clients:
    if len(clients[client].output_buffer) > 0:
      writeable_sockets.append(client)
  return writeable_sockets

def main_loop():
  global now
  global last
  global sockets

  player_counter = 0
  world = World()
  last = datetime.now()
  start = False
  while True:
    writeable_sockets = get_writeable()
    readable, writable, errors = select.select(sockets, writeable_sockets, sockets, 0.005)

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
        new_client = ConnectedClient(new_socket, Player(world, player_counter))
        player_counter += 1
        if player_counter == 2:
          start = True
          last = datetime.now()

    for socket in errors:
      client[socket].close()

    for client in clients.values():
      client.update()

    now = datetime.now()
    delta_time = now - last
    delta = delta_time.microseconds

    if delta >= 1000 and start:
      world.update(0.001 * (delta / 1000))
      for client in clients.values():
        client.send()
      last += delta_time



if __name__ == "__main__":
    main_loop()