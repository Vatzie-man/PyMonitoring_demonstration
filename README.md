# Description:
The purpose of the project(‘PyMonitoring’) is to gather data from the cooling devices and run it through various tolerance checks. If any device’s parameters or device state is out of expected value the alarm procedure will be triggered.

The data harvesting is based on REST APIs and Selenium librarie. Notifications and harvested data can be viewed in Mattermost communicator where each user can configure alarm to its own needs.

The PyMonitoring runs on Raspberry Pi where physical pins are used for basic configuration. Additionally, there are ESP32 devices which monitor activity of Raspberry Pi and raise alarm if there is none for certain time.

Unfortunately, as the program is specific to the place, network and devices it won’t work elsewhere, so the code is only for demonstration.
End user experience can be found in in jpg_examples folder.

Project works fine, but there is still things to improve as I am constantly larning. 