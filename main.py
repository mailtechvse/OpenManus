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



# app = Flask(__name__)
app = FastAPI()


@app.route('/run_agent', methods=['POST'])
async def run_agent_endpoint(request:Request):
    # prompt = request.json.get('prompt', '')
    load_dotenv(override=True)
    
    print (os.environ)
    
    json_data = await request.json()
    prompt = json_data.get('prompt', '')
    messages = json_data.get('messages', [])
    # user_id = json_data.get('user_id', str(uuid4()))
    
    
    
    # agent = None
    agent = Manus()
    # print (f"Agent: {vars(agent.llm)}")
    agent.initialize_agent()
    
    # add messages
    for each_message in messages:
        agent.update_memory(each_message["role"],each_message["content"])
    
    # agent.llm = LLM()
    
    
    # print (f"API KEY: {agent.llm.api_key}")
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    result = await run_agent(prompt+". Also you must return the data in pure HTML Fomat for it to be rendered on the site container, along with the necessary css and js calls if required. The output should not be saved in the file instead it should be shown as html prompt. You should only give output as HTML and no other text. Also use basic html elements along with the CSS minimum, but you should try and avoid using javascript unless it requires interaction", agent, "")
    
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
    
    if args.prompt is not None:
        prompt = args.prompt
    else:
        prompt = input("Enter your prompt (or 'exit'/'quit' to quit): ")
    
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
                 
        
