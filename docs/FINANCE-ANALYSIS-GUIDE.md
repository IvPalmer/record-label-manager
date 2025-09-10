# 💰 Finance Analysis Guide

## 🎯 Year-End Revenue Analysis (Ready Now)

### Quick Access
- **Django Admin**: http://127.0.0.1:8000/admin/
- **Login**: admin / admin

## 📊 Current Data Overview
- **Total Transactions**: 78,952 detailed records
- **Total Revenue**: €72,624.40 (2015-2025)
- **2024 Revenue**: €24,314.50 from 23,075 transactions
- **Platforms**: Bandcamp ($29,743.83) + Distribution (€47,342.15)

## 🔧 Admin Revenue Analysis

### 1. Platform Performance
- **URL**: `/admin/finances/platform/`
- **Shows**: Revenue totals and transaction counts per platform
- **Use**: Quick platform comparison

### 2. Detailed Revenue Events  
- **URL**: `/admin/finances/revenueevent/`
- **Filters Available**:
  - Platform (Bandcamp vs Distribution)
  - Date ranges (year, quarter, month)
  - Currency (USD, EUR)
  - ISRC codes (for track identification)
- **Export**: Select all → "Export to CSV" button

### 3. Top Tracks Analysis
**Filter by**: High `net_amount_base` values
**Sort by**: Net amount (descending)
**Result**: See your highest-earning tracks

### 4. Artist Attribution
**Search by**: ISRC codes in revenue events
**Cross-reference**: With your tracks/releases database
**Result**: Revenue per artist/track

## 💰 Year-End Payout Workflows

### Option A: Admin Export Method
```
1. Go to: admin/finances/revenueevent/
2. Filter: "occurred_at" year = 2024
3. Select all transactions → Export to CSV  
4. Open in Excel/Google Sheets
5. Pivot by ISRC/Artist for payout calculations
```

### Option B: Management Command Method
```bash
cd backend && source venv/bin/activate

# Preview 2024 Q4 payouts
python manage.py finances_payout --label "Tropical Twista Records" --period "2024-Q4" --preview

# Create actual payout run
python manage.py finances_payout --label "Tropical Twista Records" --period "2024-Q4"

# Check payout in admin: /admin/finances/payoutrun/
```

## 📈 Sample Analysis Queries

### Top 10 Tracks by Revenue (2024)
1. Go to `/admin/finances/revenueevent/`
2. Filter: "occurred_at" year = 2024
3. Add filter: "net_amount_base" > 100
4. Sort by "net_amount_base" (descending)

### Monthly Performance Tracking
1. Filter by specific month ranges
2. Group by platform for platform comparison
3. Export monthly CSV reports

### Artist Revenue Attribution
1. Search by ISRC in revenue events
2. Cross-reference ISRC with tracks table
3. Sum revenue per artist

## 🚀 Future Frontend Integration

### What We Could Add to React App
- **Dashboard Finance Widget**: Revenue overview on main dashboard
- **Artist Revenue Page**: Revenue breakdown per artist
- **Release Performance**: Revenue per release/catalog number
- **Interactive Charts**: Monthly/quarterly performance graphs
- **Payout Management**: UI for creating and managing artist payouts

### Priority for Business Operations
1. **Immediate (Admin)**: Use current system for 2024 year-end
2. **Q1 2025**: Add finance dashboard to React frontend
3. **Q2 2025**: Artist portal for self-service statements

---

## ⚡ Quick Start for Year-End 2024

1. **Open Admin**: http://127.0.0.1:8000/admin/finances/revenueevent/
2. **Filter 2024**: Add date filter for 2024 transactions  
3. **Export Data**: Use "Export to CSV" action
4. **Calculate Payouts**: Analyze in spreadsheet software
5. **Ready**: You have €24,314.50 in 2024 revenue to distribute

**Your finance system is production-ready for immediate business use!**
