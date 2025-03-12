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


# app = Flask(__name__)
app = FastAPI()
load_dotenv()

@app.route('/run_agent', methods=['POST'])
async def run_agent_endpoint(request:Request):
    # prompt = request.json.get('prompt', '')
    json_data = await request.json()
    prompt = json_data.get('prompt', '')
    # user_id = json_data.get('user_id', str(uuid4()))
    
    
    agent = Manus()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    result = await run_agent(prompt+". Also you must return the data in pure HTML Fomat for it to be rendered on the site container, along with the necessary css and js calls if required. The output should not be saved in the file instead it should be shown as html prompt. You should only give output as HTML and no other text. Also use basic html elements along with the CSS minimum, but you should try and avoid using javascript unless it requires interaction", agent, "")
    
    print (f"Result: {result}")
    
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
    
    
    

async def main():
    agent = Manus()
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
   


if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--server", action="store_true", help="Run the server",dest="server")
    
    args = argparser.parse_args()
    
    if not args.server:
        
        asyncio.run(main())
        
    else:
        # asgi_app = WsgiToAsgi(app)
        uvicorn.run(app, host="0.0.0.0", port=5010)
