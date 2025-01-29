# mars_chronicles_full.py
import streamlit as st
import json
import uuid
from openai import OpenAI

## --------------------------
## Configuration & Constants
## --------------------------
DEFAULT_PROFILE = {
    "name": "Alex",
    "gender": "Non-binary",
    "genre": "Sci-Fi",
    "progress": 0,
    "inventory": [],
    "location": "Mars Colony Alpha",
    "story_id": str(uuid.uuid4())
}

GENRES = [
    "Sci-Fi", "Mystery", "Romance", "Horror", "Comedy",
    "Political Thriller", "Cyberpunk", "Survival", "Historical Fiction", "Noir"
]

DEEPSEEK_CLIENT = OpenAI(
    api_key=st.secrets["DEEPSEEK_KEY"],
    base_url="https://api.deepseek.com"
)

## --------------------------
## Session Management
## --------------------------
def init_session():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = DEFAULT_PROFILE.copy()
    if 'story_choices' not in st.session_state:
        st.session_state.story_choices = []

## --------------------------
## Story Generation Engine
## --------------------------
def generate_story_segment(context: str) -> tuple:
    """Generate story segment with 2-4 choices using DeepSeek R1"""
    try:
        response = DEEPSEEK_CLIENT.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "system",
                "content": f"""Generate a branching narrative segment for a Mars colony story with:
                - Protagonist: {st.session_state.user_data['name']} ({st.session_state.user_data['gender']})
                - Genre: {st.session_state.user_data['genre']}
                - Current location: {st.session_state.user_data['location']}
                - Previous context: {context}
                
                Format rules:
                1. Write 2-3 paragraph story segment
                2. End with 2-4 numbered choices
                3. Keep choices impactful and distinct"""
            }],
            temperature=0.7,   # Controls creativity (0=deterministic, 1=random)
            top_p=0.9,         # Focuses response distribution
            max_tokens=1500    # Allows longer complex narratives
        )
        
        full_text = response.choices[0].message.content
        story_text = "\n".join([line for line in full_text.split("\n") if not line.startswith(('1.', '2.', '3.', '4.'))])
        choices = [line[3:] for line in full_text.split("\n") if line.startswith(tuple(f"{i}." for i in range(1,5)))]
        
        return story_text, choices[:4]
    
    except Exception as e:
        st.error(f"Story generation failed: {str(e)}")
        return None, []

## --------------------------
## Game State Management
## --------------------------
def save_game_state():
    return json.dumps(st.session_state.user_data)

def load_game_state(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state.user_data.update(data)
        st.success("Game loaded successfully!")
    except Exception as e:
        st.error(f"Invalid save file: {str(e)}")

## --------------------------
## UI Components
## --------------------------
def display_choices(choices: list):
    """Create adaptive columns for 2-4 choices"""
    col_count = min(len(choices), 4)
    cols = st.columns(col_count)
    
    for idx, choice in enumerate(choices):
        with cols[idx % col_count]:
            if st.button(choice, key=f"choice_{idx}"):
                st.session_state.user_data['progress'] += 1
                st.session_state.story_choices.append(choice)
                st.rerun()

## --------------------------
## Main Application
## --------------------------
def main():
    st.set_page_config(page_title="Mars Chronicles 2035", layout="wide")
    init_session()
    
    # Sidebar Controls
    with st.sidebar:
        st.header("Character Profile")
        st.session_state.user_data['name'] = st.text_input("Name", value=st.session_state.user_data['name'])
        st.session_state.user_data['gender'] = st.selectbox(
            "Gender",
            ["Male", "Female", "Non-binary", "Other"],
            index=["Male", "Female", "Non-binary", "Other"].index(st.session_state.user_data['gender'])
        )
        st.session_state.user_data['genre'] = st.selectbox("Story Genre", GENRES, index=GENRES.index(st.session_state.user_data['genre']))
        
        # Save/Load System
        st.download_button(
            label="💾 Save Progress",
            data=save_game_state(),
            file_name=f"mars_story_{st.session_state.user_data['story_id']}.json",
            mime="application/json"
        )
        uploaded_file = st.file_uploader("⬆️ Load Game", type=["json"])
        if uploaded_file:
            load_game_state(uploaded_file)

    # Main Story Interface
    st.title("🚀 Mars Chronicles 2035")
    
    # Generate Story Content
    context = "New story" if st.session_state.user_data['progress'] == 0 else \
              " ".join(st.session_state.story_choices[-3:])
    
    story_text, choices = generate_story_segment(context)
    
    if story_text and choices:
        st.markdown(f"### Chapter {st.session_state.user_data['progress'] + 1}")
        st.markdown(story_text)
        display_choices(choices)
    elif not choices:
        st.warning("Failed to generate valid story choices. Try again!")

if __name__ == "__main__":
    main()
