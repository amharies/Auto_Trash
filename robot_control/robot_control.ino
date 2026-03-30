#include <AccelStepper.h>
#include <MultiStepper.h>
#include <WiFi.h>

const char* ssid = "Galaxy S24 FF0D";     // <--- REPLACE WITH YOUR WIFI NETWORK NAME
const char* password = "1q2w3e4r"; // <--- REPLACE WITH YOUR WIFI PASSWORD
WiFiServer server(80);                     // Server running on port 80

float xpos = 0; //position of car relative to (0,0) corner in cm
float ypos = 0; 
int maxSpeed = 500; // REDUCED FROM 10000: max speed of wheels (10000 will instantly lock up stepper motors)
// int trigger1 = 2;
// int echo1 = 3;
// int trigger2 = 4;
// int echo2 = 5;
float wheelCircum = 128.0/5.0; //circumference of the wheels in cm
float targetx = 160;
float targety = 175;
float duration1, distance1, duration2, distance2;
int count = 0;

// IMPORTANT: ESP32-WROOM-32 cannot use pins 6-11 (they are used for internal flash).
// Pin 20 also does not exist on the WROOM-32.
// We must also avoid "strapping pins" like GPIO 5 and 12, because if the stepper driver pulls them high/low during boot, the ESP32 will crash.
// We have updated these to completely safe ESP32 GPIO pins based on your exact board:
AccelStepper stepper1(1, 19, 18); // Step: 19, Dir: 18
AccelStepper stepper2(1, 26, 25); // Step: 26, Dir: 25
AccelStepper stepper3(1, 33, 32); // Step: 33, Dir: 32
AccelStepper stepper4(1, 13, 14); // Step: 13, Dir: 14

MultiStepper steppersControl;
long gotoposition[4];

void setup() {
  Serial.begin(115200); // Initialize Serial communication with PC for debugging
  
  // Connect to WiFi network
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());
  
  // Start the TCP server
  server.begin();

  stepper1.setMaxSpeed(maxSpeed);
  stepper2.setMaxSpeed(maxSpeed);
  stepper3.setMaxSpeed(maxSpeed);
  stepper4.setMaxSpeed(maxSpeed);
  steppersControl.addStepper(stepper1);
  steppersControl.addStepper(stepper2);
  steppersControl.addStepper(stepper3);
  steppersControl.addStepper(stepper4);

  delay(1000);
}

void loop() {
  // Check if a client has connected to send data
  WiFiClient client = server.available();
  if (client) {
    if (client.connected() && client.available() > 0) {
      String data = client.readStringUntil('\n');
      int commaIndex = data.indexOf(',');
      if (commaIndex > 0) {
        targetx = data.substring(0, commaIndex).toFloat();
        targety = data.substring(commaIndex + 1).toFloat();
        
        Serial.print("Received via WiFi - targetx: ");
        Serial.print(targetx);
        Serial.print(", targety: ");
        Serial.println(targety);

        // Reset the position counters whenever we receive a legitimate new target command from PC
        count = 5; // Set it past 5 to disable the hardcoded test movements below
      }
    }
    client.stop(); // Close the connection
  }

  // Calculate required steps based on target coordinates
  int xsteps = (int) ((targetx - xpos) / wheelCircum * 200 * 8) * 50 / 46;
  int ysteps = (int) ((targety - ypos) / wheelCircum * 200 * 8);
  int steps12 = (int) ((xsteps + ysteps));
  int steps03 = (int) ((ysteps - xsteps));

  // Note: the original code resets target and position but didn't update xpos/ypos.
  // The logic here is preserved as you wrote it.
  gotoposition[0] = steps03;
  gotoposition[1] = steps12;
  gotoposition[2] = steps12;
  gotoposition[3] = steps03;

  steppersControl.moveTo(gotoposition);

  // This is a blocking call! It will drive the motors to the target before returning.
  steppersControl.runSpeedToPosition();
  
  // Keep advancing the count state machine
  count++;

  // Handle the hardcoded test movements if count is between 1 and 4
  if (count > 0 && count < 5) {

    if (count == 1) {
      delay(500); // 500ms pause between test moves
      targetx = -75;
      targety = -50;
    }
    else if (count == 2) {
      delay(500);
      targetx = -50;
      targety = 0;
    }
    else if (count == 3) {
      delay(500);
      targetx = 0;
      targety = -75;
    }
    else if (count == 4) {
      delay(500);
      targetx = 30;
      targety = 75;
    }
    
    // Reset stepper positions so the next calculation is relative to the current spot
    stepper1.setCurrentPosition(0);
    stepper2.setCurrentPosition(0);
    stepper3.setCurrentPosition(0);
    stepper4.setCurrentPosition(0);
  }
}

void getpos() {
  // Empty as in the original code, but kept to prevent compilation errors if referenced elsewhere
}
