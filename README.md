# Roborock S5 RPi remote controller
Welcome to an example of how you can use Python, python-miio, RPi, some electronics and woodworking to make a remote controller for Roborock S5 vacuum cleaner.

The material shown here is a snapshot of SW and HW that runs in my house so my whole family can use Roborock S5 without the smartphone app. The script is not that much generic so that you just snap in into your environment and run. Still, where it was not too demanding I have tried to stay as generic as possible. With these instructions you should be able to understand how it works and what you need to do to adapt it to your environment.

[This video](https://youtu.be/L5m7eMEBG1w) shows how simple it is to start a cleanup of two segments. It also shows the log output of the Python script. Having this remote controller doesn't affect functionality of an official MiHome application nor does it require modification of the vacuum itself. The output of the MiHome application is shown at the top left corner of the video.

## How it works
### An overview
The idea is rather simple: python-miio library allows you to get the status of and control the Roborock S5 vacuum cleaner via the python script. You can easily run the following actions (the python-miio library can do much more but these are the ones important for us):
 * start the cleaning of the rooms with given IDs
 * abort cleaning and go to the charger
 * go to a predefined place for the vacuum maintenance
 * (I have almost forgotten) triggering the famous "Hi, I'm over here!" sentence

Around that features list I have added a UI in the form of Raspberry Pi, push buttons and LEDs mounted on the wooden panel with room symbols so my kids can use it.
### User interface
The script controls cleaning of 11 zones. Front panel contains 11 (kids friendly) symbols for each zone. Each zone symbol holds one push button (connected to pull-resistor and RPi input line) and one LED (connected to RPi output line via limiting resistor). Besides that, the bottom section of the panel has 3 control buttons: start cleaning, abort and go home and go to the maintenance point. Together with them there is one signal LED which is used as a heartbeat indicator of the whole remote controller device.

This simple UI allows users to schedule multiple rooms cleaning: first select rooms that you want to clean and then press the 'start cleaning' button. During selection of the rooms (before you pressed the 'start cleaning' button) you can unschedule a particular room by pressing its button once more (gosh, I'd love elevators to have this feature - if you select the floor number by mistake you can deselect it but pressing that number again :) ).

Cleaning procedure can be paused/aborted by pressing the 'home button'.

In our case the vacuum charger (it's home) is hidden below the shoe closet so we cannot access it easily for maintenance reasons. Roboock S5 can be instructed to go to a predefined position for easy maintenance (e.g. near the trash bin) by pressing the 'maintenance button'.
### The script
Go to the `---- Main script ----` section in the [vacuum.py](vacuum.py) file and check the main blocks:

`ip,token = SystemInit()` extracts the Roborock's IP address and access token from the calling command line (TODO: add example of command line). Both parameters are needed for the communication with the vacuum. The way of getting them will be explained in [this](https://github.com/aleksandarzivkovic/roborock_remote/tree/doc_update#what-you-should-change-so-it-works-for-you) section. (TODO: replace absolute url with relative). A script logging mechanism is defined here. Logs will go to a standard output and to file `/tmp/vacuum.log`. Log file size is limited to a maximum of 1MB with keeping the last 5 log files. A `Ctrl+C` handler is defined here, which is handy during the debugging phase. 

`g_Vacuum = VacuumThread(ip, token, StatusChange)` loads `python-miio` library and runs the thread that initiates communication with the vacuum and checks its status (by pinging it every 5 seconds). Every time a thread detects the modified status a `StatusChange` callback will be triggered. This object contains methods for controlling the vacuum: `clean`,`find`,`home` and `maintenance`. `clean` method has one argument which is a list of segment IDs to be cleaned. For example, here is a map with segment IDs for our home: ![](rooms_mapping.jpg) `maintenance` actually executes goto command which sends vacuum to a predefined x,y position. When looking at the Android application map the position of the charger is the coordinate system start point (with coordinates 25500, 25500). In our case the maintenance position is 9m right and 0.5m up, therefore x,y positions are defined as:
```
self.m_x = 25500+9000
self.m_y = 25500+500
```

`ui = UIThread()` loads Python libraries for reading GPIO inputs and driving LEDs with PWM. This thread runs an empty loop while actions are executed with button press events and status change events.

Since this remote device has many buttons and LEDs the important point is the `g_gpioMap` map. This is a table where each row represents one GPIO line from RPi. For each GPIO line this table defines: line direction (button or LED), descriptive name (usable only for logging - here in Serbian), button press callback function, LED ID (that is used within UI mechanism) and room ID (that is used by the `python-miio` library). Any HW modification or change of the segment IDs needs to be reported here in order for a script to work properly.

### Where the script runs

#### Raspberry Pi OS
TODO

#### Hardware
TODO
Pull-ups that I use are TODO Ohms and LED current limiting resistors are TODO Ohms

## What you need to do so it works for you
1. Place a Raspberry Pi and the vacuum at the same WiFi network
2. Find a vacuum IP address and fix the IP address of the vacuum. This can be done by checking the list of DHCP clients on your home router and fixing a vacuum IP address based on its MAC address
3. Get the vacuum access token. I recommend the method described [here](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor).
4. Find out the segment IDs. It is assumed that you have already defined segments for your home and with this step you need to identify the ID of each segment. Use [test.py](test.py) script to manually add numbers and check where your vacuum goes. Small hint here: during the test observe the Android map - when vacuum starts cleaning of the segment an app will mark that segment in its map so you don't need to wait for a vacuum to actually go there.
5. Here is your DIY part: print your own symbols for segments and make appropriate casing with buttons and LEDs. Can I use the common sentence from web sites about cooking here: please post pictures of your results! :)
6. Depending on the number of segments wire buttons and LEDs and update the `g_gpioMap` map
7. Setup a RPi OS so the script is always started at power-up and lock the filesystem for writting to prevent SD card wareout. The details are described [here]()

