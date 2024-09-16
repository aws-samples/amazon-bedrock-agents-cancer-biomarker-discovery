import streamlit as st
from util.bedrock import BedrockAgent
from util.bedrock import BedrockAgent
import argparse
import sys

# Add command-line argument parsing
parser = argparse.ArgumentParser(description="Biomarker Research Agent Streamlit App")
parser.add_argument("--env", type=str, default="research-assistant", help="Environment name")

# Check if the script is run directly (not through streamlit run)
if __name__ == "__main__":
    args = parser.parse_args()
    environment_name = args.env
else:
    # If run through streamlit run, parse sys.argv manually
    args = sys.argv[1:]  # Skip the first argument, which is the script name
    environment_name = "env1"  # Default value
    if "--env" in args:
        env_index = args.index("--env")
        if env_index + 1 < len(args):
            environment_name = args[env_index + 1]

# Initialize BedrockAgent with the environment name
bedrock = BedrockAgent(environment_name)

st.set_page_config(layout="wide", page_title="Biomarker Research Agent")

# Custom CSS
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    }
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar for S3 PNG Image Viewer and S3 Image Retrieval
with st.sidebar:
    st.header('Image Controls')
    

    st.subheader("Biomarker Imaging Results")
    png_files = bedrock.list_png_files()
    selected_file = st.selectbox('Select a file to view the imaging results:', png_files)
    load_image = st.checkbox('Load and display selected image')

   
    invocation_id = 1
    fetch_image = st.button("Fetch Chart")
     # Action List
    st.subheader("Available Actions")
    actions = bedrock.listActions()
    selected_actions = []
    for action in actions:
        if st.checkbox(action, key=f"action_{action}"):
            selected_actions.append(action)
    
    if st.button("Select Actions"):
        st.session_state.selected_actions = selected_actions
        st.success(f"Selected actions: {', '.join(selected_actions)}")

# Main content
st.title("Biomarker Research Agent")

col1, col2 = st.columns([6, 1])
with col2:
    st.link_button("Github 😎", "https://github.com/aws-samples/amazon-bedrock-agents-cancer-biomarker-discovery")

if "chat_history" not in st.session_state or len(st.session_state["chat_history"]) == 0:
    st.session_state["chat_history"] = [
        {
            "role": "assistant",
            "prompt": "Hello! I am a biomarker research agent. How may I help you today?",
        }
    ]

for index, chat in enumerate(st.session_state["chat_history"]):
    with st.chat_message(chat["role"]):
        if index == 0:
            st.markdown(chat["prompt"])
        elif chat["role"] == "assistant":
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(chat["prompt"], unsafe_allow_html=True)
                
                if "files" in chat:
                    displayed_files = set()
                    for file in chat["files"]:
                        if file['path'] not in displayed_files:
                            if file['type'].startswith('image/'):
                                st.image(file['path'], caption=file['name'])
                            else:
                                st.download_button(f"Download {file['name']}", file['path'], file['name'])
                            displayed_files.add(file['path'])
            
            with col2:
                if st.button("Show Trace", key=f"trace_{index}"):
                    st.text_area("Trace", value=chat.get("trace", "No trace available"), height=300)
        else:
            st.markdown(chat["prompt"])
if 'selected_actions' in st.session_state:
    st.write("Currently selected actions:", ', '.join(st.session_state.selected_actions))


image_placeholder = st.empty()


if selected_file and load_image:
    try:
        image = bedrock.get_image_from_s3(selected_file)
        image_placeholder.image(image, caption=selected_file, use_column_width=True)
    except Exception as e:
        st.error(f"Unable loading image: {str(e)}")

elif fetch_image:
    s3_image = bedrock.get_s3_image(invocation_id)
    if s3_image:
        try:
            image_placeholder.image(s3_image['path'], caption=s3_image['name'], use_column_width=True)
        except Exception as e:
            st.error(f"Unable loading image: {str(e)}")
    else:
        image_placeholder.error("Failed to fetch image from S3.")


# Input area
prompt = st.chat_input("Ask the bot a question...")

if prompt:
    st.session_state["chat_history"].append({"role": "human", "prompt": prompt})

    with st.chat_message("human"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            response_placeholder = st.empty()
        
        with col2:
            trace_placeholder = st.empty()

        response_text, trace_text, files_generated = bedrock.invoke_agent(prompt, trace_placeholder)
        
        st.session_state["chat_history"].append(
            {"role": "assistant", "prompt": response_text, "trace": trace_text, "files": files_generated}
        )

        response_placeholder.markdown(response_text, unsafe_allow_html=True)
        
        displayed_files = set()
        for file in files_generated:
            if file['path'] not in displayed_files:
                if file['type'].startswith('image/'):
                    st.image(file['path'], caption=file['name'])
                else:
                    st.download_button(f"Download {file['name']}", file['path'], file['name'])
                displayed_files.add(file['path'])

        bedrock.cleanup_temp_files()

# Clear chat button
if st.button("Clear Chat"):
    st.session_state["chat_history"] = []
    bedrock.new_session()
    bedrock.cleanup_temp_files()
    st.rerun()