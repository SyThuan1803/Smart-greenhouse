# Ref: https://pypi.org/project/arduino-python3/
import serial
import time
import regex as re
import threading 
from flask import Flask, render_template, url_for, request, redirect
import queue

app = Flask(__name__)

cmd_queue = queue.Queue()
@app.route('/')
def hello_world():
    return render_template('index.html',dat0=data[0],dat1=data[1],dat2=data[2],dat3=data[3])#, dat1=data[0], dat2=data[1])

@app.route('/control.html/FAN')
def auto1():
    if request.method== 'POST':
        return render_template('/control.html',Device="FAN",status_manual='ON')
    else:
        return render_template('/control.html',Device="FAN",status_manual='ON')


@app.route('/control.html/WATER')
def auto2():
    if request.method== 'POST':
        return render_template('/control.html',Device="WATER",status_manual='ON')
    else:
        return render_template('/control.html',Device="WATER",status_manual='ON')


@app.route('/control.html/LIGHT')
def auto3():
    if request.method== 'POST':
        return render_template('/control.html',Device="LIGHT",status_manual='ON')
    else:
        return render_template('/control.html',Device="LIGHT",status_manual='ON')
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
    #global data

    while not is_stopping:
        dat = str(ser.read_until(expected='---'))
        update_data(dat)


def controlThread(ser):
    global is_stopping

    while not is_stopping:
        if cmd_queue.empty():
            time.sleep(1)
        else:
            cmd = cmd_queue.get()
            print(cmd)
            ser.write(cmd.encode())


def update_data(dat):
    # Update data function, parse raw serial data and then update.
    cur_time_form = r"At: ([\w+ :]*)\\n>>"                  # Example: At: Sat Jan  7 12:16:38 2023 -
    humidity_form = r"Humidity \(\%\): ([0-9.]*)"           # Example: Humidity (%): 53.00
    temperature_form = r"Temperature \(C\): ([0-9.]*)"      # Example: Temperature (C): 30.00
    photoresistor_form = r"Photoresistor: ([0-9.]*)"        # Example: Photoresistor: 780
    soil_moisture_form = r"Soil moisture: ([0-9.]*)"        # Example: Soil moisture: 1223
    fan_form = r"Fan \(red led\): ([OFN]*)"               # Example: Fan (red led): OFF
    bulb_form = r"Bulb \(yellow led\): ([OFN]*)"          # Example: Bulb (yellow led): ON
    waterp_form = r"Water pump \(green led\): ([OFN]*)"   # Example: Water pump (green led): ON
    auto_mode_form = r"Auto mode: ([OFN]*)"

    #global data
    #data = [None for i in range (5)]
    # [print(data[i]) for i in range(5)]
    # try:
    cur_time_data = get_data_from_format(cur_time_form, dat)
    humi_data = get_data_from_format(humidity_form, dat)
    temp_data = get_data_from_format(temperature_form, dat)
    phot_data = get_data_from_format(photoresistor_form, dat)
    soil_data = get_data_from_format(soil_moisture_form, dat)
    fan_status = get_data_from_format(fan_form, dat)
    bulb_status = get_data_from_format(bulb_form, dat)
    waterp_status = get_data_from_format(waterp_form, dat)
    auto_mode = get_data_from_format(auto_mode_form, dat)
    # n???u ch???n fan -> c???n ph???i c?? ???????c bulb v?? water
    # check auto_mode, ?????c ???????c 3 tr???ng th??i auto or not c???a 3 thi???t b???
    # 1a
    # except:
    #     raise("Serial data was wrong format or something went ")

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
    if int(phot_data) < 3000:
        data[2]="day"
    else:
        data[2]="night"
    data[3] = soil_data
    data[4] = cur_time_dict
    data[5] = fan_status
    data[6] = bulb_status
    data[7] = waterp_status
    data[8] = auto_mode
    

    # # The below code block just for debug, after done please do comment it
    # print(cur_time_dict['hmsdmy_form'])
    # print(humi_data)
    # print(temp_data)
    # print(phot_data)
    # print(soil_data)
    # print('----------------')

    return True
    

def get_data_from_format(regex_form, str):
    # Function return data from struct raw data
    return re.search(regex_form, str).group(1)


if __name__ == "__main__":
    global is_stopping
    is_stopping = False
    
    global data 
    data = [None for i in range (9)]
    # Nam
    # # update_data("At: Thu Jan  1 00:00:09 1970\\n>>Humidity (%): 0.00	Temperature (C): 0.00	Photoresistor: 4095	Soil moisture: 1086")
    # update_data("At: Thu Jan  1 00:00:44 1970\\n>> Humidity (%): 82.00	Temperature (C): 26.00	Photoresistor: 4028	Soil moisture: 1005\\nFan (red led): OFF	Bulb (yellow led): ON	Water pump (green led): ON\\nAuto mode: ON\\n---")
    # [print(a) for a in data]

    #Dat
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