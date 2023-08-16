import requests
import subprocess
import re
import folium

website = 'psg.fr'
print(f"Destination: {website}\n")
print("tracing path to desired destination...\n")


def run_tracepath(website):
    try:
        tracepath_output = subprocess.check_output(["tracepath", website], universal_newlines=True)
        print("Trace path data:")
        print(tracepath_output)
        return tracepath_output
    except subprocess.CalledProcessError as e:
        print("Error running tracepath:", e)
        return None

raw_data = run_tracepath(website)

def extract_ip_addresses(tracepath_output):
    ip_addresses = []
    if tracepath_output:
        lines = tracepath_output.splitlines()
        for line in lines:
            match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
            if match:
                ip_addresses.append(match.group())
    return ip_addresses

ip_addresses = extract_ip_addresses(raw_data)

latitudes = []
longitudes = []

print("\nFiltered data: ")
for ip in ip_addresses:
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url)
        data = response.json()
        print(f"{ip:>25}     {data['city']}, {data['regionName']}")
        latitudes.append(data['lat'])
        longitudes.append(data['lon'])
    except:
        print(f"{ip:>25}     unable to locate")

m = folium.Map(location=[latitudes[0], longitudes[0]], zoom_start=5)

# Add markers for each set of coordinates
for lat, lon in zip(latitudes, longitudes):
    folium.Marker([lat, lon]).add_to(m)

lines = folium.PolyLine(
    locations=list(zip(latitudes, longitudes)),
    color='blue',
    weight=2,
    opacity=1
).add_to(m)

# Save the map to an HTML file
m.save('coordinates_map.html')
