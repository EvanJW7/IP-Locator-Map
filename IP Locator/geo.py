#!/usr/bin/env python3
"""
Enhanced Network Route Tracer and Visualizer
Traces network routes to target websites and creates interactive maps.
"""

import requests
import subprocess
import re
import folium
import geocoder
import argparse
import json
import time
import logging
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Trace network route and create interactive map')
    parser.add_argument('--target', '-t', default='github.com', help='Target website to trace')
    parser.add_argument('--timeout', default=30, type=int, help='Timeout in seconds for traceroute')
    parser.add_argument('--output', '-o', default='coordinates_map.html', help='Output HTML file')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--export-format', choices=['html', 'json', 'csv'], default='html', 
                       help='Export format for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--parallel', '-p', action='store_true', help='Use parallel processing for IP lookups')
    return parser.parse_args()

def load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration from file or return defaults."""
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Could not load config file {config_path}: {e}")
    
    return {
        "default_target": "github.com",
        "timeout": 30,
        "output_file": "coordinates_map.html",
        "rate_limit_delay": 0.1,
        "max_workers": 5
    }

def suggest_alternative_targets() -> List[str]:
    """Suggest alternative targets when the current one fails."""
    return [
        "google.com",
        "github.com", 
        "amazon.com",
        "microsoft.com",
        "apple.com",
        "netflix.com",
        "facebook.com",
        "twitter.com"
    ]

def run_traceroute(website: str, timeout: int = 30) -> Optional[str]:
    """Run traceroute command with timeout and error handling."""
    try:
        logger.info(f"Starting traceroute to {website}")
        
        # Use more robust traceroute settings
        # -w 1: wait 1 second per hop (faster)
        # -q 1: send 1 query per hop (faster)
        # -n: don't resolve hostnames (faster)
        # -m 15: maximum 15 hops (prevent getting stuck)
        traceroute_cmd = ["traceroute", "-w", "1", "-q", "1", "-n", "-m", "15", website]
        
        # Use subprocess.run instead of check_output for better control
        result = subprocess.run(
            traceroute_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0 or result.stdout.strip():
            # Even if traceroute doesn't complete fully, we can use partial results
            logger.info("Traceroute completed (may be partial)")
            return result.stdout
        else:
            logger.error(f"Traceroute failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
            return None
        
    except subprocess.TimeoutExpired:
        logger.error(f"Traceroute timed out after {timeout} seconds")
        logger.info("Try a different target or increase timeout with --timeout 60")
        return None
    except FileNotFoundError:
        logger.error("traceroute command not found. Please install it.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running traceroute: {e}")
        return None

def extract_ip_addresses(traceroute_output: str) -> List[str]:
    """Extract IP addresses from traceroute output."""
    ip_addresses = []
    if traceroute_output:
        lines = traceroute_output.splitlines()
        for line in lines:
            # Skip lines that are just asterisks or empty
            if '*' in line and line.strip().count('*') >= 2:
                continue
                
            # Improved regex to match IP addresses
            matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
            for match in matches:
                # Validate IP address (basic check)
                if match not in ip_addresses and match != '0.0.0.0':
                    ip_addresses.append(match)
    
    logger.info(f"Extracted {len(ip_addresses)} unique IP addresses")
    return ip_addresses

def get_current_location() -> Optional[List[float]]:
    """Get current location using multiple methods automatically."""
    try:
        logger.info("Getting current location...")
        
        # Method 1: Try ipinfo.io first (often more accurate)
        try:
            response = requests.get('https://ipinfo.io/json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'loc' in data:
                    lat, lon = map(float, data['loc'].split(','))
                    location = [lat, lon]
                    logger.info(f"Location from ipinfo.io: {location}")
                    return location
        except Exception as e:
            logger.debug(f"ipinfo.io failed: {e}")
        
        # Method 2: Try geocoder as fallback
        try:
            g = geocoder.ip('me')
            if g.latlng:
                location = g.latlng
                logger.info(f"Location from geocoder: {location}")
                return location
        except Exception as e:
            logger.debug(f"geocoder failed: {e}")
        
        # Method 3: Try a third service
        try:
            response = requests.get('https://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'latitude' in data and 'longitude' in data:
                    location = [data['latitude'], data['longitude']]
                    logger.info(f"Location from ipapi.co: {location}")
                    return location
        except Exception as e:
            logger.debug(f"ipapi.co failed: {e}")
        
        logger.warning("Could not determine current location automatically")
        return None
            
    except Exception as e:
        logger.error(f"Error getting current location: {e}")
        return None

def get_ip_location(ip: str, rate_limit_delay: float = 0.1) -> Optional[Dict]:
    """Get location information for an IP address with rate limiting."""
    time.sleep(rate_limit_delay)  # Rate limiting
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        logger.debug(f"Error getting location for {ip}: {e}")
        return None
    except ValueError as e:
        logger.debug(f"Error parsing JSON for {ip}: {e}")
        return None

def get_locations_parallel(ip_addresses: List[str], max_workers: int = 5) -> Dict[str, Dict]:
    """Get locations for multiple IPs using parallel processing."""
    logger.info(f"Getting locations for {len(ip_addresses)} IPs using {max_workers} workers")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_ip_location, ip): ip for ip in ip_addresses}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            results[ip] = future.result()
    return results

def create_enhanced_map(latitudes: List[float], longitudes: List[float], 
                       cities: List[str], ip_addresses: List[str]) -> folium.Map:
    """Create an enhanced map with markers, popups, and route line."""
    if not latitudes or not longitudes:
        logger.error("No coordinates available for map creation")
        return None
    
    # Create map centered on first location
    m = folium.Map(location=[latitudes[0], longitudes[0]], zoom_start=2)
    
    # Add markers with popups
    for i, (lat, lon, city, ip) in enumerate(zip(latitudes, longitudes, cities, ip_addresses)):
        popup_text = f"""
        <b>Hop {i+1}</b><br>
        <b>IP:</b> {ip}<br>
        <b>City:</b> {city}<br>
        <b>Coordinates:</b> {lat:.4f}, {lon:.4f}
        """
        
        # Color markers based on hop number and add descriptive icons
        if i == 0:
            color = 'red'  # Start point
            icon = 'home'  # Home icon for start point
        elif i == len(latitudes) - 1:
            color = 'green'  # End point
            icon = 'flag'  # Flag icon for destination
        else:
            color = 'blue'  # Intermediate hops
            icon = 'info-sign'  # Info icon for intermediate hops
        
        folium.Marker(
            [lat, lon], 
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Hop {i+1}: {city}",
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(m)
    
    # Add route line (dashed to show it's an approximation)
    if len(latitudes) > 1:
        folium.PolyLine(
            locations=list(zip(latitudes, longitudes)),
            color='blue',
            weight=3,
            opacity=0.8,
            popup="Network Route (Approximate)",
            dash_array='10, 5'  # Creates dashed line: 10px dash, 5px gap
        ).add_to(m)
    
    # Add enhanced legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 30px; left: 30px; width: 220px; 
                background-color: rgba(255, 255, 255, 0.95); border: 2px solid #666; border-radius: 10px; 
                z-index: 9999; font-family: Arial, sans-serif; font-size: 12px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 18px; backdrop-filter: blur(5px);">
        <div style="font-weight: bold; font-size: 15px; margin-bottom: 12px; color: #333; border-bottom: 2px solid #ddd; padding-bottom: 8px;">
            🗺️ Network Route Legend
        </div>
        <div style="margin-bottom: 10px; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 18px; background-color: #ff4444; border-radius: 50%; margin-right: 10px; border: 2px solid #cc0000; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></span>
            <span style="color: #333; font-weight: 500;">Start Point (Your Location)</span>
        </div>
        <div style="margin-bottom: 10px; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 18px; background-color: #4444ff; border-radius: 50%; margin-right: 10px; border: 2px solid #0000cc; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></span>
            <span style="color: #333; font-weight: 500;">Intermediate Network Hops</span>
        </div>
        <div style="margin-bottom: 10px; display: flex; align-items: center;">
            <span style="display: inline-block; width: 18px; height: 18px; background-color: #44ff44; border-radius: 50%; margin-right: 10px; border: 2px solid #00cc00; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></span>
            <span style="color: #333; font-weight: 500;">Destination (Target Website)</span>
        </div>
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 11px; color: #666; font-style: italic;">
            💡 Click markers for details • Blue dashed line shows approximate route
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def export_results(latitudes: List[float], longitudes: List[float], 
                  cities: List[str], ip_addresses: List[str], 
                  format: str = 'html', output_file: str = 'coordinates_map.html'):
    """Export results in various formats."""
    if format == 'json':
        data = {
            'route': [
                {
                    'hop': i+1,
                    'ip': ip, 
                    'city': city, 
                    'latitude': lat, 
                    'longitude': lon
                }
                for i, (ip, city, lat, lon) in enumerate(zip(ip_addresses, cities, latitudes, longitudes))
            ],
            'summary': {
                'total_hops': len(ip_addresses),
                'total_cities': len(set(cities)),
                'start_point': cities[0] if cities else None,
                'end_point': cities[-1] if cities else None
            }
        }
        json_file = output_file.replace('.html', '.json')
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results exported to {json_file}")
    
    elif format == 'csv':
        import csv
        csv_file = output_file.replace('.html', '.csv')
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Hop', 'IP', 'City', 'Latitude', 'Longitude'])
            for i, (ip, city, lat, lon) in enumerate(zip(ip_addresses, cities, latitudes, longitudes)):
                writer.writerow([i+1, ip, city, lat, lon])
        logger.info(f"Results exported to {csv_file}")

def main():
    """Main function."""
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = load_config(args.config)
    
    # Use command line arguments or config defaults
    target = args.target or config.get('default_target', 'google.com')
    timeout = args.timeout or config.get('timeout', 30)
    output_file = args.output or config.get('output_file', 'coordinates_map.html')
    rate_limit_delay = config.get('rate_limit_delay', 0.1)
    max_workers = config.get('max_workers', 5)
    
    logger.info(f"Starting network trace to {target}")
    print(f"\n🎯 Destination: {target}")
    print("🔄 Tracing route to destination...")
    print("⏱️  This may take a few minutes\n")
    
    # Run traceroute
    raw_data = run_traceroute(target, timeout)
    if not raw_data:
        logger.error("Failed to get traceroute data")
        print(f"\n❌ Failed to trace route to {target}")
        print("🔍 This could be due to:")
        print("   - Network restrictions or firewalls")
        print("   - Target website blocking traceroute requests")
        print("   - Slow network connection")
        print("   - Target website being down")
        
        # Suggest alternatives
        alternatives = suggest_alternative_targets()
        print(f"\n💡 Try one of these alternative targets:")
        for alt in alternatives[:5]:  # Show first 5 alternatives
            print(f"   python3 geo.py --target {alt}")
        
        print(f"\n⏱️  Or increase timeout:")
        print(f"   python3 geo.py --target {target} --timeout 60")
        return
    
    # Extract IP addresses
    ip_addresses = extract_ip_addresses(raw_data)
    if not ip_addresses:
        logger.error("No IP addresses found in traceroute output")
        return
    
    # Get current location automatically
    current_location = get_current_location()
    if not current_location:
        logger.warning("Could not determine current location, using default")
        current_location = [0, 0]  # Default coordinates
    
    latitudes = [current_location[0]]
    longitudes = [current_location[1]]
    cities = ["Your Location"]
    
    # Get locations for IP addresses
    print("🌍 Getting location data for IP addresses...")
    if args.parallel:
        location_data = get_locations_parallel(ip_addresses, max_workers)
    else:
        location_data = {}
        for ip in ip_addresses:
            location_data[ip] = get_ip_location(ip, rate_limit_delay)
    
    # Process results
    print("\n📍 Location data:")
    for ip in ip_addresses:
        data = location_data.get(ip)
        if data and data.get('status') == 'success':
            city = data.get('city', 'Unknown')
            region = data.get('regionName', '')
            country = data.get('country', '')
            lat = data.get('lat')
            lon = data.get('lon')
            
            print(f"{ip:>25}     {city}, {region}, {country}")
            latitudes.append(lat)
            longitudes.append(lon)
            cities.append(city)
        else:
            print(f"{ip:>25}     Home router (private)")
    
    # Create summary
    if cities:
        print(f"\n🎉 Congrats! Your internet connection made it all the way to {cities[-1]}")
        print(f"📊 Total IPs visited: {len(ip_addresses)}")
        print(f"🌍 Total cities visited: {len(set(cities))}")
    
    # Create enhanced map
    print(f"\n🗺️  Creating interactive map...")
    m = create_enhanced_map(latitudes, longitudes, cities, ip_addresses)
    if m:
        m.save(output_file)
        print(f"✅ Map saved to: {output_file}")
        
        # Export in additional formats if requested
        if args.export_format != 'html':
            export_results(latitudes, longitudes, cities, ip_addresses, 
                          args.export_format, output_file)
    
    print(f"\n🚀 Analysis complete! Open {output_file} in your browser to view the map.")

if __name__ == '__main__':
    main()
    



