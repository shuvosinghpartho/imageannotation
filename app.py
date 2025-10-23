# # # import streamlit as st
# # # from pymongo import MongoClient

# # # #MongoDB Connection
# # # client = MongoClient("mongodb://localhost:27017/")
# # # db = client["test_db"]   # database name
# # # collection = db["users"] # collection name

# # # st.title("🚀Streamlit + MongoDB Demo")

# # # #User Input Form
# # # st.header("Add a User")
# # # name = st.text_input("Enter name")
# # # age = st.number_input("Enter age", min_value=1, max_value=100)
# # # if st.button("Add to Database"):
# # #     if name:
# # #         collection.insert_one({"name": name, "age": age})
# # #         st.success(f"Added {name} successfully!")
# # #     else:
# # #         st.warning("Please enter a name.")

# # # #Show Data from MongoDB
# # # st.header("User List")
# # # users = list(collection.find({}, {"_id": 0}))
# # # if users:
# # #     st.table(users)
# # # else:
# # #     st.write("No users found.")




# # import streamlit as st
# # from pymongo import MongoClient
# # import random

# # # MongoDB Connection
# # client = MongoClient("mongodb://localhost:27017/")
# # db = client["movie_db"]
# # collection = db["movies"]

# # # Streamlit App UI
# # st.set_page_config(page_title="🎬 Movie Recommender", layout="centered")
# # st.title("🎥 Movie Recommendation App")
# # st.write("Add movies to your personal database and get random suggestions!")

# # # Add Movie Section 
# # st.subheader("➕ Add a New Movie")
# # movie_name = st.text_input("Enter movie name")

# # if st.button("Add Movie"):
# #     if movie_name.strip():
# #         # Avoid duplicates
# #         if collection.find_one({"name": movie_name.strip()}, {"_id": 0}):
# #             st.warning(f"'{movie_name}' already exists!")
# #         else:
# #             collection.insert_one({"name": movie_name.strip()})
# #             st.success(f"✅ '{movie_name}' added successfully!")
# #     else:
# #         st.error("Please enter a valid movie name.")

# # st.divider()

# # # Display All Movies
# # st.subheader("🎞️ Movie List")
# # movies = [doc["name"] for doc in collection.find({}, {"_id": 0})]
# # if movies:
# #     st.write(movies)
# # else:
# #     st.info("No movies found yet. Add some above!")

# # st.divider()

# # # Random Movie Suggestion
# # st.subheader("🎲 Feeling Lucky?")
# # if st.button("Suggest a Random Movie"):
# #     if movies:
# #         random_movie = random.choice(movies)
# #         st.success(f"🍿 You should watch: **{random_movie}**")
# #     else:
# #         st.warning("No movies available! Please add some first.")






# import streamlit as st
# from PIL import Image, ImageDraw
# from pymongo import MongoClient
# import io

# # --- MongoDB Connection ---
# client = MongoClient("mongodb://localhost:27017/")
# db = client["image_annotation"]
# collection = db["annotations"]

# st.title("🖼️ Image Annotation Tool")

# # --- Upload Image ---
# uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
# if uploaded_file:
#     image = Image.open(uploaded_file)
#     st.image(image, caption="Original Image", use_column_width=True)

#     # --- Draw bounding box ---
#     st.write("Enter bounding box coordinates:")
#     x = st.number_input("X", min_value=0)
#     y = st.number_input("Y", min_value=0)
#     w = st.number_input("Width", min_value=1)
#     h = st.number_input("Height", min_value=1)
#     label = st.text_input("Label", value="object")

#     if st.button("Annotate"):
#         draw = ImageDraw.Draw(image)
#         draw.rectangle([(x, y), (x + w, y + h)], outline="red", width=3)
#         st.image(image, caption="Annotated Image")

#         # Save to MongoDB
#         annotation = {
#             "filename": uploaded_file.name,
#             "annotations": [{
#                 "x": x, "y": y, "width": w, "height": h, "label": label
#             }]
#         }
#         collection.insert_one(annotation)
#         st.success("Annotation saved to MongoDB ✅")




import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import random
import io
import zipfile
from datetime import datetime
from pymongo import MongoClient
import base64
from bson import ObjectId

# MongoDB Configuration
@st.cache_resource
def get_mongodb_connection():
    """Initialize MongoDB connection"""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        db = client['image_annotation_db']
        return db
    except Exception as e:
        st.error(f"❌ MongoDB Connection Error: {e}")
        return None

# Initialize MongoDB
db = get_mongodb_connection()

st.set_page_config(page_title="Image Annotation App", layout="wide", page_icon="🎨")

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .history-item {
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🎨 Image Annotation Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload an image and generate 10 different annotated versions instantly</p>', unsafe_allow_html=True)

# Sidebar for settings and history
with st.sidebar:
    st.header("⚙️ Annotation Settings")
    
    annotation_size = st.slider("Annotation Size", 50, 300, 100, 10)
    line_width = st.slider("Line Width", 2, 10, 4, 1)
    
    st.divider()
    
    selected_shapes = st.multiselect(
        "Select Annotation Types",
        ["rectangle", "circle", "ellipse", "triangle", "pentagon", "cross", "arrow", "mask", "dotted", "text"],
        default=["rectangle", "circle", "ellipse", "triangle", "pentagon", "cross", "arrow", "mask", "dotted", "text"]
    )
    
    st.divider()
    
    # User identification
    st.markdown("### 👤 User Info")
    user_name = st.text_input("Your Name (optional)", value="Anonymous")
    
    st.divider()
    
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. Upload your image
    2. Adjust settings (optional)
    3. View annotated versions
    4. Download images
    5. View history below
    """)
    
    st.divider()
    
    # History section
    st.markdown("### 📜 Recent History")
    if db is not None:
        try:
            recent_uploads = list(db.uploads.find().sort("timestamp", -1).limit(5))
            
            if recent_uploads:
                for upload in recent_uploads:
                    with st.expander(f"🖼️ {upload.get('user_name', 'Anonymous')} - {upload.get('timestamp', '').strftime('%Y-%m-%d %H:%M')}"):
                        st.write(f"**Annotations:** {upload.get('annotation_count', 0)}")
                        st.write(f"**Image Size:** {upload.get('image_width', 0)}x{upload.get('image_height', 0)}")
                        if st.button("Load", key=f"load_{upload['_id']}"):
                            st.session_state.load_history_id = str(upload['_id'])
                            st.rerun()
            else:
                st.info("No history yet")
        except Exception as e:
            st.warning(f"Could not load history: {e}")
    else:
        st.warning("📴 MongoDB not connected")

# Function to save to MongoDB
def save_to_mongodb(user_name, original_image, annotated_images, settings):
    """Save upload data to MongoDB"""
    if db is None:
        return None
    
    try:
        # Convert original image to base64
        img_buffer = io.BytesIO()
        original_image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Convert annotated images to base64
        annotated_data = []
        for name, img in annotated_images:
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            annotated_data.append({
                'name': name,
                'image_data': base64.b64encode(img_buffer.getvalue()).decode()
            })
        
        # Create document
        document = {
            'user_name': user_name,
            'timestamp': datetime.now(),
            'original_image': img_base64,
            'image_width': original_image.size[0],
            'image_height': original_image.size[1],
            'annotated_images': annotated_data,
            'annotation_count': len(annotated_images),
            'settings': settings
        }
        
        # Insert into MongoDB
        result = db.uploads.insert_one(document)
        return result.inserted_id
    except Exception as e:
        st.error(f"Error saving to database: {e}")
        return None

# Function to load from MongoDB
def load_from_mongodb(upload_id):
    """Load upload data from MongoDB"""
    if db is None:
        return None
    
    try:
        document = db.uploads.find_one({'_id': ObjectId(upload_id)})
        if document:
            # Convert base64 back to images
            original_image = Image.open(io.BytesIO(base64.b64decode(document['original_image'])))
            
            annotated_images = []
            for item in document['annotated_images']:
                img = Image.open(io.BytesIO(base64.b64decode(item['image_data'])))
                annotated_images.append((item['name'], img))
            
            return {
                'user_name': document['user_name'],
                'timestamp': document['timestamp'],
                'original_image': original_image,
                'annotated_images': annotated_images,
                'settings': document.get('settings', {})
            }
    except Exception as e:
        st.error(f"Error loading from database: {e}")
        return None

# Check if loading from history
if 'load_history_id' in st.session_state:
    loaded_data = load_from_mongodb(st.session_state.load_history_id)
    if loaded_data:
        st.session_state.loaded_original = loaded_data['original_image']
        st.session_state.annotated_images = loaded_data['annotated_images']
        st.success(f"✅ Loaded history from {loaded_data['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    del st.session_state.load_history_id

# Main upload area
uploaded_file = st.file_uploader("📤 Upload an image", type=["jpg", "jpeg", "png"], help="Supported formats: JPG, JPEG, PNG")

# Use loaded image if available
if 'loaded_original' in st.session_state and uploaded_file is None:
    image = st.session_state.loaded_original
else:
    image = Image.open(uploaded_file).convert("RGB") if uploaded_file else None

if image:
    # Load and display original image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption="📷 Original Image", use_container_width=True)
    
    w, h = image.size
    st.info(f"📐 Image dimensions: {w}x{h} pixels")
    
    st.divider()

    # Generate annotations
    col1, col2 = st.columns(2)
    with col1:
        generate_btn = st.button("🎨 Generate Annotations", type="primary", use_container_width=True)
    with col2:
        save_to_db = st.checkbox("💾 Save to Database", value=True)
    
    if generate_btn:
        with st.spinner("Generating annotated images..."):
            colors = ["red", "green", "blue", "purple", "orange", "yellow", "pink", "cyan", "magenta", "lime"]
            annotated_images = []

            for shape in selected_shapes:
                img_copy = image.copy()
                draw = ImageDraw.Draw(img_copy)

                # Calculate position based on annotation size
                max_x = max(50, w - annotation_size - 50)
                max_y = max(50, h - annotation_size - 50)
                x = random.randint(50, max_x)
                y = random.randint(50, max_y)
                width = min(annotation_size, w - x - 50)
                height = min(annotation_size, h - y - 50)
                color = random.choice(colors)

                # Draw different shapes
                if shape == "rectangle":
                    draw.rectangle([(x, y), (x + width, y + height)], outline=color, width=line_width)
                
                elif shape == "circle":
                    radius = min(width, height) // 2
                    draw.ellipse([(x, y), (x + 2*radius, y + 2*radius)], outline=color, width=line_width)
                
                elif shape == "ellipse":
                    draw.ellipse([(x, y), (x + width, y + height)], outline=color, width=line_width)
                
                elif shape == "triangle":
                    draw.polygon([
                        (x + width//2, y), 
                        (x, y + height), 
                        (x + width, y + height)
                    ], outline=color, width=line_width)
                
                elif shape == "pentagon":
                    draw.polygon([
                        (x + width//2, y),
                        (x, y + height//3),
                        (x + width//5, y + height),
                        (x + 4*width//5, y + height),
                        (x + width, y + height//3)
                    ], outline=color, width=line_width)
                
                elif shape == "cross":
                    draw.line([(x, y), (x + width, y + height)], fill=color, width=line_width)
                    draw.line([(x + width, y), (x, y + height)], fill=color, width=line_width)
                
                elif shape == "arrow":
                    draw.line([(x, y + height//2), (x + width, y + height//2)], fill=color, width=line_width)
                    arrow_size = 15 + line_width
                    draw.polygon([
                        (x + width, y + height//2), 
                        (x + width - arrow_size, y + height//2 - arrow_size//2), 
                        (x + width - arrow_size, y + height//2 + arrow_size//2)
                    ], fill=color)
                
                elif shape == "mask":
                    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
                    mask_color = tuple(list(ImageColor.getrgb(color)) + [100])
                    ImageDraw.Draw(overlay).rectangle([(x, y), (x + width, y + height)], fill=mask_color)
                    img_copy = Image.alpha_composite(img_copy.convert("RGBA"), overlay).convert("RGB")
                
                elif shape == "dotted":
                    dot_spacing = 10
                    for dx in range(x, x + width, dot_spacing):
                        draw.ellipse([(dx-2, y-2), (dx+2, y+2)], fill=color)
                        draw.ellipse([(dx-2, y+height-2), (dx+2, y+height+2)], fill=color)
                    for dy in range(y, y + height, dot_spacing):
                        draw.ellipse([(x-2, dy-2), (x+2, dy+2)], fill=color)
                        draw.ellipse([(x+width-2, dy-2), (x+width+2, dy+2)], fill=color)
                
                elif shape == "text":
                    try:
                        font = ImageFont.truetype("arial.ttf", 30)
                    except:
                        font = ImageFont.load_default()
                    draw.text((x, y), "ANNOTATION", fill=color, font=font)

                annotated_images.append((f"{shape.capitalize()}", img_copy))

            # Store in session state
            st.session_state.annotated_images = annotated_images
            
            # Save to MongoDB if checkbox is checked
            if save_to_db and db is not None:
                settings = {
                    'annotation_size': annotation_size,
                    'line_width': line_width,
                    'selected_shapes': selected_shapes
                }
                upload_id = save_to_mongodb(user_name, image, annotated_images, settings)
                if upload_id:
                    st.success(f"✅ Generated {len(annotated_images)} annotated images and saved to database!")
                else:
                    st.warning(f"⚠️ Generated {len(annotated_images)} images but failed to save to database")
            else:
                st.success(f"✅ Generated {len(annotated_images)} annotated images!")

    # Display annotated images
    if 'annotated_images' in st.session_state and st.session_state.annotated_images:
        st.subheader("🖼️ Annotated Versions")
        
        # Create download all button
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for name, img in st.session_state.annotated_images:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                zip_file.writestr(f"{name}_annotation.png", img_buffer.getvalue())
        
        zip_buffer.seek(0)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                label="📦 Download All as ZIP",
                data=zip_buffer,
                file_name=f"annotated_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )
        
        st.divider()
        
        # Display images in grid
        cols = st.columns(2)
        for idx, (name, img) in enumerate(st.session_state.annotated_images):
            with cols[idx % 2]:
                st.image(img, caption=f"🏷️ {name} Annotation", use_container_width=True)
                
                # Individual download button
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                st.download_button(
                    label=f"💾 Download {name}",
                    data=img_buffer,
                    file_name=f"{name}_annotation.png",
                    mime="image/png",
                    key=f"download_{idx}",
                    use_container_width=True
                )
                
                st.markdown("---")

else:
    # Show example when no image is uploaded
    st.info("👆 Please upload an image to get started!")
    
    with st.expander("ℹ️ What this app does"):
        st.markdown("""
        This app generates multiple annotated versions of your image with different shapes and styles:
        
        - **Rectangle**: Standard bounding box
        - **Circle**: Circular annotation
        - **Ellipse**: Oval-shaped annotation
        - **Triangle**: Three-sided polygon
        - **Pentagon**: Five-sided polygon
        - **Cross**: X-mark annotation
        - **Arrow**: Directional pointer
        - **Mask**: Semi-transparent overlay
        - **Dotted**: Dotted line boundary
        - **Text**: Text label annotation
        
        Perfect for:
        - Creating training data for computer vision
        - Demonstrating annotation styles
        - Quick image markup
        - Educational purposes
        
        **New MongoDB Features:**
        - All uploads are automatically saved to database
        - View recent history in sidebar
        - Load previous annotations anytime
        - Track all your annotation projects
        """)
    
    # Database statistics
    if db is not None:
        st.divider()
        st.subheader("Database Statistics")
        try:
            total_uploads = db.uploads.count_documents({})
            total_annotations = sum([doc.get('annotation_count', 0) for doc in db.uploads.find()])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Uploads", total_uploads)
            with col2:
                st.metric("Total Annotations", total_annotations)
            with col3:
                if total_uploads > 0:
                    avg = total_annotations / total_uploads
                    st.metric("Avg per Upload", f"{avg:.1f}")
        except Exception as e:
            st.error(f"Could not load statistics: {e}")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        Shuvo Singh Partho| Upload • Annotate • Save • Download
    </div>
""", unsafe_allow_html=True)