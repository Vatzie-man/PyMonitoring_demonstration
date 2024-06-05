# Description:

Hi there,

If you’re here, it’s likely because my CV directed you to this project. I am continuously improving it as I learn new things. Django, in particular, is a work in progress since I started learning it most recently.

The purpose of the project (‘PyMonitoring’) is to gather data from cooling devices and run it through various tolerance checks. If any device’s parameters or state deviate from expected values, an alarm procedure is triggered.

The data harvesting is based on REST APIs and the Selenium library. Notifications and harvested data can be viewed in the Mattermost communicator, where each user can configure alarms to their own needs.

PyMonitoring runs on a Raspberry Pi, utilizing its physical pins for basic configuration. Additionally, there are ESP32 devices that monitor the activity of the Raspberry Pi and raise an alarm if there is no activity for a certain period.

Unfortunately, as the program is tailored to specific locations, networks, and devices, it won’t function elsewhere, so the code is only for demonstration purposes. End-user experience examples can be found in the jpg_examples folder.

The project works well, but there are still areas for improvement as I am constantly learning.
