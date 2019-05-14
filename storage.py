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

import json
import copy
import datetime
import traceback

##################################################################################################################

def store_readout(readout):
  store_readout_to_file(readout)
  store_readout_to_database(readout)
  print 'done.'

##################################################################################################################

def store_readout_to_file(readout):
  measurements = []
  if 'measurements' in readout:
    measurements = copy.deepcopy(readout['measurements'])
  if 'measurement' in readout:
    measurements.append(copy.deepcopy(readout['measurement']))
  print 'storing measurements...'
  for measurement in measurements:
    with open('measurements-' + measurement['uid'] + '.json', 'a') as f:
      if 'scale' in readout and 'battery' in readout['scale']:
        # add the scale battery level to each measurement
        measurement['battery'] = readout['scale']['battery']
      f.write(json.dumps(measurement, sort_keys=True) + ',\n')

##################################################################################################################

def store_readout_to_database(readout):
  
  import users
  aliases = {}
  for alias, uid in users.USER_MAPPING.items():
    aliases[uid] = alias
  
  MONGODB_HOST = '123.123.123.123'
  MONGODB_PORT = 27017
  
  if MONGODB_HOST == '123.123.123.123':
    print 'the database connection must first be configured.'
    return
  
  import pymongo
  
  print 'connecting to database...'
  database = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT, appname='bt-scale')['bt-scale']
  
  print 'storing / updating users...'
  for user in copy.deepcopy(readout['users']):
    if user['uid'] in aliases:
      # add the alias to the user
      user['alias'] = aliases[user['uid']]
    # always overwrite the user data
    database['users'].update({'uid':user['uid']}, {"$set" : user}, upsert=True)
  
  print 'storing / updating measurements...'
  measurements = []
  if 'measurements' in readout:
    measurements = copy.deepcopy(readout['measurements'])
  if 'measurement' in readout:
    measurements.append(copy.deepcopy(readout['measurement']))
  for measurement in measurements:
    if 'scale' in readout and 'battery' in readout['scale']:
      # add the scale battery level to each measurement
      measurement['battery'] = readout['scale']['battery']
    if measurement['uid'] in aliases:
      # add the alias to each measurement
      measurement['alias'] = aliases[measurement['uid']]
    
    # overwrite time field with datetime object, we don't want
    # a string in the database, but an object we can aggregate upon
    measurement['time'] = datetime.datetime.utcfromtimestamp(measurement['timestamp'])
    
    database['measurements'].update({'uid':measurement['uid'], 'timestamp':measurement['timestamp']}, {"$set" : measurement}, upsert=True)

##################################################################################################################
