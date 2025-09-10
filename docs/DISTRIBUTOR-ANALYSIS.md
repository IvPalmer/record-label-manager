# Distribution Data Analysis & Re-modeling Plan

## Current Issues
- Two different distributors with different file formats
- Mixed data in single `RevenueEvent` table causing NULL values
- Need proper aggregation and column mapping

## File Format Analysis

### ZEBRALUTION (2021-2022)
**Files**: 2021-Q3 through 2022-Q3
**Delimiter**: Semicolon (;)
**Number Format**: European (1,234 = decimal)
**Encoding**: May need detection

**Key Columns**:
- Artist (Track Artist)
- Title (Track Title) 
- ISRC
- Provider (Zebralution)
- Shop (Spotify, AppleMusic, etc.)
- Sales (Stream count)
- Revenue-EUR (Gross)
- Rev.less Publ.EUR (Net to label)

**Sample Row**:
```
"Dos Kanye feat. Shaman Shaman";"Contraa";DEBE72100448;TTR069;Zebralution;AppleMusic;1;0,001184526;0,001184526
```

### LABELWORX (2023-2025) 
**Files**: 2022-Q4 through 2025-Q2  
**Delimiter**: Comma (,)
**Number Format**: English (1.234 = decimal)
**File Suffix**: __converted.csv

**Key Columns**:
- Track Artist
- Track Title
- ISRC
- Catalog (TTR number)
- Store Name (Spotify, Apple Music, etc.)
- Qty (Stream count)
- Value (Gross)
- Royalty (Net to label)

**Sample Row**:
```
BirdZzie,En Tu Puerta Estamos Cuatro,1.1876462759535,QZNRS2038186,SoundCloud
```

## Proposed Re-modeling

### 1. Separate Source Tables

#### `ZebralutionRevenue`
```sql
- period (text)
- artist_name (text)
- track_title (text) 
- isrc (text)
- label_order_nr (text)
- shop (text)          -- AppleMusic, Spotify, etc.
- sales (integer)      -- Stream count
- revenue_eur (decimal)
- revenue_net_eur (decimal)
- row_hash (unique)
```

#### `LabelworxRevenue`  
```sql
- catalog_number (text)
- track_artist (text)
- track_title (text)
- isrc (text)
- store_name (text)    -- Apple Music, Spotify, etc.
- qty (integer)        -- Stream count  
- value (decimal)      -- Gross
- royalty (decimal)    -- Net to label
- row_hash (unique)
```

#### `BandcampRevenue`
```sql
- transaction_date (datetime)
- artist_name (text)
- item_name (text)
- item_type (text)     -- album, track
- quantity (integer)   -- Downloads
- amount_received (decimal)
- currency (text)
- buyer_country (text)
- row_hash (unique)
```

### 2. Unified Analytics View
```sql
CREATE VIEW consolidated_analytics AS
SELECT 
    'Zebralution' as vendor,
    artist_name as track_artist,
    track_title,
    isrc,
    '' as catalog_number,
    shop as platform,
    sales as streams,
    0 as downloads,
    revenue_net_eur as revenue,
    EXTRACT(year FROM period::date) as year,
    EXTRACT(quarter FROM period::date) as quarter
FROM ZebralutionRevenue

UNION ALL

SELECT
    'Labelworx' as vendor,
    track_artist,
    track_title, 
    isrc,
    catalog_number,
    store_name as platform,
    qty as streams,
    0 as downloads, 
    royalty as revenue,
    -- Parse year/quarter from file path or use default
    2024 as year, 1 as quarter  
FROM LabelworxRevenue

UNION ALL

SELECT
    'Bandcamp' as vendor,
    artist_name as track_artist,
    item_name as track_title,
    '' as isrc,
    '' as catalog_number,
    'Bandcamp' as platform,
    0 as streams,
    quantity as downloads,
    amount_received as revenue,
    EXTRACT(year FROM transaction_date) as year,
    EXTRACT(quarter FROM transaction_date) as quarter
FROM BandcampRevenue;
```

## Next Steps

1. **Create separate import commands** for each distributor
2. **Handle number format conversion** (comma vs dot)
3. **Map columns correctly** between formats
4. **Create unified analytics view** for dashboard
5. **Test data quality** and aggregation accuracy

## Benefits
- **Clean separation** by data source
- **No more NULL values** 
- **Proper column mapping** for each format
- **Easier maintenance** and debugging
- **Accurate aggregations** per distributor type
