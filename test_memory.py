from mem0 import Memory

config = {
    "llm": {
        "provider": "openai",
        "config": {
            "api_key": "hermes-local",
            "model": "gpt-5.4",
            "openai_base_url": "http://localhost:8642/v1"
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "lana_memory",
            "path": "/Users/fernandoserina/lana_memory/chroma_db"
        }
    }
}

print("Connecting...")
memory = Memory.from_config(config)

print("Adding test memory...")
memory.add(
    "Fernando wants Lana to become an autonomous digital persona with persistent memory.",
    user_id="lana"
)

print("Searching...")
results = memory.search(
    "What does Fernando want Lana to become?",
    filters={"user_id": "lana"}
)

for item in results.get("results", []):
    print(f"  Memory: {item.get('memory', item)}")
    print(f"  Score:  {item.get('score', 'N/A')}")
    print("---")

print("\n✅ Mem0 is working with:")
print(f"   LLM: Hermes API (localhost:8642)")
print(f"   Embeddings: HuggingFace (all-MiniLM-L6-v2)")
print(f"   Storage: Chroma (local)")
