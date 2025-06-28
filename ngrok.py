from pyngrok import ngrok

# Start the tunnel to localhost:8000 (your Django dev server)
public_url = ngrok.connect(8000)
print("Ngrok tunnel started at:", public_url)

# Keep it running
input("Press Enter to exit...\n")
