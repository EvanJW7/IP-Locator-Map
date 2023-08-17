import requests
import subprocess
import re
import folium

target_website = 'binance.com'

#Get raw tracepath output
def run_traceroute(website):
    try:
        traceroute_output = subprocess.check_output(["traceroute", website], universal_newlines=True)
        return traceroute_output
    except subprocess.CalledProcessError as e:
        print("Error running tracepath:", e)
        return None

#Extract IP addresses from raw traceroute output
def extract_ip_addresses(tracepath_output):
    ip_addresses = []
    if tracepath_output:
        lines = tracepath_output.splitlines()
        for line in lines:
            match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
            if match:
                ip_addresses.append(match.group())
    return ip_addresses


def main():
    print(f"\nDestination: {target_website}\n")
    print("Tracing route to desired destination...")
    print("This may take a few minutes")

    raw_data = run_traceroute(target_website)
    ip_addresses = extract_ip_addresses(raw_data)
    ip_addresses.append(ip_addresses.pop(0))
    latitudes = []
    longitudes = []
    cities = []

    #Print IPs and their location and map them
    print("\nFiltered data: ")
    for ip in ip_addresses:
        try:
            url = f"http://ip-api.com/json/{ip}"
            response = requests.get(url)
            data = response.json()
            print(f"{ip:>25}     {data['city']}, {data['regionName']}, {data['country']}")
            latitudes.append(data['lat'])
            longitudes.append(data['lon'])
            if data['city'] not in cities:
                cities.append(data['city'])
        except:
            print(f"{ip:>25}     Private IP, unable to locate")

    print(f"\nCongrats! Your internet connection made it all the way to {data['city']}")
    print(f"Total IPs visited: {len(ip_addresses)}")
    print(f"Total cities visited: {len(cities)}")

    m = folium.Map(location=[latitudes[0], longitudes[0]], zoom_start=2)

    for lat, lon in zip(latitudes, longitudes):
        folium.Marker([lat, lon]).add_to(m)

    folium.PolyLine(
        locations=list(zip(latitudes, longitudes)),
        color='blue',
        weight=2,
        opacity=1
    ).add_to(m)

    m.save('ip_coordinates_map.html')


if __name__ == '__main__':
    main()

