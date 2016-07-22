# -*- coding: utf-8 -*-
# inspired from https://gist.github.com/bradmontgomery/2219997
# updated to fit need

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import parse_qs
from pprint import pprint
import ConfigParser
import SocketServer
import requests
import os


class Config:
  def __init__(self, configfile=None):
    self.conf = dict()

    self.configfile = os.path.abspath(configfile)
    self.config = ConfigParser.SafeConfigParser()

    if configfile:
      self.config.read(self.configfile)

  def read_as_dict(self):
    for section in self.config.sections():
      for option in self.config.options(section):

        # lists in the config options
        if option in [""]:
          self.conf[option] = []
          for infile in self.config.get(section, option).strip().split(","):
            self.conf[option].append(infile.strip())

        # booleans in config options
        elif option in []:
          if self.config.get(section, option).lower() == "false":
            self.conf[option] = False

          if self.config.get(section, option).lower() == "true":
            self.conf[option] = True

        # ints in config options
        elif option in ["port"]:
          self.conf[option] = int(self.config.get(section, option))

        # floats in config options
        elif option in ["version"]:
          self.conf[option] = float(self.config.get(section, option))

        # everything else
        else:
          self.conf[option] = self.config.get(section, option)

    return self.conf

  def get_var(self, section, var):
    try:
      return self.config.get(section, var)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
      return None

  def get_section(self, section):
    try:
      options = self.config.items(section)
    except ConfigParser.NoSectionError:
      return None

    opt_dict = dict()
    for pairs in options:
      opt_dict[pairs[0]] = pairs[1]

    return opt_dict

  def set_var(self, section, var, value):
    try:
      return self.config.set(section, var, value)
    except ConfigParser.NoSectionError:
      return None

  def list_config(self):
    print "Configuration Options:"
    for section in self.config.sections():
      print "%s" % (section)
      for (name, value) in self.config.items(section):
        print "\t%s:\t%s" % (name, value)
    return


class fbhandler(BaseHTTPRequestHandler):
  def _set_headers(self):
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()

  def do_HEAD(self):
    self._set_headers()

  def do_GET(self):
    self._set_headers()
    params = parse_qs(self.path[2:])
    if params and "hub.challenge" in params:
      print "Sent hub.challenge: %s" % (params["hub.challenge"][0])
      self.wfile.write("%s" % (params["hub.challenge"][0]))
    else:
      print "Ignored request: %s" % (self.path)
      self.wfile.write("Ignored request: %s" % (self.path))

  def do_POST(self):
    self._set_headers()
    fbdata = self.rfile.read(int(self.headers.getheader("content-length", 0)))
    data = {
      "value1": str(fbdata)
    }
    try:
      res = requests.post("https://maker.ifttt.com/trigger/%s/with/key/%s" % (config["event"], config["maker"]),
        data={
          "value1": fbdata,
          "value2": None,
          "value3": None
        }
      )
      if res.status_code == 200:
        self.wfile.write("Sent POST to trigger IFTTT event: %s" % (config["maker"]))
    except:
      import traceback
      traceback.print_exc()


configobj = Config("fbwh.conf")
config = configobj.read_as_dict()
def run(server_class=HTTPServer, handler_class=fbhandler):
  server_address = (config["ip"], config["port"])
  httpd = server_class(server_address, handler_class)
  print "[+] Starting HTTP server (%s:%s) to trigger event %s" % (config["ip"] if config["ip"] and config["ip"] != "" else "0.0.0.0", config["port"], config["event"])
  httpd.serve_forever()


if __name__ == "__main__":
  run()

