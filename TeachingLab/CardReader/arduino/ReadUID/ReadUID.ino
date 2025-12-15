#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

// I2C Connections (SDA/SCL)
#define PN532_IRQ   (2)
#define PN532_RESET (3) 

Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);

void setup(void) {
  Serial.begin(115200);
  while (!Serial) delay(10); 

  // --- DIAGNOSTICS (Only runs once at start) ---
  Serial.println("Initializing...");

  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (! versiondata) {
    // If you see this, check your wiring!
    Serial.println("ERROR: Didn't find PN53x board");
    while (1); 
  }
  
  // Configure board to read RFID tags
  nfc.SAMConfig();
  
  Serial.println("System Ready. Waiting for card...");
}

void loop(void) {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };  
  uint8_t uidLength;                        

  // Wait for an ISO14443A type card
  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
  
  if (success) {
    
    // Only process 4-byte UIDs (Classic Mifare)
    if (uidLength == 4)
    {
      // --- 1. CALCULATE BIG ENDIAN (Standard Hex Reading) ---
      uint32_t uid_big = 0;
      uid_big = uid[0];
      uid_big <<= 8;
      uid_big |= uid[1];
      uid_big <<= 8;
      uid_big |= uid[2];
      uid_big <<= 8;
      uid_big |= uid[3];

      // --- 2. CALCULATE LITTLE ENDIAN (Reversed) ---
      uint32_t uid_little = 0;
      uid_little = uid[3];
      uid_little <<= 8;
      uid_little |= uid[2];
      uid_little <<= 8;
      uid_little |= uid[1];
      uid_little <<= 8;
      uid_little |= uid[0];

      // --- 3. PRINT CSV FORMAT ---
      // Format: HEX_VALUE, DEC_LITTLE_ENDIAN, DEC_BIG_ENDIAN
      
      Serial.print("NewCard:");
      Serial.print(uid_big, HEX); 
      Serial.print(",");
      Serial.println(uid_little);
      
      // Delay 1 second to avoid spamming the same card
      delay(1000);
    }
  }
}