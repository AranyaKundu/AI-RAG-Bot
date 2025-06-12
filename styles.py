def get_main_styles():
    return """
    <style>
    :root {
        --primary-color: #4361ee;
        --background-color: #f5f7fa;
        --background-color-hover: #2f2f2f;
        --favorite-color: #ffd700;
        --footer-background-color: #ffffff;
        --secondary-background: #f9fafc;
        --text-color: #333333;
        --text-color-hover: #daa520;
        --sidebar-color: #f0f2f6;
        --card-background: #ffffff;
        --card-shadow: rgba(0, 0, 0, 0.05);
        --user-message-bg: #edf2fa;
        --assistant-message-bg: #f0f7ff;
        --input-background: #ffffff;
        --input-text-color: #333;
        --button-primary-bg: #4361ee;
        --button-primary-text: #ffffff;
        --button-secondary-bg: #f0f0f0;
        --button-secondary-text: #555;
        --border-color: #e0e0e0;
    }
    
    /* Message content styling */
    .stChatMessageContent {
        color: var(--text-color) !important;
        max-width: 650px !important;
    }
    
    /* Chat container centering */
    [data-testid="stChatMessageContent"] {
        margin-left: auto;
        margin-right: auto;
    }
    
    /* User message styling */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: var(--user-message-bg);
    }
    
    /* Assistant message styling */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: var(--assistant-message-bg);
    }
    
    /* Button styling */
    .stButton button {
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
    }
    textarea [data-testid="stChatInputTextArea"] {
        font-size: 1rem !important;
    }
    </style>
    """

def get_sidebar_button_styles():
    return """
    <style>
    /* Target buttons in the sidebar */
    [data-testid="stSidebar"] button {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-align: left;
        justify-content: left;
        max-width: 250px;  
    }
    
    div[data-baseweb="select"] :hover, 
    div[data-baseweb="select"] :focus{
        background-color: var(--background-color-hover);
        color: var(--text-color-hover);
        fill: var(--text-color-hover);
    }
    
    div[data-testid="stSelectbox"] label[data-testid="stWidgetLabel"],
    .stNumberInput label[data-testid="stWidgetLabel"]{
        display: none !important;
    }

    /* Style the dropdown options container using data-testid */
    # ul[data-testid="stSelectboxVirtualDropdown"] {
    #     line-height: 1 !important;
    #     background-color: var(--background-color) !important;
    #     height: auto !important;
    #     padding: 0px !important;
    # }

    # [data-testid="stSelectboxVirtualDropdown"] > div, [data-testid="stSelectboxVirtualDropdown"] > div > div {
    #     height: auto !important;
    #     max-height: 100px !important
    # }

    .stTooltipHoverTarget {
        line-height: 1.4 !important;
    }
    /* Style cursor to pointer */
    div[data-testid="stElementContainer"] {
        cursor: pointer;
    }
    </style>
    """

def get_main_container_styles():
    return """
    <style>
    .st-key-mainContainer {
        padding-bottom: 100px;
        width: 100%;
        max-width: 850px;
        position: relative;
        overflow: auto;
        align-self: center;
    }
    
    /* Ensure chat messages are centered and properly sized */
    [data-testid="stChatMessage"] {
        margin-left: auto !important;
        margin-right: auto !important;
        max-width: 850px !important;
        width: 100% !important;
    }
    
    /* Set message content width */
    .stChatMessageContent {
        max-width: 850px !important;
    }
    
    /* Center markdown content inside messages */
    .stChatMessageContent [data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 800px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    </style>
    """

def get_button_styles():
    return """
    <style>
    .stButton button {
        padding: 5px 10px;
        font-size: 14px;
        border-radius: 15px;
        border: 1px solid var(--border-color);
        max-width: 250px;
        transition: all 0.2s;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        background-color: var(--background-color-hover);
        border: none;
        color: var(--text-color-hover);
    }
    /* Primary button styling */
    .stButton button[data-testid="baseButton-primary"] {
        background-color: var(--button-primary-bg);
        color: var(--button-primary-text);
    }
    /* Secondary button styling */
    .stButton button[data-testid="baseButton-secondary"] {
        background-color: var(--button-secondary-bg);
        color: var(--button-secondary-text);
    }
    /* Active chat styling */
    .active-chat {
        background-color: #d1e7dd !important;
    }
    </style>
    """

def get_main_section_styles():
    return """
    <style>
    .stMain {
            z-index: 1;
        }
    .stSidebar {
        position: fixed !important;
        top: 0;
        bottom: 0;
        overflow-x: hidden;
        overflow-y: auto;
    }
    .stSlider > label[data-testid="stWidgetLabel"] {
        display: none !important;
    }
    div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"] {
        display: none !important;
    }
    </style>
    """

def get_bottom_container_styles():
    return """
    {
        position: fixed;
        height: auto;
        bottom: 35px;
        left: 50%;
        transform: translateX(-50%);
        width: 70%;
        max-width: 850px;
        background-color: var(--card-background);
        border-radius: 28px;
        border: 1px solid var(--sidebar-color);
        padding: 12px;
        box-shadow: 0 5px 15px var(--card-shadow);
        display: flex;
        flex-direction: column;
        z-index: 99999999;
    }
    """

def get_bottom_content_styles():
    return """
    {   
        display: block;
        position: fixed;
        bottom: 0px;
        left: 50%;
        transform: translateX(-50%);
        right: 0;
        width: 100%;
        text-align: center;
        color: var(--light-text);
        font-size: 0.8rem;
        padding: 10px 0;
        background-color: var(--footer-background-color);
        z-index: 99999998;
    }
    """

def get_user_dropdown_styles(username, month="Current Month", total_cost=0.0):
    
    return f"""
    <style>
    /* User dropup styling */
    .user-dropdown {{
        position: fixed;
        bottom: 10px;
        right: 20px;
        z-index: 99999999;
    }}
    .user-dropdown img {{
        width: 30px;
        height: 30px;
        border-radius: 50%;
        cursor: pointer;
        background-color: var(--card-background);
        padding: 5px;
        box-shadow: 0 2px 5px var(--card-shadow);
    }}
    .user-dropdown .dropdown-content {{
        display: none;
        position: absolute;
        background: var(--card-background);
        width: 220px;
        box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
        padding: 10px;
        border-radius: 8px;
        bottom: 40px;
        right: 0;
        color: var(--text-color);
    }}
    /* Show dropdown on hover and focus */
    .user-dropdown:hover .dropdown-content,
    .user-dropdown:focus-within .dropdown-content {{
        display: block;
        cursor: pointer;
        z-index: 99999999;
        animation: fadeIn 0.3s;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .dropdown-content a, .dropdown-content p {{
        text-decoration: none;
        color: var(--text-color);
        font-size: 0.9rem;
        margin: 8px 0;
        padding: 5px;
        border-radius: 4px;
        transition: background 0.2s;
    }}
    .dropdown-content a:hover,
    .dropdown-content a:focus {{
        background: var(--secondary-background);
        outline: none;
    }}
    .dropdown-username {{
        font-weight: bold;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
        margin-bottom: 8px;
    }}
    .dropdown-usage {{
        color: var(--light-text);
        font-size: 0.85rem;
    }}
    .dropdown-logout {{
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid var(--border-color);
    }}
    .dropdown-logout a {{
        color: var(--error-color);
        font-weight: 500;
    }}
    </style>
    <div class="user-dropdown">
        <img src="https://img.icons8.com/ios-filled/30/000000/user.png" alt="User Icon" tabindex="0"/>
        <div class="dropdown-content">
            <p class="dropdown-username">{username}</p>
            <p class="dropdown-usage">Usage - {month}: ${total_cost:.2f}</p>
            <p class="dropdown-logout"><a href="?logout=1" target="_parent">Logout</a></p>
        </div>
    </div>
    """

def get_welcome_styles():
    return """
    <style>
    .centered {
        text-align: center;
    }
    </style>
    <h1 class="centered">Welcome to the AI-Powered App</h1>
    """

def get_latex_styles():
    return """
    <style>
    /* LaTeX styling */
    .katex { 
        font-size: 1.1em !important;
    }
    .math-block {
        display: block;
        margin: 1em 0;
    }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.0/dist/katex.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/katex@0.16.0/dist/katex.min.css" rel="stylesheet">
    """ 