// TODO : limites déplacement moteur (0 - 10 000 par exemple)
// TODO : accélération / décélération moteur (pour éviter les à-coups)

// Bibliothèques
#include <Wire.h>
#define AS5600_ADDRESS 0x36  // Adresse I2C de l'AS5600
#define RAW_ANGLE_REG  0x0C  // Registre de l'angle brut (12 bits)
#define CONFIG_REG     0x0B  // Registre de configuration
#define PIN_AS5600_PWM A0


// Brochage moteur
const uint8_t PIN_STEP = 6;   // STEP -> D9
const uint8_t PIN_DIR  = 5;   // DIR -> D8
const uint8_t PIN_EN   = 7;  // EN -> D10 (avec 1k série, et pull-up 10k vers VDD)
const uint8_t ledPin   = 13;  // LED -> 13

// Variables globales
long motorPosition = 0;       // en micro-pas
float angle_i2c = 0.0;        // en degrés
float stepsPerDegree = 15432.0 / 360.0;  // 42.9 pas/degré

// Déclarations des fonctions (en haut du fichier)
void blinkLED(int nb_clignotements, int delai_ms);
void activateMotor();
void deactivateMotor();
void moveSteps(long steps, unsigned int usDelayMin, unsigned int dir);
void get_angle();
float get_angle_pwm();
void get_angle_i2c();
bool moveToAnglePID(float targetAngle, float precision, int maxIterations = 50);
void moveToAngle(float targetAngle, float precision = 0.3, int maxPIDIterations = 50);

// Buffer pour la lecture série
#define SERIAL_BUFFER_SIZE 64
char serialBuffer[SERIAL_BUFFER_SIZE];
uint8_t bufferIndex = 0;

enum AngleMode {
    MODE_I2C,
    MODE_PWM
};

AngleMode angleMode = MODE_I2C;

void setup() {
    Serial.begin(9600);  // Initialise la communication série à 9600 bauds
    Wire.begin();        // initialise I²C sur A4/A5
    delay(500);
    Wire.setClock(100000);
    Wire.setWireTimeout(1000, true);
    while (!Serial) {
        ;  // Attend que le port série soit prêt
    }

    // Initial states
    pinMode(PIN_STEP, OUTPUT);
    digitalWrite(PIN_STEP, LOW);
    pinMode(PIN_DIR, OUTPUT);
    digitalWrite(PIN_DIR, LOW);
    // Assure driver OFF au boot (EN = HIGH)
    pinMode(PIN_EN, OUTPUT);
    digitalWrite(PIN_EN, HIGH);
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);

    // Vérifie la présence de l'AS5600
/*     Wire.beginTransmission(AS5600_ADDRESS);
    byte error = Wire.endTransmission();
    if (error == 0) {
        Serial.println("OK CONNECT AS5600");
    } else {
        Serial.print("ERR 102 AS5600 : ");
        Serial.print(error);
    } */
    Serial.println("READY");
}

void loop() {
    // Lecture non-bloquante du Serial
    while (Serial.available() > 0) {
        char incomingChar = Serial.read();
        if (incomingChar == '\n') {
            serialBuffer[bufferIndex] = '\0';  // Termine la chaîne
            processCommand(serialBuffer);
            bufferIndex = 0;  // Réinitialise le buffer
        } else if (bufferIndex < SERIAL_BUFFER_SIZE - 1) {
            serialBuffer[bufferIndex++] = incomingChar;
        }
    }
}

void processCommand(char* command) {
    char* token;
    char* cmd = strtok(command, " ");

    if (strcmp(cmd, "led") == 0) {
        int nb_clignotements = atoi(strtok(NULL, " "));
        int delai_ms = atoi(strtok(NULL, " "));
        blinkLED(nb_clignotements, delai_ms);
        Serial.println("OK");
    }
    else if (strcmp(cmd, "move") == 0) {
        token = strtok(NULL, " ");
        if (token != NULL) {
            long steps = atol(token);
            token = strtok(NULL, " ");
            unsigned int usDelay = token ? atoi(token) : 400;
            token = strtok(NULL, " ");
            unsigned int dir = token ? atoi(token) : 0;
            activateMotor();
            digitalWrite(PIN_DIR, dir ? HIGH : LOW);
            moveSteps(steps, usDelay, dir);
            deactivateMotor();
            Serial.println("DONE");
        }
    }
    else if (strcmp(cmd, "pos") == 0) {
        Serial.print("Position: ");
        Serial.println(motorPosition);
    }
    else if (strcmp(cmd, "angle") == 0) {
        get_angle();
        Serial.println(angle_i2c, 2);
        Serial.println("OK READ AS5600");
    }
    else if (strcmp(cmd, "goto") == 0) {
        float targetAngle = atof(strtok(NULL, " "));
        float precision = 0.5;
        moveToAngle(targetAngle, precision);
    }
}

// ---------- Fonctions de contrôle de la led ----------
void blinkLED(int nb_clignotements, int delai_ms) {
    for (int i = 0; i < nb_clignotements; i++) {
        digitalWrite(ledPin, HIGH);
        delay(delai_ms);
        digitalWrite(ledPin, LOW);
        delay(delai_ms);
    }
}

// ---------- Fonctions de contrôle moteur ----------
void activateMotor() {
    digitalWrite(PIN_EN, LOW);  // active le driver
    delay(2);  // petit délai pour que le driver s'initialise
}

void deactivateMotor() {
    digitalWrite(PIN_EN, HIGH);  // driver désactivé -> plus de maintien
}

// steps: nombre de pas (microsteps selon réglage du driver, ici 1/8e)
// dir: 0 = sens A, 1 = sens B
void moveSteps(long steps, unsigned int usDelayMin, unsigned int dir) {
    digitalWrite(ledPin, HIGH);
    const unsigned int usDelayMinActual = 100;
    const unsigned int usDelayStart = 1000;
    const unsigned int timeIncrement = 10;

    if (usDelayMin < usDelayMinActual) {
        usDelayMin = usDelayMinActual;
    }

    int accel_steps = (usDelayStart - usDelayMin + timeIncrement - 1) / timeIncrement;
    if (accel_steps < 0) accel_steps = 0;

    if (steps <= 2 * accel_steps && accel_steps > 0) {
        long halfSteps = steps / 2;
        for (long i = 0; i < steps; i++) {
            unsigned int usDelay = (i < halfSteps) ?
                max(usDelayStart - (i * timeIncrement), usDelayMin) :
                min(usDelayMin + ((i - halfSteps) * timeIncrement), usDelayStart);
            digitalWrite(PIN_STEP, HIGH);
            delayMicroseconds(usDelay);
            digitalWrite(PIN_STEP, LOW);
            delayMicroseconds(usDelay);
        }
    } else {
        long stepsAtFullSpeed = max(steps - 2 * accel_steps, 0L);
        for (long i = 0; i < accel_steps; i++) {
            unsigned int usDelay = max(usDelayStart - (i * timeIncrement), usDelayMin);
            digitalWrite(PIN_STEP, HIGH);
            delayMicroseconds(usDelay);
            digitalWrite(PIN_STEP, LOW);
            delayMicroseconds(usDelay);
        }
        for (long i = 0; i < stepsAtFullSpeed; i++) {
            digitalWrite(PIN_STEP, HIGH);
            delayMicroseconds(usDelayMin);
            digitalWrite(PIN_STEP, LOW);
            delayMicroseconds(usDelayMin);
        }
        for (long i = 0; i < accel_steps; i++) {
            unsigned int usDelay = min(usDelayMin + (i * timeIncrement), usDelayStart);
            digitalWrite(PIN_STEP, HIGH);
            delayMicroseconds(usDelay);
            digitalWrite(PIN_STEP, LOW);
            delayMicroseconds(usDelay);
        }
    }

    // Mise à jour de la position (en micro-pas)
    if (dir == 0) {
        motorPosition += steps;  // Sens positif
    } else {
        motorPosition -= steps;  // Sens négatif
    }

    // Gestion du débordement (optionnel, pour garder motorPosition dans [0, 1600[)
    motorPosition = ((motorPosition % 1600) + 1600) % 1600;
    digitalWrite(ledPin, LOW);
}

void get_angle() {
    if (angleMode == MODE_I2C) {
        get_angle_i2c();
    } else {
        angle_i2c = get_angle_pwm();
    }
}

float get_angle_pwm() {
    unsigned long highTime = pulseIn(PIN_AS5600_PWM, HIGH, 100000);
    unsigned long lowTime  = pulseIn(PIN_AS5600_PWM, LOW, 100000);

    if (highTime == 0 || lowTime == 0) {
        Serial.println("ERR PWM timeout");
        return -1;
    }

    float period = highTime + lowTime;
    float duty = (float)highTime / period;

    // AS5600 PWM = 0–100% sur 360°
    return duty * 360.0;
}

void get_angle_i2c() {
    for (int attempts = 0; attempts < 3; attempts++) {
        Wire.beginTransmission(AS5600_ADDRESS);
        Wire.write(RAW_ANGLE_REG);
        byte error = Wire.endTransmission();
        if (error == 0) {
            Wire.requestFrom(AS5600_ADDRESS, 2);
            if (Wire.available() >= 2) {
                uint16_t rawAngle = (Wire.read() << 8) | Wire.read();
                rawAngle &= 0x0FFF;
                angle_i2c = (rawAngle * 360.0) / 4096.0;
                return;
            }
        }
        delay(10);
    }
    Serial.println("ERR I2C: failed after 3 attempts");
    angle_i2c = -1.0;
}

// --------- Fonction de déplacement vers un angle ---------
float Kp = 1.0;  // Coefficient proportionnel
float Ki = 0.1;  // Coefficient intégral
float Kd = 0.01; // Coefficient dérivé


bool moveToAnglePID(float targetAngle, float precision = 0.3, int maxIterations = 50) {
    float Kp = 3.0, Ki = 0.0, Kd = 0.1;
    float integral = 0.0, previousError = 0.0;

    for (int i = 0; i < maxIterations; i++) {
        get_angle();
        float currentAngle = angle_i2c;
        if (currentAngle < 0) {
            Serial.println("ERR 102 AS5600 read failed in PID");
            return false;
        }

        float error = targetAngle - currentAngle;
        if (error > 180) error -= 360;
        else if (error < -180) error += 360;

        if (fabs(error) < precision) {
            return true; // convergence atteinte
        }

        integral += error;
        float derivative = error - previousError;
        float output = Kp * error + Ki * integral + Kd * derivative;

        int stepCount = constrain(abs(output) * stepsPerDegree, 1, 10);
        uint8_t dir = (output > 0) ? 0 : 1;

        activateMotor();
        digitalWrite(PIN_DIR, dir ? HIGH : LOW);
        moveSteps(stepCount, 100, dir);
        deactivateMotor();

        previousError = error;
        delay(10);
    }

    return false; // Échec après toutes les itérations
}

void moveToAngle(float targetAngle, float precision = 0.3, int maxPIDIterations = 50) {
    digitalWrite(ledPin, HIGH);

    // Lecture initiale
    get_angle();
    float startAngle = angle_i2c;
    if (startAngle < 0) {
        Serial.println("ERR 102 AS5600 read failed");
        blinkLED(3, 200);
        return;
    }

    // Calcul de l’erreur en degrés (gestion 360°)
    float error = targetAngle - startAngle;
    if (error > 180) error -= 360;
    else if (error < -180) error += 360;

    // Si l’erreur est très faible, inutile de bouger
    if (fabs(error) < (2 * precision)) {
        Serial.println("OK MOVE skipped (already in position)");
        digitalWrite(ledPin, LOW);
        return;
    }

    // Mouvement grossier
    int theoreticalSteps = round(error * stepsPerDegree);
    uint8_t dir = (error > 0) ? 0 : 1;

    activateMotor();
    digitalWrite(PIN_DIR, dir ? HIGH : LOW);
    moveSteps(abs(theoreticalSteps), 200, dir);
    deactivateMotor();

    // Vérification du déplacement réel
    get_angle();
    float endAngle = angle_i2c;
    if (endAngle < 0) {
        Serial.println("ERR 102 AS5600 read failed after move");
        blinkLED(3, 200);
        digitalWrite(ledPin, LOW);
        return;
    }

    float delta = fabs(endAngle - startAngle);
    if (delta > 180) delta = 360 - delta; // gestion du 0°/360°

    if (fabs(error) > 5.0 && delta < 0.5) {
        Serial.println("ERR 101 Motor blocked - no movement detected");
        blinkLED(10, 100);
        digitalWrite(ledPin, LOW);
        return;
    }

    // Ajustement fin avec PID limité
    get_angle();;
    float residualError = fabs(targetAngle - angle_i2c);

    if (residualError > precision) {
        bool success = moveToAnglePID(targetAngle, precision, maxPIDIterations);
        if (!success) {
            Serial.println("ERR 103 PID did not converge");
            blinkLED(5, 200);
            digitalWrite(ledPin, LOW);
            return;
        }
    }

    digitalWrite(ledPin, LOW);
    Serial.println("OK MOVE completed");
}
