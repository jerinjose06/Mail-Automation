import sys
from langchain_ollama import ChatOllama

def main():
    print("Initializing LLM pointing strictly to qwen3.5:4b with temperature=0...")
    
    try:
        llm = ChatOllama(
            model="qwen3.5:4b",
            temperature=0,
        )
        print("Sending dummy prompt to the local LLM...")
        response = llm.invoke("Hello, are you online? Please reply with a short confirmation.")
        print("\n--- LLM Response ---")
        print(response.content)
        print("--------------------")
        print("Verification successful: Clean text loop completed.")
    except Exception as e:
        print(f"Error during verification: {e}")
        print("If the error is about model not found, make sure to pull it using `ollama pull qwen3.5:4b` or change the model name to `llama3.2:3b`.")
        sys.exit(1)

if __name__ == "__main__":
    main()
