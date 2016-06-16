
extends Node2D

var ball_speed = 80
var direction = Vector2(-1,0)
const PAD_SPEED = 150
var screen_size = null
var pad_size = null
var connection = null
var peer_stream = null
var connected = false
var output_buffer = ""
var input_buffer = ""

func _ready():
  connection = StreamPeerTCP.new()
  connection.connect("127.0.0.1", 7755)
  screen_size = get_viewport_rect().size
  pad_size = get_node("left").get_texture().get_size()
  print(pad_size)
  set_process(true)
  pass

func _process(delta):
  if !connected:
    if connection.get_status() == connection.STATUS_CONNECTED:
      connected = true
      peer_stream = PacketPeerStream.new()
      peer_stream.set_stream_peer(connection)
  else:
    var bytes_available = connection.get_available_bytes()
    if bytes_available > 0:
      input_buffer += connection.get_string(bytes_available)
    if output_buffer.length() > 0:
      connection.put_data(output_buffer.to_ascii())
      output_buffer = ""

  while true:
    var p_index = input_buffer.find("\n")
    if p_index < 0:
      break
    var packet = input_buffer.left(p_index)
    input_buffer = input_buffer.right(p_index + 1)
    var p_data = {}
    p_data.parse_json(packet)
    if p_data.has("object"):
      var pos = Vector2(p_data["pos_x"], p_data["pos_y"])
      get_node(p_data["object"]).set_pos(pos)

  if (Input.is_action_pressed("left_move_up")):
    var new_packet = {"action": "left_up", "delta": delta}
    output_buffer += new_packet.to_json() + "\n"
  if (Input.is_action_pressed("left_move_down")):
    var new_packet = {"action": "left_down", "delta": delta}
    output_buffer += new_packet.to_json() + "\n"
  if (Input.is_action_pressed("right_move_up")):
    var new_packet = {"action": "up", "delta": delta}
    output_buffer += new_packet.to_json() + "\n"
  if (Input.is_action_pressed("right_move_down")):
    var new_packet = {"action": "down", "delta": delta}
    output_buffer += new_packet.to_json() + "\n"
