import asyncio
from app.agent.manus import Manus
from app.logger import logger
from flask import Flask, request, jsonify 
from fastapi import FastAPI, Request
import uvicorn
import argparse
from uuid import uuid4
from asgiref.wsgi import WsgiToAsgi
from starlette.responses import JSONResponse, HTMLResponse
import json
from load_dotenv import load_dotenv
import re
import os
import requests
import httpx



# app = Flask(__name__)
app = FastAPI()


@app.route('/run_agent', methods=['POST'])
async def run_agent_endpoint(request:Request):
    # prompt = request.json.get('prompt', '')
    load_dotenv(override=True)
    
    # print (os.environ)
    
    json_data = await request.json()
    prompt = json_data.get('prompt', '')
    messages = json_data.get('messages', [])
    max_steps = json_data.get('max_steps', 10)
    # user_id = json_data.get('user_id', str(uuid4()))
    
    
    
    # agent = None
    agent = Manus()
    # print (f"Agent: {vars(agent.llm)}")
    agent.initialize_agent()
    
    # add messages
    for each_message in messages:
        agent.update_memory(each_message["role"],each_message["content"])
    
    # print (f"Agent Memory: {agent.memory.messages}")
    
    # agent.llm = LLM()
    
    
    # print (f"API KEY: {agent.llm.api_key}")
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    result = await run_agent(prompt+". Also you must return the data in pure HTML Fomat for it to be rendered on the site container without using too many dark or light colors so as to avoid the contrast problem (use neutral colours), along with the necessary css and js calls if required. The output should be saved in the file only if the user explicitly asks else it should render HTML only. You should only give output as HTML and no other text. Also use basic html elements along with the CSS minimum, but you should try and avoid using javascript unless it requires interaction", agent, "")
    
    # print (f"Result: {result}")

    # bring everythign to one line 
    result = result.replace("\n","")
    
    html_content = re.findall(".*(```html.*?```)",result)
    return_data = None
    if len(html_content) == 0:
        return_data = f"The HTML Couldnt be rendered properly, I have the processing data {result}"
    
    else:
        return_data = html_content[0].replace("```html","").replace("```","")
    
    print (f"Return Data {return_data}")
    # print (f"jsonified data {jsonify(return_data)}")
    
    
    return JSONResponse(content=json.dumps({"return_data":return_data}), status_code=200)
    

@app.route("/oauth2/callback",methods=["GET"])
async def oauth2_callback(request:Request):
    # this is the callback function that is used to get the token
    # here we are going to ge the tokens and use that to pass that to the Env file
    
    if "code" not in request.query_params:
        return JSONResponse({"message":"Error, code not found"},status_code=400)
    
    if "state" not in request.query_params:
        return JSONResponse({"message":"Error, state not found"},status_code=400)
    
    #use this to get the token and refresh token from query and state for Zoho 
    load_dotenv(override=True)
    code = request.query_params["code"]
    state = request.query_params["state"]
    
    parameters = {
        "client_id": os.environ["ZOHO_CLIENT_ID"],
        "client_secret": os.environ["ZOHO_CLIENT_SECRET"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.environ["REDIRECT_URI"]
      
    }
    # print (parameters)
    
    try:
        
        async with httpx.AsyncClient() as client:
            print (os.environ)
            response = await client.post(url=os.environ.get("TOKEN_URL","https://accounts.zoho.in/oauth2/v2/token/"),data=parameters)
            token = response.json()["access_token"]
            refresh_token = response.json()["refresh_token"]
            
            # print (f"Token: {token}, Refresh Token: {refresh_token}")
            
            with open("./.env","r") as f:
                lines = f.readlines()
                
            new_line = []
            for each_line in lines:
                if re.match("^#",each_line):
                    new_line.append(each_line)
                    continue
                
                each_line_split = each_line.split("=")
                
                if each_line_split[0]=="ZOHO_ACCESS_TOKEN":
                    new_line.append(f"ZOHO_ACCESS_TOKEN={token}\n")
                    
                elif each_line_split[0] == "ZOHO_REFRESH_TOKEN":
                    new_line.append(f"ZOHO_REFRESH_TOKEN={refresh_token}\n")

                else:
                    new_line.append(each_line)
                   
            with open("./.env","w") as f:
                f.writelines(new_line)
            # lets get the refresh token
            
            
                                         
             
       
        # print (response)
        
        
    except Exception as e:
        # return JSONResponse({"message":f"Error in getting the token, Error: {e}"},status_code=500)
        return HTMLResponse(content=f"Error in getting the token, Error: {e}",status_code=500)
    
    return HTMLResponse(content="Token received successfully, You can close this window",status_code=200)
    # return JSONResponse({"message":"Token received successfully","content":response.json()},status_code=200)
    
    
    
    
    


# application to save the messages in the file
@app.route('/messages',methods=["POST","GET","DELETE"])
async def messages_route(request: Request):
    
    # we only use the local file for the reference
    if request.method == "POST":
        # here we need to look for the messages that are to be saved in the region
        json_data = await request.json()
        
        print (f"Json Data: {json_data}, type:{type(json_data)}")
        
        if "message_file" not in json_data:
            return JSONResponse({"message": "Error, message_file must be included in the post request"},status_code=400)
        
        if "messages" not in json_data:
            return JSONResponse({"message":"messages in form of array should be loaded in the POST request"},status_code=400)
        
        # here we are saving the data in the file
        
        message_file = json_data["message_file"]
        
        try:
            os.makedirs("./tmp/file_base")
        except:
            print (f"File Already exists")
            True
            
            # the path exists
        
        with open(f"./tmp/file_base/{message_file}","wb") as f:
            f.write(f"{json.dumps(json_data["messages"])}".encode("utf-8"))
        
        
        return JSONResponse({"message": "Operation Successful .. "},status_code=200)
        
    
    elif request.method == "GET":
        # here if the parameters are set then we can get the file data or we get the file names        
        request_data = dict(request.query_params)
        print (f"Request Parameters:{request_data}")
        
        # print (f"Request Data: {request_data},type:{type(request_data)}")
        if request_data is None or request_data == "" or request_data == {}:
            # we get the list of the filenames here
            directory = os.listdir("./tmp/file_base")
            return JSONResponse({"files":directory},status_code=200)

        elif "message_file" in request_data is not None:
            content = ""
            try:
                message_file = request_data["message_file"].strip()
                print (f"Message File: {message_file}")
                f = open(f"./tmp/file_base/{message_file}","rb")
                content =  f.read()
            except Exception as e_file:
                print ("Error in reading the file, Error: ",e_file)
                return JSONResponse({"message":f"File {request_data["message_file"]} doesn't exist"},status_code=404)
                
           
            return JSONResponse({"content":json.loads(content.decode("utf-8"))},status_code=200)            
        
        else:
            # malformed requrest
            return JSONResponse({"message":"Error in request formation"},status_code=400)
    
    # here we are deleting the file
    elif request.method == "DELETE":
        
        request_data = await request.json()
        
        # here we are going to find the list of the files that are to be deleted
        
        if not isinstance(request_data,list):
            return JSONResponse({"message":"The request should be a list of the files that are to be deleted"}, status_code=400)
        
        error_files = []
        success_files = []
        
        for each_file in request_data:
            
            try:
                os.remove(f"./tmp/file_base/{each_file}")
                success_files.append(each_file)
            except:
                error_files.append(each_file)
                
        return JSONResponse({"success_files":success_files,"error_files":error_files},status_code=200)
        
        
        
    else: 
        return JSONResponse({"message":"Error in request formation"},status_code=400)
    
    
    
    

async def main():
    agent = Manus()
    run = True
    while (run):
        if args.prompt is not None:
            prompt = args.prompt
        else:
            prompt = input("Enter your prompt (or 'exit'/'quit' to quit): ")
            if prompt.strip() in ("exit","quit"):
                run = False
                break
        
        await run_agent(prompt, agent)        
            
        
        
    


async def run_agent(prompt: str, agent:Manus, user_id: str="")->str:
    
    prompt_lower = prompt.lower()
    if prompt_lower in ["exit", "quit"]:
        logger.info("Goodbye!")
        return "OK, Goodbye!"
    if not prompt.strip():
        logger.warning("Skipping empty prompt.") 
        return "No input, No output"
    logger.warning("Processing your request...")
    data = await agent.run(prompt)
    print (f"data: {data}")
    return data
   

def start_server():
    
    uvicorn.run(app, host="127.0.0.1", port=5010)


if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--server", action="store_true", help="Run the server",dest="server")
    argparser.add_argument("-p","--prompt", required=False, help="Executes the prompt directly",dest="prompt")
    
    args = argparser.parse_args()
    
    if not args.server:
        asyncio.run(main())
        
    else:
        # asgi_app = WsgiToAsgi(app)
        asyncio.run(start_server())
                 
        
