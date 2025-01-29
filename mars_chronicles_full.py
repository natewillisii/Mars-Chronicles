# mars_chronicles_full.py
import streamlit as st
import json
import uuid
import time
from openai import OpenAI
from PIL import Image

## --------------------------
## Configuration & Constants
## --------------------------
DEFAULT_PROFILE = {
    "name": "Alex",
    "gender": "Non-binary",
    "age": 25,
    "origin": "New York, Earth",
    "genre": "Sci-Fi",
    "progress": 0,
    "inventory": [],
    "location": "Mars Colony Alpha",
    "story_id": str(uuid.uuid4()),
    "created": False,
    "locations": [
        {"name": "Mars Colony Alpha", "image": "images/colony_alpha.jpg"},
        {"name": "Olympus Mons Outpost", "image": "images/olympus_mons.jpg"},
        {"name": "Valles Marineris Hub", "image": "images/valles_marineris.jpg"},
        {"name": "Polar Caps Station", "image": "images/polar_caps.jpg"}
    ]
}

GENRES = [
    "Sci-Fi", "Mystery", "Romance", "Horror", "Comedy",
    "Political Thriller", "Cyberpunk", "Survival", "Historical Fiction", "Noir"
]

EARTH_ORIGINS = [
    "New York, Earth", "Tokyo, Earth", "Mumbai, Earth", "Cairo, Earth",
    "São Paulo, Earth", "Sydney, Earth", "London, Earth", "Shanghai, Earth",
    "Dubai, Earth", "Nairobi, Earth"
]

## --------------------------
## Cached Resources
## --------------------------
@st.cache_resource
def get_api_client():
    return OpenAI(
        api_key=st.secrets["DEEPSEEK_KEY"],
        base_url="https://api.deepseek.com"
    )

@st.cache_data
def load_image(path: str):
    try:
        return Image.open(path)
    except FileNotFoundError:
        return None

## --------------------------
## Core Game Functionality
## --------------------------
def generate_story_segment(context: str) -> tuple:
    """Generate story segment with 2-4 choices using DeepSeek R1"""
    try:
        client = get_api_client()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "system",
                "content": f"""Generate a branching narrative segment for a Mars colony story with:
                - Protagonist: {st.session_state.user_data['name']} 
                - Gender: {st.session_state.user_data['gender']}
                - Age: {st.session_state.user_data['age']}
                - Earth Origin: {st.session_state.user_data['origin']}
                - Genre: {st.session_state.user_data['genre']}
                - Current location: {st.session_state.user_data['location']}
                - Previous context: {context}
                
                Format rules:
                1. Incorporate character background
                2. 2-3 paragraph story segment
                3. End with 2-4 numbered choices
                4. Maintain continuity"""
            }],
            temperature=0.7,
            top_p=0.9,
            max_tokens=1500
        )
        
        full_text = response.choices[0].message.content
        story_text = "\n".join([line for line in full_text.split("\n") if not line.startswith(('1.', '2.', '3.', '4.'))])
        choices = [line[3:] for line in full_text.split("\n") if line.startswith(tuple(f"{i}." for i in range(1,5)))]
        
        # Update location based on progress
        progress = st.session_state.user_data['progress'] + 1
        if progress < len(st.session_state.user_data['locations']):
            st.session_state.user_data['location'] = st.session_state.user_data['locations'][progress]['name']
        
        return story_text, choices[:4]
    
    except Exception as e:
        st.error(f"Story generation failed: {str(e)}")
        return None, []

## --------------------------
## UI Components
## --------------------------
def show_loading(message="Generating your Mars adventure..."):
    """Modern loading screen"""
    with st.spinner(message):
        time.sleep(1.5)

def show_colony_map():
    """Display current colony map"""
    location_name = st.session_state.user_data['location']
    location = next((loc for loc in st.session_state.user_data['locations'] 
                    if loc['name'] == location_name), None)
    
    if location:
        img = load_image(location['image'])
        if img:
            st.sidebar.image(img, use_column_width=True, caption=location_name)
            st.sidebar.markdown(f"**Current Location:** {location_name}")
        else:
            st.sidebar.error("Map image not found!")

## --------------------------
## Main Application Flow
## --------------------------
def main():
    st.set_page_config(
        page_title="Mars Chronicles 2035",
        page_icon="🚀",
        layout="wide"
    )
    
    # Initialize session state
    if 'user_data' not in st.session_state:
        st.session_state.user_data = DEFAULT_PROFILE.copy()
    if 'story_choices' not in st.session_state:
        st.session_state.story_choices = []
    
    # Character Creation
    if not st.session_state.user_data['created']:
        st.title("🚀 Mars Chronicles 2035 - Character Creation")
        
        with st.form("character_creation"):
            st.header("Create Your Character")
            
            name = st.text_input("Character Name", value=DEFAULT_PROFILE['name'])
            gender = st.selectbox(
                "Gender Identity",
                ["Male", "Female", "Non-binary", "Other"],
                index=2
            )
            age = st.number_input(
                "Character Age (Earth Years)",
                min_value=1,
                max_value=125,
                value=25
            )
            origin = st.selectbox(
                "Earth Origin",
                EARTH_ORIGINS,
                index=0
            )
            genre = st.selectbox(
                "Story Genre", 
                GENRES, 
                index=0
            )
            
            if st.form_submit_button("Begin Your Mars Adventure"):
                st.session_state.user_data.update({
                    "name": name,
                    "gender": gender,
                    "age": age,
                    "origin": origin,
                    "genre": genre,
                    "created": True
                })
                show_loading("Initializing your Mars colony...")
                st.rerun()
        
        return
    
    # Main Game Interface
    with st.sidebar:
        st.header("Martian Colony Map")
        show_colony_map()
        
        st.header("Game Controls")
        st.download_button(
            label="💾 Save Progress",
            data=json.dumps(st.session_state.user_data),
            file_name=f"mars_story_{st.session_state.user_data['story_id']}.json",
            mime="application/json"
        )
        uploaded_file = st.file_uploader("⬆️ Load Game", type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                st.session_state.user_data.update(data)
                st.success("Game loaded successfully!")
            except Exception as e:
                st.error(f"Invalid save file: {str(e)}")
    
    st.title("🚀 Your Mars Chronicle")
    
    # Generate Story Content
    context = "New story" if st.session_state.user_data['progress'] == 0 else \
              " ".join(st.session_state.story_choices[-3:])
    
    story_text, choices = generate_story_segment(context)
    
    if story_text and choices:
        st.markdown(f"### Chapter {st.session_state.user_data['progress'] + 1}")
        st.markdown(story_text)
        
        # Display choices
        cols = st.columns(min(len(choices), 4))
        for idx, choice in enumerate(choices):
            with cols[idx % 4]:
                if st.button(choice, key=f"choice_{idx}"):
                    st.session_state.user_data['progress'] += 1
                    st.session_state.story_choices.append(choice)
                    show_loading()
                    st.rerun()
    elif not choices:
        st.warning("Failed to generate valid story choices. Try again!")

if __name__ == "__main__":
    main()
