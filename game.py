import numpy
import physics
import random
import network

class World:
  WORLD_SIZE = numpy.array([1024.0, 640.0])
  GRAVITY = 200.0
  MAX_VELOCITY = 2000.0

  def __init__(self):
    self.map = Map(self.WORLD_SIZE[0], self.WORLD_SIZE[1])
    self.players = []

  def update(self, delta):
    self.step_players(delta)
    self.collision_check()

  def step_players(self, delta):
    for player in self.players:
      player.velocity[1] += self.GRAVITY * delta
      if player.velocity[1] > self.MAX_VELOCITY:
        player.velocity[1] = self.MAX_VELOCITY
      player.update(delta)
      for o_player in self.players:
        if player.id != o_player.id:
          intersection = player.box.intersects(o_player.box)
          if intersection is not None:
            self.resolve_collision(player, o_player.box, intersection)

  def collision_check(self):
    for player in self.players:
      for rect in self.map.collidable:
        intersection = player.box.intersects(rect)
        if intersection is not None:
          self.resolve_collision(player, rect, intersection)

  def resolve_collision(self, entity, rect, intersection):
    if intersection[0] < 0:
      print entity.position
      print rect.position
      entity.position[0] = rect.position[0] + rect.size[0]
      entity.velocity[0] = 0
    if intersection[0] > 0:
      entity.position[0] = rect.position[0] - entity.box.size[0]
      entity.velocity[0] = 0
    if intersection[1] < 0:
      entity.position[1] = rect.position[1] - entity.box.size[1]
      entity.velocity[1] = 0
      entity.can_jump = True
    if intersection[1] > 0:
      entity.position[1] = rect.position[1] + rect.size[1]
      entity.velocity[1] = 0
    entity.box.position = entity.position

  def handshake(self):
    return network.pack({"map": self.map.grid})

class Map:
  TILE_SIZE = 32.0

  def __init__(self, width, height):
    self.width = int(width / self.TILE_SIZE)
    self.height = int(height / self.TILE_SIZE)
    self.grid = self.populate()
    self.collidable = self.gen_collidable()

  def populate(self):
    grid = []
    for i in xrange(self.height):
      grid.append([])
      for j in xrange(self.width):
        grid[i].append(0)

    for i in xrange(self.width):
      grid[self.height - 1][i] = 1
    return grid

  def gen_collidable(self):
    collidable = []
    for i in xrange(self.height):
      for j in xrange(self.width):
        if self.grid[i][j] == 1:
          collidable.append(physics.Rectangle(
            numpy.array([j*self.TILE_SIZE, i*self.TILE_SIZE]), numpy.array([self.TILE_SIZE, self.TILE_SIZE])))
    return collidable

class Player:
  PLAYER_SIZE = 32.0
  JUMP_VELOCITY = 250.0
  MOVE_SPEED = 3.0

  def __init__(self, world, pk):
    world.players.append(self)
    self.world = world
    self.id = pk
    self.can_jump = False
    self.position = numpy.array([0.0, 0.0])
    self.velocity = numpy.array([0.0, 0.0])
    self.box = physics.Rectangle(self.position, numpy.array([self.PLAYER_SIZE, self.PLAYER_SIZE]))

  def update(self, delta):
    self.position += self.velocity * delta
    self.box.center = self.position

  def process_command(self, p_command):
    command = network.unpack(p_command)
    if "action" in command:
      c_act = command["action"]
      if c_act == "up" and self.can_jump:
        self.velocity[1] = -self.JUMP_VELOCITY
        self.can_jump = False
      if c_act == "left":
        self.position[0] -= self.MOVE_SPEED
      if c_act == "right":
        self.position[0] += self.MOVE_SPEED
      for o_player in self.world.players:
        if self.id != o_player.id:
          intersection = self.box.intersects(o_player.box)
          if intersection is not None:
            self.world.resolve_collision(self, o_player.box, intersection)
          print o_player.position
          print self.position

  def output(self):
    rtn = ""
    for player in self.world.players:
      rtn += network.pack({"object":"player", "id":player.id, "pos_x":player.position[0], "pos_y":player.position[1]})
    return rtn