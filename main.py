"""Python file to serve as the frontend"""
import streamlit as st
from streamlit_chat import message

from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from dotenv import load_dotenv

# From here down is all the StreamLit UI.
def setup():
    load_dotenv()
    llm = OpenAI(temperature=0)
    chain = ConversationChain(llm=llm)

    title = "Orchestra Search Demo"
    st.set_page_config(page_title=title, page_icon=":violin:")
    st.header(title)

    if "bot_messages" not in st.session_state:
        st.session_state["bot_messages"] = []

    if "user_messages" not in st.session_state:
        st.session_state["user_messages"] = []

    if "step" not in st.session_state:
        st.session_state["step"] = 1

    if "user_data" not in st.session_state:
        st.session_state["user_data"] = {}
    
    if "job_data" not in st.session_state:
        st.session_state["job_data"] = {}

    return chain

def get_output_parser():
    response_schemas = [
        ResponseSchema(name="response", description="bot's response to the user's input. Call out if any information is missing."),
        ResponseSchema(name="instrument", description="instrument the user plays"),
        ResponseSchema(name="position", description="desired position"),
        ResponseSchema(name="location", description="user's location"),
        ResponseSchema(name="side_gigs", description="whether the user is looking for side gigs", type="boolean"),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    return output_parser

def get_preference_prompt(output_parser, user_input):
    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template="I will give you my job preference. Give response along with the specified format. Return empty string for missing fields.\n{format_instructions}\n{user_info}",
        input_variables=["user_info"],
        partial_variables={"format_instructions": format_instructions}
    )

    processed_input = prompt.format_prompt(user_info=user_input)
    return processed_input.to_string()

def step_1(chain):
    # Display chat
    if st.session_state["bot_messages"]:
        for i in reversed(range(len(st.session_state["bot_messages"]) -1, -1, -1)):
            message(st.session_state["user_messages"][i], is_user=True, key=str(i) + "_user")
            message(st.session_state["bot_messages"][i], key=str(i))

    def missing_information(user_data):
        # Check for any empty fields
        missing_keys = []
        for key, value in user_data.items():
            if not value:
                missing_keys.append(key)
            
        return missing_keys
    
    st.session_state.bot_messages.append("Welcome to the Orchestra Search Demo! Please enter some information about your job search.")
    chat_value =  "I am a violinist from Minneapolis, looking for an assistant concertmaster position anywhere in the US. I'm also looking for side gigs in regional orchestras."
    missing_keys = missing_information(st.session_state.user_data)

    while len(missing_keys) > 0:
        user_input = st.text_area(
            label = "Your response: ", 
            value = chat_value, 
            key = "input"
        )
        def submit_message():
            if user_input:
                # Get input template
                output_parser = get_output_parser()
                processed_input = get_preference_prompt(output_parser, user_input)
                
                # Run inference
                output = chain.run(input=processed_input)            

                # Add messages for display
                st.session_state.user_messages.append(user_input)

                # Process output into a structured format
                parsed_output = output_parser.parse(output)
                response = parsed_output.pop('response')

                st.session_state.user_data.update(parsed_output)
                st.session_state.bot_messages.append(response)

                if len(missing_information(st.session_state.user_data)) > 0:
                    chat_value = "Please enter your " + ", ".join(missing_keys) + "."

        st.button("Submit information", on_click=submit_message)
       
    st.session_state.step = 2
       

def step_2(chain):
    st.text("Some information here")

# Execution
def execute():
    chain = setup()
    with st.expander("Step 1", expanded=(st.session_state.step==1)):
        step_1(chain)

    if st.session_state.step > 1:
        with st.expander("Step 2", expanded=(st.session_state.step==2)):
            step_2(chain)

    with st.expander("Debug prints", expanded=False):

        st.text("User data: ")
        st.json(st.session_state.user_data)

        st.text("Job data: ")
        st.json(st.session_state.job_data)

        st.text("session state:")
        st.text(st.session_state)

execute()