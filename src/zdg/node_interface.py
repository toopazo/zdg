"""
Interface to connect two or more nodes (Docker containers) together using point-to-point ZMQ sockets (client-server)
"""

import os
import time

import zmq

#  Socket to talk to server
context = zmq.Context()


class ZdgNodeIface:
    """
    ZdgNodeIface
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def create_inbound_sockets():
        """
        create_client_sockets
        """

        inbound_list = str(os.environ["ZDG_INBOUND_LIST"])
        print(f"Inbound list: {inbound_list}")

        if len(inbound_list) == 0:
            return {}

        inbound_sockets = {}
        socket_cnt = 0
        for h_p in inbound_list.split(";"):
            socket_cnt += 1

            h, p = h_p.split()
            # print(f"h_p {h_p}")
            # print(f"h {h}")
            # print(f"p {p}")

            socket_hostname = str(h)
            socket_port = int(p)

            socket_socket = context.socket(zmq.REP)
            socket_url = f"tcp://{socket_hostname}:{socket_port}"
            print(f"Binding socket to {socket_url}")
            socket_socket.bind(socket_url)

            # Subscribe to zipcode, default is NYC, 10001
            # topic_filter = "10001"
            # socket_sub.setsockopt_string(zmq.SUBSCRIBE, topic_filter)
            # client_socket.setsockopt_string(zmq.SUBSCRIBE, "")

            inbound_sockets[f"socket_{socket_cnt}"] = {
                "hostname": socket_hostname,
                "port": socket_port,
                "url": socket_url,
                "socket": socket_socket,
            }

        return inbound_sockets

    @staticmethod
    def create_outbound_sockets():
        """
        create_server_sockets
        """

        outbound_list = str(os.environ["ZDG_OUTBOUND_LIST"])
        print(f"Outbound list: {outbound_list}")

        if len(outbound_list) == 0:
            return {}

        outbound_sockets = {}
        socket_cnt = 0
        for h_p in outbound_list.split(";"):
            socket_cnt += 1

            h, p = h_p.split()
            # print(f"h_p {h_p}")
            # print(f"h {h}")
            # print(f"p {p}")

            socket_hostname = str(h)
            # pub_hostname = "0.0.0.0"
            socket_port = int(p)

            # pub_socket = context.socket(zmq.PUB)
            # pub_url = f"tcp://{pub_hostname}:{pub_port}"
            # print(f"Connecting socket to {pub_url}")
            # pub_socket.connect(pub_url)

            socket_socket = context.socket(zmq.REQ)
            socket_url = f"tcp://{socket_hostname}:{socket_port}"
            print(f"Connecting socket to {socket_url}")
            socket_socket.connect(socket_url)

            outbound_sockets[f"socket_{socket_cnt}"] = {
                "hostname": socket_hostname,
                "port": socket_port,
                "url": socket_url,
                "socket": socket_socket,
            }

        return outbound_sockets

    @staticmethod
    def process_outbound_message(message: dict, socket_dict: dict):
        socket = socket_dict["socket"]
        socket_url = socket_dict["url"]

        verbose = False

        # Send request to server
        if verbose:
            print(f"[outbound] Sending to     {socket_url} a reqst with keys: {message.keys()}")
        try:
            socket.send_pyobj(message)
        except zmq.error.ZMQError:
            print("")
            print("")
            fname = ZdgNodeIface.process_outbound_message.__name__
            print(f"[{fname}] zmq.error.ZMQError: Socket operation on non-socket")
            print(f"[{fname}] {ZdgNodeIface.create_outbound_sockets.__name__}")
            print("")
            print("")
            ZdgNodeIface.create_outbound_sockets()

        # # Get the reply from server
        # reply = socket.recv_pyobj()
        # print(f"[outbound] Receiving from {socket_url}: {reply}")

        REQUEST_TIMEOUT = 2500
        REQUEST_RETRIES = 3
        SERVER_ENDPOINT = socket_url

        retries_left = REQUEST_RETRIES
        while True:
            if (socket.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
                reply = socket.recv_pyobj()
                if verbose:
                    print(f"[outbound] Receiving from {socket_url} a reply with keys: {reply.keys()}")
                break
                # if int(reply) == sequence:
                #     print("Server replied OK (%s)", reply)
                #     retries_left = REQUEST_RETRIES
                #     break
                # else:
                #     print("Malformed reply from server: %s", reply)
                #     continue

            retries_left -= 1
            print("No response from server")
            # Socket is confused. Close and remove it.
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()
            if retries_left == 0:
                print("Server seems to be offline, abandoning")
                raise RuntimeError

            print("Reconnecting to server")
            # Create new connection
            socket = context.socket(zmq.REQ)
            socket.connect(SERVER_ENDPOINT)
            print(f"Resending message {message.keys()}")
            socket.send_pyobj(message)

        return message, reply

    @staticmethod
    def process_inbound_message(inbound_fnct, socket_dict: dict):
        """
        process_inbound_message
        """
        socket = socket_dict["socket"]
        socket_url = socket_dict["url"]

        verbose = False

        # Wait for the next request from client
        message = socket.recv_pyobj()
        if verbose:
            print(f"[inbound]  Receiving from {socket_url}     a reqst with keys: {message.keys()}")

        # Process message
        reply = inbound_fnct(message)
        assert isinstance(reply, dict)

        # Send reply to client
        if verbose:
            print(f"[inbound]  Sending to     {socket_url}     a reply with keys: {reply.keys()}")
        socket.send_pyobj(reply)

        return message, reply

    @staticmethod
    def acknowledge_message(message):
        """
        acknowledge_message
        """
        reply = {"message_time": message["time"]}
        return reply

    @staticmethod
    def process_m_to_0_communication(inbound_sockets: dict, inbound_fnct):
        """
        process_m_to_0_communication
        """
        fname = ZdgNodeIface.process_m_to_0_communication.__name__
        print(fname)

        # https://zguide.zeromq.org/docs/chapter2/#Handling-Multiple-Sockets

        # Initialize poll set
        poller = zmq.Poller()

        for in_key, in_val in inbound_sockets.items():
            in_socket_cnt = in_key
            in_socket_socket = in_val["socket"]
            in_socket_url = in_val["url"]
            print(f"Register socket to Poller: socket_cnt {in_socket_cnt}, url {in_socket_url}")
            poller.register(in_socket_socket, zmq.POLLIN)

        # Process messages from both sockets
        message_t0 = time.time()
        message_cnt = 0
        while True:
            message_cnt += 1

            try:
                socket_list = dict(poller.poll())
            except KeyboardInterrupt:
                break

            for in_key, in_val in inbound_sockets.items():
                in_socket_cnt = in_key
                in_socket_socket = in_val["socket"]
                in_socket_url = in_val["url"]

                if in_socket_socket in socket_list:
                    message, reply = ZdgNodeIface.process_inbound_message(inbound_fnct=inbound_fnct, socket_dict=in_val)
                    _ = message
                    _ = reply

            if message_cnt % 100 == 0:
                message_t100 = time.time()
                message_dt = message_t100 - message_t0
                message_rate = message_cnt / message_dt
                print(f"[{fname}] Effective inbound message rate {message_rate} message/s")
                message_t0 = time.time()

    @staticmethod
    def process_0_to_n_communication(outbound_sockets: dict, outbound_fnct):
        """
        process_0_to_n_communication
        """
        fname = ZdgNodeIface.process_0_to_n_communication.__name__
        print(fname)

        # This is not an ideal solution
        # Allow for downstream nodes to initalize
        # time.sleep(10)

        # Process messages from both sockets
        message_t0 = time.time()
        message_cnt = 0
        while True:
            message_cnt += 1

            message = {
                "data": outbound_fnct(),
                "time": time.time(),
                "counter": message_cnt,
            }

            for out_key, out_val in outbound_sockets.items():
                # out_socket_cnt = out_key
                # out_socket_socket = out_val["socket"]
                # out_socket_url = out_val["url"]
                _ = out_key

                ZdgNodeIface.process_outbound_message(message=message, socket_dict=out_val)

            if message_cnt % 100 == 0:
                message_t100 = time.time()
                message_dt = message_t100 - message_t0
                message_rate = message_cnt / message_dt
                print(f"[{fname}] Effective outbound message rate {message_rate} message/s")
                message_t0 = time.time()

    @staticmethod
    def process_n_to_m_communication(inbound_sockets: dict, inbound_fnct, outbound_sockets: dict, outbound_fnct):
        """
        process_n_to_m_communication
        """
        print(ZdgNodeIface.process_n_to_m_communication.__name__)

        # https://zguide.zeromq.org/docs/chapter2/#Handling-Multiple-Sockets

        # Initialize poll set
        poller = zmq.Poller()

        # # Initialize poll set
        # poller = zmq.Poller()
        # poller.register(receiver, zmq.POLLIN)
        # poller.register(subscriber, zmq.POLLIN)

        # # Process messages from both sockets
        # while True:
        #     try:
        #         socks = dict(poller.poll())
        #     except KeyboardInterrupt:
        #         break

        #     if receiver in socks:
        #         message = receiver.recv_pyobj()
        #         # process task

        #     if subscriber in socks:
        #         message = subscriber.recv_pyobj()
        #         # process weather update

        for in_key, in_val in inbound_sockets.items():
            in_socket_cnt = in_key
            in_socket_socket = in_val["socket"]
            in_socket_url = in_val["url"]
            print(f"Register socket to Poller: socket_cnt {in_socket_cnt}, url {in_socket_url}")
            poller.register(in_socket_socket, zmq.POLLIN)

        # Process messages from both sockets
        message_cnt = 0
        while True:
            message_cnt += 1

            try:
                socket_list = dict(poller.poll())
            except KeyboardInterrupt:
                break

            # if receiver in active_socket:
            #     message = receiver.recv_pyobj()
            #     # process task

            # if subscriber in active_socket:
            #     message = subscriber.recv_pyobj()
            #     # process weather update

            for in_key, in_val in inbound_sockets.items():
                in_socket_cnt = in_key
                in_socket_socket = in_val["socket"]
                in_socket_url = in_val["url"]

                if in_socket_socket in socket_list:
                    inbound_message, inbound_reply = ZdgNodeIface.process_inbound_message(
                        # target_fnct=ZmqNodeIface.acknowledge_message,
                        inbound_fnct=inbound_fnct,
                        socket_dict=in_val,
                    )
                    _ = inbound_reply

                    # For every inbound message, send the same outbound message data to all outbound sockets
                    outbound_data = outbound_fnct(inbound_message)

                    for out_key, out_val in outbound_sockets.items():
                        # out_socket_cnt = out_key
                        # out_socket_socket = out_val["socket"]
                        # out_socket_url = out_val["url"]
                        _ = out_key

                        outbound_message = {
                            "data": outbound_data,
                            "time": time.time(),
                            "counter": message_cnt,
                        }

                        ZdgNodeIface.process_outbound_message(message=outbound_message, socket_dict=out_val)

    @staticmethod
    def run(inbound_fnct, outbound_fnct):
        """
        Pull data from subscribers and push data to publishers
        """

        # print(f"os.uname() {os.uname()}")
        # print(f"print(os.environ) {os.environ}")
        print(f"zmq.zmq_version() {zmq.zmq_version()}")
        # print(f"zmq.__version__ {zmq.__version__}")

        inbound_sockets = ZdgNodeIface.create_inbound_sockets()
        outbound_sockets = ZdgNodeIface.create_outbound_sockets()

        n_in = len(inbound_sockets)
        m_out = len(outbound_sockets)

        print(f"inbound length {n_in}")
        print(f"outbound length {m_out}")

        if (n_in > 0) and (m_out > 0):
            ZdgNodeIface.process_n_to_m_communication(inbound_sockets, inbound_fnct, outbound_sockets, outbound_fnct)
        elif (n_in == 0) and (m_out > 0):
            ZdgNodeIface.process_0_to_n_communication(outbound_sockets, outbound_fnct)
        elif (n_in > 0) and (m_out == 0):
            ZdgNodeIface.process_m_to_0_communication(inbound_sockets, inbound_fnct)
        elif (n_in == 0) and (m_out == 0):
            print("Nothing to do here, empty inbound_sockets and outbound_sockets")
        else:
            raise RuntimeError
