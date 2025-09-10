# 🎵 Record Label Manager - Quick Start

## One-Command Launch 🚀

```bash
./start.sh
```

That's it! This single command will:

- ✅ Start the Django backend server (port 8000)
- ✅ Start the React frontend server (port 5173) 
- ✅ Open both applications in your browser
- ✅ Display live server logs

## What Opens Automatically

### 🔧 Django Admin Interface
- **URL**: http://127.0.0.1:8000/admin/
- **Login**: `admin` / `admin`
- **Features**: 
  - Browse 272K+ financial records
  - Export revenue data to CSV
  - Manage payout runs
  - View platform analytics

### 🎨 Frontend Application  
- **URL**: http://127.0.0.1:5173/
- **Features**:
  - Artist management
  - Release tracking
  - Calendar views
  - Demo submissions

## Finance Module Ready! 💰

Your finance system is loaded with:
- **€215,479** total revenue processed
- **272,701** transaction records 
- **2024 Performance**: €67,541 revenue
- **Q4 2024 Payout**: €8,121.76 ready for artists

## Quick Finance Commands

```bash
# Open backend terminal
cd backend && source venv/bin/activate

# Preview Q4 2024 payout
python manage.py finances_payout --label "Tropical Twista Records" --period "2024-Q4" --preview

# Create actual payout run  
python manage.py finances_payout --label "Tropical Twista Records" --period "2024-Q4"

# Import new financial data
python manage.py finances_ingest --label "Tropical Twista Records"
python manage.py finances_normalize --label "Tropical Twista Records"
```

## Stop Everything

Press **Ctrl+C** in the terminal running `start.sh` - it will automatically stop both servers.

## Troubleshooting

- **Backend issues**: Check `logs/backend.log`
- **Frontend issues**: Check `logs/frontend.log`  
- **Port conflicts**: The script will show alternative URLs
- **Missing dependencies**: Follow the setup instructions shown

---

## 🎉 You're Ready for Year-End Payouts!

The system contains your complete financial history and is ready to calculate and export artist payments for 2024.
