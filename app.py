import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY = "tT8_3FDErKx9"
PROJECT_TOKEN = "tywP9jSNS9Aj"
RUN_TOKEN = "tc40WWSOVSGd"


class Data:
    def __init__(self, project_token, api_key):
        self.project_token = project_token
        self.api_key = api_key
        self.params = {
            "api_key": api_key
        }
        self.data = self.get_most_recent_data()

    def get_most_recent_data(self):
        response = requests.get(f"https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data",
                                params=self.params)
        data = json.loads(response.text)
        return data

    def get_total_cases(self):
        data = self.data["total"]
        for content in data:
            if content["name"] == "Coronavirus Cases:":
                return content["value"]

    def get_total_deaths(self):
        data = self.data["total"]
        for content in data:
            if content["name"] == 'Deaths:':
                return content["value"]

    def get_by_country(self, country):
        data = self.data["country"]
        for content in data:
            if content["name"].lower() == country.lower():
                return content

    def get_list_of_countries(self):
        data = self.data["country"]
        countries = []
        for country in data:
            countries.append(country["name"].lower())
        return countries

    ####
    def update_data(self):
        response = requests.post(f"https://www.parsehub.com/api/v2/projects/{self.project_token}/run",
                                 params=self.params)

        def poll():
            time.sleep(0.1)
            while True:
                old_data = self.data
                new_data = self.get_most_recent_data()
                if new_data != old_data:
                    self.data = new_data
                    print("DATA UPDATED SUCCESSFULLY ")
                    break
                time.sleep(5)

        t = threading.Thread(target=poll)
        t.start()


def speak(text):
    engine = pyttsx3.init()
    en_voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
    engine.setProperty('voice', en_voice_id)
    engine.say(text)
    engine.runAndWait()


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        audio_text = ""

        try:
            audio_text = r.recognize_google(audio)
        except Exception as e:
            speak("please speak more clearly")
    return audio_text


def main():
    print("------- COVID 19 STATISTICS (WITH VOICE RECOGNITION) -------")
    data = Data(PROJECT_TOKEN, API_KEY)
    END_PHRASE = "stop"
    TOTAL_PATTERNS = {
        re.compile("[\w\s]+ total [\w\s]+ cases"): data.get_total_cases,
        re.compile("[\w\s]+ total cases"): data.get_total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
        re.compile("[\w\s]+ total deaths"): data.get_total_deaths
    }
    COUNTRY_PATTERNS = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_by_country(country)["total_cases"],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_by_country(country)["total_deaths"]
    }
    countries = data.get_list_of_countries()
    while True:
        print("listening...")
        user_text = get_audio()
        answer = None
        print(user_text, "\n")
        for pattern, fct in COUNTRY_PATTERNS.items():
            if pattern.match(user_text):
                words = set(user_text.lower().split(" "))
                for country in countries:
                    if country in words:
                        answer = fct(country)
                        break
        for pattern, fct in TOTAL_PATTERNS.items():
            if pattern.match(user_text):
                answer = fct()
                break

        if answer:
            print(answer)
            speak(answer)
        if user_text.find("update") != -1:
            print("updating data ...")
            data.update_data()
        if user_text.find(END_PHRASE) != -1:  # stop the app
            break


main()
