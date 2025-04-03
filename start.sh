!/bin/bash

# Start both scripts in the background
python main.py --server & 
PID1=$!
streamlit run ui/main.py &
PID2=$!

# Function to handle termination signals
cleanup() {
    echo "Stopping scripts..."
    kill $PID1 $PID2
    wait
}

# Trap termination signals and call cleanup
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait