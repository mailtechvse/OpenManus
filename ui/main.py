import streamlit as st
import requests
import os

from load_dotenv import load_dotenv
import json

load_dotenv()
BASE_URL = os.environ["BASE_URL"]


with st.sidebar:
    
    aws_access_key = st.text_input("Enter AWS Access Key", type="password")
    aws_secret_key = st.text_input("Enter AWS Secret Key", type="password")
    
    
st.title("Playground")


if "messages" not in st.session_state:
    st.session_state.messages = []

else:
    for each_message in st.session_state.messages:
       st.chat_message(each_message["role"]).html(each_message["content"])
        

data = st.chat_input("Enter your message here", key="chat_input")

if data:
    st.chat_message("user").markdown(data)
    (question, answer) = (data,"")
    # make a call to the api
    try:
        response = requests.post(BASE_URL+"run_agent",json={"prompt":str(data)})
        
        if response.status_code != 200:
             st.chat_message("assistant").markdown(f"!!! Error in processing the data, Contact Administrator")
             answer = """!!! Error in processing the data, Contact Administrator"""
        else:
            # all good we need to process the data
            response_data = json.loads(response.json())
            print (f"type: {type(response_data)}, data: {response_data}")
            if "return_data" in response_data:
                st.chat_message("assistant").html(response_data["return_data"])  
                answer = response_data["return_data"]
            else:
                st.chat_message("assistant").html(response_data)
                answer = response_data
            
        
    
    except Exception as e:
        st.chat_message("assistant").markdown(f"!!! Error in processing the data, Error {e}")
        answer = f"!!! Error in processing the data, Error {e}"
    
    finally:
        st.session_state.messages.append({"role":"user","content":question})
        st.session_state.messages.append({"role":"assistant","content":answer})    
    
    # here we send the requests to the user


