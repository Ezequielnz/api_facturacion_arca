# AFIP Web Services API

A Python FastAPI application designed to interact with AFIP (Administración Federal de Ingresos Públicos) Web Services in an easy, reusable way. This API provides a simple interface to AFIP's electronic invoice services and other AFIP web services.

## Features

- Simplified interface to AFIP Web Services
- Authentication and authorization system
- Token management with automatic renewal
- Certificate management for AFIP authentication
- Electronic invoice generation and querying
- Support for multiple AFIP services (WSFE, etc.)
- Clean, scalable API structure

## Project Structure

```
app/
├── config/             # Configuration settings
├── dependencies/       # Shared dependencies
├── models/             # Database models and schemas
├── routes/             # API endpoints
├── services/           # Business logic and AFIP services
│   ├── certificados/   # AFIP certificates
│   └── tickets/        # Authentication tickets
├── static/             # Static assets (CSS, JS)
└── templates/          # HTML templates
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- AFIP certificates (for production use)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/api_facturacion_arca.git
   cd api_facturacion_arca
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Place your AFIP certificates in the `app/services/certificados/` directory:
   - `certificado.crt`: Your AFIP certificate
   - `MiClavePrivada.key`: Your private key

5. Start the development server:
   ```
   uvicorn app.main:app --reload
   ```

6. Visit `http://localhost:8000` in your browser to access the API.

## Environment Variables

- `ENVIRONMENT`: Set to `dev` for testing mode or `prod` for production
- `AFIP_CUIT`: Your CUIT number for AFIP authentication
- `SECRET_KEY`: Secret key for JWT token generation (change in production)

## API Documentation

When the application is running, visit `/docs` for automatic Swagger documentation or `/redoc` for ReDoc documentation.

### Main Endpoints

- `/api/afip/status`: Check AFIP server status
- `/api/afip/invoice/types`: Get available invoice types
- `/api/afip/invoice/last-number/{punto_venta}/{tipo_comprobante}`: Get last invoice number

## Using in Other Projects

To reuse this API in other projects:

1. Clone the repository or install as a dependency
2. Configure your AFIP certificates
3. Make API calls to the relevant endpoints

Example using Python requests:
```python
import requests

# Get AFIP server status
response = requests.get("http://localhost:8000/api/afip/status", 
                       headers={"Authorization": f"Bearer {token}"})
print(response.json())
```

## Development

### Adding New AFIP Services

1. Update `app/services/afip_client.py` with new service methods
2. Add new routes in `app/routes/afip.py`
3. Update schemas in `app/models/schemas.py` if necessary

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 