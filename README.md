# BT-Scale



A Python 2.7 script for the Sanitas SBF70 / Silvercrest SBF75 / Beurer BF700 / BF710 / BF800 / Runtastic Libra diagnostic scales.



**scale.py**

```python
DEFAULT_SCALE_MAC_ADDRESS = users.SCALE # the users.py file contains the mac address
DEFAULT_MEASURE_ALIAS = users.ALIAS # DOWNLOAD DATA FROM THE SCALE AND PERFORM A LIVE MEASURING FOR THIS ALIAS
DEFAULT_MEASURE_ALIAS = None # DO NOT PERFORM A LIVE MEASURING, ONLY DOWNLOAD DATA FROM THE SCALE

# very safe and informative defaults
DO_CHECK_UNKNOWN = True
DO_SAVE_UNKNOWN = True
DO_DELETE_UNKNOWN = False
DO_DELETE_MEASUREMENTS = False

VERBOSE      = False # way too verbose
VERBOSE_COMM = True
LOG_PEXPECT  = False # may be helpful with debugging
```



The script *scale.py* can be executed directly via `python scale.py`. Before you do this, you need to adjust the default Bluetooth LE address of the scale. You can find this `mac address` with the bundled executable `bt-scale` or any smartphone ble-scanner like <https://play.google.com/store/apps/details?id=com.macdom.ble.blescanner>



Initially it is highly recommended to leave `DEFAULT_MEASURE_ALIAS` set to `None`. This means that the script will not start a live measurement, but only fetch data from the scale, or adjust user properties.



A successful readout would result in the following information:

```JSON
{
  "timestamp": 1556305150, 
  "scale": {
    "battery": 37.6
  }, 
  "users": [
    {
      "uid": "0000000000001234", 
      "name": "T", 
      "birthday": "1999-01-23", 
      "height": 123, 
      "gender": "male", 
      "activity": 3
    }
  ], 
  "measurements": [
    {
      "timestamp": 1556305134, 
      "time": "2019-04-26T20:58:54", 
      "weight": 12.34, 
      "impedance": 123, 
      "fat": 12.3, 
      "water": 12.3, 
      "muscle": 12.3, 
      "bone": 12.3, 
      "bmr": 1234, 
      "amr": 1234, 
      "bmi": 12.3, 
      "uid": "0000000000001234"
    }
  ]
}
```



If it were a live measurement, then `measurement-weight` with the stable weight and `measurement-weights` with an array of all the weights leading to the stable weight would also be found in this `JSON` object, as well as a `measurement` object containing the data of the live measurement. Maybe those live weight readings could be live-streamed via MQTT to a smartwatch or something for live monitoring.



All the `time` fields contain the *localized* ISO format (the default locale of the machine that runs the script). This is primarily meant for debugging, to see the time at a glance without needing to consider TZOs. The `timestamp` is the UTC Unix timestamp.



<u>Live measurements</u>

You should generally avoid using live measurement, because it is far more efficient to just stand on the scale and let the scale store the measurement in its internal storage, and the next time the script runs it will download all the measurements. The scale needs to be manually woken up so that the script can connect to it, I think that this is a problem with `gatttool`, which this script makes use of. If you step on the scale and do a measurement, without this script, then the scale stays awake for about 15 seconds, which is a good time to start this script.



Live measurements do no harm, but can be problematic. If you want to perform a live measurement, then you need to define the `alias`  on which this measurement will be made. This alias then **must** be in the *users.py* file in the USER_MAPPING and the corresponding `uid` in the USERS list. There are safeguards built into the script if an alias cannot be resolved to a USERS list entry. It then simply does not start a live measurement, but only behave as if it were `None`



The main problem with live measurements is that you need to know when to stand on the scale. If you stand on the scale while any other commands are being executed (like get the scale status, download stored measurements), then the scale aborts those commands and starts issuing weight measuring notifications. In that case, the command would need to get replayed, but this script doesn't handle this (apparently smartphone apps also don't handle this). So you either need to keep an eye on the script, which tells you when you can step on the scale, or watch the bottom left corner of the scale for your (up-to-)three-letter username to appear on the scale. It's hard to read on the scale. So it's best to leave live measurements deactivated and trigger the script right after the bubbles on the scale display have moved to the right, just when the summary shows up. During this entire time, while the summary shows, the script can connect without problems to the scale and download the fresh measurement.



***Note:*** *You may not be able to avoid live measurements if the scale has problems in discerning automatically between users because they have similar weight and body fat characteristics.* There are ways to tweak the weight and body fat sensitivity on the scale, but this script has no commands for it.



<u>Deletion of measurements</u>

The script needs to explicitly tell the scale to delete the measurements that are stored on the scale. By default the script won't do this, all new measurements are added to the scale's internal storage.  If you want the script to delete any downloaded measurements, just set  `DO_DELETE_MEASUREMENTS` to `True`. You may not want to do this if you want to use this script in parallel with an app. *In that case first let this script download the data, and later connect with the app and have it download and delete the data from the scale.*



<u>Unknown measurements</u>

The scale may have measurements stored on it where it does not know to which user they belong, probably because the weight- and fat-threshold in the scale couldn't find a corresponding match. These are stored on the scale as unknown measurements. If such measurements are found on the scale, they will be downloaded and stored into a `JSON` file, each time they are encountered. If you set `DO_DELETE_UNKNOWN` to `True`, then these unknown entries will be deleted from the scale after they have been saved into a file. These unknown measurements have limited information stored in them, namely the timestamp, the weight and the impedance. If you would use a smartphone app to assign these unknown measurements to a given user on the scale, these would probably get computed on the scale to form true measurements, with all the complete information a normal measurement contains. This script does not handle these assignments.



If you don't want to get bugged by these newly created files of unknown measurements, set `DO_SAVE_UNKNOWN` to `False` or set `DO_CHECK_UNKNOWN` to `False` to disable all unknown-measurements related stuff until you have decided what to do. Setting `DO_CHECK_UNKNOWN` to `False` speeds up the script, if you intend to ignore the unknown measurements. Currently this data is just dumped into the `JSON` file, it does not add this information to the response object.



These files would look like this *unknown-measurements-2019-04-26T11;24;55.json* file: 

```JSON
[
  {
    "timestamp": 1556099468, 
    "time": "2019-04-24T11:51:08", 
    "weight": 12.3,
    "impedance": 123
  }, 
  {
    "timestamp": 1556267316, 
    "time": "2019-04-26T10:28:36", 
    "weight": 12.3,
    "impedance": 0
  }
]
```

You could calculate all the other parameters with this information, if you know the user's age, height, gender and activity properties; you'd have to guess to which user these measurements belong to.



**users.py**

```python
SCALE = 'XX:XX:XX:XX:XX:XX'  # mac address of the scale
ALIAS = 'somebody' # default alias to use

USER_MAPPING = {
  "somebody": "0000000000001234", # map alias somebody to uid 0000000000001234
}

USERS = [ # this data is also stored on the scale
  {
    "name": "XY",     # 1 to 3 UPPERCASE LETTERS!
    "birthday": "1999-01-23",
    "height": 123,    # cm or foot, depending on scale setting
    "gender": "male", # or "female", depending on the body
    "activity": 3,    # see list in scale.py
    "uid": "0000000000001234" # MUST BE 16 hexadecimal characters!
  },
]
```



<u>User Management</u>

1. The `uid`  of the user is what defines the user. Any other parameter that gets changed in the file will get uploaded to the scale. If you change the name or the birthday, you may run into problems when you're using a smartphone app in parallel, some of them rely on this information to define a user. This means that you can change the `height` or `activity` even after the user has been added to the scale, in that case the data on the scale will get updated. Are more/less active? Change the `activity` value in the file. You have grown? Change the `height` value in the file. *You will always get prompted before any change is made to the scale*. You can then either `ctrl-c` out of the script, or just type `enter` to abort the script, or type and submit `YES` to upload the changes to the scale. Afterwards the script will exit and will have to be re-run for any other action.



2. If the scale has a user with an `uid` which is **not** in the *users.py* file, the script will offer you to delete the user from the scale. Only if you then type and submit `YES`, the user will be deleted from the scale and the script exits. For any other entry (`enter` or anything else) the script will display the information of the unknown user, so that you can copy and paste it into the *users.py* file as a new user. Then the script will exit.



3. If the script has a user with an `uid` which is **not** in the scale, then the user will get uploaded to the scale and the script will exit, no questions asked (remember that it's no problem to delete an accidentally added user).



*If there are multiple user-actions to be made, the script will have to be run multiple times.* For example if the USERS variable is empty and the scale has two users stored on it, you will have to run the script two times to add the information to the file. This may be a bit tedious, but adding the logic to avoid this not worth the time.



**storage.py**

This file is self-explanatory. It is an example of how to store relevant data into a file and/or into a database.

By default, any measurement will be stored (appended) into a `JSON`-like file, for example *measurements-0000000000001234.json*. It's not real `JSON`, because there is no indication that there is an array, it's lines of `JSON` documents, with a comma appended at each line:

```JSON
{"amr": 1234, "battery": 37.6, "bmi": 12.3, "bmr": 12345, "bone": 12.34, "fat": 12.3, "impedance": 123, "muscle": 12.3, "time": "2019-04-26T17:33:11", "timestamp": 1556292791, "uid": "0000000000001234", "water": 12.3, "weight": 12.34},
{"amr": 1234, "battery": 37.6, "bmi": 12.3, "bmr": 12345, "bone": 12.34, "fat": 12.3, "impedance": 123, "muscle": 12.3, "time": "2019-04-26T17:48:55", "timestamp": 1556293735, "uid": "0000000000001234", "water": 12.3, "weight": 12.34},
```

This can be easily assembled into a proper `JSON` format.



----



***Note:*** *The following is intended to enable scripted automation **after** everything has been set up correctly, when the system is understood and no further user interaction is necessary. Their usage should be halted any time changes need to be made to the users until it is clear that everything can run automatically again.*



**server.py** and **server_handler.py**

This is an *optional* HTTP server which at the moment only triggers the script. In my case it is used so that another server can issue a `/trigger` via `curl` or the  `requests` module when an Amazon Dash button has been pressed. You could also use `/fetch ` on a smartphone browser and wait a little, this would then display the result as plain-text `JSON`. `/trigger?alias=somebody`  and `/fetch?alias=somebody` is also supported.

It can also serve as a basis for creating a UI for displaying the measurements (TODO).

You may want to run the server in a GNU screen session: 

 `screen -AmdS scale python ~/bt-scale/server.py`



**bt-scale.go** and its precompiled (for the Raspberry Pi) executable **bt-scale**

This helper executable has two purposes: 1) to help you find the `mac address` of the scale and 2) to instruct the scale to take a measurement for a specific `uid`. Instructing it to take a measurement turns on the scale for the user and then exits immediately. The measurement could then be downloaded with *scale.py*.

1. `sudo ./bt-scale` will start to print the `mac addresses` of all the Bluetooth LE devices which are nearby, with their respective name, if it is available.

   The Silvercrest SBF75 shows up as `found XX:XX:XX:XX:XX:X | SBF75`.
   
   ```
   scanning...
   found AA:AA:AA:AA:AA:AA | CC-RT-BLE
   found AA:AA:AA:AA:AA:AA | 
   found AA:AA:AA:AA:AA:AA | 
   found AA:AA:AA:AA:AA:AA | CC-RT-BLE
   found XX:XX:XX:XX:XX:XX | SBF75   
   found AA:AA:AA:AA:AA:AA | CC-RT-BLE
   ...
   ```

2. `sudo ./bt-scale -mac=XX:XX:XX:XX:XX:XX -uid=0000000000001234` will instruct the scale to take a measurement for the user `0000000000001234`.  In this mode there are four possible results: 

   * `disconnected, measurement trigger succeeded`, 
   * `disconnected, measurement trigger failed, unknown user id`,
   * `disconnected, measurement trigger failed, unknown reason` and
   * `disconnected, program execution timeout` (probably was never connected to begin with)

With the optional flag `-stderr=true` everything but the result will be written to `stderr` instead of to `stdout`, which can be useful for Unix pipes. See how *cronjob.py* makes use of it.

The optional flag `-timeout` specifies the timeout in seconds for this program to run, this defaults to `30` seconds. The program can run a little bit longer if it got fully connected to the scale after `29` seconds or so. Then it will continue to trigger the measurement, which is a matter of very few seconds or milliseconds to execute.

The real reason for bundling this executable is to add the ability to wake up the scale once a night with a `cronjob`, and as soon as `disconnected, measurement trigger succeeded` is returned, *scale.py* can connect to download the measurements. `gatttool`, which *scale.py* relies on, does not have the ability to wake up the scale; I don't know why; it probably times out too fast.



**cronjob.py**

This script can either be triggered by a `cronjob` or by fetching `/download` on the optional HTTP server.

`0 3 * * * python ~/bt-scale/cronjob.py > ~/.scale-cronjob.log 2>&1` would download the new measurements from the scale every night at 3 am and insert them into the database and/or `JSON` file.

The generated log file *.scale-cronjob.log* would then contain the following helpful data in case you need to debug something:

```

----------------------------------------------
cronjob.py started running at 2019-04-28T03:00:01.626285
----------------------------------------------

scanning...
found AA:AA:AA:AA:AA:AA | CC-RT-BLE
found AA:AA:AA:AA:AA:AA | 
found AA:AA:AA:AA:AA:AA | CC-RT-BLE
found AA:AA:AA:AA:AA:AA | 
found AA:AA:AA:AA:AA:AA | 
found AA:AA:AA:AA:AA:AA | CC-RT-BLE
found AA:AA:AA:AA:AA:AA | CC-RT-BLE
found XX:XX:XX:XX:XX:XX | SBF75
connecting...
connected
sending init request E601
ack init request | E6 00 20
sending measurement request E7400000000000001234
ack measurement request | E7 F0 40 00
done, disconnecting...
disconnected, measurement trigger succeeded

----------------------------------------------
will start running scale.py in 5 seconds
connecting...
connection_status -> successful

---------------------------------------------
init?
char-write-req 0x002e E601
init.

---------------------------------------------
set scale time
char-write-req 0x002e E95CC4B06C

---------------------------------------------
get scale status
char-write-req 0x002e E74F0000000000000000
scale status -> e7 f0 4f 01 5e 14 dc 01 01 01 01 05
{
  "battery": 36.9
}

---------------------------------------------
get user list
char-write-req 0x002e E733
userlist status -> e7 f0 33 00 01 08
{
  "max": 8, 
  "count": 1
}
-------
user status -> e7 34 01 01 00 00 00 00 00 00 12 34 ~~ ~~ ~~ ~~
{
  "uid": "0000000000001234", 
  "name": "XY", 
  "year": 1999
}
user ack data
char-write-req 0x002e E7F1340101

---------------------------------------------
get user details for XY
char-write-req 0x002e E7360000000000001234
user detail status -> e7 f0 36 00 ~~ ~~ ~~ ~~ ~~ ~~ ~~ ~~
{
  "name": "XY", 
  "birthday": "1999-01-23", 
  "height": 123, 
  "gender": "male", 
  "activity": 3, 
  "uid": "0000000000001234"
}

---------------------------------------------
users in file and in scale
-----
user details in file match those in the scale for uid 0000000000001234

---------------------------------------------
request unknown measurements
char-write-req 0x002e E746
measurements_status e7 f0 46 01

---------------------------------------------
request saved measurements for XY
char-write-req 0x002e E7410000000000001234
measurements status -> e7 f0 41 00 00 -> 0 stored measurements

---------------------------------------------
disconnected

---------------------------------------------

{
  "timestamp": 1556394092, 
  "scale": {
    "battery": 36.9
  }, 
  "users": [
    {
      "uid": "0000000000001234", 
      "name": "XY", 
      "birthday": "1999-01-23", 
      "height": 123, 
      "gender": "male", 
      "activity": 3
    }
  ]
}

---------------------------------------------

storing measurements...
connecting to database...
storing / updating users...
storing / updating measurements...
done.

all done in 4.702 seconds
```

