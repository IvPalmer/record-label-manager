# Bandcamp API Integration

This document describes the new Bandcamp API integration that replaces CSV file imports for Bandcamp sales data.

## Overview

Previously, Bandcamp sales data was imported from CSV exports. This new integration fetches data directly from the Bandcamp API, providing more accurate and up-to-date sales information.

## Features

- **Direct API Integration**: Fetches data directly from Bandcamp's API
- **OAuth2 Authentication**: Secure authentication with automatic token refresh
- **Chunked Data Retrieval**: Fetches data in yearly chunks to avoid API rate limits
- **Duplicate Prevention**: Uses unique transaction IDs to prevent duplicate imports
- **Error Handling**: Robust error handling with detailed logging
- **Flexible Date Ranges**: Support for custom date ranges
- **Dry Run Mode**: Preview what would be imported without actually importing

## Setup

### 1. Bandcamp API Credentials

1. Go to [Bandcamp Developer Console](https://bandcamp.com/developer)
2. Create a new API application
3. Note down your `Client ID` and `Client Secret`

### 2. Environment Variables

Create a `.env` file in the project root with your credentials:

```bash
BANDCAMP_CLIENT_ID=your_client_id_here
BANDCAMP_CLIENT_SECRET=your_client_secret_here
```

### 3. Install Dependencies

The required dependencies are already included in `requirements.txt`:
- `requests` - for HTTP API calls
- `python-dotenv` - for environment variable management

## Usage

### Command Line Interface

The main command to fetch Bandcamp data is:

```bash
python manage.py fetch_bandcamp_api
```

#### Command Options

- `--start-date YYYY-MM-DD`: Start date for data fetch (default: 1 year ago)
- `--end-date YYYY-MM-DD`: End date for data fetch (default: today)
- `--band-id ID`: Specific band ID to fetch (default: fetch all bands)
- `--clear-existing`: Clear existing Bandcamp data before importing
- `--dry-run`: Preview what would be imported without actually importing
- `--label-name NAME`: Label name to associate with imported data (default: "Tropical Twista Records")

#### Examples

```bash
# Fetch last year's data
python manage.py fetch_bandcamp_api

# Fetch specific date range
python manage.py fetch_bandcamp_api --start-date 2024-01-01 --end-date 2024-12-31

# Clear existing data and import fresh
python manage.py fetch_bandcamp_api --clear-existing

# Preview what would be imported
python manage.py fetch_bandcamp_api --dry-run

# Fetch data for specific band
python manage.py fetch_bandcamp_api --band-id 12345
```

## API Service Architecture

### BandcampAPI Class

The main API service is located in `finances/services/bandcamp_api.py`:

- **Token Management**: Handles OAuth2 client credentials flow
- **Automatic Refresh**: Refreshes tokens when they expire
- **Caching**: Caches tokens in Django cache to avoid unnecessary API calls
- **Chunked Fetching**: Retrieves data in manageable chunks
- **Error Handling**: Comprehensive error handling with logging

### Key Methods

- `get_client_credentials()`: Obtain initial API credentials
- `refresh_access_token()`: Refresh expired access tokens
- `ensure_valid_access_token()`: Ensure we have a valid token
- `get_my_bands()`: Retrieve bands associated with account
- `get_sales_report()`: Fetch sales data for specified date range

## Data Structure

The API returns comprehensive sales data including:

- Transaction details (ID, date, amount)
- Item information (name, type, artist)
- Financial data (gross, net, fees, taxes)
- Buyer information (name, location)
- Shipping details (if applicable)
- Catalog information (ISRC, UPC, catalog number)

## Database Integration

### Models Updated

The existing `RevenueEvent` model handles both CSV and API data:

- `source_file`: References the API fetch operation
- `row_hash`: Uses API transaction ID for uniqueness
- All existing fields are populated from API data

### Data Source Tracking

- API fetches are tracked as `DataSource` with name "bandcamp_api"
- `SourceFile` records API calls with metadata
- Views distinguish between API and CSV data sources

## Frontend Integration

### Updated Views

The finance views have been enhanced to support API data:

- **Data Source Filter**: Filter by API vs CSV data
- **Source Metadata**: Display data source information
- **Enhanced Analytics**: Better analytics with API data quality

### New Endpoints

- `/api/finances/data-source-summary/`: Summary of API vs CSV data
- Enhanced filter options include data source filtering

## Migration from CSV

### Recommended Approach

1. **Backup Existing Data**: Backup your current database
2. **Test with Dry Run**: Use `--dry-run` to preview API data
3. **Gradual Migration**: Import API data alongside existing CSV data
4. **Comparison**: Compare API vs CSV data for accuracy
5. **Switch Over**: Once confident, use `--clear-existing` for clean import

### Comparison Command

```bash
# Import API data without clearing CSV data
python manage.py fetch_bandcamp_api

# Check data source summary in analytics
# Compare revenue totals and transaction counts
```

## Troubleshooting

### Common Issues

1. **Invalid Credentials**
   - Check your `BANDCAMP_CLIENT_ID` and `BANDCAMP_CLIENT_SECRET`
   - Verify credentials are active in Bandcamp Developer Console

2. **API Rate Limits**
   - The service automatically chunks requests to avoid rate limits
   - Consider smaller date ranges if issues persist

3. **Token Expiration**
   - Tokens are automatically refreshed
   - Check Django cache configuration if having issues

4. **Data Discrepancies**
   - API data may be more current than CSV exports
   - Check date ranges and currency conversions

### Logging

Enable detailed logging by setting Django's logging level:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'finances.services.bandcamp_api': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

## Development

### Testing

```bash
# Test API connection
python manage.py fetch_bandcamp_api --dry-run --start-date 2024-01-01 --end-date 2024-01-02

# Test with single band
python manage.py fetch_bandcamp_api --band-id YOUR_BAND_ID --dry-run
```

### Adding New Features

The API service is designed to be extensible:

- Add new endpoints in `BandcampAPI` class
- Extend data processing in the management command
- Update models if new data fields are needed

## Security

- API credentials are stored in environment variables
- Tokens are cached securely in Django's cache system
- No sensitive data is logged (tokens are not logged)
- HTTPS is used for all API communications

## Performance

- **Chunked Requests**: Large date ranges are split into yearly chunks
- **Caching**: API tokens are cached to reduce API calls
- **Batch Processing**: Database operations are batched for efficiency
- **Progress Reporting**: Real-time progress updates during import

## Support

For issues or questions:

1. Check the Django logs for detailed error messages
2. Use `--dry-run` to test without importing
3. Verify API credentials and permissions
4. Check Bandcamp API documentation for any changes
