import streamlit as st
import requests
import os
import sys

# get the previous path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# runtime loading to ensure that the paths are created--- this needs to be put into other place or file which is part of init
if not os.path.exists("./tmp"):
    os.mkdir("./tmp")
if not os.path.exists("./tmp/files"):
    os.mkdir("./tmp/files")

from load_dotenv import load_dotenv
import json

import loaders.runtime_loaders as runtime_loaders

from app import tool as tools

# st.session_state

# resetting the session_state on first run
if "counter" not in st.session_state:
    st.session_state.clear()
    st.session_state["counter"] = "STARTED"
    st.session_state["messages"] = []
    

tools_list = tools.__all__


load_dotenv()
BASE_URL = os.environ["BASE_URL"]
st.session_state["BASE_URL"] = BASE_URL
(credentials,configuration_array) = runtime_loaders.get_credentials()


# MODULE -  chat history 
chat_history = ["New Chat"]
f"Getting the chat history"
get_chat_history = runtime_loaders.get_messages()


# chat_history
# get the chat history from the files
if get_chat_history["status_code"] == 200:
    for each_file in get_chat_history["message"]["files"]:
        chat_history.append(each_file)

    
# MODULE - Message History
# here we are going to check if the chat_history is selected
message_history = []
if "chat_history" in st.session_state and st.session_state.chat_history != "New Chat":
    # f"{st.session_state.chat_history}"
    message_history = runtime_loaders.get_messages(message_folder=st.session_state.chat_history)
    if message_history["status_code"] == 200:
        
        st.session_state.messages = message_history["message"]["content"]
        
else:
    st.session_state.messages = []






# DEF - Set Credentials 
def set_credentials():
    print (f"session state {st.session_state}")

with st.sidebar:
    st.sidebar.title("Agentic Framework")
    
    tabs = st.tabs(["Home", "Settings"])
    
    with st.expander("About"):
        st.write("Open Manus is a tool that helps you to generate content using OpenAI")
    
    with tabs[0]:
        st.title("Home")
        st.write("Welcome to Agentic Framework")    
       
        with st.expander("Files"):
            f"Upload Files Here"
            uploaded_file = st.file_uploader("Choose a file")
            if uploaded_file:
                # make directories
                with open(f"./tmp/files/{uploaded_file.name}","wb") as f:
                    f.write(uploaded_file.getvalue())
                st.write("File Uploaded Successfully")
                
            files_list = os.listdir("./tmp/files")
            for each_file in files_list:
                st.checkbox(each_file,value=False,key=f"file_checkbox.{each_file}")
            
            
             
                        
            # list of the files to be displayed here
            
            
                
                
                # lets save the file
                # runtime_loaders.save_messages(uploaded_file.name,json.loads(uploaded_file.getvalue().decode("utf-8")))
       
        with st.expander("Chat History",expanded=True):
            st.radio("Select History",options=chat_history, key=f"chat_history", on_change=runtime_loaders.set_chat_history)

        
        with st.expander("Select Tools"):
            for each_tool in tools_list:
                st.checkbox(str(each_tool),value=True,key=f"tool_checkbox.{each_tool}",on_change=runtime_loaders.set_prompt_suffix)
        
        
        
        
        # lets put in the lsit of the tools 
        
        

    with tabs[1]:
    
        st.title("Settings")
        st.divider()
        st.header("AWS Settings")
        aws_access_key = st.text_input("Enter AWS Access Key", key="env.AWS_ACCESS_KEY_ID", type="password", value=credentials["env"]["AWS_ACCESS_KEY_ID"],on_change=runtime_loaders.set_credentials)
        aws_secret_key = st.text_input("Enter AWS Secret Key", key="env.AWS_SECRET_ACCESS_KEY", type="password", value=credentials["env"]["AWS_SECRET_ACCESS_KEY"],on_change=runtime_loaders.set_credentials)
        
        
        st.divider()
        st.header("Open AI Settings")
        
        
        open_ai_credentials = st.text_input("Enter Open AI Credentials", key="toml.llm.api_key", type="password", value=credentials["toml"]["llm"]["api_key"],on_change=runtime_loaders.set_credentials)
        # open_ai_model = st.multiselect("Select Open AI Model", key="toml.llm.model",options=runtime_loaders.OPEN_AI_MODELS,on_change=runtime_loaders.set_credentials)
        open_ai_base_url = st.text_input("Enter Open AI Base URL", key="toml.llm.base_url",value=credentials["toml"]["llm"]["base_url"],on_change=runtime_loaders.set_credentials)
        
        st.divider()
        st.header("Notion Settings")
        notion_credentials  = st.text_input("Enter Notion Credentials", key="env.NOTION_API_KEY", type="password", value=credentials["env"]["NOTION_API_KEY"],on_change=runtime_loaders.set_credentials)

        


    
   

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
    files_selected = []
    if "file_checkbox" in "--".join(st.session_state.keys()):
        for each_key in st.session_state.keys():
            if "file_checkbox" in each_key and st.session_state[each_key]:
                files_selected.append(each_key.split(".")[1])
                
    files_prompt = ".You should put the files in the location ./tmp/files/ as a folder only if required and specified in the prompt." if len(files_selected) == 0 else f"You MUST refer to the files in the folder ./tmp/files/: {files_selected} for your operation"  
    # files_prompt  
    try:
        response = requests.post(BASE_URL+"run_agent",json={"prompt":f"{data} {files_prompt} {st.session_state.prompt_suffix if 'prompt_suffix' in st.session_state else ''}","messages":st.session_state.messages})
        
        if response.status_code != 200:
             st.chat_message("assistant").markdown(f"!!! Error in processing the data, Contact Administrator")
             answer = """!!! Error in processing the data, Contact Administrator"""
        else:
            # all good we need to process the data
            response_data = json.loads(response.json())
            # print (f"type: {type(response_data)}, data: {response_data}")
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
        
        runtime_loaders.save_messages(f"{st.session_state.chat_history if 'chat_history' and st.session_state.chat_history!="None" in st.session_state else ''}",st.session_state.messages)
    
    # here we send the requests to the user


