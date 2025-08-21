import smtplib
import requests
import os
from itertools import combinations

# Retrieve environment variables
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
RECIPIENT = os.getenv("RECIPIENT")
AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME")
AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")

# Constants
# API_URL = "https://api.x-eh.com/extapi3/"
API_URL = "https://excuser-three.vercel.app/v1/excuse/3"
BAR_TO_PSI = 14.5038

def get_tire_data():
    """Fetches car name and tire pressures in psi using Basic Auth."""
    
    # Define a user-agent header to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Pass the auth and headers to the requests.get() call
        response = requests.get(API_URL, auth=(AUTH_USERNAME, AUTH_PASSWORD), headers=headers)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        print("Request successful!")
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
    
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        return None, None
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None

def send_message(message):
    """Sends an email message."""
    # (Email sending logic remains the same)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, RECIPIENT, message)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

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
