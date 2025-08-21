import smtplib
import requests
import os
from itertools import combinations

# Retrieve environment variables
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
RECIPIENT = os.getenv("RECIPIENT")
ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("API_REFRESH_TOKEN")

API_URL = "https://api.x-eh.com/extapi3/"
TOKEN_REFRESH_URL = "https://api.x-eh.com/api/token/refresh/" # Assuming this is the correct URL
BAR_TO_PSI = 14.5038

# def get_new_access_token():
#     try:
#         # Send the refresh token to the token refresh endpoint
#         response = requests.post(TOKEN_REFRESH_URL, json={'refresh': REFRESH_TOKEN})
#         response.raise_for_status()
#         new_tokens = response.json()
        
#         # In a real-world scenario, you'd need to update the GitHub Secret.
#         # This is not possible directly from a GitHub Action.
#         # For simplicity in this script, we'll just return the new token.
#         return new_tokens.get('access')
#     except Exception as e:
#         print(f"Failed to refresh token: {e}")
#         return None

def get_tire_data():
    """Returns car_name and tire pressures in psi."""
    global ACCESS_TOKEN
    
    # Use a loop to handle token expiration
    for _ in range(2): # Attempt the request twice
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        
        try:
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status()
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
            # Check for a 401 Unauthorized error (likely due to an expired token)
            if e.response.status_code == 401:
                print("Access token expired, attempting to refresh...")
                new_token = get_new_access_token()
                if new_token:
                    ACCESS_TOKEN = new_token
                    # Loop will now try the request again with the new token
                    continue
            
            # If it's a different error or refresh failed, print and return
            print(f"API Error: {e}")
            return None, None
            
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None, None

    # If both attempts fail
    return None, None

def send_message(message):
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
