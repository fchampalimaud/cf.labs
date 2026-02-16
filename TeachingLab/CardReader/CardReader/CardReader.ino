/**************************************************************************/
/* INCREDIBLE CARD DUMPER for Arduino Uno + PN532
    
    This sketch attempts to read EVERY readable block on the card.
    It prints the output in a Hex/ASCII matrix, similar to a hex editor.
*/
/**************************************************************************/

#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

// I2C Configuration (Standard for Shields on Uno)
// Interrupt (IRQ) is on Pin 2
// Reset is on Pin 3
#define PN532_IRQ   (2)
#define PN532_RESET (3)

Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);

void setup(void) {
  Serial.begin(115200);
  while (!Serial) delay(10); 

  Serial.println("----------------------------------------");
  Serial.println("     PN532 NFC READER - FULL DUMP       ");
  Serial.println("----------------------------------------");

  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (! versiondata) {
    Serial.print("Didn't find PN53x board");
    while (1); // Halt
  }
  
  Serial.print("Found chip PN5"); Serial.println((versiondata>>24) & 0xFF, HEX); 
  Serial.println("Waiting for an ISO14443A Card to dump...");
  Serial.println("");
}

void loop(void) {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };  // Buffer to store the returned UID
  uint8_t uidLength;                        // Length of the UID (4 or 7 bytes)

  // 1. Wait for a card
  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
  
  if (success) {
    Serial.println("\n---------------- CARD DETECTED ----------------");
    
    // 2. Print Basic Info
    Serial.print("UID Value (HEX): ");
    nfc.PrintHex(uid, uidLength);
    Serial.print("UID Length:      "); Serial.print(uidLength, DEC); Serial.println(" bytes");

    // 3. Determine Card Type and Dump Memory
    if (uidLength == 4)
    {
      Serial.println("Type:            Mifare Classic (1KB)");
      Serial.println("Action:          Attempting full sector dump...");
      dumpMifareClassic(uid, uidLength);
    }
    else if (uidLength == 7)
    {
      Serial.println("Type:            Mifare Ultralight");
      Serial.println("Action:          Attempting full page dump...");
      dumpMifareUltralight();
    }
    else 
    {
      Serial.println("Type:            Unknown / Standard ISO14443A");
      Serial.println("Note:            Cannot dump memory without known protocol.");
    }
    
    Serial.println("\n--- Scan complete. Remove card to scan again. ---");
    delay(3000); // Wait before scanning again to avoid spamming
  }
}

// =============================================================
//  HELPER: DUMP MIFARE CLASSIC (1K)
// =============================================================
void dumpMifareClassic(uint8_t *uid, uint8_t uidLength) {
  // Default Key A (Factory Default)
  uint8_t keya[6] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
  uint8_t data[16];
  uint8_t success;

  // Mifare Classic 1K has 16 Sectors (0 to 15)
  // Each Sector has 4 Blocks
  for (uint8_t sector = 0; sector < 16; sector++) {
    
    Serial.println("-----------------------------------------------");
    Serial.print("SECTOR "); Serial.print(sector, DEC); 
    
    // Authenticate the Sector first
    // We use the first block of the sector (sector * 4) to authenticate
    success = nfc.mifareclassic_AuthenticateBlock(uid, uidLength, sector * 4, 0, keya);
    
    if (success) {
      Serial.println(": Auth SUCCESS (Key A: FF FF FF FF FF FF)");
      
      // If Auth success, read all 4 blocks in this sector
      for (uint8_t i = 0; i < 4; i++) {
        uint8_t blockNum = (sector * 4) + i;
        
        // Read the block
        success = nfc.mifareclassic_ReadDataBlock(blockNum, data);
        
        if (success) {
          // Print Block Number
          Serial.print("  Block "); 
          if(blockNum < 10) Serial.print(" "); // Alignment padding
          Serial.print(blockNum); Serial.print(":  ");
          
          // Print HEX data
          nfc.PrintHexChar(data, 16); 
        } else {
          Serial.print("  Block "); Serial.print(blockNum); Serial.println(": [Read Failed]");
        }
      }
    } else {
      Serial.println(": Auth FAILED (Unknown Key / Locked)");
    }
  }
}

// =============================================================
//  HELPER: DUMP MIFARE ULTRALIGHT
// =============================================================
void dumpMifareUltralight() {
  uint8_t data[32]; // Ultralight reads 4 pages at once sometimes, but we read 1 page (4 bytes) at a time
  uint8_t success;

  // Print Header
  Serial.println("Page   Hex Data          ASCII");
  Serial.println("----   --------          -----");

  // Ultralight usually has pages 0 to 15 readable standard
  for (uint8_t page = 0; page < 16; page += 4) {
    // Read 4 pages at a time (standard Adafruit function reads 16 bytes/4 pages at once)
    success = nfc.mifareultralight_ReadPage(page, data);
    
    if (success) {
      for(uint8_t i=0; i<4; i++) {
        uint8_t currentPage = page + i;
        Serial.print("  "); 
        if(currentPage < 10) Serial.print("0");
        Serial.print(currentPage); 
        Serial.print("   ");
        
        // Print the 4 bytes of this page
        for(uint8_t b=0; b<4; b++) {
           uint8_t byteVal = data[(i*4)+b];
           if(byteVal < 0x10) Serial.print("0");
           Serial.print(byteVal, HEX); Serial.print(" ");
        }
        
        Serial.print("    ");
        
        // Print ASCII representation
        for(uint8_t b=0; b<4; b++) {
           char c = data[(i*4)+b];
           // Only print printable characters (ASCII 32-126)
           if (c >= 32 && c <= 126) Serial.print(c);
           else Serial.print(".");
        }
        Serial.println("");
      }
    }
  }
}