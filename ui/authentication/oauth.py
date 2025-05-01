import streamlit as st
from streamlit_oauth import OAuth2Component
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


"""_summary_ Function to run the otauth
"""
def run_oauth(application="ZOHO")->None:
    # Check if token exists in session state
    extra_params = {}
    
    if application == "ZOHO":
    # Set environment variables
        AUTHORIZE_URL = os.environ.get('AUTHORIZE_URL')
        TOKEN_URL = os.environ.get('TOKEN_URL')
        REFRESH_TOKEN_URL = os.environ.get('REFRESH_TOKEN_URL')
        REVOKE_TOKEN_URL = os.environ.get('REVOKE_TOKEN_URL')
        CLIENT_ID = os.environ.get('ZOHO_CLIENT_ID')
        CLIENT_SECRET = os.environ.get('ZOHO_CLIENT_SECRET')
        REDIRECT_URI = os.environ.get('REDIRECT_URI')
        SCOPE = os.environ.get('SCOPE')
        extra_params = {"access_type": "offline"}
        

    # Create OAuth2Component instance
    oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL, REVOKE_TOKEN_URL)

    
    if 'token' not in st.session_state:
        # If not, show authorize button
        result = oauth2.authorize_button("Authorize", REDIRECT_URI, SCOPE,extras_params=extra_params)
        if result and 'token' in result:
            # If authorization successful, save token in session state
            st.session_state.token = result.get('token')
            st.rerun()
    else:
        # If token exists in session state, show the token
        token = st.session_state['token']
        st.json(token)
        if st.button("Refresh Token"):
            # If refresh token button is clicked, refresh the token
            token = oauth2.refresh_token(token)
            st.session_state.token = token
            st.rerun()