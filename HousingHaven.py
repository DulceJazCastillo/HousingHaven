import streamlit as st
from openai import OpenAI
import csv 
import pandas as pd
import folium 
from streamlit_folium import st_folium
from audio_recorder_streamlit import audio_recorder
homie = OpenAI(api_key="")

datafile = 'Affordable_Housing_info.csv'
page_bg_img = '''
<style>
[data-testid="stAppViewContainer"] {
background-image: url("https://images.unsplash.com/photo-1511389026070-a14ae610a1be?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
background-size: cover;
}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

def transcribe_text_to_voice(audio_location):
    audio_file = open(audio_location, "rb")
    transcript = homie.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcript.text

def create_profile(text):
    response = homie.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages = [
            {
                "role": "system",
                "content": "You are a highly skilled AI trained to make profiles based on the audio file contents. The profiles are neatly organized and easy to read."
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )
    return response.choices[0].message.content

def get_completion(prompt, model="gpt-3.5-turbo"):
    completion = homie.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": """
             You are a chatbot that is helping with affordable housing and is knowledgeable on what places are good to live in based on what inputs are given.
             The results should a list of the users needs when looking for a new place to live. Is should only about the user needs nothing else.
             Keep it to a minimum of 5 points.   
             """},
            {"role": "user", "content": prompt},
        ]
    )
    if completion.choices:
        return completion.choices[0].message.content
    else:
        return "Sorry, unable to generate a response for this prompt."

def main():
    menu_selection = st.sidebar.radio("Menu", ["Home", "Chat", "Profile Maker", "Housing"])
        
    if menu_selection == "Home":
        st.title("Welcome to Housing Haven")
        st.write("Warning Personal information that is put in maybe saved into the systems!")
        st.write('''
            Welcome to our About page, we are Housing haven. Our goal is to help provide information on what to do about housing based on your own information that you have provided. 
            We have three main features.
            1. Our chat box where a Model asks for these in order from the user: name, location, situation, annual income, any other information that the user wishes to provide to the model to better help equip themselves. 
            2. The second takes the given or preferred location(s) and eligibility based on tax forms, bills, see if you are filed as an independent or dependent to match you with a program that is best to assist the customer. 
            3. The last one analyzes an audio file and creates a profile based on the audio contents.
''')
        st.write("For support contact us at housinghaven@gmail.com")

    elif menu_selection == "Chat":
        st.title("Housing Haven AI Chatbot")
        with st.form(key="chat"):
            st.write("Please enter the following information:")
            name = st.text_input("Your Name:")
            location = st.text_input("Your Location:")
            situation = st.text_area("Describe your housing situation:")
            needs = st.text_area("What are your housing needs:")
            income = st.number_input("What is your monthly rental:", min_value=0, step=10000)

            submitted = st.form_submit_button("Submit")

            if submitted:
                prompt = f"Name: {name}\nLocation: {location}\nSituation: {situation}\nNeeds: {needs}\n Annual Income: {income}\n"
                response = get_completion(prompt)
                st.write("Housing Haven AI:")
                st.write(response)

    elif menu_selection == "Profile Maker":
        st.title("Audio Analysis and Profile Creation")
        st.write("Please give a brief description on who you are and what you're looking for in terms of housing.")

        recording_duration = st.slider("Recording Duration (seconds)", min_value=10, max_value=120, value=60, step=10)

        audio_bytes = audio_recorder(recording_duration)
        if audio_bytes:
            audio_location = "audio_file.wav"
            with open(audio_location, "wb") as f:
                f.write(audio_bytes)

            text = transcribe_text_to_voice(audio_location)
            st.write("Does the information here look correct? If not please record once again.")
            st.write(text)

            continue_recording = st.button("Continue")
            if continue_recording:
                api_response = create_profile(text)
                st.write("Here is your Homie Profile:")
                st.write(api_response)
            else:
                st.write("")

    elif menu_selection == "Housing":
        @st.cache_data 
        def read_data():
            def parse_lat_lon(point):
                return point.split("(")[-1].split(")")[0].split()
            
            data = []
            with open(datafile, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                print("reading...")
                for row in reader: 
                    longitude, latitude = parse_lat_lon(row['New Georeferenced Column'])
                    data.append({
                        'name': row['City'],
                        'latitude': float(latitude),
                        'longitude': float(longitude)
                    })
                return data

        data = read_data()

        STARTING_POINT = (37.36125, -121.90595)
        map = folium.Map(location = STARTING_POINT, zoom_start=9)

        for city in data:
            location = city['latitude'], city['longitude']
            folium.Marker(location, popup=city['name']).add_to(map)


        st.header("Affordable Housing Locations in the Bay Area")

        st_folium(map, width=700)
        df= pd.read_csv("Affordable_Housing_Info.csv")
        st.dataframe(df, height=1500)

if __name__ == "__main__":
    main()