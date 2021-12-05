# Roborock S5 RPi remote controller
An example of how you can use python, python-miio, RPi and some electronics and woodworking to make a remote controller for Roborock S5 vacuum cleaner.

This repository is a snapshot of SW and HW that runs in my house so my whole family can use Roborock S5 without the smartphone app. It's not intended to be that much generic so that you just snap in into your envornoment and run. Still, where it is was not too demanding I have tried to stay as generic as possible. With these instructions you should be able to understand how it works and what you need to do to adapt it to your environment. 

## How it works for me
### An overview
The idea is rather simple: python-miio library allows you to control Roborock S5 vacuum cleaner via python script. You can easily run the following actions (the python-miio library can do much more but these are the ones important for us):
 * start the cleaning of the rooms with given IDs
 * abort cleaning and go to the charger
 * go to a predefined place for easier vacuum maintenance
 * (I have almost forgotten) triggering the famous "Hi, I'm over here!" sentence

Around that features list I have added a UI in the form of Raspberry Pi, push buttons and LEDs mounted on the wooden panel with room symbols so my kids can use it.
### User interface
The script controls cleaning of 11 zones. Front panel contains 11 (kids friendly) symbols for each zone. Each symbol holds one push button (connected to pull-resistor and RPi input line) and one LED (connected to RPi output line via limiting resistor). Besides that, bottom section of the panel has 3 control buttons to: start cleaning, abort and go home, go to maintenance point. Together with them there is one signal LED which is used as a heartbeat indicator of the whole remote controller device.

This simple UI allows users to schedule multiple rooms cleaning: first select rooms that you want to clean and then press the 'start cleaning' button. During selection of the rooms (before you pressed the 'start cleaning' button) you can unschedule a particular room by pressing its button once more (gosh, I'd love elevators to have this feature - if you select the floor number by mistake you can deselect it but pressing that number again :) ).

Cleaning procedure can be paused/aborted by pressing the 'home button'.

In our case the vacuum charger (it's home) is hidden below shoes closet so we cannot access it easily for maintenance reasons. Roboock S5 can be instructed to go to a predefined position for easy maintenance (e.g. near the trash bin) by pressing the 'maintenance button'.
### The script
TODO
### Where the script lives
TODO


## What you should change so it works for you
