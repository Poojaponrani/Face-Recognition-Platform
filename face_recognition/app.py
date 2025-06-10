from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import base64
import io
from PIL import Image
import sqlite3
import datetime
import re
import json
import requests
import faiss
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app)

# Database setup
conn = sqlite3.connect('faces.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS faces (
    name TEXT PRIMARY KEY,
    encoding BLOB,
    timestamp TEXT
)
''')
conn.commit()

# Embedding + FAISS setup
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384
faiss_index = faiss.IndexFlatL2(dimension)
faiss_mapping = []  # maps FAISS index to (name, timestamp)

def rebuild_faiss_index():
    global faiss_index, faiss_mapping
    faiss_index.reset()
    faiss_mapping = []

    c.execute('SELECT name, timestamp FROM faces')
    rows = c.fetchall()
    texts = [f"{name} registered at {timestamp}" for name, timestamp in rows]
    if not texts:
        return

    embeddings = embedding_model.encode(texts)
    faiss_index.add(np.array(embeddings))
    faiss_mapping = rows

# Save face with timestamp
def save_face(name, encoding):
    enc_bytes = encoding.tobytes()
    timestamp = datetime.datetime.now().isoformat()
    c.execute('REPLACE INTO faces (name, encoding, timestamp) VALUES (?, ?, ?)', (name, enc_bytes, timestamp))
    conn.commit()
    rebuild_faiss_index()

# Load faces from DB
def load_faces():
    c.execute('SELECT name, encoding FROM faces')
    rows = c.fetchall()
    names = []
    encodings = []
    for name, enc_blob in rows:
        enc = np.frombuffer(enc_blob, dtype=np.float64)
        names.append(name)
        encodings.append(enc)
    return names, encodings

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        image_data = data.get('image')

        if not name or not image_data:
            return jsonify(status="error", reason="Missing name or image")

        if "," in image_data:
            image_data = image_data.split(",")[1]

        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_np = np.array(img)

        face_locations = face_recognition.face_locations(img_np)
        if not face_locations:
            return jsonify(status="error", reason="No face detected")

        face_encodings = face_recognition.face_encodings(img_np, face_locations)
        encoding = face_encodings[0]

        save_face(name, encoding)

        return jsonify(status="success")
    except Exception as e:
        return jsonify(status="error", reason=str(e))

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify(status="error", reason="Missing image")

        if "," in image_data:
            image_data = image_data.split(",")[1]

        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_np = np.array(img)

        face_locations = face_recognition.face_locations(img_np)
        if not face_locations:
            return jsonify(status="error", reason="No face detected")

        face_encodings = face_recognition.face_encodings(img_np, face_locations)
        known_names, known_encodings = load_faces()

        results = []

        for encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, encoding)
            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
            results.append(name)

        return jsonify(status="success", names=results)
    except Exception as e:
        return jsonify(status="error", reason=str(e))

@app.route('/clear-db', methods=['POST'])
def clear_db():
    try:
        c.execute('DELETE FROM faces')
        conn.commit()
        rebuild_faiss_index()
        return jsonify(status="success", message="All entries deleted.")
    except Exception as e:
        return jsonify(status="error", reason=str(e))

@app.route('/delete-name', methods=['POST'])
def delete_name():
    try:
        data = request.get_json()
        name = data.get("name")
        if not name:
            return jsonify(status="error", reason="Name required")
        c.execute('DELETE FROM faces WHERE name = ?', (name,))
        conn.commit()
        rebuild_faiss_index()
        return jsonify(status="success", message=f"Deleted entry for {name}.")
    except Exception as e:
        return jsonify(status="error", reason=str(e))

@app.route('/list-db', methods=['GET'])
def list_db():
    try:
        c.execute('SELECT name, timestamp FROM faces ORDER BY timestamp')
        rows = c.fetchall()
        return jsonify(status="success", data=rows)
    except Exception as e:
        return jsonify(status="error", reason=str(e))

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        if not user_message:
            return jsonify(response="⚠️ Empty message.")

        query_embedding = embedding_model.encode([user_message])

        k = 5
        if faiss_index.ntotal == 0:
            context_lines = []
        else:
            distances, indices = faiss_index.search(np.array(query_embedding), k)
            context_lines = [f"{faiss_mapping[i][0]} registered at {faiss_mapping[i][1]}" for i in indices[0] if i < len(faiss_mapping)]

        context = "\n".join(context_lines)
        prompt = f"""You are a helpful assistant. Based on the registration logs below, answer the user's question.

Registration Data:
{context}

Question: {user_message}
"""

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mistral",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
        )

        output = response.json()
        reply = output.get("message", {}).get("content", "⚠️ No response from Mistral.")
        return jsonify(response=reply)
    except Exception as e:
        return jsonify(response=f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    rebuild_faiss_index()
    app.run(debug=True)
