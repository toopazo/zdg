"""
Create a directed graph where each node is a Docker container and each edge is a ZMQ point-to-point socket
"""
import os
import pathlib

import yaml

# import random


class ZdgNode:
    """
    Class to create a directed graph where each node is a Docker container and each edge is a ZMQ point-to-point socket
    """

    def __init__(self, container_name: str, image: str, command: str) -> None:
        """
        __init__
        """
        self.current_dir = pathlib.Path(__file__).parent.resolve()

        self.container_name = container_name
        self.image = image
        self.command = command

        # self.volumes = [".:/app"]
        self.volumes = []
        self.environment = [f"ZDG_CONTAINER_NAME={self.container_name}"]
        self.depends_on = []

    def update_inbound_list(self, in_h_list: list, in_p_list: list):
        """
        update_inbound_list
        """
        env = "ZDG_INBOUND_LIST"
        h_p_list = ""
        for _, in_p in zip(in_h_list, in_p_list):
            if len(h_p_list) == 0:
                # h_p_list = f"{in_h} {port}"
                h_p_list = f"* {in_p}"
            else:
                # h_p_list = f"{h_p_list};{in_h} {port}"
                h_p_list = f"{h_p_list};* {in_p}"
        self.environment.append(f"{env}={h_p_list}")

        self.depends_on = in_h_list

    def update_outbound_list(self, out_h_list: list, out_p_list: list):
        """
        update_outbound_list
        """
        env = "ZDG_OUTBOUND_LIST"
        h_p_list = ""
        for out_h, out_p in zip(out_h_list, out_p_list):
            if len(h_p_list) == 0:
                h_p_list = f"{out_h} {out_p}"
            else:
                h_p_list = f"{h_p_list};{out_h} {out_p}"
        self.environment.append(f"{env}={h_p_list}")

    def update_yml(self):
        """
        update_yml
        """
        datad = {
            self.container_name: {
                "command": self.command,
                "container_name": self.container_name,
                "depends_on": self.depends_on,
                "environment": self.environment,
                "image": self.image,
                "volumes": self.volumes,
                # "working_dir": self.working_dir
            }
        }
        return datad

    @staticmethod
    def write_yml(datad: dict, yaml_path: str):
        """
        write_yml
        """
        # datad = self.update_yml()
        # yaml_path = str(self.current_dir / f"pubsub_compose_{self.container_name}.yml")
        with open(yaml_path, "w", encoding="utf-8") as f_d:
            yaml.dump(datad, f_d, default_flow_style=False)

    @staticmethod
    def get_comments():
        """
        get_comments
        """
        l1 = "# Run it using"
        l2 = "#   sudo docker compose -f zdg_compose_dgraph.yml up --remove-orphans"
        l3 = ""
        l4 = "# Execute a commnad on a running container using"
        l5 = "#   docker exec -it zdg bash"
        l6 = ""
        l7 = "# Remove all stopped containers"
        l8 = "#   sudo docker rm $(sudo docker ps --filter status=exited -q)"
        return [l1, l2, l3, l4, l5, l6, l7, l8]

    @staticmethod
    def demo_compose():
        """
        demo_compose
        """
        compose_data = {"services": {}}

        current_dir = pathlib.Path(__file__).parent.resolve()

        node_demo_command = "/bin/bash zdg_node_demo.sh"
        working_dir = "/demo"

        num_source_nodes = 2
        num_middle_nodes = 1  # random.randint(1, 5)
        num_sink_nodes = 1

        # Creating nodes
        source_node_list = []
        for i in range(0, num_source_nodes):
            container_name = f"source_node_{i}"
            source_ni = ZdgNode(container_name, "zdg", node_demo_command)
            source_ni.volumes.append(f"{os.path.split(__file__)[0]}:{working_dir}")
            source_node_list.append(source_ni)
            print(f"Creating source node {container_name}")

        middle_node_list = []
        for i in range(0, num_middle_nodes):
            container_name = f"middle_node_{i}"
            middle_ni = ZdgNode(container_name, "zdg", node_demo_command)
            middle_ni.volumes.append(f"{os.path.split(__file__)[0]}:{working_dir}")
            middle_node_list.append(middle_ni)
            print(f"Creating middle node {container_name}")

        sink_node_list = []
        for i in range(0, num_sink_nodes):
            container_name = f"sink_node_{i}"
            sink_ni = ZdgNode(container_name, "zdg", node_demo_command)
            sink_ni.volumes.append(f"{os.path.split(__file__)[0]}:{working_dir}")
            sink_node_list.append(sink_ni)
            print(f"Creating sink node {container_name}")

        # Connecting nodes
        zmq_port = 5550
        port_data = {}
        for source_ni in source_node_list:
            assert isinstance(source_ni, ZdgNode)
            container_name = source_ni.container_name

            inbound_list_h = []
            inbound_list_p = []

            outbound_list_h = [n.container_name for n in middle_node_list]
            outbound_list_p = []
            for h in outbound_list_h:
                zmq_port += 1
                outbound_list_p.append(zmq_port)
                port_data[f"{container_name}_to_{h}"] = zmq_port

            source_ni.update_inbound_list(inbound_list_h, inbound_list_p)
            source_ni.update_outbound_list(outbound_list_h, outbound_list_p)
            compose_data["services"][container_name] = source_ni.update_yml()[container_name]
            compose_data["services"][container_name]["working_dir"] = working_dir

            print(f"Connecting source node {container_name} to speak to:")
            for h, p in zip(outbound_list_h, outbound_list_p):
                print(f"  middle node {h} in port {p}")

        for middle_ni in middle_node_list:
            assert isinstance(middle_ni, ZdgNode)
            container_name = middle_ni.container_name

            inbound_list_h = [n.container_name for n in source_node_list]
            inbound_list_p = []
            for k, v in port_data.items():
                _ = v
                if f"_to_{container_name}" in k:
                    inbound_list_p.append(port_data[k])

            outbound_list_h = [n.container_name for n in sink_node_list]
            outbound_list_p = []
            for h in outbound_list_h:
                zmq_port += 1
                outbound_list_p.append(zmq_port)
                port_data[f"{container_name}_to_{h}"] = zmq_port

            middle_ni.update_inbound_list(inbound_list_h, inbound_list_p)
            middle_ni.update_outbound_list(outbound_list_h, outbound_list_p)
            compose_data["services"][container_name] = middle_ni.update_yml()[container_name]
            compose_data["services"][container_name]["working_dir"] = working_dir

            print(f"Connecting middle node {container_name} to speak to:")
            for h, p in zip(outbound_list_h, outbound_list_p):
                print(f"  middle node {h} in port {p}")

        for sink_ni in sink_node_list:
            assert isinstance(sink_ni, ZdgNode)
            container_name = sink_ni.container_name

            inbound_list_h = [n.container_name for n in middle_node_list]
            inbound_list_p = []
            for k, v in port_data.items():
                _ = v
                if f"_to_{container_name}" in k:
                    inbound_list_p.append(port_data[k])

            outbound_list_h = []
            outbound_list_p = []

            sink_ni.update_inbound_list(inbound_list_h, inbound_list_p)
            sink_ni.update_outbound_list(outbound_list_h, outbound_list_p)
            compose_data["services"][container_name] = sink_ni.update_yml()[container_name]
            compose_data["services"][container_name]["working_dir"] = working_dir

            print(f"Connecting sink node {container_name} to speak to:")
            for h, p in zip(outbound_list_h, outbound_list_p):
                print(f"  sink node {h} in port {p}")

        print("port_data")
        for k, v in port_data.items():
            print(f"Comunication from {k} uses port {v}")

        u_yaml_path = str(current_dir / "zdg_compose_dgraph.yml")
        ZdgNode.write_yml(compose_data, u_yaml_path)
        u_lines = ["\n"]
        for l_i in ZdgNode.get_comments():
            u_lines.append(l_i)
            u_lines.append("\n")
        with open(u_yaml_path, "a", encoding="utf-8") as f_d:
            f_d.writelines(u_lines)


if __name__ == "__main__":
    ZdgNode.demo_compose()
