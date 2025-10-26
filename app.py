import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import io
import zipfile
import random
import time

# --- Mediapipe Initialization ---
# Initialize Mediapipe Face Mesh solutions
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# --- Utility Functions ---

def to_bgr(color_rgb):
    """Converts an RGB tuple (r, g, b) to a BGR tuple (b, g, r)."""
    return (color_rgb[2], color_rgb[0], color_rgb[1])

# Define some attractive colors (R, G, B)
COLORS = {
    "red": (230, 25, 75),
    "green": (60, 180, 75),
    "yellow": (255, 225, 25),
    "blue": (0, 130, 200),
    "orange": (245, 130, 48),
    "purple": (145, 30, 180),
    "cyan": (70, 240, 240),
    "magenta": (240, 50, 230),
    "lime": (210, 245, 60),
    "pink": (250, 190, 212),
    "teal": (0, 128, 128),
    "white": (255, 255, 255),
    "black": (0, 0, 0)
}
COLOR_LIST_BGR = [to_bgr(c) for c in COLORS.values()]

def get_landmark_points(face_landmarks, width, height):
    """
    Converts normalized Mediapipe landmarks to pixel coordinates.
    Returns a dictionary of landmark lists.
    """
    points = {}
    all_points = []
    
    # --- This is not the full list, but the key ones for drawing contours ---
    # We can get these constants from mp_face_mesh.FACEMESH_...
    # For simplicity, we'll just extract all points
    
    for idx, landmark in enumerate(face_landmarks.landmark):
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        all_points.append((x, y))

    # Note: To get specific parts like lips, eyes, etc.,
    # you would use the specific indices from FACEMESH_LIPS, etc.
    # For this app, we'll draw based on the connection sets.
    return all_points

def draw_styled_annotations(image, face_landmarks, style_config):
    """
    Draws annotations on an image based on a style configuration dictionary.
    
    style_config keys:
    - 'draw_tesselation': (bool)
    - 'tesselation_color': (b, g, r)
    - 'tesselation_thickness': int
    - 'draw_contours': (bool)
    - 'contours_color': (b, g, r)
    - 'contours_thickness': int
    - 'draw_landmarks': (bool) - Draws individual dots
    - 'landmarks_color': (b, g, r)
    - 'landmarks_radius': int
    - 'draw_specific': list of tuples, e.g., [('lips', (b,g,r), thick), ('eyes', (b,g,r), thick)]
    """
    
    annotated_image = image.copy()
    
    # 1. Draw Face Tesselation (the full mesh)
    if style_config.get('draw_tesselation', False):
        mp_drawing.draw_landmarks(
            image=annotated_image,
            landmark_list=face_landmarks,
            connections=mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing.DrawingSpec(
                color=style_config.get('tesselation_color', (220, 220, 220)),
                thickness=style_config.get('tesselation_thickness', 1)
            )
        )

    # 2. Draw Main Contours (Face outline, Lips, Eyes, Eyebrows)
    if style_config.get('draw_contours', False):
        # We draw each part separately to control color/thickness if needed
        # For this generic style, we'll use one spec
        contour_spec = mp_drawing.DrawingSpec(
            color=style_config.get('contours_color', (30, 230, 30)),
            thickness=style_config.get('contours_thickness', 2)
        )
        
        # mp_face_mesh.FACEMESH_CONTOURS combines all these
        mp_drawing.draw_landmarks(
            image=annotated_image,
            landmark_list=face_landmarks,
            connections=mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=contour_spec
        )

    # 3. Draw Specific Parts (if defined)
    if style_config.get('draw_specific'):
        for part, color, thickness in style_config['draw_specific']:
            spec = mp_drawing.DrawingSpec(color=color, thickness=thickness)
            connections = []
            if part == 'lips':
                connections = mp_face_mesh.FACEMESH_LIPS
            elif part == 'left_eye':
                connections = mp_face_mesh.FACEMESH_LEFT_EYE
            elif part == 'right_eye':
                connections = mp_face_mesh.FACEMESH_RIGHT_EYE
            elif part == 'left_eyebrow':
                connections = mp_face_mesh.FACEMESH_LEFT_EYEBROW
            elif part == 'right_eyebrow':
                connections = mp_face_mesh.FACEMESH_RIGHT_EYEBROW
            elif part == 'face_oval':
                 connections = mp_face_mesh.FACEMESH_FACE_OVAL

            mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks,
                connections=connections,
                landmark_drawing_spec=None,
                connection_drawing_spec=spec
            )

    # 4. Draw Landmark Dots
    if style_config.get('draw_landmarks', False):
        h, w, _ = annotated_image.shape
        points = get_landmark_points(face_landmarks, w, h)
        for point in points:
            cv2.circle(
                annotated_image, 
                point, 
                style_config.get('landmarks_radius', 1), 
                style_config.get('landmarks_color', (230, 30, 30)), 
                -1
            )
            
    return annotated_image

# --- 10 Variation Style Definitions ---
# We create 10 specific "recipes" for our variations.
def get_variation_styles():
    styles = []
    
    # Style 1: Classic Contours
    styles.append({
        'name': 'Classic Contours',
        'draw_contours': True,
        'contours_color': to_bgr(COLORS['green']),
        'contours_thickness': 2
    })
    
    # Style 2: Full Tesselation (Wireframe)
    styles.append({
        'name': 'Wireframe',
        'draw_tesselation': True,
        'tesselation_color': to_bgr(COLORS['white']),
        'tesselation_thickness': 1
    })
    
    # Style 3: Key Features (Lips & Eyes)
    styles.append({
        'name': 'Key Features',
        'draw_specific': [
            ('lips', to_bgr(COLORS['red']), 2),
            ('left_eye', to_bgr(COLORS['blue']), 2),
            ('right_eye', to_bgr(COLORS['blue']), 2)
        ]
    })
    
    # Style 4: Face Oval + Eyebrows
    styles.append({
        'name': 'Oval & Brows',
        'draw_specific': [
            ('face_oval', to_bgr(COLORS['orange']), 3),
            ('left_eyebrow', to_bgr(COLORS['purple']), 2),
            ('right_eyebrow', to_bgr(COLORS['purple']), 2)
        ]
    })
    
    # Style 5: All Landmark Dots
    styles.append({
        'name': 'Landmark Cloud',
        'draw_landmarks': True,
        'landmarks_color': to_bgr(COLORS['cyan']),
        'landmarks_radius': 1
    })
    
    # Style 6: Neon Wireframe
    styles.append({
        'name': 'Neon Wireframe',
        'draw_tesselation': True,
        'tesselation_color': to_bgr(COLORS['magenta']),
        'tesselation_thickness': 1
    })

    # Style 7: Thick Contours
    styles.append({
        'name': 'Thick Contours',
        'draw_contours': True,
        'contours_color': to_bgr(COLORS['yellow']),
        'contours_thickness': 3
    })
    
    # Style 8: Minimalist Eyes
    styles.append({
        'name': 'Minimalist Eyes',
        'draw_specific': [
            ('left_eye', to_bgr(COLORS['lime']), 2),
            ('right_eye', to_bgr(COLORS['lime']), 2)
        ]
    })
    
    # Style 9: "All-in" (Contours + Tesselation)
    styles.append({
        'name': 'All-In',
        'draw_tesselation': True,
        'tesselation_color': (100, 100, 100), # Dim
        'tesselation_thickness': 1,
        'draw_contours': True,
        'contours_color': to_bgr(COLORS['teal']),
        'contours_thickness': 2
    })
    
    # Style 10: Just the Lips
    styles.append({
        'name': 'Just Lips',
        'draw_specific': [
            ('lips', to_bgr(COLORS['pink']), 3)
        ]
    })
    
    return styles

# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="AI Face Annotator")

# Custom CSS for a cleaner look
st.markdown("""
<style>
    /* Main app content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Hide the Streamlit header/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom button style for download */
    [data-testid="stDownloadButton"] > button {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background-color: #0056b3;
    }
    
    /* Style image captions */
    .stImage > figcaption {
        font-size: 0.9rem;
        font-style: italic;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Controls ---
st.sidebar.title("Controls")
uploaded_file = st.sidebar.file_uploader(
    "Upload your image", 
    type=["png", "jpg", "jpeg"],
    help="Upload an image containing one or more faces."
)

st.sidebar.header("Live Preview Toggles")
st.sidebar.info("Use these to control the 'Annotated Preview' on the right.")
show_tesselation = st.sidebar.checkbox("Show Full Mesh (Tesselation)", False)
show_contours = st.sidebar.checkbox("Show Main Contours", True)
show_landmark_dots = st.sidebar.checkbox("Show All Landmark Dots", False)


# --- Main Application Body ---
st.title("🤖 AI-Powered Face Annotator")
st.write("Upload an image to detect facial landmarks and generate 10 unique annotation styles. Preview them below and download them all as a ZIP file.")
st.markdown("---")

if uploaded_file is None:
    st.info("Upload an image using the sidebar to get started.")

else:
    # --- 1. Load and Process Image ---
    try:
        image = Image.open(uploaded_file)
        
        # Convert PIL image to OpenCV format (NumPy array)
        # We use RGB, as Mediapipe expects RGB
        img_rgb = np.array(image.convert('RGB'))
        
        # We'll need a BGR version for OpenCV drawing functions
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        
        height, width, _ = img_bgr.shape
        
        # --- 2. Run Face Mesh Detection ---
        # We use a context manager for the FaceMesh model
        # max_num_faces=5: Scalable as requested
        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=5,
            refine_landmarks=True,
            min_detection_confidence=0.5) as face_mesh:
            
            results = face_mesh.process(img_rgb)

        if not results.multi_face_landmarks:
            st.error("No faces were detected in the uploaded image. Please try another one.")
        else:
            # --- 3. Display Side-by-Side Preview (using sidebar toggles) ---
            st.header("Original vs. Annotated Preview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(image, caption="Original Image", use_column_width=True)

            with col2:
                # Create the style config from the sidebar toggles
                preview_style = {
                    'draw_tesselation': show_tesselation,
                    'tesselation_color': to_bgr(COLORS['white']),
                    'tesselation_thickness': 1,
                    'draw_contours': show_contours,
                    'contours_color': to_bgr(COLORS['green']),
                    'contours_thickness': 2,
                    'draw_landmarks': show_landmark_dots,
                    'landmarks_color': to_bgr(COLORS['red']),
                    'landmarks_radius': 1
                }
                
                # Create a copy to draw the preview on
                preview_image = img_bgr.copy()
                
                # Iterate over all detected faces
                for face_landmarks in results.multi_face_landmarks:
                    preview_image = draw_styled_annotations(
                        preview_image, 
                        face_landmarks, 
                        preview_style
                    )
                
                # Display the preview image (OpenCV is BGR, so we tell Streamlit)
                st.image(preview_image, caption="Annotated Preview (Live)", channels="BGR", use_column_width=True)
            
            st.markdown("---")

            # --- 4. Generate 10 Variations ---
            st.header("Generated Variations")
            st.write("Below are 10 different styles applied to your image. Use the button at the bottom to download them all.")

            generated_images = []
            variation_styles = get_variation_styles()
            
            # Show a progress bar
            st.write("Generating variations...")
            progress_bar = st.progress(0)
            
            for i, style in enumerate(variation_styles):
                variation_image = img_bgr.copy()
                
                # Apply the style to all detected faces
                for face_landmarks in results.multi_face_landmarks:
                    variation_image = draw_styled_annotations(
                        variation_image, 
                        face_landmarks, 
                        style
                    )
                
                generated_images.append((style['name'], variation_image))
                progress_bar.progress((i + 1) / 10)
            
            progress_bar.empty() # Remove progress bar after completion

            # --- 5. Display Variations in a Responsive Grid ---
            # 5 columns per row, 2 rows total
            row1_cols = st.columns(5)
            row2_cols = st.columns(5)
            
            for i, col in enumerate(row1_cols + row2_cols):
                with col:
                    caption, img = generated_images[i]
                    st.image(img, caption=f"Style {i+1}: {caption}", channels="BGR", use_column_width=True)

            st.markdown("---")
            
            # --- 6. Prepare and Offer ZIP Download ---
            st.header("Download All")
            
            # Create a zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for i, (name, img) in enumerate(generated_images):
                    # Convert from OpenCV BGR to RGB, then to PIL Image
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img_rgb)
                    
                    # Save PIL image to a byte buffer
                    img_byte_arr = io.BytesIO()
                    pil_img.save(img_byte_arr, format='PNG')
                    
                    # Write bytes to zip file
                    zip_file.writestr(
                        f"variation_{i+1}_{name.replace(' ', '_').lower()}.png", 
                        img_byte_arr.getvalue()
                    )

            st.download_button(
                label="Download All 10 Variations (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"annotated_{uploaded_file.name.split('.')[0]}.zip",
                mime="application/zip",
                help="Click to download a ZIP file containing all 10 generated images."
            )

    except Exception as e:
        st.error(f"An error occurred while processing the image: {e}")
        st.exception(e)
