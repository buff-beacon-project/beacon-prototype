import zmq


def get_zmq_pub_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://localhost:%s" % port)
    return socket

class Controller:
    def __init__(self, pub_port):
        self.socket = get_zmq_pub_socket(pub_port)

    ####
    # note: https://github.com/zeromq/pyzmq/issues/957
    # subscriber needs:
    #   socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    # The subscriber will have to eat the topic with an extra receive:
    #   topic = socket.recv_string()
    #   data = socket.recv_json()
    def send(self, data):
        topic = "pulse"
        socket = self.socket
        socket.send_string(topic, zmq.SNDMORE)
        socket.send_json(data)
