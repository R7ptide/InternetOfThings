# Materials to request

## Must

| Item                                                                                                | Slide page | Used for                                                                |
| --------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------- |
| Tiny Machine Learning Kit: Arduino Nano 33 BLE Sense Rev2, Tiny ML shield, USB-A to micro-USB cable V | 108-110    | Color sensing and the TinyML classifier (the assignment's required kit) |
| Arduino UNO R4 WiFi (+ USB cable)                                                                   | 7          | Line controller: belt, servo, ultrasonic, MQTT over Wi-Fi               |
| Arduino IO Expansion Shield V7 (DFR0265)                                                            | 58         | Easy plug-in of sensors and servo to the UNO                            |
| Raspberry Pi 5                                                                                     V | 5-6        | Gateway: broker and sort logic                                          |
| 130 DC Motor Module (DFR0411)                                                                      V | 71         | Belt motor, PWM speed control, no extra driver needed                   |
| 9g Servo                                                                                            | 54         | Diverter arm                                                            |
| Ultrasonic Module                                                                                  V | 47         | Detects an item arriving (2-400 cm)                                     |
| Power Supply Module                                                                                V | 56         | Separate power for the motor and servo, so they don't disturb the board |
| Breadboard, jump wires, resistors                                                                  V/X | 17-19      | Prototyping and wiring                                                  |
| Digital sensor cable (FIT0011) and analog sensor cable (FIT0769)                                    | 92-93      | Connecting sensors to the IO shield                                     |

## Should

| Item                                  | Slide page | Used for                                                                |
| ------------------------------------- | ---------- | ----------------------------------------------------------------------- |
| TCS34725 I2C color sensor (SEN0212)   | 78         | Better color sensor if the Nano's built-in one is noisy (3-10 mm range) |
| I2C Digital Wattmeter (SEN0291)       | 79         | Power and energy per item, for the experiments                          |
| 4-pin I2C/UART sensor cable (FIT0773) | 94         | Connecting the I2C sensors above                                        |
| I2C LCD1602 or 16x2 RGB LCD (DFR0464) | 29, 90     | Local status display on the line                                        |
| Analog Ambient Light sensor (DFR0026) | 76         | Logging light level, since lighting is the main color risk              |
| Digital 5A Relay module (DFR0017)     | 59         | Emergency stop for the belt                                             |
