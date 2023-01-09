# Ref: https://pypi.org/project/arduino-python3/
import serial
import time
import regex as re
import threading 
from flask import Flask, render_template
import queue

app = Flask(__name__)

cmd_queue = queue.Queue()
@app.route('/')
def hello_world():
    print(data[0])
    print(data[1])
    print(data[2])
    print(data[3])
    return render_template('view2.html')#, dat1=data[0], dat2=data[1])


@app.route('/auto')
def auto():
    return 'Current data:<br>Humidity: ' + str(data[0]) + '<br>Temperature: ' + str(data[1])

# Should del
@app.route('/turn_on')  
def turn_on():
    cmd_queue.put('1')
    return render_template('ok.html', led="Led is ON")

# Should del
@app.route('/turn_off')
def turn_off():
    cmd_queue.put('0')
    return render_template('ok.html', led="Led is OFF")


def readingThread(ser):
    global is_stopping
    global data

    while not is_stopping:
        dat = str(ser.read_until(expected='---'))
        update_data(dat)


def controlThread(ser):
    pass
    # global is_stopping

    # while not is_stopping:
    #     if cmd_queue.empty():
    #         time.sleep(1)
    #     else:
    #         cmd = cmd_queue.get()
    #         print(cmd)
    #         ser.write(cmd.encode())


def update_data(dat):
    # Update data function, parse raw serial data and then update.
    cur_time_form = r"At: ([\w+ :]*) -"                     # Example: At: Sat Jan  7 12:16:38 2023 -
    humidity_form = r"Humidity \(\%\): ([0-9.]*)"           # Example: Humidity (%): 53.00
    temperature_form = r"Temperature \(C\): ([0-9.]*)"      # Example: Temperature (C): 30.00
    photoresistor_form = r"Photoresistor: ([0-9.]*)"        # Example: Photoresistor: 780
    soil_moisture_form = r"Soil moisture: ([0-9.]*)"        # Example: Soil moisture: 1223

    global data
    data = [None for i in range (5)]

    try:
        cur_time_data = get_data_from_format(cur_time_form, dat)
        humi_data = get_data_from_format(humidity_form, dat)
        temp_data = get_data_from_format(temperature_form, dat)
        phot_data = get_data_from_format(photoresistor_form, dat)
        soil_data = get_data_from_format(soil_moisture_form, dat)
    except:
        raise("Serial data was wrong format or something went ")

    cur_time = time.strptime(cur_time_data)
    cur_time_dict = {
        'day': cur_time.tm_mday,
        'mon': cur_time.tm_mon,
        'year': cur_time.tm_year,
        'hour': cur_time.tm_hour,
        'min': cur_time.tm_min,
        'sec': cur_time.tm_sec,
        'dmyhms_form': f'{cur_time.tm_mday}/{cur_time.tm_mon}/{cur_time.tm_year} - {cur_time.tm_hour}:{cur_time.tm_min}:{cur_time.tm_sec}',
        'hmsdmy_form': f'{cur_time.tm_hour}:{cur_time.tm_min}:{cur_time.tm_sec} - {cur_time.tm_mday}/{cur_time.tm_mon}/{cur_time.tm_year}'
        }

    data[0] = humi_data
    data[1] = temp_data
    data[2] = phot_data
    data[3] = soil_data
    data[4] = cur_time_dict
    

    # The below code block just for debug, after done please do comment it
    print(cur_time_dict['hmsdmy_form'])
    print(humi_data)
    print(temp_data)
    print(phot_data)
    print(soil_data)
    print('----------------')

    return True
    

def get_data_from_format(regex_form, str):
    # Function return data from struct raw data
    return re.search(regex_form, str).group(1)


if __name__ == "__main__":
    global is_stopping
    is_stopping = False
    global data
    data = [0, 0]   # Data structure: [humidity, temperature]
    h_serial = serial.Serial('COM8', 115200, timeout=1)

    h_reading_thread = threading.Thread(target=readingThread, args=(h_serial,))
    h_reading_thread.start()

    h_control_thread = threading.Thread(target=controlThread, args=(h_serial,))
    h_control_thread.start()

    app.run()


    is_stopping = True
    h_reading_thread.join()
    h_control_thread.join()

    h_serial.close()
    print("OK\n")