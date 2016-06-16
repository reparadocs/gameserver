import numpy
import math

def normalize(vector):
  length = math.sqrt(vector[0]*vector[0] + vector[1]*vector[1])
  return numpy.array([vector[0] / length, vector[1] / length])

class Rectangle:
  def __init__(self, position, size):
    self.position = position
    self.size = size
    self.center = self.position + self.size / 2.0

  def intersects(self, rect):
    center = self.position + self.size / 2.0
    center_distance = center - rect.center
    total_size = self.size / 2.0 + rect.size / 2.0
    x_overlap = total_size[0] - abs(center_distance[0])
    y_overlap = total_size[1] - abs(center_distance[1])
    if x_overlap <= 0 or y_overlap <= 0:
      return None

    if x_overlap > y_overlap:
      if center_distance[1] > 0:
        return numpy.array([0, 1])
      return numpy.array([0, -1])
    else:
      if center_distance[1] > 0:
        return numpy.array([1, 0])
      return numpy.array([-1, 0])

  def contains(self, point):
    x_val = abs(point[0] - self.position[0])
    y_val = abs(point[1] - self.position[1])
    if x_val < self.size[0] and y_val < self.size[1]:
      return True
    return False