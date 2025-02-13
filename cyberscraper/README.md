# CyberScraper 🤖

Advanced web scraping system with Tor network integration and proxy rotation capabilities.

## 🌐 Features

- Tor network integration for anonymous scraping
- Automatic proxy rotation system
- Anti-detection mechanisms


## 🛠 Setup & Installation

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/Samer-Gassouma/AI-ODYSSEY-HACATHON.git
cd cyberscraper
```

2. Build and run using Docker:
```bash
docker-compose build
docker-compose up
```

## 🔧 Configuration

### Tor Configuration

The system uses Tor with the following configuration:
- SOCKS Port: 9050
- Control Port: 9051
- Password: cyberneticAccess101

Default torrc settings:
```plaintext
SOCKSPort 9050
ControlPort 9051
HashedControlPassword 16:81F9DDCEDC62F114603303CA8B639533CD97143821196E2F8D48054E47
```



## 🚀 Usage

### Basic Scraping Request

```bash
curl -X POST http://localhost:5000/infiltrate \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com", "use_tor": true}'
```

### Response Format

```json
{
    "url": "https://example.com",
    "title": "Page Title",
    "text_content": "Extracted text...",
    "links": ["https://link1.com", "https://link2.com"],
    "headers": ["Header 1", "Header 2"],
    "meta_tags": {
        "description": "Page description",
        "keywords": "key, words"
    }
}
```

## 🛡️ Security Features

- Random User-Agent rotation
- Header randomization
- Proxy validation and rotation
- Tor circuit renewal
- Request timing randomization
