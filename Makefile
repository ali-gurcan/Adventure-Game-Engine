.PHONY: play generate editor test install clean

# Start the game with the default template world
play:
	python3 main.py play test_world2.json

# Generate a new dynamic world using Ollama and play it
generate:
	python3 main.py generate

# Open the built-in world editor
editor:
	python3 main.py editor

# Run the automated testing script to verify game mechanics
test:
	python3 auto_test.py

# Install python dependencies required by the engine
install:
	pip install rich

# Clean up generated save data and pycache
clean:
	rm -f save_data.json
	find . -type d -name "__pycache__" -exec rm -r {} +
