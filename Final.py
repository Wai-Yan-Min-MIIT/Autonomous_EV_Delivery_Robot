import os
import ydlidar
import time
import serial
import math

# Initialize serial communication with ESP32
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
except serial.SerialException as e:
    print(f"Failed to open serial port: {e}")
    exit(1)

# Initialize LIDAR
ydlidar.os_init()
ports = ydlidar.lidarPortList()
port = "/dev/ydlidar"
for key, value in ports.items():
    port = value
laser = ydlidar.CYdLidar()
laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 115200)
laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
laser.setlidaropt(ydlidar.LidarPropScanFrequency, 8.0)
laser.setlidaropt(ydlidar.LidarPropSampleRate, 3)
laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)

# Start LIDAR
ret = laser.initialize()
if not ret:
    print("Failed to initialize LIDAR")
    ser.close()
    exit(1)

ret = laser.turnOn()
if not ret:
    print("Failed to turn on LIDAR")
    laser.disconnecting()
    ser.close()
    exit(1)

time.sleep(1)  # Wait for LIDAR to stabilize
scan = ydlidar.LaserScan()

# Main loop to keep LIDAR scanning indefinitely
while True:
    try:
        # Process LIDAR scan
        r = laser.doProcessSimple(scan)
        if r:
            # Process scan data
            obstacle_detected = False
            for point in scan.points:
                # Validate range and angle
                distance = point.range  # in meters
                angle = point.angle    # in degrees

                # Check for obstacle: range between 0 and 1 meter, angle ±1.75°
                if 0 < distance < 0.5 and -1.75 <= angle <= 1.75:
                    obstacle_detected = True
                    print(f"Object Detected at angle: {angle:.2f}°, range: {distance:.4f}m")
                    break  # Exit loop once obstacle is found

            # Send signal to ESP32
            if obstacle_detected:
                ser.write(b"True\n")
                print("Sent 'True' to ESP32")
            else:
                ser.write(b"False\n")
                print("Sent 'False' to ESP32 - No obstacle detected")

            # Debug info
            freq = 1.0 / scan.config.scan_time if scan.config.scan_time > 0 else 0.0
            print(f"Scan [{scan.stamp}]: {scan.points.size()} points at {freq:.2f} Hz")
        else:
            print("Failed to get LIDAR data, retrying...")
            time.sleep(0.1)  # Brief delay before retrying
            continue  # Retry on next iteration

        time.sleep(0.05)  # Adjust based on desired scan rate

    except KeyboardInterrupt:
        print("Program interrupted by user")
        break
    except Exception as e:
        print(f"Error during scanning: {e}")
        time.sleep(1)  # Wait before retrying to avoid rapid error loops
        continue  # Continue scanning despite errors

# Cleanup
laser.turnOff()
laser.disconnecting()
ser.close()
print("LIDAR and serial connection closed")