import smtplib
import requests
import os
from itertools import combinations
import json
import time

# Retrieve environment variables
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
# RECIPIENTS is now a list, split from a comma-separated string
RECIPIENTS = os.getenv("RECIPIENTS").split(',')
AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME")
AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")

# Constants
API_ENDPOINTS = {
    "car1": "https://api.x-eh.com/extapi2/",
    "car2": "https://api.x-eh.com/extapi3/"
}
BAR_TO_PSI = 14.5038
POLLING_INTERVAL = 3600 # 1 hour in seconds
CAR_DELAY = 60 # 60 seconds delay between car checks

def get_tire_data(api_url):
    """
    Fetches car name and tire pressures in psi from a given API endpoint.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(api_url, auth=(AUTH_USERNAME, AUTH_PASSWORD), headers=headers)
        response.raise_for_status()
        print(f"Request to {api_url} successful!")
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
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {api_url}: {e}")
        return None, None
    except KeyError as e:
        print(f"Error parsing JSON from {api_url}. Missing key: {e}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred for {api_url}: {e}")
        return None, None

def send_message(subject, body):
    """
    Sends an email message with a given subject and body to multiple recipients.
    """
    message = f"Subject: {subject}\n\n{body}"
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, RECIPIENTS, message)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

def check_pressure_difference(car_name, pressures):
    """
    Checks if any tire pressure differs by more than 2 psi.
    """
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

def main():
    """
    Main function for continuous monitoring of tire pressures.
    """
    # Use a dictionary to keep track of the alert state for each car
    alert_states = {car_name_key: False for car_name_key in API_ENDPOINTS.keys()}
    
    while True:
        for car_name_key, api_url in API_ENDPOINTS.items():
            print(f"--- Processing {car_name_key} from {api_url} ---")
            car_name, pressures = get_tire_data(api_url)
            
            if pressures:
                message_body = (
                    f"{car_name} Tire Pressure (psi):\n"
                    + " / ".join([f"{tire}: {psi:.1f}" for tire, psi in pressures.items()])
                )
                print(message_body)
                
                alert = check_pressure_difference(car_name, pressures)
                
                if alert:
                    if not alert_states[car_name_key]:
                        print(f"Tire pressure ALERT for {car_name} detected. Sending email.")
                        send_message(f"Tire Pressure ALERT: {car_name}", alert)
                        alert_states[car_name_key] = True
                    else:
                        print(f"Tire pressure ALERT for {car_name} is ongoing. No new email sent.")
                else:
                    if alert_states[car_name_key]:
                        send_message(f"Tire Pressure ALERT Resolved: {car_name}", "All tire pressures are now within the acceptable range.")
                        print(f"Tire pressure ALERT for {car_name} has been resolved.")
                    
                    alert_states[car_name_key] = False
            print("-" * 40)
            
            # Add a small delay between each car check
            time.sleep(CAR_DELAY)
        
        # Wait for a longer interval before the next full cycle
        print(f"Waiting for {POLLING_INTERVAL/60} minutes before the next full check...")
        time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    main()
