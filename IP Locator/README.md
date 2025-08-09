# Enhanced Network Route Tracer and Visualizer

A powerful Python script that traces network routes to target websites and creates interactive maps with detailed location information.

## 🚀 Features

### Core Features
- **Network Route Tracing** - Trace the path your internet connection takes to reach target websites
- **Interactive Maps** - Create beautiful, interactive maps showing the route
- **Location Data** - Get detailed city, region, and country information for each hop
- **Multiple Export Formats** - Export results as HTML, JSON, or CSV

### Advanced Features
- **Command Line Interface** - Full CLI with arguments and options
- **Configuration Files** - Customizable settings via JSON config files
- **Parallel Processing** - Fast IP lookup using multiple threads
- **Rate Limiting** - Respectful API usage with configurable delays
- **Enhanced Error Handling** - Robust error handling and logging
- **Progress Indicators** - Visual feedback during processing
- **Enhanced Maps** - Color-coded markers, popups, tooltips, and legends

## 📦 Installation

### Prerequisites
- Python 3.7+
- `traceroute` command (usually pre-installed on macOS/Linux)

### Install Dependencies
```bash
pip install requests folium geocoder
```

## 🎯 Usage

### Basic Usage (One Click!)
```bash
# Trace route to Google (default) - just run this!
python3 geo.py

# Trace route to any website - now works with most targets!
python3 geo.py --target github.com
python3 geo.py --target amazon.com
python3 geo.py --target microsoft.com
python3 geo.py --target apple.com
python3 geo.py --target netflix.com

# Use custom timeout
python3 geo.py --target any-website.com --timeout 60
```

### Advanced Usage
```bash
# Use parallel processing for faster IP lookups
python3 geo.py --parallel

# Export results as JSON
python3 geo.py --export-format json

# Use custom configuration file
python3 geo.py --config my_config.json

# Enable verbose logging
python3 geo.py --verbose

# Custom output file
python3 geo.py --output my_route_map.html
```

### Command Line Options
```
--target, -t          Target website to trace (default: google.com)
--timeout             Timeout in seconds for traceroute (default: 30)
--output, -o          Output HTML file (default: coordinates_map.html)
--config, -c          Configuration file path
--export-format       Export format: html, json, csv (default: html)
--verbose, -v         Enable verbose logging
--parallel, -p        Use parallel processing for IP lookups
```

## 🎯 Supported Targets

The script now works with **most websites**, including:
- ✅ **google.com** - Fast and reliable
- ✅ **github.com** - Developer favorite
- ✅ **amazon.com** - E-commerce giant
- ✅ **microsoft.com** - Tech company
- ✅ **apple.com** - Apple services
- ✅ **netflix.com** - Streaming service
- ✅ **facebook.com** - Social media
- ✅ **twitter.com** - Social platform
- ✅ **Most other websites** - Just try it!

### Why Some Targets Might Still Fail
- **Corporate firewalls** blocking traceroute
- **CDN networks** with complex routing
- **Geographic restrictions** or network policies
- **Target websites** specifically blocking traceroute requests

## 📍 Location Accuracy

### Automatic Location Detection
The script automatically detects your location using multiple services for maximum accuracy:
1. **ipinfo.io** - Primary service (most accurate)
2. **geocoder.ip()** - Fallback service
3. **ipapi.co** - Additional fallback service

This ensures you get the most accurate location possible without any manual input required!

### Why Location Might Be Approximate
- IP geolocation points to your ISP's data center, not your exact location
- Your actual location might be several miles away from the detected location
- This is normal and expected for IP-based geolocation

## ⚙️ Configuration

Create a `config.json` file to customize settings:

```json
{
  "default_target": "google.com",
  "timeout": 30,
  "output_file": "coordinates_map.html",
  "rate_limit_delay": 0.1,
  "max_workers": 5,
  "api_endpoint": "http://ip-api.com/json/",
  "map_settings": {
    "zoom_start": 2,
    "tile_layer": "OpenStreetMap"
  }
}
```

## 🗺️ Map Features

### Interactive Elements
- **Color-coded markers**: Red (start), Blue (intermediate), Green (end)
- **Detailed popups**: Show hop number, IP address, city, and coordinates
- **Tooltips**: Hover information for each marker
- **Route line**: Blue dashed line showing approximate network path
- **Legend**: Color coding explanation

### Map Controls
- **Zoom**: Mouse wheel or zoom controls
- **Pan**: Click and drag to move around
- **Fullscreen**: Fullscreen button in top-right
- **Layer control**: Switch between different map layers

## 📊 Output Formats

### HTML (Default)
- Interactive map with all features
- Opens in any web browser
- Self-contained (no internet required to view)

### JSON
```json
{
  "route": [
    {
      "hop": 1,
      "ip": "192.168.0.1",
      "city": "Your Location",
      "latitude": 41.8781,
      "longitude": -87.6298
    }
  ],
  "summary": {
    "total_hops": 15,
    "total_cities": 8,
    "start_point": "Your Location",
    "end_point": "Mountain View"
  }
}
```

### CSV
```csv
Hop,IP,City,Latitude,Longitude
1,192.168.0.1,Your Location,41.8781,-87.6298
2,96.120.27.17,Boston,42.3601,-71.0589
```

## 🔧 Troubleshooting

### Common Issues

**"traceroute command not found"**
- Install traceroute: `brew install traceroute` (macOS) or `sudo apt install traceroute` (Linux)

**"ModuleNotFoundError"**
- Install missing packages: `pip install requests folium geocoder`

**Script stalls/hangs**
- Use `--timeout` to set a shorter timeout
- Try a different target website
- Check your internet connection

**Traceroute fails or times out**
- Some websites block traceroute requests
- Try alternative targets: `google.com`, `github.com`, `amazon.com`
- Increase timeout: `--timeout 60`
- Check if your network allows traceroute

**No location data**
- Some IPs are private or don't have location data
- Check if the IP geolocation API is accessible

### When Traceroute Fails

If you see an error like "Failed to trace route to target.com", try these solutions:

1. **Use a different target** (recommended):
   ```bash
   python3 geo.py --target google.com
   python3 geo.py --target github.com
   python3 geo.py --target amazon.com
   ```

2. **Increase timeout**:
   ```bash
   python3 geo.py --target target.com --timeout 60
   ```

3. **Check your network**:
   - Some corporate networks block traceroute
   - Try from a different network if possible

### Debug Mode
```bash
python3 geo.py --verbose
```

## 🎨 Customization

### Custom Map Styles
Modify the `create_enhanced_map` function to:
- Change marker colors and icons
- Add custom popup content
- Modify the route line style
- Add additional map layers

### Custom API Endpoints
Update the `get_ip_location` function to use different geolocation APIs:
- ip-api.com (current)
- ipinfo.io
- freegeoip.app
- Custom API

## 📈 Performance Tips

1. **Use parallel processing** for faster IP lookups: `--parallel`
2. **Adjust rate limiting** in config for your API limits
3. **Use shorter timeouts** for faster results
4. **Choose closer targets** for faster tracing

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests!

## 📄 License

This project is open source and available under the MIT License.
