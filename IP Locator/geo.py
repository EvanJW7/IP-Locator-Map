import requests
import subprocess
import re
import folium
import geocoder 

target_website = 'psg.fr'

#Get raw tracepath output
def run_traceroute(website):
    try:
        traceroute_output = subprocess.check_output(["traceroute", website], universal_newlines=True)
        print("Raw data")
        print(traceroute_output)
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

#Get my current location for the mapping location of first router (because it will be private)
def get_current_location():
    g = geocoder.ip('me')  # 'me' represents your current IP address
    if g.latlng:
        latitude, longitude = g.latlng
        return [latitude, longitude]
    else:
        return None


def main():
    print(f"\nDestination: {target_website}\n")
    print("Tracing route to desired destination...")
    print("This may take a few minutes\n")
    latitudes = []
    longitudes = []
    cities = []
    
    raw_data = run_traceroute(target_website)
    ip_addresses = extract_ip_addresses(raw_data)
    current_location = get_current_location()
    latitudes.append(current_location[0])
    longitudes.append(current_location[1])


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
            cities.append(data['city'])
        except:
            print(f"{ip:>25}     Home router (private)")

    print(f"\nCongrats! Your internet connection made it all the way to {cities[-1]}")
    print(f"Total IPs visited: {len(ip_addresses)}")
    print(f"Total cities visited: {len(cities)}\n")

    m = folium.Map(location=[latitudes[0], longitudes[0]], zoom_start=2)

    for lat, lon in zip(latitudes, longitudes):
        folium.Marker([lat, lon]).add_to(m)

    folium.PolyLine(
        locations=list(zip(latitudes, longitudes)),
        color='blue',
        weight=2,
        opacity=1
    ).add_to(m)

    m.save('coordinates_map.html')


if __name__ == '__main__':
    main()
    



