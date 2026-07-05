import time
import requests
from picamera2 import Picamera2
from sense_hat import SenseHat

SERVER = "http://ip/8000"     # base URL only — no /scan

def capture_and_send():
    sense = SenseHat()
    sense.low_light = False

    picam2 = Picamera2()
    config = picam2.create_still_configuration(main={"size": (2304, 1296)})
    picam2.configure(config)

    sense.clear(255, 255, 255)          # light on
    picam2.start()
    time.sleep(3)
    picam2.capture_file("scan.jpg")
    picam2.close()
    sense.clear()                       # light off

    with open("scan.jpg", "rb") as f:
        response = requests.post(
            f"{SERVER}/manualscan",       
            files={"image_file": f},       
        )
    print("Server replied:", response.json())

if __name__ == "__main__":
    while True:
        try:
            r = requests.get(f"{SERVER}/scan-requested")
            if r.json()["requested"]:
                print("Scan requested — capturing...")
                capture_and_send()
                requests.post(f"{SERVER}/scan-done")
        except Exception as e:
            print("Poll error:", e)
        time.sleep(10)