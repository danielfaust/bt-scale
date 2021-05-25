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

'''

You can always ctrl-c out of this script without causing any harm whatsoever

'''

import os
import sys
import json
import time
import pexpect
import datetime
import traceback
import collections

#===============================================
sys.dont_write_bytecode = True
#===============================================

# ensure that the current working directory is the one of this script.
# this is probably bad practice but it safeguards a lot of things.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

activity_levels = [ # only for reference, it's used nowhere in the code
  'sedentary', # 1 - no activity
  'mild',      # 2 - sitting activities, little and light physical effort (walking, light gardening, gymnastic exercises)
  'moderate',  # 3 - light activities, middle physical effort, at least 2-4 times a week for 30 minutes
  'heavy',     # 4 - heavy activities, high physical effort, at least 4-6 times a week for 30 minutes
  'extreme'    # 5 - extreme activities, extreme physical effort, at least 4-6 times a week for 30 minutes
]

##################################################################################

DO_CHECK_UNKNOWN = True
DO_SAVE_UNKNOWN = True
DO_DELETE_UNKNOWN = False
DO_DELETE_MEASUREMENTS = False

VERBOSE      = False
VERBOSE_COMM = True
LOG_PEXPECT  = False

##################################################################################

import users
DEFAULT_SCALE_MAC_ADDRESS = users.SCALE
DEFAULT_MEASURE_ALIAS = users.ALIAS

##################################################################################

def start_measurement_script(scale_mac_address=None, measure_alias=None):
  
  if scale_mac_address is None:
    scale_mac_address = DEFAULT_SCALE_MAC_ADDRESS
  
  if scale_mac_address == 'XX:XX:XX:XX:XX:XX':
    print 'there is no scale configured in users.py, exiting.'
    sys.exit(0)
  
  DO_MEASURE = True
  if measure_alias is None:
    measure_alias = DEFAULT_MEASURE_ALIAS
  if measure_alias is None:
    DO_MEASURE = False
  
  ##################################################################################
  
  USERS = users.USERS
  USER_MAPPING = users.USER_MAPPING
  
  aborting = False
  
  ##################################################################################
  
  #-------------------------------------------------------------
  
  def weight(data):
    return {'weight': int(data[-5:].replace(' ', ''), 16) / 20.0}
    
  #-------------------------------------------------------------
  
  def scale(data):
    # print data
    data = data.replace(' ', '')[6:]
    # print data
    
    offset = 0
    _users = int(data[offset:offset+2], 16)
    # print _users # != 0 if an invalid user id is given to the command
    
    offset = 2
    _battery = round(int(data[offset:offset+2], 16) / 255.0 * 100, 1)
    if VERBOSE: print ' - battery', _battery , '%'
    
    offset = 4
    _weight = int(data[offset:offset+2], 16) / 10.0
    if VERBOSE: print ' - weight threshold', _weight
    
    offset = 6
    _fat = int(data[offset:offset+2], 16) / 10.0
    if VERBOSE: print ' - fat threshold', _fat
    
    offset = 8
    _unit = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - unit', _unit # 1=kg, 2=lb, 4=st
    
    offset = 10
    _user_exist = int(data[offset:offset+2], 16)
    # print 'user exists', _user_exist
    
    offset = 12
    _user_ref_weight_exists = int(data[offset:offset+2], 16)
    # print 'user has reference weight', _user_ref_weight_exists
    
    offset = 14
    _user_measurement_exists = int(data[offset:offset+2], 16)
    # print 'user has measurements', _user_measurement_exists
  
    offset = 16
    _version = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - version', _version
  
    return collections.OrderedDict([
      ('battery',          _battery),
      #('weight-threshold', _weight),
      #('fat-threshold',    _fat),
      #('unit',             _unit),
      #('version',          _version),
    ])
  
  #-------------------------------------------------------------
  
  def user_list(data):
    # print data
    data = data.replace(' ', '')[6:]
    # print data
    
    offset = 2
    _users_count = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - user count', _users_count
    
    offset = 4
    _users_max = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - max users', _users_max
    
    return collections.OrderedDict([
      ('max',   _users_max),
      ('count', _users_count),
    ])
  
  #-------------------------------------------------------------
  
  def user(data):
    # print data
    data = data.replace(' ', '')[4:]
    # print data
    
    offset = 0
    _user_index = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - user index', _user_index
    offset = 2
    _users_count = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - max users', _users_count
  
    #e734010100000000000000655400004b
    
    offset = 4
    _user_id = data[offset:offset+16]
    if VERBOSE: print ' - user id hex', _user_id
  
    offset = 20
    _name_c1 = int(data[offset+0:offset+0+2], 16)
    _name_c2 = int(data[offset+2:offset+2+2], 16)
    _name_c3 = int(data[offset+4:offset+4+2], 16)
    _name = ((chr(_name_c1) if _name_c1 > 0 else '') + (chr(_name_c2) if _name_c2 > 0 else '') + (chr(_name_c3) if _name_c3 > 0 else '')).strip()
    if VERBOSE: print ' - name', _name
    
    offset = 26
    _year = 1900 + int(data[offset:offset+2], 16)
    if VERBOSE: print ' - year', _year
    
    return collections.OrderedDict([
      #('count', _users_count),
      #('index',  _user_index),
      ('uid',  _user_id),
      ('name', _name),
      ('year', _year),
    ])
  
  #-------------------------------------------------------------
  
  def user_detail(data):
    # print data
    data = data.replace(' ', '')[6:]
    # print data
    
    offset = 2
    _name_c1 = int(data[offset+0:offset+0+2], 16)
    _name_c2 = int(data[offset+2:offset+2+2], 16)
    _name_c3 = int(data[offset+4:offset+4+2], 16)
    _name = ((chr(_name_c1) if _name_c1 > 0 else '') + (chr(_name_c2) if _name_c2 > 0 else '') + (chr(_name_c3) if _name_c3 > 0 else '')).strip()
    if VERBOSE: print ' - name', _name
    
    offset = 8
    _year = 1900 + int(data[offset:offset+2], 16)
    if VERBOSE: print ' - year', _year
  
    offset = 10
    _month = 1 + int(data[offset:offset+2], 16)
    if VERBOSE: print ' - month', _month
  
    offset = 12
    _day = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - day', _day
    
    _birthday = str(datetime.date(_year, _month, _day))
  
    offset = 14
    _height = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - height', _height
  
    offset = 16
    _male = int(data[offset:offset+1], 16) != 0
    if VERBOSE: print ' - male', _male
  
    offset = 17
    _activity = int(data[offset:offset+1], 16)
    if VERBOSE: print ' - activity', _activity
    
    return collections.OrderedDict([
      ('name',      _name),
      ('birthday',  _birthday),
      ('height',    _height),
      ('gender',    'male' if _male else 'female'),
      ('activity',  _activity),
    ])
  
  #-------------------------------------------------------------
  
  def unknown_measurement(data):
    # print data
    data = data[12:].replace(' ', '')
    # print data
    
    offset = 0
    _slot = int(data[offset:offset+2], 16)
    if VERBOSE: print ' - slot', _slot
    
    offset = 2
    _timestamp = int(data[offset:offset+8], 16)
    _time = datetime.datetime.fromtimestamp(_timestamp).isoformat()
    if VERBOSE: print 'time', datetime.datetime.fromtimestamp(_time).isoformat()
    
    offset = 10
    _weight = int(data[offset:offset+4], 16) / 20.0 # -> * 50.0 / 1000.0, unit is 50g
    if VERBOSE: print ' - weight', _weight, 'kg'
    
    offset = 14
    _impedance = int(data[offset:offset+4], 16)
    if VERBOSE: print ' - impedance', _impedance
    
    return collections.OrderedDict([
      ('timestamp', _timestamp),
      ('time',      _time),
      ('weight',    _weight),
      ('impedance', _impedance),
      ('slot', _slot),
    ])
    
  #-------------------------------------------------------------
  
  def measurement(data):
    # print data
    data = (data[0][12:] + ' ' +data[1][12:]).replace(' ', '')
    # print data
    
    offset = 0
    _timestamp = int(data[offset:offset+8], 16)
    _time = datetime.datetime.fromtimestamp(_timestamp).isoformat()
    if VERBOSE: print ' - time', _time
    
    offset = 8
    _weight = int(data[offset:offset+4], 16) / 20.0 # -> * 50.0 / 1000.0, unit is 50g
    if VERBOSE: print ' - weight', _weight, 'kg'
    
    offset = 12
    _impedance = int(data[offset:offset+4], 16)
    if VERBOSE: print ' - impedance', _impedance
  
    offset = 16
    _fat = int(data[offset:offset+4], 16) / 10.0
    if VERBOSE: print ' - fat', _fat, '%'
    
    offset = 20
    _water = int(data[offset:offset+4], 16) / 10.0
    if VERBOSE: print ' - water', _water, '%'
  
    offset = 24
    _muscle = int(data[offset:offset+4], 16) / 10.0
    if VERBOSE: print ' - muscle', _muscle, '%'
    
    offset = 28
    _bone = int(data[offset:offset+4], 16) / 20.0
    if VERBOSE: print ' - bone', _bone, 'kg'
    
    offset = 32
    _bmr = int(data[offset:offset+4], 16)
    if VERBOSE: print ' - bmr', _bmr, 'kcal'
    
    offset = 36
    _amr = int(data[offset:offset+4], 16)
    if VERBOSE: print ' - amr', _amr, 'kcal'
    
    offset = 40
    _bmi = int(data[offset:offset+4], 16) / 10.0
    if VERBOSE: print ' - bmi', _bmi
  
    return collections.OrderedDict([
      ('timestamp', _timestamp),
      ('time',      _time),
      ('weight',    _weight),
      ('impedance', _impedance),
      ('fat',       _fat),
      ('water',     _water),
      ('muscle',    _muscle),
      ('bone',      _bone),
      ('bmr',       _bmr),
      ('amr',       _amr),
      ('bmi',       _bmi),
    ])
    
  #-------------------------------------------------------------
  
  def compile_user(user):
    
    _uid  = user['uid']
    if VERBOSE: print 'uid', _uid
    
    _name = user['name']
    _name_0 = '{:02x}'.format(ord(_name[0]))
    _name_1 = '00'
    _name_2 = '00'
    if len(_name) > 1:
      _name_1 = '{:02x}'.format(ord(_name[1]))
    if len(_name) > 2:
      _name_2 = '{:02x}'.format(ord(_name[2]))
    _name_123 = _name_0 + ' ' + _name_1 + ' ' + _name_2
    if VERBOSE: print 'name_123', _name_123
    
    _birthday = user['birthday']
    _year = '{:02x}'.format(int(_birthday[0:4]) - 1900)
    _month = '{:02x}'.format(int(_birthday[5:7]) - 1)
    _day = '{:02x}'.format(int(_birthday[8:10]))
    _ymd = _year + ' ' + _month + ' ' + _day
    if VERBOSE: print 'ymd', _ymd
  
    _height = '{:02x}'.format(user['height'])
    if VERBOSE: print 'height', _height
  
    _gender = '8' if user['gender'] == 'male' else '0'
    if VERBOSE: print 'gender', _gender
    
    _activity = '{:1x}'.format(user['activity'])
    if VERBOSE: print 'activity', _activity
    
    _user_hex = (_uid + _name_123 + _ymd + _height + _gender + _activity).upper()
    if VERBOSE: print 'user_hex', _user_hex
    
    return _user_hex
  
  ##################################################################################
  
  def read_line(child, token='0x002e value: ', timeout=4, include_active=False):
    line = ''
    abort = False
    try:
      child.expect(token, timeout=timeout)
      line = child.readline().strip()
    except pexpect.exceptions.TIMEOUT:
      return ''
    if include_active:
      return line
    else:
      while True:
        if line.startswith('e7 58'):
          abort = True
          try:
            if VERBOSE_COMM: print 'ignoring active measurement', line, '->', weight(line)['weight']
            child.expect("0x002e value: ", timeout=4)
            line = child.readline().strip()
          except pexpect.exceptions.TIMEOUT:
            line = ''
            break
        else:
          break
    return line
  
  def check_status(status, message):
    if not status:
      print ''
      print 'unable to get '+message+' status, will exit now. (TODO: implement retry)'
      print ''
      sys.exit(1)
  
  ##################################################################################
  
  messages = []
  readout = collections.OrderedDict()
  
  child = pexpect.spawn('gatttool -I -b ' + scale_mac_address)
  if LOG_PEXPECT: child.logfile = open("pexpect.log.txt", "w")
  child.sendline('connect')
  try:
    
    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    child.expect('Attempting to connect to ' + scale_mac_address, timeout=4)
    print 'connecting...'
    connection_status = read_line(child, token='(Connection|connect) ', timeout=4)
    print 'connection_status -> ' + connection_status
    if not connection_status:
      if VERBOSE_COMM: print 'timed out, could not connect. exiting.'
      return {'sys-exit': 'timeout-while-connecting'}
    elif 'error' in connection_status:
      if VERBOSE_COMM: print 'could not connect. exiting.'
      return {'sys-exit': 'error-while-connecting'}
    #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    
    WRITE_REQ = 'char-write-req 0x002e '
    
    ###################################################
    # ANNOUNCE TO SCALE
    ###################################################
    
    print ''
    print '---------------------------------------------'
    if VERBOSE_COMM: print 'init?'
    cmd = WRITE_REQ + 'E6 01'.replace(' ', '')
    if VERBOSE_COMM: print cmd
    child.sendline(cmd)
    child.expect("0x002e value: e6 00 20", timeout=4)
    if VERBOSE_COMM: print 'init.'
    
    ###################################################
    # SET TIMESTAMP ON SCALE
    ###################################################
    
    readout['timestamp'] = int(time.time())
    if VERBOSE_COMM: print ''
    if VERBOSE_COMM: print '---------------------------------------------'
    if VERBOSE_COMM: print 'set scale time'
    cmd = WRITE_REQ + 'E9 {:X}'.format(readout['timestamp']).replace(' ', '')
    if VERBOSE_COMM: print cmd
    child.sendline(cmd)
    
    ###################################################
    # GET SCALE STATUS
    ###################################################
    
    if VERBOSE_COMM: print ''
    if VERBOSE_COMM: print '---------------------------------------------'
    if VERBOSE_COMM: print 'get scale status'
    cmd = WRITE_REQ + 'E7 4F 00 00 00 00 00 00 00 00'.replace(' ', '')
    if VERBOSE_COMM: print cmd
    child.sendline(cmd)
    scale_status = read_line(child)
    check_status(scale_status, 'scale')
    if VERBOSE_COMM: print 'scale status -> ' + scale_status
    scale_status = scale(scale_status)
    if VERBOSE_COMM: print json.dumps(scale_status, indent=2)
    readout['scale'] = scale_status
    
    ###################################################
    # GET USER LIST
    ###################################################
    
    if VERBOSE_COMM: print ''
    if VERBOSE_COMM: print '---------------------------------------------'
    if VERBOSE_COMM: print 'get user list'
    cmd = WRITE_REQ + 'E7 33'.replace(' ', '')
    if VERBOSE_COMM: print cmd
    child.sendline(cmd)
    userlist_status = read_line(child)
    check_status(userlist_status, 'userlist')
    if VERBOSE_COMM: print 'userlist status -> ' + userlist_status
    userlist_status = user_list(userlist_status)
    if VERBOSE_COMM: print json.dumps(userlist_status, indent=2)
    #-----------------------------------------
    userlist_count = userlist_status['count']
    if userlist_count > 0:
      #-----------------------------------------
      readout['users'] = []
      for i in range(userlist_count):
        if VERBOSE_COMM: print '-------'
        user_status = read_line(child)
        check_status(user_status, 'user')
        if VERBOSE_COMM: print 'user status -> ' + user_status
        user_status = user(user_status)
        if VERBOSE_COMM: print json.dumps(user_status, indent=2)
        readout['users'].append(user_status)
        #-----------------------------------------
        if VERBOSE_COMM: print 'user ack data'
        cmd = WRITE_REQ + ('E7 F1 34 ' + '{:02x}'.format(userlist_count) + '{:02x}'.format(i+1)).replace(' ', '')
        if VERBOSE_COMM: print cmd
        child.sendline(cmd)
    
    ###################################################
    # GET USER DETAILS
    ###################################################

    if 'users' in readout:
      for user in readout['users']:
        
        _current_user_id = user['uid']
        
        #-----------------------------------------
        if VERBOSE_COMM: print ''
        if VERBOSE_COMM: print '---------------------------------------------'
        if VERBOSE_COMM: print 'get user details for ' + user['name']
        cmd = WRITE_REQ + ('E7 36 ' + _current_user_id).replace(' ', '')
        if VERBOSE_COMM: print cmd
        child.sendline(cmd)
        user_detail_status = read_line(child)
        check_status(user_detail_status, 'user detail')
        if VERBOSE_COMM: print 'user detail status -> ' + user_detail_status
        user_detail_status = user_detail(user_detail_status)
        user_detail_status['uid'] = _current_user_id
        if VERBOSE_COMM: print json.dumps(user_detail_status, indent=2)
        for key, value in user_detail_status.items():
          if key not in ['name', 'uid']:
            user[key] = value
        del user['year']
    
    ###################################################
    # PARTITION USERS
    ###################################################
    
    users_in_scale_but_not_in_file = []
    users_in_file_but_not_in_scale = []
    users_in_file_and_in_scale = {}
    
    if 'users' in readout:
      for scale_user in readout['users']:
        scale_user_in_file = False
        for file_user in USERS:
          if file_user['uid'] == scale_user['uid']:
            scale_user_in_file = True
            users_in_file_and_in_scale[file_user['uid']] = (file_user, scale_user)
        if not scale_user_in_file:
          users_in_scale_but_not_in_file.append(scale_user)
    for file_user in USERS:
      if file_user['uid'] not in users_in_file_and_in_scale:
        users_in_file_but_not_in_scale.append(file_user)
    
    ###################################################
    # USERS IN SCALE BUT NOT IN FILE
    ###################################################
    if len(users_in_scale_but_not_in_file):
      print ''
      print '---------------------------------------------'
      print 'users in scale but not in file'
      for user in users_in_scale_but_not_in_file:
        print ''
        print 'THE USER WITH THE FOLLOWING DATA IS NOT FOUND IN THE SCALE'
        print ''
        print json.dumps(user, indent=2, sort_keys=True)
        print ''
        print 'DO YOU WANT TO DELETE THE USER FROM THE SCALE?'
        print ''
        answer = raw_input("Type 'YES' (exactly as shown) to DELETE the user\nfrom the scale or press ENTER to leave it there: ")
        if answer == 'YES':
          ###################################################
          # DELETE USER
          ###################################################
          print ''
          print 'DELETING USER'
          print ''
          cmd = WRITE_REQ + ('E7 32 ' + user['uid']).replace(' ', '')
          if VERBOSE_COMM: print cmd
          child.sendline(cmd)
          child.expect("0x002e value: e7 f0 32 00", timeout=4)
          print 'user deleted'
          print ''
          print 'OK, the user has been deleted from the scale.'
          print ''
          print 'Will exit now so that you can think about it.'
          print ''
          return {'sys-exit': 'user-deleted-please-review'}
        else:
          print ''
          print 'OK, NOT DELETED! You should manually add the following\ninformation to the users.py file.'
          print ''
          print json.dumps(user, indent=2, sort_keys=True)
          print ''
          print 'will exit now, so you can add the user to the file.'
          print ''
          return {'sys-exit': 'user-not-deleted-please-review'}
      
    ###################################################
    # USERS IN FILE BUT NOT IN SCALE
    ###################################################
    if len(users_in_file_but_not_in_scale):
      print ''
      print '---------------------------------------------'
      print 'users in file but not in scale'
      for user in users_in_file_but_not_in_scale:
        print ''
        print 'WILL NOW STORE THIS TO THE SCALE:'
        print ''
        print json.dumps(user, indent=2, sort_keys=True)
        print ''
        ###################################################
        # UPLOAD USER TO SCALE
        ###################################################
        _user_hex = compile_user(user)
        cmd = WRITE_REQ + ('E7 31 ' + _user_hex).replace(' ', '')
        if VERBOSE_COMM: print cmd
        child.sendline(cmd)
        child.expect("0x002e value: e7 f0 31 00", timeout=4)
        print 'user added'
        print ''
        print 'OK, the new user which was in the file has now been uploaded to the scale.'
        print ''
        print 'Will exit now so that you can think about it.'
        print ''
        return {'sys-exit': 'user-added-please-review'}
    
    ###################################################
    # USERS IN FILE AND IN SCALE
    ###################################################
    if len(users_in_file_and_in_scale):
      print ''
      print '---------------------------------------------'
      print 'users in file and in scale'
      for user_id in users_in_file_and_in_scale:
        print '-----'
        data_in_file  = json.dumps(users_in_file_and_in_scale[user_id][0], sort_keys=True)
        data_in_scale = json.dumps(users_in_file_and_in_scale[user_id][1], sort_keys=True)
        if data_in_file == data_in_scale:
          print 'user details in file match those in the scale for uid', user_id
        else:
          print ''
          print 'USER DETAILS IN FILE DIFFER FROM THOSE IN SCALE FOR UID', user_id
          print ''
          print ' -  file:', data_in_file
          print ' - scale:', data_in_scale
          print ''
          print 'DO YOU WANT TO SAVE DETAILS FROM THE FILE TO THE SCALE?'
          print ''
          answer = raw_input("Type 'YES' (exactly as shown) to UPDATE the user\nfrom the scale or press ENTER to leave it there: ")
          if answer == 'YES':
            _user_hex = compile_user(users_in_file_and_in_scale[user_id][0])
            cmd = WRITE_REQ + ('E7 35 ' + _user_hex).replace(' ', '')
            if VERBOSE_COMM: print cmd
            child.sendline(cmd)
            child.expect("0x002e value: e7 f0 35 00", timeout=4)
            print 'user updated'
            print ''
            print 'OK, the existing user which had different information in the file has now been uploaded to the scale.'
            print ''
            print 'Will exit now so that you can think about it.'
            print ''
            return {'sys-exit': 'user-updated-please-review'}
          else:
            print ''
            print 'OK, NOT UPDATED! You should manually adjust the following\ninformation in the users.py file.'
            print ''
            print 'FROM'
            print json.dumps(users_in_file_and_in_scale[user_id][0], indent=2, sort_keys=True)
            print ''
            print 'TO'
            print json.dumps(users_in_file_and_in_scale[user_id][1], indent=2, sort_keys=True)
            print ''
            print 'will exit now, so you can edit the user in the file.'
            print ''
            return {'sys-exit': 'user-differs-please-review'}
    
    ###################################################
    # READ STORED MESSAGES FOR UNKNOWN USERS
    ###################################################
    
    if DO_CHECK_UNKNOWN:
      
      unknown_measurements = []
      
      #-----------------------------------------
      if VERBOSE_COMM: print ''
      if VERBOSE_COMM: print '---------------------------------------------'
      if VERBOSE_COMM: print 'request unknown measurements'
      cmd = WRITE_REQ + ('E7 46').replace(' ', '')
      if VERBOSE_COMM: print cmd
      child.sendline(cmd)
      measurements_status = read_line(child)
      check_status(measurements_status, 'measurements')
      if VERBOSE_COMM: print 'measurements_status', measurements_status
      
      if measurements_status == 'e7 f0 46 00': # scale responds with 'e7 f0 46 01' if there are none
        
        while True:
          unknown_measurement_status = read_line(child)
          check_status(unknown_measurement_status, 'measurements')
          if VERBOSE_COMM: print 'unknown_measurement_status', unknown_measurement_status
          _total_measurements = unknown_measurement_status[6:8]
          _current_measurement = unknown_measurement_status[9:11]
          unknown_measurement_status = unknown_measurement(unknown_measurement_status)
          unknown_measurements.append(unknown_measurement_status)
          if VERBOSE_COMM: print json.dumps(unknown_measurement_status, indent=2)
          cmd = WRITE_REQ + 'E7 F1 47'.replace(' ', '') + _total_measurements + _current_measurement
          if VERBOSE_COMM: print cmd
          child.sendline(cmd)
          if _total_measurements == _current_measurement:
            break
        
        if DO_SAVE_UNKNOWN:
          _time = datetime.datetime.fromtimestamp(readout['timestamp']).isoformat().replace(':', ';')
          with open('unknown-measurements-'+_time+'.json', 'w') as f:
            f.write(json.dumps(unknown_measurements, indent=2))
        
        if DO_DELETE_UNKNOWN:
          for unknown_measurement in unknown_measurements:
            if VERBOSE_COMM: print 'delete unknown measurement from slot ', unknown_measurement['slot']
            cmd = WRITE_REQ + ('E7 49 ' + '{:02x}'.format(unknown_measurement['slot'])).replace(' ', '')
            if VERBOSE_COMM: print cmd
            child.sendline(cmd)
            delete_unknown_measurement_status = read_line(child)
            check_status(delete_unknown_measurement_status, 'measurements')
            if VERBOSE_COMM: print 'delete_unknown_measurement_status', delete_unknown_measurement_status
    
    ###################################################
    # READ STORED MESSAGES FOR KNOWN USERS
    ###################################################

    if 'users' in readout:

      for user in readout['users']:
        
        _current_user_id = user['uid']
        
        #-----------------------------------------
        if VERBOSE_COMM: print ''
        if VERBOSE_COMM: print '---------------------------------------------'
        if VERBOSE_COMM: print 'request saved measurements for ' + user['name']
        cmd = WRITE_REQ + ('E7 41 ' + _current_user_id).replace(' ', '')
        if VERBOSE_COMM: print cmd
        child.sendline(cmd)
        measurements_status = read_line(child)
        check_status(measurements_status, 'measurements')
        measurements_count = int(measurements_status[9:11], 16)
        if VERBOSE_COMM: print 'measurements status -> ' + measurements_status, '->', measurements_count/2, 'stored measurements'
        if measurements_count > 0:
          #-----------------------------------------
          readout['measurements'] = []
          data = []
          for i in range(measurements_count):
            measurement_status = read_line(child)
            check_status(measurement_status, 'measurement')
            if VERBOSE_COMM: print 'measurement', i+1, measurement_status
            if i % 2 == 0:
              data.append(measurement_status)
            if i % 2 == 1:
              data.append(measurement_status)
              data = measurement(data)
              data['uid'] = _current_user_id
              if VERBOSE_COMM: print json.dumps(data, indent=2)
              readout['measurements'].append(data)
              data = []
            cmd = WRITE_REQ + 'E7 F1 42 {:02X} {:02X}'.format(measurements_count, i+1).replace(' ', '')
            if VERBOSE_COMM: print cmd
            child.sendline(cmd)
          #-----------------------------------------
          if DO_DELETE_MEASUREMENTS:
            if VERBOSE_COMM: print 'delete saved measurements for ' + user['name']
            cmd = WRITE_REQ + ('E7 43 ' + _current_user_id).replace(' ', '')
            if VERBOSE_COMM: print cmd
            child.sendline(cmd)
            child.expect("0x002e value: e7 f0 43 00", timeout=4)
            if VERBOSE_COMM: print 'deletion ok'
    
    ###################################################
    # START MEASURING
    ###################################################
      
    if DO_MEASURE:
      
      _measure_user_id = None
      if measure_alias in USER_MAPPING:
        _measure_user_id = USER_MAPPING[measure_alias]
      
      if not _measure_user_id or _measure_user_id not in users_in_file_and_in_scale:
        print ''
        print 'EXITING, USER', measure_alias, 'IS NOT PROPERLY SET UP, SO NO MEASUREMENTS WILL BE DONE'
        print ''
        return {'sys-exit': 'user-not-set-up-please-review'}
      
      messages.append('measuring begins after ' + str(round(time.time() - readout['timestamp'], 3)) + ' seconds')
      
      #-----------------------------------------
      if VERBOSE_COMM: print ''
      if VERBOSE_COMM: print '---------------------------------------------'
      if VERBOSE_COMM: print 'do a measurement for', measure_alias
      cmd = WRITE_REQ + ('E7 40 ' + _measure_user_id).replace(' ', '')
      if VERBOSE_COMM: print cmd
      child.sendline(cmd)
      child.expect("0x002e value: e7 f0 40 00", timeout=4)
      print ''
      print 'waiting for live measurement data, timeout in 5 seconds...'
      print ''
      measurement_timeout = 5
      while True:
        try:
          measurement_status = read_line(child, token="0x002e value: ", timeout=measurement_timeout, include_active=True)
          if measurement_status == '':
            print 'timed out during live measurement.'
            break
          elif measurement_status.startswith('e7 58 01'):
            _weight = weight(measurement_status)
            print 'ACTIVE', measurement_status, '->', _weight['weight']
            if 'measurement-weights' not in readout:
              readout['measurement-weights'] = []
            readout['measurement-weights'].append(_weight['weight'])
          elif measurement_status.startswith('e7 58 00'):
            _weight = weight(measurement_status)
            print 'FINAL', measurement_status, '->', _weight['weight']
            readout['measurement-weight'] = _weight['weight']
            if measurement_timeout != 10:
              if VERBOSE_COMM: print 'incrementing timeout to 10 seconds for approaching summary readout'
              measurement_timeout = 10
          elif measurement_status.startswith('e7 59'):
            _measured_user_id = measurement_status.replace(' ', '')[-16:]
            data = []
            if VERBOSE_COMM: print 'SUMMARY', measurement_status
            #-----------------------------------------
            if VERBOSE_COMM: print 'ack part 1/3 of summary'
            cmd = WRITE_REQ + 'E7 F1 59 03 01'.replace(' ', '')
            if VERBOSE_COMM: print cmd
            child.sendline(cmd)
            summary_2_status = read_line(child)
            if VERBOSE_COMM: print 'summary_2_status', summary_2_status
            data.append(summary_2_status)
            #-----------------------------------------
            if VERBOSE_COMM: print 'ack part 2/3 of summary'
            cmd = WRITE_REQ + 'E7 F1 59 03 02'.replace(' ', '')
            if VERBOSE_COMM: print cmd
            child.sendline(cmd)
            summary_3_status = read_line(child)
            if VERBOSE_COMM: print 'summary_3_status', summary_3_status
            data.append(summary_3_status)
            data = measurement(data)
            data['uid'] = _measured_user_id
            data['uid-check'] = _measure_user_id # can also serve as an indicator that it was a live measurement
            if VERBOSE_COMM: print json.dumps(data, indent=2)
            readout['measurement'] = data
            #-----------------------------------------
            if VERBOSE_COMM: print 'ack part 3/3 of summary'
            cmd = WRITE_REQ + 'E7 F1 59 03 03'.replace(' ', '')
            if VERBOSE_COMM: print cmd
            child.sendline(cmd)
            #-----------------------------------------
            if DO_DELETE_MEASUREMENTS:
              if VERBOSE_COMM: print 'delete saved measurements for', measure_alias
              cmd = WRITE_REQ + ('E7 43 ' + _measured_user_id).replace(' ', '')
              if VERBOSE_COMM: print cmd
              child.sendline(cmd)
              child.expect("0x002e value: e7 f0 43 00", timeout=4)
              print 'deletion ok'
            break
        except:
          print ''
          print '---------------------------------------------'
          traceback.print_exc()
          print ''
          break
    
    ###################################################
    # DONE, MAYBE CHECK IF THERE IS STILL SIME DATA IN THE AIR
    ###################################################
      
    if False:
      if VERBOSE_COMM: print ''
      if VERBOSE_COMM: print '---------------------------------------------'
      if VERBOSE_COMM: print 'something else?'
      something_status = read_line(child, token="0x002e value: ", timeout=3)
      if something_status == '':
        print 'nope.'
      else:
        print 'yes', something_status
    
    ###################################################
    # DISCONNECT
    ###################################################
    
    child.sendline('disconnect')
    print ''
    print '---------------------------------------------'
    print 'disconnected'
    
    ###################################################
    # FINISHED
    ###################################################
    
  except SystemExit as e:
    aborting = True
  except KeyboardInterrupt as e:
    print '\nkeyboard interrupt. exiting.'
    aborting = True
  except:
    print ''
    print '---------------------------------------------'
    traceback.print_exc()
    print ''
  
  if not aborting and 'timestamp' in readout:
  
    if 'users' in readout or 'measurements' in readout or 'measurement-weights' in readout:
      
      print ''
      print '---------------------------------------------'
      print ''
      print json.dumps(readout, indent=2)
      print ''
      print '---------------------------------------------'
      print ''
      
      #----------------------------------------------------
      import storage
      storage.store_readout(readout)
      #----------------------------------------------------
        
    for message in messages:
      print ''
      print message
    
    print ''
    print 'all done in script.py in', round(time.time() - readout['timestamp'], 3), 'seconds'
    print ''
    
    return readout
  
  return {'sys-exit': 'problem-while-gathering-data'}
  
if __name__== "__main__":
  start_measurement_script()
