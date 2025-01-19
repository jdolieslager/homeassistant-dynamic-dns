# Dynamic DNS for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A Dynamic DNS integration for Home Assistant that supports multiple DNS providers:

- DuckDNS
- No-IP
- DNSimple

## Installation

### HACS (Recommended)

1. Open HACS
2. Go to "Integrations"
3. Click the three dots menu in the top right
4. Select "Custom repositories"
5. Add `https://github.com/jdolieslager/homeassistant-dynamic-dns`
6. Select "Integration" as category
7. Click "Add"
8. Find and install "Dynamic DNS" in HACS
9. Restart Home Assistant

### Manual

1. Copy the `custom_components/dynamic_dns` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings -> Devices & Services
2. Click "Add Integration"
3. Search for "Dynamic DNS"
4. Follow the configuration steps

## Supported Providers

### DuckDNS
- Requires: Domain and Token
- Updates your DuckDNS subdomain

### No-IP
- Requires: Username, Password, and Hostname
- Updates your No-IP hostname

### DNSimple
- Requires: Account ID, Token, Zone, and Record Name
- Updates DNS records in your DNSimple zones

## Options

- Update Interval: How often to check and update DNS records (minimum 60 seconds)

## Services

### Diagnostics
- Service: `dynamic_dns.diagnostics`
- Shows diagnostic information for all Dynamic DNS entries

## Development

### Prerequisites

- Docker (for containerized testing)
- Make (optional, for using Makefile commands)
- Python 3.11 or higher (for local development)

### Testing

Using Docker (recommended):
```bash
make test-docker
```

Local testing:
```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run tests
make test
```

### Linting
```bash
make lint
```

### Cleanup
```bash
make clean
```

### HACS Validation
```bash
make validate
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

[releases-shield]: https://img.shields.io/github/release/jdolieslager/homeassistant-dynamic-dns.svg
[releases]: https://github.com/jdolieslager/homeassistant-dynamic-dns/releases
[license-shield]: https://img.shields.io/github/license/jdolieslager/homeassistant-dynamic-dns.svg 