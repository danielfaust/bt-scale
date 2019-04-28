# -*- coding: utf-8 -*-

# 好

'''
 * This file is part of BT-Scale (https://github.com/danielfaust/bt-scale).
 * Copyright (c) 2019 Daniel Faust.
 * 
 * This program is free software: you can redistribute it and/or modify  
 * it under the terms of the GNU General Public License as published by  
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but 
 * WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License 
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import json
import traceback

#===============================================
sys.dont_write_bytecode = True
#===============================================

# ensure that the current working directory is the one of this script.
# this is probably bad practice but it safeguards a lot of things.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SERVER_PORT = 8088

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

storage = {}

class ScaleServer(BaseHTTPRequestHandler):
  
  def log_message(self, format, *args):
    return
    
  def do_GET(self):    
    try:
      import server_handler
      reload(server_handler)
      return server_handler.do_GET(self, storage)
    except:
      traceback.print_exc()
      self.send_response(200)
      self.send_header('Content-type', 'text/plain')
      self.end_headers()
      response = {
        'error': 'exception-in-server_handler'
      }
      self.wfile.write(json.dumps(response, indent=2))

httpd = HTTPServer(('0.0.0.0', SERVER_PORT), ScaleServer)
print 'Starting server on port', SERVER_PORT, '...'
httpd.serve_forever()
