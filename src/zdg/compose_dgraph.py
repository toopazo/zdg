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

    def __init__(self, node_name: str, node_image: str, node_command: str, opt: dict) -> None:
        """
        __init__
        """
        # self.current_dir = pathlib.Path(__file__).parent.resolve()

        self.node_name = node_name
        self.node_image = node_image
        self.node_command = node_command

        # self.volumes = [".:/app"]
        # self.volumes = []
        self.environment = [f"ZDG_CONTAINER_NAME={self.node_name}"]
        self.depends_on = []

        self.opt = opt

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
        # datad = {
        #     self.node_name: {
        #         "command": self.node_command,
        #         "container_name": self.node_name,
        #         "depends_on": self.depends_on,
        #         "environment": self.environment,
        #         "image": self.node_image,
        #         # "volumes": self.volumes,
        #         # "working_dir": self.working_dir
        #     }
        # }

        # # Use opt to update and overwrite values
        # for key, val in self.opt.items():
        #     datad[self.node_name][key] = val

        datad = {self.node_name: {}}

        # Write all opt (key, val) pairs
        for key, val in self.opt.items():
            datad[self.node_name][key] = val

        # Update reserved (key, val) pairs
        datad[self.node_name]["command"] = self.node_command
        datad[self.node_name]["container_name"] = self.node_name
        datad[self.node_name]["depends_on"] = self.depends_on
        try:
            _ = [datad[self.node_name]["environment"].append(item) for item in self.environment]
        except KeyError:
            datad[self.node_name]["environment"] = self.environment
        datad[self.node_name]["image"] = self.node_image

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
        l2 = "#   sudo docker compose -f compose_dgraph.yml up --remove-orphans"
        l3 = ""
        l4 = "# Execute a commnad on a running container using"
        l5 = "#   docker exec -it zdg bash"
        l6 = ""
        l7 = "# Remove all stopped containers"
        l8 = "#   sudo docker rm $(sudo docker ps --filter status=exited -q)"
        return [l1, l2, l3, l4, l5, l6, l7, l8]


class ZdgEdge:
    """
    Class to create a directed graph where each node is a Docker container and each edge is a ZMQ point-to-point socket
    """

    def __init__(self, node1: ZdgNode, node2: ZdgNode) -> None:
        self.node1 = node1
        self.node2 = node2


class ZdgCompose:
    """
    Class to create a directed graph where each node is a Docker container and each edge is a ZMQ point-to-point socket
    """

    def __init__(self, edge_list: list, port_num: int) -> None:
        zmq_port = port_num
        port_data = {}
        name1_list = []
        name2_list = []
        node_list = []
        for edge in edge_list:
            assert isinstance(edge, ZdgEdge)

            name1 = edge.node1
            node2 = edge.node2
            port_key = f"{name1.node_name}_to_{node2.node_name}"
            if port_key in port_data.keys():
                print(f"Edge is already registered {port_key}")
                raise ValueError

            name1_list.append(name1.node_name)
            name2_list.append(node2.node_name)
            node_list.append(name1)
            node_list.append(node2)

            port_data[port_key] = zmq_port
            zmq_port += 1
        name1_set = set(name1_list)
        name2_set = set(name2_list)
        node_set = set(node_list)

        compose_data = {"services": {}}

        # For each node1, connect to all node2 we want to send data to
        for name1 in name1_set:
            outbound_list_h = []
            outbound_list_p = []
            for port_key, port_val in port_data.items():
                prefix = f"{name1}_to_"
                if prefix in port_key:
                    name2 = port_key.replace(prefix, "")
                    outbound_list_h.append(name2)
                    outbound_list_p.append(port_val)
            for node in node_set:
                assert isinstance(node, ZdgNode)
                if name1 == node.node_name:
                    node.update_outbound_list(outbound_list_h, outbound_list_p)
                    node.update_inbound_list([], [])
                    compose_data["services"][name1] = node.update_yml()[name1]

        # For each node2, connect to all node1 we want to receive data from
        for name2 in name2_set:
            inbound_list_h = []
            inbound_list_p = []
            for port_key, port_val in port_data.items():
                sufix = f"_to_{name2}"
                if sufix in port_key:
                    name1 = port_key.replace(sufix, "")
                    inbound_list_h.append(name1)
                    inbound_list_p.append(port_val)
            for node in node_set:
                assert isinstance(node, ZdgNode)
                if name2 == node.node_name:
                    no_outbound_env = True
                    for env in node.environment:
                        if "ZDG_OUTBOUND_LIST" in env:
                            no_outbound_env = False
                    if no_outbound_env:
                        node.update_outbound_list([], [])
                    node.update_inbound_list(inbound_list_h, inbound_list_p)
                    compose_data["services"][name2] = node.update_yml()[name2]

        # # Append to inbound_list and outbound_list
        # node1.update_inbound_list(inbound_list_h, inbound_list_p)
        # node1.update_outbound_list(outbound_list_h, outbound_list_p)
        self.port_data = port_data
        self.compose_data = compose_data
        # self.compose_path = compose_path

    def dump(self, compose_path: str):
        """
        dump
        """
        port_data = self.port_data
        compose_data = self.compose_data
        # compose_path = self.compose_path

        arg = ZdgCompose.__name__
        for k, v in port_data.items():
            print(f"{arg}: Edge {k} is registered on port {v}")

        # current_dir = pathlib.Path(__file__).parent.resolve()
        # compose_path = str(current_dir / "compose_dgraph.yml")
        ZdgNode.write_yml(compose_data, compose_path)
        u_lines = ["\n"]
        for l_i in ZdgNode.get_comments():
            u_lines.append(l_i)
            u_lines.append("\n")
        with open(compose_path, "a", encoding="utf-8") as f_d:
            f_d.writelines(u_lines)


# if __name__ == "__main__":
#     ZdgNode.demo_compose()
