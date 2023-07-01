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


def get_preference_prompt(output_parser, user_input):
    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template="I will give you my job preference. Give response along with the specified format. Return empty string for missing fields.\n{format_instructions}\n{user_info}",
        input_variables=["user_info"],
        partial_variables={"format_instructions": format_instructions}
    )

    processed_input = prompt.format_prompt(user_info=user_input)
    return processed_input.to_string()

def dislay_chat():
    max_count = max(len(st.session_state["bot_messages"]), len(st.session_state["user_messages"]))
    for i in reversed(range(max_count-1, -1, -1)):
        if i < len(st.session_state["bot_messages"]):
            message(st.session_state["bot_messages"][i], key=str(i))
        if i < len(st.session_state["user_messages"]):
            message(st.session_state["user_messages"][i], is_user=True, key=str(i) + "_user")     

def step_1(chain):
    def missing_information(user_data, response_schemas):
        # Check for any key missing from user_data that is required by the response schemas
        missing_keys = []
        for schema in response_schemas:
            if schema.name == "response":
                continue
            if schema.name not in user_data or user_data[schema.name] == "":
                missing_keys.append(schema.name)
        return missing_keys
    
    response_schemas = [
        ResponseSchema(name="response", description="bot's response to the user's input. Call out if any information is missing."),
        ResponseSchema(name="instrument", description="instrument the user plays"),
        ResponseSchema(name="position", description="desired position"),
        ResponseSchema(name="location", description="user's location"),
        ResponseSchema(name="side_gigs", description="whether the user is looking for side gigs", type="boolean"),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        
    def submit_message():
        if user_input:
            # Get input template
            processed_input = get_preference_prompt(output_parser, user_input)
            
            # Run inference
            output = chain.run(input=processed_input)            

            # Add messages for display
            st.session_state.user_messages.append(user_input)

            # Process output into a structured format
            parsed_output = output_parser.parse(output)
            response = parsed_output.pop('response')

            # Pop any empty strings
            parsed_output = {k: v for k, v in parsed_output.items() if v != ""}
            st.session_state.user_data.update(parsed_output)
            st.session_state.bot_messages.append(response)

            missing_keys = missing_information(st.session_state.user_data, response_schemas)
            if missing_keys:
                missing_str = ", ".join(missing_keys)
                st.session_state.bot_messages.append(f"Could you also provide information for: {missing_str}?")
            else:
                st.session_state.step = 2
            
            # Clear input
            st.session_state.input = ""

    # UI
    if len(st.session_state["bot_messages"]) == 0:
        st.session_state.bot_messages.append("Welcome to the Orchestra Search Demo! Please enter some information about your job search.")

    dislay_chat()
    user_input = st.text_area(
        label = "Your response: ", 
        value = "", 
        placeholder = "I am a violinist from Minneapolis, looking for an assistant concertmaster position anywhere in the US. I'm also looking for side gigs in regional orchestras.",
        key = "input"
    )
    st.button("Submit information", on_click=submit_message)
       

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