# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-w-asynchronous-web-server-micropython/

# Import necessary modules
import network
import socket
import time
from machine import Pin, ADC
import uasyncio as asyncio
# Wi-Fi credentials
ssid = 'NhaNghiBamBooK2-3'
password = '0913860306@@@'

# Create several LEDs
led_blink = Pin(20, Pin.OUT)
led_control = Pin(19, Pin.OUT)

# Initialize variables
state = "OFF"
temperature = 1  # Starting value for auto-incrementing temperature

# Auto-incrementing temperature counter
def get_next_temperature(current_temp):
    # Increment temperature and reset to 1 if it exceeds 100
    next_temp = current_temp + 1
    if next_temp > 100:
        next_temp = 1
    return next_temp
#kkk
# HTML template for the webpage
def webpage(temperature, state):
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pico Web Server</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                    background-color: #f5f5f5;
                }}
                h1 {{
                    color: #2c3e50;
                    margin-bottom: 30px;
                }}
                h2 {{
                    color: #3498db;
                    margin-top: 30px;
                }}
                .control-panel {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .btn {{
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 15px 32px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 18px;
                    margin: 10px 5px;
                    cursor: pointer;
                    border-radius: 8px;
                    min-width: 200px;
                    transition: background-color 0.3s;
                }}
                .btn-on {{
                    background-color: #2ecc71;
                }}
                .btn-off {{
                    background-color: #e74c3c;
                }}
                .btn-fetch {{
                    background-color: #9b59b6;
                }}
                .btn:hover {{
                    opacity: 0.9;
                    transform: scale(1.05);
                }}
                .status {{
                    font-size: 18px;
                    font-weight: bold;
                    margin: 15px 0;
                }}
                .status-on {{
                    color: #2ecc71;
                }}
                .status-off {{
                    color: #e74c3c;
                }}
                @media (max-width: 600px) {{
                    .btn {{
                        width: 80%;
                        padding: 20px;
                        font-size: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <h1>Raspberry Pi Pico Web Server</h1>
            
            <div class="control-panel">
                <h2>LED Control</h2>
                <form action="./lighton">
                    <input type="submit" class="btn btn-on" value="TURN ON LIGHT" />
                </form>
                <form action="./lightoff">
                    <input type="submit" class="btn btn-off" value="TURN OFF LIGHT" />
                </form>
                <p class="status {('status-on' if state=='ON' else 'status-off')}">
                    Light status: {state}
                </p>
            </div>
            
            <div class="control-panel">
                <h2>Auto Temperature Display</h2>
                <p class="status">Temperature: <span id="temperature-value">{temperature}</span>&deg;C</p>
                <p>(Auto-incrementing from 1 to 100 every 3 seconds)</p>
            </div>
            
            <script>
                // Function to fetch the current temperature
                async function fetchTemperature() {{
                    try {{
                        const response = await fetch('./temperature');
                        const data = await response.json();
                        document.getElementById('temperature-value').textContent = data.temperature;
                    }} catch (error) {{
                        console.error('Error fetching temperature:', error);
                    }}
                }}
                
                // Update temperature every 3 seconds without page refresh
                setInterval(fetchTemperature, 3000);
            </script>
        </body>
        </html>
        """
    return str(html)

# Init Wi-Fi Interface
def init_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Connect to your network
    wlan.connect(ssid, password)
    # Wait for Wi-Fi connection
    connection_timeout = 10
    while connection_timeout > 0:
        print(wlan.status())
        if wlan.status() >= 3:
            break
        connection_timeout -= 1
        print('Waiting for Wi-Fi connection...')
        time.sleep(1)
    # Check if connection is successful
    if wlan.status() != 3:
        print('Failed to connect to Wi-Fi')
        return False
    else:
        print('Connection successful!')
        network_info = wlan.ifconfig()
        print('IP address:', network_info[0])
        return True

# Asynchronous functio to handle client's requests
async def handle_client(reader, writer):
    global state
    
    print("Client connected")
    request_line = await reader.readline()
    print('Request:', request_line)
    
    # Skip HTTP request headers
    while await reader.readline() != b"\r\n":
        pass
    
    request = str(request_line, 'utf-8').split()[1]
    print('Request:', request)
    
    # Process the request and update variables
    if request == '/lighton?':
        print('LED on')
        led_control.value(1)
        state = 'ON'
    elif request == '/lightoff?':
        print('LED off')
        led_control.value(0)
        state = 'OFF'
    elif request == '/temperature':
        # Return just the temperature as JSON
        response = f'{{"temperature": {temperature}}}'
        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(response)
        await writer.drain()
        await writer.wait_closed()
        print('Temperature data sent')
        return

    # Generate HTML response for regular pages
    response = webpage(temperature, state)

    # Send the HTTP response and close the connection
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n')
    writer.write(response)
    await writer.drain()
    await writer.wait_closed()
    print('Client Disconnected')
    
async def blink_led():
    while True:
        led_blink.toggle()  # Toggle LED state
        await asyncio.sleep(0.5)  # Blink interval

# Task to periodically update temperature
async def update_temperature():
    global temperature
    while True:
        # Get next temperature in sequence
        temperature = get_next_temperature(temperature)
        print(f"Updated temperature to: {temperature}°C")
        await asyncio.sleep(3)  # Update every 3 seconds

async def main():    
    if not init_wifi(ssid, password):
        print('Exiting program.')
        return
    
    # Initialize temperature value
    global temperature
    temperature = 1  # Start at 1
    print(f"Initial temperature: {temperature}°C")
    
    # Start the server and run the event loop
    print('Setting up server')
    server = asyncio.start_server(handle_client, "0.0.0.0", 80)
    asyncio.create_task(server)
    asyncio.create_task(blink_led())
    asyncio.create_task(update_temperature())
    
    while True:
        # Add other tasks that you might need to do in the loop
        await asyncio.sleep(5)
        print('This message will be printed every 5 seconds')
        

# Create an Event Loop
loop = asyncio.get_event_loop()
# Create a task to run the main function
loop.create_task(main())

try:
    # Run the event loop indefinitely
    loop.run_forever()
except Exception as e:
    print('Error occurred: ', e)
except KeyboardInterrupt:
    print('Program Interrupted by the user')