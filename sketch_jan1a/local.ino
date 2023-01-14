#include "dht11.h"
#include <chrono>
#include <ctime>
#include <string>

#define dht11Pin 4            // Humi & Temp
#define cdsLSPin 2//15//2     // Phot 
#define sMSPin 12             // Soil

#define redLedPin 13  // Representing for the activate of fan (reduce temperature for tree)
#define yellowLedPin 14   // Representing for the activate of bulb (ensure the light for tree)   
#define greenLedPin 15  // Representing for the activate of water pump (provide water for tree)

dht11 DHT11;  // sensor init
//bool auto_mode = true;  // change led state (represent for state of some hardwares like fan, bulb, water pump) automatically

// Define some threshold
int temperatureThreshold = 30;      // if the temperatureValue is greater than the threshold, the fan should be turned on
int photoresistorThreshold = 3000;  // if the photoresistorValue is greater than the threshold, the bulb should be turned on
int soilMoistureThreshold = 1000;   // if the soilMoisutreValue is less than the threshold, the water bump should be turned on

// Global variable
std::string inputString = "";       // string read from Serial
bool stringComplete;
std::time_t t_c = 0;                // time control, t_c = 0 nghĩa là thiết bị đang trong mode auto, ngược lại nghĩa là đang trong mode manual
//std::string m_c = "";             // message control


void setup()
{
  Serial.begin(115200);
  pinMode(redLedPin, OUTPUT);
  pinMode(yellowLedPin, OUTPUT);
  pinMode(greenLedPin, OUTPUT);
}


void serialEvent()
{
  while (Serial.available()){
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n'){
      stringComplete = true;
      break;
    }
  }
}


static inline void ltrim(std::string &s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](unsigned char ch) {
        return !std::isspace(ch);
    }));
}

// trim from end (in place)
static inline void rtrim(std::string &s) {
    s.erase(std::find_if(s.rbegin(), s.rend(), [](unsigned char ch) {
        return !std::isspace(ch);
    }).base(), s.end());
}

// trim from both ends (in place)
static inline void trim(std::string &s) {
    rtrim(s);
    ltrim(s);
}


void loop()
{ 
  auto cur = std::chrono::system_clock::now();
  std::time_t cur_t = std::chrono::system_clock::to_time_t(cur);
  
  int chk = DHT11.read(dht11Pin);
  int humidityValue = DHT11.humidity;
  int temperatureValue = DHT11.temperature;
  int photoresistorValue = analogRead(cdsLSPin);
  int soilMoistureValue = analogRead(sMSPin);

  bool redLedStatus = digitalRead(redLedPin);
  bool yellowLedStatus = digitalRead(yellowLedPin);
  bool greenLedStatus = digitalRead(greenLedPin);

  // Xuất thông tin ra Serial
  Serial.print("At: ");
  Serial.print(std::ctime(&cur_t));
  Serial.print(">> ");

  Serial.print("Humidity (%): ");
  Serial.print((float)humidityValue, 2);

  Serial.print("\tTemperature (C): ");
  Serial.print((float)temperatureValue, 2);

  Serial.print("\tPhotoresistor: ");
  Serial.print(photoresistorValue);

  Serial.print("\tSoil moisture: ");  
  Serial.println(soilMoistureValue);    // println(soilMoistureValue);

  Serial.print("Fan (red led): ");
  if (redLedStatus) Serial.print("ON\t");
  else Serial.print("OFF\t");

  Serial.print("Bulb (yellow led): ");
  if (yellowLedStatus) Serial.print("ON\t");
  else Serial.print("OFF\t");

  Serial.print("Water pump (green led): ");
  if (greenLedStatus) Serial.println("ON\t");
  else Serial.println("OFF\t");

  Serial.print("Auto mode: ");
  if (t_c != 0) Serial.println("OFF");
  else Serial.println("ON");

  Serial.println("---");
  
  if (stringComplete){
    trim(inputString);

    // TH1: Xử lý theo message control
    if (inputString != ""){
      // Example: '101-120' - nghĩa là bật đèn đỏ, tắt đèn vàng, bật đèn xanh, trạng thái này duy trì trong vòng 120 phút.
      // Task 1: Thiết lập thời gian hết hạn - t_c
      // t_c = cur_t + activate_time
      // 1->on
      // 0->off
      // a->auto
      
      // Get '120' from inputString
      int active_time = stoi(inputString.substr(4, inputString.length()-4));
      t_c = cur_t;
      struct tm* tm = localtime(&t_c);
      tm->tm_min += active_time;
      t_c = mktime(tm);


      // Task 2: Điều khiển device theo message này
      if (inputString[0] == '1') digitalWrite(redLedPin, HIGH);
      else if (inputString[0] == '0') digitalWrite(redLedPin, LOW);
      else if (inputString[0] == 'a'){
        if (temperatureValue > temperatureThreshold) digitalWrite(redLedPin, HIGH);
        else digitalWrite(redLedPin, LOW);
      }
      
      if (inputString[1] == '1') digitalWrite(yellowLedPin, HIGH);
      else if (inputString[1] == '0') digitalWrite(yellowLedPin, LOW);
      else if (inputString[1] == 'a'){
        if (photoresistorValue > photoresistorThreshold) digitalWrite(yellowLedPin, HIGH);
        else digitalWrite(yellowLedPin, LOW);
      }

      if (inputString[2] == '1') digitalWrite(greenLedPin, HIGH);
      else if (inputString[2] == '0') digitalWrite(greenLedPin, LOW);
      else if (inputString[2] == 'a'){
        if (soilMoistureValue < soilMoistureThreshold) digitalWrite(greenLedPin, HIGH);
        else digitalWrite(greenLedPin, LOW);
      }

      // clear the string
      inputString = "";
      stringComplete = false;
      
      delay(1000);
      return;
    }
  }


  // TH2: Nếu không có message nào được đọc từ serial,
  // điều khiển device theo thiết đặt từ lệnh trước (lệnh control trước)
  // hoặc chế độ auto.
  if (t_c != 0){
    double diff;
    diff = std::difftime(t_c, cur_t);

    // Nếu t_c đã hết hạn
    if (diff <= 0){
      t_c = 0;
    }

    // Nếu không có gì thay đổi, giữ nguyên điều khiển như cũ
    else {
      delay(1000);
      return;
    }      
  }
  

  // TH3: Không có message control, chạy device ở chế độ auto    
  if (temperatureValue > temperatureThreshold) digitalWrite(redLedPin, HIGH);
  else digitalWrite(redLedPin, LOW);

  if (photoresistorValue > photoresistorThreshold) digitalWrite(yellowLedPin, HIGH);
  else digitalWrite(yellowLedPin, LOW);

  if (soilMoistureValue < soilMoistureThreshold) digitalWrite(greenLedPin, HIGH);
  else digitalWrite(greenLedPin, LOW);

  delay(1000);
}