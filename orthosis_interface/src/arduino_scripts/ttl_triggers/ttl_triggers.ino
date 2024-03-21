#define TRIGGER1 4
#define TRIGGER2 5
#define TRIGGER3 6

char inChar; 

void setup() {
  // initialize serial:
  Serial.begin(9600);
  Serial.setTimeout(1);
  // Set the pins to output mode
  // pinMode(LED_BUILTIN,OUTPUT);
  pinMode(TRIGGER1, OUTPUT);
  pinMode(TRIGGER2, OUTPUT);
  pinMode(TRIGGER3, OUTPUT);

  // Set the triggers to low at start
  // digitalWrite(LED_BUILTIN,LOW);  
  digitalWrite(TRIGGER1, LOW);
  digitalWrite(TRIGGER2, LOW);
  digitalWrite(TRIGGER3, LOW);

}

void loop() {

  while (Serial.available()) {
    // get the new byte:
    inChar = (char)Serial.read();
    //Serial.println(inChar);
       
  if (inChar == 'F') {
    digitalWrite(TRIGGER1, HIGH);
    delay(100); 
    digitalWrite(TRIGGER1, LOW);
  }

  else if (inChar == 'E') {
    digitalWrite(TRIGGER2, HIGH);
    delay(100); 
    digitalWrite(TRIGGER2, LOW);
  }

  else if (inChar == 'Y') {
    digitalWrite(TRIGGER1, HIGH);
    digitalWrite(TRIGGER2, HIGH);
    delay(100); 
    digitalWrite(TRIGGER1, LOW);
    digitalWrite(TRIGGER2, LOW);
  }

  else if (inChar == 'P') {
    digitalWrite(TRIGGER1, HIGH);
    digitalWrite(TRIGGER3, HIGH);
    delay(100); 
    digitalWrite(TRIGGER1, LOW);
    digitalWrite(TRIGGER3, LOW);
  }

  else if (inChar == 'N') {
    digitalWrite(TRIGGER2, HIGH);
    digitalWrite(TRIGGER3, HIGH);
    delay(100); 
    digitalWrite(TRIGGER2, LOW);
    digitalWrite(TRIGGER3, LOW);
  }

  else {
    // digitalWrite(LED_BUILTIN, LOW);
    digitalWrite(TRIGGER1, LOW);
    digitalWrite(TRIGGER2, LOW);
    digitalWrite(TRIGGER3, LOW);    
  }
    inChar = NULL;
  }
}