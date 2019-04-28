// +build

/*
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
*/

package main

import (
	"os"
	"fmt"
	"log"
	"flag"
	"time"
	"io/ioutil"
	"encoding/hex"
	"github.com/paypal/gatt"
)

var done = make(chan struct{})
var mac string
var uid string
var final_message string
var output = os.Stdout
var program_abortion_timeout = 30;
var prevent_program_abortion = false

func onPeriphConnected(p gatt.Peripheral, err error) {
  
  prevent_program_abortion = true
  
	fmt.Fprintf(output, "connected\n")

	if err := p.SetMTU(500); err != nil {
		fmt.Fprintf(output, "Failed to set MTU, err: %s\n", err)
	}
  
	ss, err := p.DiscoverServices(nil)
	if err != nil {
		fmt.Fprintf(output, "failed to discover services, err: %s\n", err)
		return
	}
  
	for _, s := range ss {
    
    if (s.UUID().String() != "ffe0") {
      continue
    }
    
		cs, err := p.DiscoverCharacteristics(nil, s)
		if err != nil {
			fmt.Fprintf(output, "failed to discover characteristics, err: %s\n", err)
			continue
		}

		for _, c := range cs {
      if ((c.UUID().String() == "ffe1") && (c.Properties() & gatt.CharWrite) != 0 && (c.Properties() & gatt.CharNotify) != 0) {
  			_, err := p.DiscoverDescriptors(nil, c)
  			if err != nil {
  				fmt.Fprintf(output, "failed to discover descriptors, err: %s\n", err)
  				continue
  			}
			  f := func(c *gatt.Characteristic, b []byte, err error) {
				  if (b[0] == 0xe6 && b[1] == 0x00 && b[2] == 0x20) {
            fmt.Fprintf(output, "ack init request | % X\n", b)
            measuer_user := "E740" + uid
            fmt.Fprintf(output, "sending measurement request %s\n", measuer_user)            
            measure, err := hex.DecodeString(measuer_user)
            if err != nil {
                panic(err)
            }
            p.WriteCharacteristic(c, measure, false);
				  } else if (b[0] == 0xe7 && b[1] == 0xf0 && b[2] == 0x40) {
            fmt.Fprintf(output, "ack measurement request | % X\n", b)
            if (b[3] == 0x00) {
              final_message = "measurement trigger succeeded"
            } else {
              final_message = "measurement trigger failed, unknown user id"
            }
            p.Device().CancelConnection(p)
				  } else {
				    fmt.Fprintf(output, "notified: % X | %q\n", b, b)
          }
				}
				if err := p.SetNotifyValue(c, f); err != nil {
					fmt.Fprintf(output, "failed to subscribe characteristic, err: %s\n", err)
					continue
				}
        fmt.Fprintf(output, "sending init request E601\n")
        init := []byte{0xe6, 0x01}
        p.WriteCharacteristic(c, init, false);
			}
		}
	}
}

func onPeriphDisconnected(p gatt.Peripheral, err error) {
	fmt.Fprintf(output, "done, disconnecting...\n")
	fmt.Fprintf(os.Stdout, "disconnected, %s\n", final_message)
	close(done)
}

func onPeriphDiscovered(p gatt.Peripheral, a *gatt.Advertisement, rssi int) {
	fmt.Fprintf(output, "found %s | %s\n", p.ID(), p.Name())
  if (mac != "" && uid != "") {
  	if (p.ID() == mac) {
      p.Device().StopScanning()
      fmt.Fprintf(output, "connecting...\n")
      p.Device().Connect(p)
  	}
	}
}

func onStateChanged(d gatt.Device, s gatt.State) {
	switch s {
  	case gatt.StatePoweredOn:
  		fmt.Fprintf(output, "scanning...\n")
  		d.Scan([]gatt.UUID{}, true)
      if (mac != "" && uid != "") {
        time.Sleep(time.Duration(program_abortion_timeout) * time.Second)
      }
      if (prevent_program_abortion == false) {
      	fmt.Fprintf(os.Stdout, "disconnected, program execution timeout\n")
      	close(done)
      }
  		return
  	default:
  		d.StopScanning()
	}
}

func main() {
  
  final_message = "measurement trigger failed, unknown reason"
  
  flag.StringVar(&mac, "mac", "", "mac address")
  flag.StringVar(&uid, "uid", "", "user id")

  flag.IntVar(&program_abortion_timeout, "timeout", program_abortion_timeout, "program timeout in seconds")
  
  var output_to_stderr bool
  flag.BoolVar(&output_to_stderr, "stderr", false, "print everything but the result to stderr instead of stdout?")
  
  flag.Parse()
  
  if (output_to_stderr) {
    output = os.Stderr
  }
  
  log.SetFlags(0)
  log.SetOutput(ioutil.Discard)
  
  if (mac == "" || uid == "") {
    fmt.Fprintf(output, "incomplete parameters, will only scan and print out found mac adresses and their respective names\n")
  }
  
  DefaultClientOptions := []gatt.Option{
  	gatt.LnxMaxConnections(1),
  	gatt.LnxDeviceID(-1, false),
  }
  
	d, err := gatt.NewDevice(DefaultClientOptions...)
	if err != nil {
		fmt.Fprintf(output, "no permissions to access device? failed to open device, err: %s\n", err)
		return
	}
	d.Handle(
		gatt.PeripheralDiscovered(onPeriphDiscovered),
		gatt.PeripheralConnected(onPeriphConnected),
		gatt.PeripheralDisconnected(onPeriphDisconnected),
	)
	d.Init(onStateChanged)
	<-done
}
