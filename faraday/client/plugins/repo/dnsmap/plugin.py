#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
'''
from __future__ import absolute_import
from __future__ import print_function

from __future__ import with_statement
from faraday.client.plugins import core
import re
import os
import sys
import random

current_path = os.path.abspath(os.getcwd())

__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class DnsmapParser(object):
    """
    The objective of this class is to parse an xml file generated by the
    dnsmap tool.

    TODO: Handle errors.
    TODO: Test dnsmap output version. Handle what happens if the parser
    doesn't support it.
    TODO: Test cases.

    @param dnsmap_filepath A proper simple report generated by dnsmap
    """

    def __init__(self, output):
        self.items = []
        if "\n\n" in output:
            self.parse_txt(output)
        else:
            self.parse_csv(output)

    def parse_txt(self, output):
        hosts = self.split_output_lines(output)

        for host_data in hosts:
            if len(host_data) == 2:
                ip = self.clean_ip(host_data[1])
                hostname = host_data[0]
                self.add_host_info_to_items(ip, hostname)
            elif len(host_data) > 2:
                hostname = host_data.pop(0)
                for ip_address in host_data:
                    ip = self.clean_ip(ip_address)
                    self.add_host_info_to_items(ip, hostname)

    def parse_csv(self, output):
        hosts = list(filter(None, output.splitlines()))

        for host in hosts:
            host_data = host.split(",", 1)
            if host_data[1].count(',') == 0:
                ip = host_data[1]
                hostname = host_data[0]
                self.add_host_info_to_items(ip, hostname)
            else:
                hostname = host_data.pop(0)
                ips = host_data[0].split(",")
                for ip_address in ips:
                    self.add_host_info_to_items(ip_address, hostname)

    def split_output_lines(self, output):
        splitted = output.splitlines()
        hosts_list = []
        aux_list = []
        for i in range(0, len(splitted)):
            if not splitted[i]:
                hosts_list.append(aux_list)
                aux_list = []
                continue
            else:
                aux_list.append(splitted[i])

        return hosts_list

    def clean_ip(self, item):
        ip = item.split(':', 1)
        return ip[1].strip()

    def add_host_info_to_items(self, ip_address, hostname):
        data = {}
        exists = False
        for item in self.items:
            if ip_address in item['ip']:
                item['hosts'].append(hostname)
                exists = True

        if not exists:
            data['ip'] = ip_address
            data['hosts'] = [hostname]
            self.items.append(data)


class DnsmapPlugin(core.PluginBase):
    """Example plugin to parse dnsmap output."""

    def __init__(self):

        core.PluginBase.__init__(self)
        self.id = "Dnsmap"
        self.name = "Dnsmap Output Plugin"
        self.plugin_version = "0.3"
        self.version = "0.30"
        self.options = None
        self._current_output = None
        self.current_path = None
        self._command_regex = re.compile(
            r'^(sudo dnsmap|dnsmap|\.\/dnsmap).*?')

        self.xml_arg_re = re.compile(r"^.*(-r\s*[^\s]+).*$")

        global current_path

        self._output_file_path = os.path.join(
            self.data_path,
            "%s_%s_output-%s.txt" % (
                self.get_ws(),
                self.id,
                random.uniform(1, 10)
            )
        )

    def canParseCommandString(self, current_input):
        if self._command_regex.match(current_input.strip()):
            return True
        else:
            return False

    def parseOutputString(self, output, debug=False):
        """
        This method will discard the output the shell sends, it will read it
        from the xml where it expects it to be present.
        """
        parser = DnsmapParser(output)
        for item in parser.items:
            h_id = self.createAndAddHost(
                        item['ip'],
                        hostnames=item['hosts'])

        return True

    def processCommandString(self, username, current_path, command_string):
        """
        Adds the parameter to get output to the command string that the
        user has set.
        """
        arg_match = self.xml_arg_re.match(command_string)

        if arg_match is None:
            return "%s -r %s \\n" % (command_string, self._output_file_path)
        else:
            return re.sub(arg_match.group(1),
                          r"-r %s" % self._output_file_path,
                          command_string)


def createPlugin():
    return DnsmapPlugin()

if __name__ == '__main__':
    parser = DnsmapParser(sys.argv[1])
    for item in parser.items:
        if item.status == 'up':
            print(item)
