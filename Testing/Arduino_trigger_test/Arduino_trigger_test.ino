#define LED 9

char inChar;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.setTimeout(1);

  pinMode(LED,OUTPUT);

  digitalWrite(LED,LOW);

}

void loop() {
  while(Serial.available()){

    inChar = (char)Serial.read();

    if (inChar=='F'){
      digitalWrite(LED,LOW);
    }

    else if(inChar=='T'){
      digitalWrite(LED,HIGH);
    }

    inChar = NULL;
    delay(100);

  }

}




















