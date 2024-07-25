# Install Tailscale
sudo apt update
sudo apt upgrade -y
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/buster.gpg | sudo apt-key add -
curl -fsSL https://pkgs.tailscale.com/stable/raspbian/buster.list | sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt update
sudo apt install tailscale

# Download the project
wget https://github.com/ArtiomDominic/complaints-suggestions/archive/refs/heads/main.tar.gz

# Install pip
apt install python3-pip

# Install the project requirements
cd coplaints-suggestions-main
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# # Copy .env file to the root of the project
# tar -xvf main.tar.gz

# # Run the project in the background
# python main.py
# Ctrl + Z
# bg
# disown
# # Check pid
# ps -aef