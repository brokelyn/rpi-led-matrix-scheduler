# Led Matrix Scheduler

This application is a scheduler for different animations and effects which can be displayed on a led matrix.
Instead of having a main file which calls all the different programmed effects, this application will call
each python file in the submodule folder. Each submodule can decide how often and how long its want to display 
its content. Therefore creating new animations or effects is just creating a new submodule.

This projects is designed to run on a raspberry pi. Therefore each part of the steps
is specific for the the pi and may not work on other devices or operating systems.

## Structure of the project

In the top folder there are classes which will schedule the different submodule.

- the `init.py` file is used to define the different led matrix options. For further information see [rpi-rgb-led-matrix]('https://github.com/hzeller/rpi-rgb-led-matrix')
- the `settings.yp` file contains different constants required for this application. See section **Installing / Usage** for more information
- the `submodule.py` file is the super class of each submodule, which saves and provides the different methods for scheduling a submodule
- the `scheduler.py` file will load all submodules and schedule them accordingly to their requests

In the `submodules` folder are the different submodules
- each submodule needs a `__init__` method with the following parameters
    1. parameter `add_loop`
        - by calling this method an effect of this module will be repeatedly executed
        - the first parameter is the priority number. The higher the more rarely the method is executed
        - the second parameter will be the function which will be called repeatedly
        - the method will return a `function id` which can be used to delte this loop later
    2. parameter `rmv_loop`
        - this method will remove a previous added loop function
        - it take the `function id` as parameter to remove the loop
        - the `function id` is provided by the `add_loop` function
    3. parameter `add_event`
        - this method will add a one time execution of an effect of this module
        - the first parameter is the priority number. If more than one event is active the one with the lowest priority will be executed
        - the second parameter will be the function which will be called once
    - each of this parameters will be saved by the super class like this `super().__init__(add_loop, rmv_loop, add_event)`
    - so using one of the method can be done by `self.add_event_fnc(2, self.fnc_name)`
- each submodule can a have a `service` function
    - the `servide` function which will be executed in an extra thread by the scheduler
    - it can be useful when requesting an api in the background and then display an event
    - it can be used by implementing the `def service(self):` function
    - if there is no need for the `service` function it is **not required to implement it** 
        
A good example submodule is the `clock` submodule. Own submodule can be developed by adding a python file to
the submodule folder and following the submodule structure above. The submodule should be detected and started 
automatically by the scheduler.

## Dependencies

There are a few dependencies required by the application.
The most important dependency is the [rpi-rgb-led-matrix]('https://github.com/hzeller/rpi-rgb-led-matrix')
from **hzeller**. The whole project build on this library.
 
Most of the dependencies are required by the different modules. If these
modules are not required or desired they can be removed without any side effects.

- Python 3 is required
- python package `ping3` is required by
    - `OnlineService` module
    - `StandbyService` module
    
- python package `requests` is required by
    - `PiholeStats` module
    - `StatsSyncthing` module
    
- python package `PIL` is required by
    - `BootService` module
    - `PiholeStats` module
    - `StatsSyncthing` module
   
- linux package `nmap` is required by
    - `NetworkTracker` module
    
## Setting Environment Variables

A few modules are using device ip to check their online state or to
perform api calls. This device ips are defined as environment variables.
In the `settings` file their are constants pointing on the required devices.

1. Set up the environment variable
    - Edit the profile file by `sudo vim /etc/eviroment`
    - A variable can be added by inserting `export <enviroment variable name>=<value>`
    - For example `export MY_IP=127.0.0.1`
    - The new environment variables should apply after a reboot
2. Add the environment variables to the `settings` file
    - fill the `os.environ['STANDBY_DEVICE_IP']` with your environment variable name

## Installing / Usage

1. Setting up the led matrix. 
    - A guide can be found in the github repo [rpi-rgb-led-matrix]('https://github.com/hzeller/rpi-rgb-led-matrix').

2. Installing the `python binding`
    - The binding can be found here [here]('https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python')
    - When the binding is installed it can be tested by one of the scripts in the 
      [sample]('https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python')
      folder by just executing `sudo python3 <sample_script.py>`
      
3. Setting the path to the binding
    - the project contains a `settings` file which needs a **absolute path** to the python binding
    - set the `PATH_PYTHON_BINDING` variable to your correct path
    
4. Environment variables for modules
    - every other variable in the `settings` file is optional and is required by the different modules
    - when not using any of the modules the variables can be set to `None` or be commented out
    - when using modules requiring the variables, set them accordingly to the **Setting Environment Variables**
    
5. Starting the application
    - start the application with the command `sudo python3 scheduler.py`
    - when using environment variables the command `sudo -E python3 scheduler.py` is needed to keep the user environment variables
    - `sudo` is required by the [rpi-rgb-led-matrix]('https://github.com/hzeller/rpi-rgb-led-matrix') library and the `ping3` package

### Autostart

The easiest way is to use `cron`. Just add `@reboot sudo -E python3 <path_to_scheduler.py>` as cronjob.
This can be done by accessing the cron file with `crontab -e`.
