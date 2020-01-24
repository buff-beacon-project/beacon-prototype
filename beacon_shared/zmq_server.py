import zmq
import sys, traceback

def get_zmq_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:%s" % port)
    return socket

class ZMQServer:
    def __init__(self, handlers):
        self.handlers = handlers
        self.socket = None

    def start(self, port):
        if self.socket:
            raise Exception('ZMQ server already started')

        self.socket = get_zmq_socket(port)
        # zmq requests come in as { command: '<string>', data: {} }
        while True:
            try:
                request = self.socket.recv_json()
                response = self.handle_request(request)
                self.socket.send_json(response)
            except Exception as e:
                print(e)
                traceback.print_exc(file=sys.stdout)
                self.socket.send_json({ "error": { "message": str(e) } })

    def handle_request(self, req):
        if not 'command' in req:
            raise Exception('Request malformed. Lacking a "command" property.')

        command = req['command']
        if not command in self.handlers:
            raise Exception('Ho handler defined for command "{}"'.format(command))

        handler = self.handlers[command]
        response = handler(req['data'])
        if not response:
            return { "ok": True }
        else:
            return { "ok": True, "data": response }
