import streamlit as st
import urllib, os
import requests
import json
import pandas as pd
from PIL import Image
import time
from typing import Union, Optional

from pathlib import Path


# Download a single file and make its content available as a string.
@st.cache(show_spinner=False)
def get_file_content_as_string(path):
    if Path(path).exists:
        return open(path).read()
    url = "https://raw.githubusercontent.com/cwerner/imgcaption-ui/master/" + path
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")


class EndPoint:
    def __init__(
        self,
        url: str,
        port: Union[str, int],
        secure: bool = False,
        name: str = "UNKNOWN",
    ):
        self.url = url
        self.name = name
        self.port = port
        self.secure = secure
        self.name = name

    def __repr__(self):
        return self.format()

    def format(self, extra: Optional[str] = ""):
        prefix = "https://" if self.secure else "http://"
        return f"{prefix}{self.url}:{self.port}{extra}"

    def is_reachable(self, timeout: Optional[int] = 3):
        try:
            response = requests.get(self.format(), timeout=timeout)
        except requests.exceptions.ConnectTimeout:
            return False
        return True if response.status_code < 400 else False


ep1 = EndPoint("172.27.60.92", 5000, secure=False, name="InceptionV3")
ep2 = EndPoint("172.27.60.92", 5001, secure=False, name="UNDEFINED")
endpoints = {ep.name: ep for ep in [ep1, ep2]}


def main():

    readme_text = st.markdown(get_file_content_as_string("instructions.md"))

    # Once we have the dependencies, add a selector for the app mode on the sidebar.
    st.sidebar.title("What to do")
    app_mode = st.sidebar.selectbox(
        "Choose the app mode",
        ["Show instructions", "Run the app", "Show the source code"],
    )
    if app_mode == "Show instructions":
        st.sidebar.success('To continue select "Run the app".')
    elif app_mode == "Show the source code":
        readme_text.empty()
        st.code(get_file_content_as_string("app.py"))
    elif app_mode == "Run the app":
        readme_text.empty()
        run_the_app()


# This is the main app app itself, which appears when the user selects "Run the app".
def run_the_app():

    st.header("General")
    st.write(
        "👈 Please provide an image by drag-dropping it onto the canvas or navigating to it"
    )

    # select endpoint
    st.sidebar.subheader("Endpoints")

    endpoint = st.sidebar.radio("Choose model", list(endpoints.keys()))

    # @st.cache
    # def process_image():

    uploaded_file = st.sidebar.file_uploader("Select image", type=["png", "jpg"])

    if uploaded_file:

        files = {"image": ("local.jpg", uploaded_file, "image/jpg")}

        # image = Image.open(fpath)
        st.image(uploaded_file, caption="Image to process", use_column_width=True)

        with st.spinner("Quering server..."):
            # check if reachable
            if endpoints[endpoint].is_reachable():
                response = requests.post(
                    endpoints[endpoint].format(extra="/model/predict"), files=files
                )
                json_data = json.loads(response.text)
                if response.status_code == 200:
                    st.success("Done!")
                else:
                    st.error("Model prediction failed")
                    return
            else:
                st.error("Endpoint is not reachable! Do you need an active VPN?")
                return

        caption = json_data["predictions"][0]["caption"]
        prob = json_data["predictions"][0]["probability"]

        st.subheader("Most likely:")
        st.write(f"*{caption}* [prob:{(prob*100):.2f}]")

        st.subheader("Alternatives:")

        for i in range(1, 3):
            caption = json_data["predictions"][i]["caption"]
            prob = json_data["predictions"][i]["probability"]
            st.write(f"*{caption}* [prob:{(prob*100):.2f}]")

        caption = st.radio(
            "Result captions",
            [json_data["predictions"][i]["caption"] for i in range(3)],
        )

        # st.dataframe(res)

    # curl -F "image=@/Users/werner-ch/Downloads/Institusgebaude_Winter_2006_02.jpg" -X POST http://172.27.60.92:5000/model/predict
    #


if __name__ == "__main__":
    main()
