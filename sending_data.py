import socket
import time
import os

# Set the IP address of your ESP32 (check the Serial Monitor when the ESP32 boots up)
ESP32_IP = '192.168.1.100' # Change this to your ESP32's actual IP address
ESP32_PORT = 80             # The port we set up in the Arduino code

def send_data(x, y):
    try:
        # Create a socket and connect to the ESP32
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0) # 2 second timeout
            s.connect((ESP32_IP, ESP32_PORT))
            
            # The format we expect on the ESP32 is "pred_x,pred_y\n"
            msg = f"{x},{y}\n"
            s.sendall(msg.encode('utf-8'))
            print(f"Sent target position to ESP32: {msg.strip()}")
            
    except Exception as e:
        print(f"Failed to send data to {ESP32_IP}: {e}")

last_data = ""

print(f"Listening for predictions to send to {ESP32_IP}:{ESP32_PORT}...")
while True:
    try:
        if os.path.exists("prediction"):
            with open("prediction", "r") as f:
                data = f.read().strip()
                
            if data and data != last_data:
                # The format in prediction is "pred_x pred_y"
                x, y = data.split()
                send_data(x, y)
                last_data = data
                
        time.sleep(0.1) # Check 10 times a second
    except KeyboardInterrupt:
        print("Stopping...")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)

