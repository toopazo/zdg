"""
Interface to connect two or more nodes (Docker containers) together using point-to-point ZMQ sockets (client-server)
"""

import os

import zmq

from zdg.node_interface import ZdgNodeIface

# import pathlib
# import time


#  Socket to talk to server
context = zmq.Context()


class ZdgNodeDemo:
    """
    ZdgNodeDemo
    """

    def __init__(self) -> None:
        self.zmq_container_name = str(os.environ["ZDG_CONTAINER_NAME"])

    def outbound_fnct(self, message={}):
        """
        outbound_fnct should be passed to ZmqNodeIface.run function and then be
        internally called by ZmqNodeIface functions
          process_n_to_m_communication
          process_0_to_n_communication
        """
        if len(message) == 0:
            # print("Assuming 0 to n role")

            data = f"From {self.zmq_container_name} with love"

            print(f"Outbound message data    {data}")
            # print(f"Outbound message time    {time}")
            # print(f"Outbound message counter {counter}")

            return data

        # print("Assuming n to m role")
        data = message["data"]
        # time = message["time"]
        # counter = message["counter"]
        # print(f"Inbound message data     {data}")
        # print(f"Inbound message time     {time}")
        # print(f"Inbound message counter  {counter}")

        data = f"{data} > From {self.zmq_container_name} with love"

        print(f"Outbound message data    {data}")
        # print(f"Outbound message time    {time}")
        # print(f"Outbound message counter {counter}")

        return data

    def inbound_fnct(self, message={}):
        """
        inbound_fnct should be passed to ZmqNodeIface.run function and then be
        internally called by ZmqNodeIface functions
          process_n_to_m_communication
          process_m_to_0_communication
        """
        # print("Assuming n to m (m>=0) role")
        mdata = message["data"]
        mtime = message["time"]
        mcounter = message["counter"]
        print(f"Inbound message data     {mdata}")
        print(f"Inbound message time     {mtime}")
        print(f"Inbound message counter  {mcounter}")

        reply = {"reply": f"Reply from node {self.zmq_container_name} to message {mcounter}"}
        return reply


if __name__ == "__main__":
    znd = ZdgNodeDemo()
    ZdgNodeIface.run(inbound_fnct=znd.inbound_fnct, outbound_fnct=znd.outbound_fnct)
