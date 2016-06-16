import json

def pack(command):
  return json.dumps(command) + '\n'

def unpack(message):
  return json.loads(message)

class ConnectedClient:
  output_buffer = ""
  input_buffer = ""
  socket_id = -1
  entity = None

  def __init__(self, socket_id, entity):
    self.entity = entity
    self.socket_id = socket_id

  def update(self):
    while True:
      command = self.input_buffer.partition("\n")
      if (command[1] == ""):
        break
      if self.entity:
        self.entity.process_command(command[0])
      self.input_buffer = command[2]

  def send(self):
    if self.entity:
      output_msg = self.entity.output()
      self.output_buffer += output_msg

def get_writable(clients):
  writable_sockets = []
  for client in clients:
    if len(clients[client].output_buffer) > 0:
      writable_sockets.append(client)
  return writable_sockets
