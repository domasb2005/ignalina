#include <FastLED.h>

#define NUM_LEDS 181


#define DATA_PIN 3
#define CLOCK_PIN 13
CRGB leds[NUM_LEDS];


unsigned long previousMillis[14];
const int ledPin = LED_BUILTIN;

int receivedState = 0; // nulinis state yra zaidimas nepaleistas. Pirmas state yra paspaude start mygtuka, pagal dokumenta taip ir toliau.

int i1 = 0;
int ir1b1=3;
int i2 = 33;
int i3 = 36;
int i4 = 41;
//int ri_rau_led5_state = 0;
int i6 = 0;
int i7 =50;
int iL1 = 85;
int iL1b10=88;
int iL2 = 118;
int iL3 = 126;
int iL4 = 129;
int iL5 = 137;


void setup() { 
    FastLED.addLeds<NEOPIXEL, DATA_PIN>(leds, NUM_LEDS);  // GRB ordering is assumed
    Serial.begin(9600);
    while (!Serial) {
        ;  // Wait for serial port to connect, needed for some boards
    }
    Serial.println("Ready to receive state numbers...");
    pinMode(ledPin, OUTPUT);       // Set LED pin as an output
}



void r1_mel_led1(){
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis[1] >= 80){
    previousMillis[1] = currentMillis;
    //int ir1b1 = i1+3;
    if (ir1b1>=33){
      ir1b1=0;
    }
    if (i1>=33){
      i1=0;
    }
    leds[ir1b1] = CRGB::Blue;
    leds[i1] = CRGB::Black;
    FastLED.show();
    i1++;
    ir1b1++;
  }
}

void r1_rau_led2(){
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis[2] >= 250){
    previousMillis[2] = currentMillis;
    for (int i = 33; i<= 35; i++){
      if(i2>=36){
        i2=33;
      }
      if(i==i2){
        leds[i] = CRGB::Red;
        FastLED.show();
      }
      else
      leds[i] = CRGB::Black;
      FastLED.show();
    }
    i2++;
  }
}

void r1_mel_led3(){
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis[3] >= 500){
    previousMillis[3] = currentMillis;
    for (int i = 36; i<= 40; i++){
      if(i3>=41){
        i3=36;
      }
      if(i==i3){
        leds[i] = CRGB::Blue;
      }
      else
      leds[i] = CRGB::Black;
      FastLED.show();
    }
    i3++;
  }
}

void r1_mel_led4(){
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis[4] >= 500){
    previousMillis[4] = currentMillis;
    for (int i = 41; i<= 45; i++){
      if(i4>=46){
        i4=41;
      }
      if(i==i4){
        leds[i] = CRGB::Blue;
      }
      else
      leds[i] = CRGB::Black;
      FastLED.show();
    }
    i4++;
  }
}

void r1_rau_led5(int i5){
  if(i5==1){
    for (int i = 46; i<= 47; i++){
      leds[i] = CRGB::Red;
      //FastLED.show();
    }
    FastLED.show();
    //i5=1;
  }
  if(i5==0){
    for (int i = 46; i<= 47; i++){
      leds[i] = CRGB::Black;
      //FastLED.show();
    }
    FastLED.show();
  }
}

void r1_rau_led6(int i6){
  if(i6==1){
    for (int i = 48; i<= 49; i++){
      leds[i] = CRGB::Red;
      //FastLED.show();
    }
    FastLED.show();
    //i5=1;
  }
  if(i6==0){
    for (int i = 48; i<= 49; i++){
      leds[i] = CRGB::Black;
      //FastLED.show();
    }
    FastLED.show();
  }
}

void r1_ora_led7(){
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis[7] >= 400){
    previousMillis[7] = currentMillis;
    for (int i = 50; i<= 55; i++){
      if(i7>=56){
        i7=50;
      }
      if(i==i7){
        leds[i] = CRGB::Purple;
      }
      else
      leds[i] = CRGB::OrangeRed;
      FastLED.show();
    }
    i7++;
  }
}

void r1_rau_led8(int i8){
  if(i8==1){
    for (int i = 56; i<= 57; i++){
      leds[i] = CRGB::Red;
      //FastLED.show();
    }
    FastLED.show();
    //i8=1;
  }
  if(i8==0){
    for (int i = 56; i<= 57; i++){
      leds[i] = CRGB::Black;
      //FastLED.show();
    }
    FastLED.show();
  }
}

void c1_twin_led9(){
  //fadeToBlackBy( leds1, 13, 20);
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis[9] >= 80){
    previousMillis[9] = currentMillis;
    int pos = 58 + random8(28);
    int spalva = 182 + random(103);//182...255 and 0..30
    if(spalva>255)
      spalva= spalva-255;
    leds[pos] = CHSV( spalva , 200, 200);// spalva pagal HUE, kiek baltos, ry6kumas 
    int pos1 = 58 + random8(28);
    leds[pos1] = CRGB::Black;
    FastLED.show();
    int pos2 = 58 + random8(28);
    leds[pos2] = CRGB::Black;
    FastLED.show();
  }
}

void L1_mel_led10(int mode) {
    if (mode == 1) {
        unsigned long currentMillis = millis();
        if (currentMillis - previousMillis[10] >= 80) {
            previousMillis[10] = currentMillis;

            if (iL1b10 >= 118) {
                iL1b10 = 86;
            }
            if (iL1 >= 118) {
                iL1 = 86;
            }
            leds[iL1b10] = CRGB::Blue;
            leds[iL1] = CRGB::Black;
            FastLED.show();
            iL1++;
            iL1b10++;
        }
    } else if (mode == 0) {
        for (int i = 85; i < 118; i++) {
            leds[i] = CRGB::Black;
        }
        FastLED.show();
    }
}

void L1_rau_led11(int mode) {
    if (mode == 1) {
        unsigned long currentMillis = millis();
        if (currentMillis - previousMillis[11] > 250) {
            previousMillis[11] = currentMillis;
            for (int i = 118; i <= 125; i++) {
                if (iL2 >= 125) {
                    iL2 = 118;
                }
                if (i == iL2) {
                    leds[i] = CRGB::Red;
                } else {
                    leds[i] = CRGB::Black;
                }
                FastLED.show();
            }
            iL2++;
        }
    } else if (mode == 0) {
        for (int i = 118; i <= 125; i++) {
            leds[i] = CRGB::Black;
        }
        FastLED.show();
    }
}

void L1_mel_led12(int mode) {
    if (mode == 1) {
        unsigned long currentMillis = millis();
        if (currentMillis - previousMillis[12] >= 500) {
            previousMillis[12] = currentMillis;
            for (int i = 125; i <= 129; i++) {
                if (iL3 >= 130) {
                    iL3 = 125;
                }
                if (i == iL3) {
                    leds[i] = CRGB::Blue;
                } else {
                    leds[i] = CRGB::Black;
                }
                FastLED.show();
            }
            iL3++;
        }
    } else if (mode == 0) {
        for (int i = 125; i <= 129; i++) {
            leds[i] = CRGB::Black;
        }
        FastLED.show();
    }
}

void L1_mel_led13(int mode) {
    if (mode == 1) {
        unsigned long currentMillis = millis();
        if (currentMillis - previousMillis[13] >= 500) {
            previousMillis[13] = currentMillis;
            for (int i = 130; i <= 137; i++) {
                if (iL4 >= 138) {
                    iL4 = 130;
                }
                if (i == iL4) {
                    leds[i] = CRGB::Blue;
                } else {
                    leds[i] = CRGB::Black;
                }
                FastLED.show();
            }
            iL4++;
        }
    } else if (mode == 0) {
        for (int i = 130; i <= 137; i++) {
            leds[i] = CRGB::Black;
        }
        FastLED.show();
    }
}

void L1_rau_led14(int i15){
  if(i15==1){
    for (int i = 138; i<= 139; i++){
      leds[i] = CRGB::Red;
      FastLED.show();
    }
    //i5=1;
  }
  if(i15==0){
    for (int i = 138; i<= 139; i++){
      leds[i] = CRGB::Black;
      FastLED.show();
    }
  }
}

void L1_rau_led15(int i15){
  if(i15==1){
    for (int i = 140; i<= 141; i++){
      leds[i] = CRGB::Red;
      //FastLED.show();
    }
    FastLED.show();
    //i5=1;
  }
  if(i15==0){
    for (int i = 140; i<= 141; i++){
      leds[i] = CRGB::Black;
      //FastLED.show();
    }
    FastLED.show();
  }
}

void L2_mult_led16(int i16){
  if(i16==1){
    for (int i = 142; i<= 149; i++){
      leds[i] = CRGB::White;
      //FastLED.show();
    }
    FastLED.show();
    //i8=1;
  }
  if(i16==0){
    for (int i = 142; i<= 149; i++){
      leds[i] = CRGB::Black;
      //FastLED.show();
    }
    FastLED.show();
  }
}

void R2_mult_led17(int i17){
  if(i17==1){
    for (int i = 150; i<= 166; i++){
      leds[i] = CRGB::White;
      //FastLED.show();
    }
    FastLED.show();
    //i8=1;
  }
  if(i17==0){
    for (int i = 150; i<= 166; i++){
      leds[i] = CRGB::Black;
      //FastLED.show();
    }
    FastLED.show();
  }
}

void LB_mult_led18(int mode) {
    static unsigned long lastBlinkTime = 0;  // To track the time for blinking
    unsigned long currentMillis = millis();

    if (mode == 0) {
        // Turn all LEDs off
        for (int i = 167; i <= 180; i++) {
            leds[i] = CRGB::Black;
        }
        FastLED.show();
    } else if (mode == 1) {
        // Turn all LEDs on (white)
        for (int i = 167; i <= 180; i++) {
            leds[i] = CRGB::White;
        }
        FastLED.show();
    } else if (mode == 2) {
        // Turn all LEDs off except for blinking 168 and 169
        for (int i = 167; i <= 180; i++) {
            if(i != 168 && i != 169)
            leds[i] = CRGB::Black;
        }

        // Blink LEDs 168 and 169 red (1 second red, 1 second black)
        if (currentMillis - lastBlinkTime >= 500) {  // 1 second interval
            lastBlinkTime = currentMillis;

            static bool isRed = false;  // Track the current blink state
            if (isRed) {
                leds[168] = CRGB::Black;
                leds[169] = CRGB::Black;
            } else {
                leds[168] = CRGB::Red;
                leds[169] = CRGB::Red;
            }
            isRed = !isRed;  // Toggle the color state
        }

        FastLED.show();
    }
}



void loop() { 
  

  if (Serial.available() > 0) {  // Check if data is available to read
    receivedState = Serial.parseInt();  // Read the incoming integer
    while (Serial.available() >0 && Serial.read() != '\n');
    Serial.print("Received state: ");
    Serial.println(receivedState);  // Print the received state
  }
  
  // last_received_state = received_state;
    if (receivedState == 0) { ////    žaidimas neprasidėjo
        r1_mel_led1();
        r1_rau_led2();
        r1_mel_led3();
        r1_mel_led4();
        r1_rau_led5(1);
        r1_rau_led6(1);

        r1_ora_led7();
        r1_rau_led8(1);
        c1_twin_led9();


        L1_mel_led10(1);
        L1_rau_led11(1);
        L1_mel_led12(1);
        L1_mel_led13(1);

        L1_rau_led14(1);
        L1_rau_led15(1);

        L2_mult_led16(1);
        R2_mult_led17(1);
        LB_mult_led18(1);
    }


    if (receivedState >= 1 && receivedState < 6) { // tipo pasileido zaidimas
        r1_mel_led1();
        r1_rau_led2();
        r1_mel_led3();
        r1_mel_led4();
        r1_rau_led5(1);
        r1_rau_led6(1);

        r1_ora_led7();
        r1_rau_led8(1);
        c1_twin_led9();


        L1_mel_led10(0);
        L1_rau_led11(0);
        L1_mel_led12(0);
        L1_mel_led13(0);

        L1_rau_led14(0);
         L1_rau_led15(0);

         L2_mult_led16(1);
        R2_mult_led17(1);
        LB_mult_led18(1);
    }
    if(receivedState >= 6){
        r1_mel_led1();
        r1_rau_led2();
        r1_mel_led3();
        r1_mel_led4();
        r1_rau_led5(1);
        r1_rau_led6(1);

        r1_ora_led7();
        r1_rau_led8(1);
        c1_twin_led9();


        L1_mel_led10(1);
        L1_rau_led11(1);
        L1_mel_led12(1);
        L1_mel_led13(1);

        L1_rau_led14(1);
        L1_rau_led15(1);

        L2_mult_led16(1);
        R2_mult_led17(1);
        LB_mult_led18(1);
    }
    if (receivedState == -1) {

        r1_mel_led1();
        r1_rau_led2();
        r1_mel_led3();
        r1_mel_led4();
        r1_rau_led5(1);
        r1_rau_led6(1);

        r1_ora_led7();
        r1_rau_led8(1);
        c1_twin_led9();


        L1_mel_led10(0);
        L1_rau_led11(0);
        L1_mel_led12(0);
        L1_mel_led13(0);

        L1_rau_led14(0);
        L1_rau_led15(0);

        L2_mult_led16(0);
        R2_mult_led17(0); // here

        // Turn off all LEDs affected by LB_mult_led18
        LB_mult_led18(2);

    }

    if (receivedState == -2) {

        r1_mel_led1();
        r1_rau_led2();
        r1_mel_led3();
        r1_mel_led4();
        r1_rau_led5(1);
        r1_rau_led6(1);

        r1_ora_led7();
        r1_rau_led8(1);
        c1_twin_led9();


        L1_mel_led10(1);
        L1_rau_led11(1);
        L1_mel_led12(1);
        L1_mel_led13(1);

        L1_rau_led14(1);
        L1_rau_led15(1);

        L2_mult_led16(0);
        R2_mult_led17(0); // here

        // Turn off all LEDs affected by LB_mult_led18
        LB_mult_led18(2);

    }


  
  
  
}