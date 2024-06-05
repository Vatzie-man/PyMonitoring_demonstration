# program to be used on RPi; it gathers data from physical pins/dips
import time
import RPi.GPIO as GPIO

# set the GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

dips = {"notifications": 5, "whatsapp": 6, "fermion_watcher": 26}

GPIO.setup(dips["notifications"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dips["whatsapp"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dips["fermion_watcher"], GPIO.IN, pull_up_down=GPIO.PUD_UP)


def get_switches_gpio():
    out = []

    for k in ["notifications", "whatsapp", "fermion_watcher"]:

        if GPIO.input(dips[k]):
            out.append(1)
        else:
            out.append(0)

    return out
