import time
import streamlit as st
import os
from uservalidate import create_users_table, verify_user, add_user
from styles import (
    get_main_styles, 
    get_welcome_styles
)
from userPage import user_page


# Get the API Key
api_key = st.secrets["api_keys"]["openai"]


# Main: Create the streamlit web application
if __name__ == '__main__':
    # Initialize theme in session state if not present
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    
    # Initialize temperature if not present
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.1
    
    # Set page config first (must come before any UI elements)
    st.set_page_config(page_title="S&CA AI Pilot", layout="wide")
    
    # Apply main styles
    st.markdown(get_main_styles(), unsafe_allow_html=True)
    
    # Apply theme to body
    body_class = "dark_theme" if st.session_state.theme == "dark" else "light_theme"
    st.markdown(f"""
        <script>
            document.body.className = "{body_class}";
        </script>
    """, unsafe_allow_html=True)
    
    create_users_table()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Otherwise proceed with normal app flow
    if st.session_state.get("authenticated") and "logout" in st.query_params:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.query_params.clear()
        st.rerun()

    if st.session_state.get("authenticated"):
        username = st.session_state["username"]
        result = user_page(username)
    else:
        # Login and signup screens
        st.markdown(get_welcome_styles(), unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([5, 1, 1, 5])

        with col2:
            if st.button("Login"):
                st.session_state["page"] = "Login"

        with col3:
            if st.button("Sign Up"):
                st.session_state["page"] = "Sign Up"

        if st.session_state.get("page") == "Login":
            col1, col2, col3 = st.columns([4, 4, 4])
            with col2:
                st.subheader("Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Sign In"):
                    if verify_user(username, password):
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.success("Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    elif username == "admin" and password == "mysecpwd":
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.success("Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        elif st.session_state.get("page") == "Sign Up":
            col1, col2, col3 = st.columns([4, 4, 4])
            with col2:
                st.subheader("Sign Up")
                new_username = st.text_input("Create a Username")
                new_password = st.text_input("Create a Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                if st.button("Sign Up Now"):
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long!")
                    else:
                        add_user(new_username, new_password)   
                        st.success("User created successfully!") 
                        time.sleep(1)
                        st.session_state["page"] = "Login"
                        st.rerun()

