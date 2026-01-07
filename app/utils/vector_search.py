import os
from openai import OpenAI
from app.config.settings import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Base directory containing province folders
BASE_DIR = r"D:\EZqanoon Statues data\statue"

# Province folders (folder_name : metadata_value)
PROVINCES = {
    "federal": "federal"
    
}

# 1️⃣ Create ONE vector store
vector_store = client.vector_stores.create(
    name="pakistan_statutes_all_provinces"
)

print("✅ Vector Store ID:", vector_store.id)

# 2️⃣ Upload files province-wise with metadata
for folder_name, province_name in PROVINCES.items():
    folder_path = os.path.join(BASE_DIR, folder_name)

    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        continue

    print(f"\n📂 Uploading files for {province_name}...")

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            # Upload file
            uploaded_file = client.files.create(
                file=open(file_path, "rb"),
                purpose="assistants"
            )

            # Attach file to vector store with metadata
            client.vector_stores.files.create(
                vector_store_id=vector_store.id,
                file_id=uploaded_file.id
            )

            print(f"✅ {province_name}: {filename}")

