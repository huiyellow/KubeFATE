# Copyright 2019-2020 VMware, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# you may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import json
import tempfile

from fml_manager.utils.fate_builders import RouteTable


class ClusterManager:
    """ClusterManager is used to manage FATE cluster"""

    def __init__(self, cluster_namespace, cluster_name=None):
        """ Init the ClusterManager instance

        :param cluster_namespace: Which namespace the cluster is belonged to
        :type cluster_namespace: string
        :param cluster_name: The name of fate cluster, no need to provide in most cases
        :type cluster_name: string

        """
        self.namespace = cluster_namespace
        self.name = cluster_name

    # get configmap in dict
    def fetch_config_map(self, component):
        args = "kubectl get configmap {} -n {} -o json".format(
            component, self.namespace).split(" ")
        try:
            data, err = subprocess.Popen(
                args, stdout=subprocess.PIPE).communicate()
            return json.loads(data)
        except Exception as error:
            print(error)

    # get route table in dict
    def fetch_route_table(self, configmap):
        route_table_json = json.loads(configmap["data"]["route_table.json"])
        return route_table_json

    def update_config_map(self, configmap, route_table):
        configmap["data"]["route_table.json"] = json.dumps(route_table)

    def patch_config_map(self, configmap, component):
        args = "kubectl patch configmap {} -n {} --patch".format(
            component, self.namespace).split(" ")
        args.append(json.dumps(configmap))
        try:
            data, err = subprocess.Popen(
                args, stdout=subprocess.PIPE).communicate()
            print(data)
        except Exception as error:
            print(error)

    def get_route_table(self):
        """ Fetch route table from configmap

        :rtype: RouteTable

        """
        # get configmap in dict
        configmap = self.fetch_config_map("rollsite-config")

        # get route table in dict
        route_table = self.fetch_route_table(configmap)

        route_table_ins = RouteTable().from_dict(route_table)
        return route_table_ins

    def set_route_table(self, route_table):
        """ Patch configmap with route table

        :param route_table: route table to patch configmap
        :type route_table: RouteTable

        """
        # get configmap in dict
        configmap = self.fetch_config_map("rollsite-config")

        # paste update to the configmap
        self.update_config_map(configmap, route_table.to_dict())

        # patch config
        self.patch_config_map(configmap, "rollsite-config")

    def get_entry_point(self):
        """ Return the entrypoint of FATE cluster

        :rtype: string

        """
        get_address = "kubectl get nodes -o jsonpath=\'{$.items[0].status.addresses[?(@.type==\'InternalIP\')].address}\'"
        get_port = "kubectl get service rollsite -n {0} -o jsonpath=\'{{.spec.ports[0].nodePort}}\'".format(
            self.namespace)

        ip = ""
        port = ""

        try:
            ip, err = subprocess.Popen(get_address.split(
                " "), stdout=subprocess.PIPE).communicate()
            port, err = subprocess.Popen(get_port.split(
                " "), stdout=subprocess.PIPE).communicate()
        except Exception as error:
            print(error)

        if ip == "" or port == "":
            raise(Exception("Unable to get entrypoint"))

        return "{}:{}".format(ip.decode("utf-8").replace("'", ""), port.decode("utf-8").replace("'", ""))
