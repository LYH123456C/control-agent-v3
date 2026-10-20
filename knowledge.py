import os
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("ZHIPU_API_KEY") or os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4"
)

def load_knowledge():
    # 改成读取自控原理的文件
    file_path = os.path.join("docs", "control_theory.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text

def split_text(text, chunk_size=200):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks

def build_vector_store(chunks):
    vectors = []
    for chunk in chunks:
        response = client.embeddings.create(
            model="embedding-3",
            input=chunk
        )
        vectors.append(response.data[0].embedding)
    return vectors

def search(query, chunks, vectors, top_k=1):
    response = client.embeddings.create(
        model="embedding-3",
        input=query
    )
    query_vec = np.array(response.data[0].embedding)
    vectors = np.array(vectors)
    
    similarities = np.dot(vectors, query_vec) / (
        np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vec)
    )
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return [chunks[i] for i in top_indices]

def save_vectors(vectors, filename="vectors.npy"):
    np.save(filename, np.array(vectors))

def load_vectors(filename="vectors.npy"):
    return np.load(filename)

def load_chunks_and_vectors():
    content = load_knowledge()
    chunks = split_text(content)
    vectors = load_vectors()
    return chunks, vectors

# 运行这个文件时，生成并保存向量
if __name__ == "__main__":
    print("正在读取自控知识库...")
    content = load_knowledge()
    chunks = split_text(content)
    print(f"共切分为 {len(chunks)} 块")
    
    print("正在调用 API 向量化，请稍候...")
    vectors = build_vector_store(chunks)
    save_vectors(vectors)
    print("向量化完成，已保存到 vectors.npy！")