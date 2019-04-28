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
import time
import datetime
import subprocess

#===============================================
sys.dont_write_bytecode = True
#===============================================

print ''
print '----------------------------------------------'
print 'cronjob.py started running at', datetime.datetime.now().isoformat()
sys.stdout.flush()

# ensure that the current working directory is the one of this script.
# this is probably bad practice but it safeguards a lot of things.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import users
mac = users.SCALE
uid = None
if len(users.USERS) > 0:
  uid = users.USERS[0]['uid'] # any user can be used in order to wake up the scale

if mac == 'XX:XX:XX:XX:XX:XX':
  print 'there is no scale configured in users.py, exiting.'
  sys.exit(0)

if uid is None:
  print 'there is no user configured in users.py, exiting.'
  sys.exit(0)

failure_counter = 0

while True:
  try:
    print '----------------------------------------------'
    print ''
    sys.stdout.flush()
    result = subprocess.check_output(["sudo", "./bt-scale", "-mac=" + mac, "-uid=" + uid, "-stderr=true"], stderr=sys.stdout, universal_newlines=True).strip()
    print result
    if result == 'disconnected, measurement trigger succeeded':
      try:
        print ''
        print '----------------------------------------------'
        print 'will start running scale.py in 5 seconds'
        time.sleep(5)
        import scale
        response = scale.start_measurement_script()
        json.dumps(response, indent=2)
        break
      except:
        failure_counter += 1
        print 'connection or readout failed, will retry in 5 seconds.', failure_counter, 'attempts were made.'
        if failure_counter == 5: # this is probably a real problem, just terminate the script.
          sys.exit(0)
        time.sleep(5)
  except:
    print 'this failure is too complex to handle, this needs manual intervention.'
    sys.exit(0)
