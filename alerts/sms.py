import smtplib
import requests
import os
from itertools import combinations

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
RECIPIENT = os.getenv("RECIPIENT")

API_URL = "https://api.x-eh.com/extapi3/"
BAR_TO_PSI = 14.5038

def send_message(message):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, RECIPIENT, message)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

def get_tire_data():
    """Returns car_name and tire pressures in psi."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()

        car_name = data["data"]["car"]["car_name"]

        tpms = data["data"]["status"]["tpms_details"]
        pressures = {
            "FL": tpms["tpms_pressure_fl"] * BAR_TO_PSI,
            "FR": tpms["tpms_pressure_fr"] * BAR_TO_PSI,
            "RL": tpms["tpms_pressure_rl"] * BAR_TO_PSI,
            "RR": tpms["tpms_pressure_rr"] * BAR_TO_PSI,
        }

        return car_name, pressures
    except Exception as e:
        print(f"Error getting tire pressure: {e}")
        return None, None

def check_pressure_difference(car_name, pressures):
    """Checks if any tire pressure differs by more than 2 psi."""
    alerts = []
    for (tire1, psi1), (tire2, psi2) in combinations(pressures.items(), 2):
        diff = abs(psi1 - psi2)
        if diff > 2:
            alerts.append(f"{tire1} vs {tire2} ({diff:.1f} psi difference)")

    if alerts:
        alert_message = (
            f"ALERT for {car_name}\n"
            + "\n".join(alerts)
        )
        return alert_message
    return None

if __name__ == "__main__":
    car_name, pressures = get_tire_data()
    if pressures:
        message = (
            f"{car_name} Tire Pressure (psi):\n"
            + " / ".join([f"{tire}: {psi:.1f}" for tire, psi in pressures.items()])
        )
        print(message)
        send_message(message)

        alert = check_pressure_difference(car_name, pressures)
        if alert:
            print(alert)
            send_message(alert)
