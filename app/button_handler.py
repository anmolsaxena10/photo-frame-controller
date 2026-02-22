import RPi.GPIO as GPIO

class ButtonHandler:
    def __init__(self, state):
        self.state = state
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(17, GPIO.FALLING, callback=self.reset)

    def reset(self, channel):
        self.state.reset()
