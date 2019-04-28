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

import os
import sys
import json
import thread
import traceback
import subprocess
from urlparse import urlparse, parse_qs

import scale

##########################################################################

def fetch_data(_alias):
  response = {'error': 'exception'}
  try:
    if _alias:
      response = scale.start_measurement_script(measure_alias=_alias) # default scale, live measurings for alias
    else:
      response = scale.start_measurement_script() # default scale, no live measurings
  except:
    traceback.print_exc()
  return response

##########################################################################

def do_GET(self, storage):
  
  path = urlparse(self.path).path
  
  if path != '/favicon.ico':
    print path
  
  if path == '/download':
    os.system('sudo python cronjob.py')
    response = {
      'todo': 'output-result'
    }
    self.send_response(200)
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write(json.dumps(response, indent=2))
    return
  
  if path == '/fetch' or path == '/trigger':
    #-----------------------------------------------------
    _alias = None
    query_components = parse_qs(urlparse(self.path).query)
    if 'alias' in query_components:
      _temp_alias = query_components['alias'][0]
      print 'requesting alias', _temp_alias
      import users
      reload(users)
      for alias, uid in users.USER_MAPPING.items():
        if _temp_alias == alias:
          _alias = alias
      if not _alias:
        response = {
          'error': 'alias-does-not-exist'
        }
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2))
        return
    #-----------------------------------------------------
    try:
      reload(scale)
    except:
      traceback.print_exc()
      response = {
        'error': 'scale-script-import-exception'
      }
      self.send_response(200)
      self.send_header('Content-type', 'text/plain')
      self.end_headers()
      self.wfile.write(json.dumps(response, indent=2))
      return
    #-----------------------------------------------------
    if path == '/trigger': # some script could trigger this when an Amazon Dash button is pressed...
      thread.start_new_thread(fetch_data, (_alias,) )
      response = {
        'ok': 'triggered-script'
      }
    else:
      response = fetch_data(_alias)
    #-----------------------------------------------------
    self.send_response(200)
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write(json.dumps(response, indent=2))
    return
  else:
    self.send_response(200)
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write("nothing here at " + self.path)
    return

##########################################################################

