# PDF Data Extraction System

Production-ready system for extracting structured data from earnings call PDFs (Cipla, Lupin, and other companies).

## 🚀 Features

- **Multi-company support**: Cipla, Lupin, and others
- **Batch processing**: Handle multiple PDFs automatically
- **Structured extraction**: Management team, Q&A segments, financial metrics
- **Production-ready**: Logging, error handling, progress tracking
- **JSON output**: Clean, structured data format

## 📁 Project Structure

```
pdf-extraction-project/
├── app.py                          # Main application
├── earnings_extractor.py           # Core extraction logic
├── requirements.txt                # Dependencies
├── README.md                       # This file
├── .gitignore                      # Git ignore patterns
│
├── data/                           # Input PDFs
│   ├── cipla/                      # Cipla PDF files
│   ├── lupin/                      # Lupin PDF files
│   └── others/                     # Other company PDFs
│
├── output/                         # Extracted JSON files
├── logs/                           # Processing logs
```

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add PDF Files
- Put Cipla PDFs in `data/cipla/` folder
- Put Lupin PDFs in `data/lupin/` folder  
- Put other company PDFs in `data/others/` folder

### 3. Run Extraction
```bash
python app.py
```

## 📊 Output Format

The system generates JSON files with this structure:

```json
{
  "company": "CIPLA",
  "report_date": "July 25, 2025",
  "quarter": "Q1",
  "fiscal_year": "2026",
  "management_team": [
    "MR. UMANG VOHRA – GLOBAL MD & CEO",
    "MR. ASHISH ADUKIA – GLOBAL CFO"
  ],
  "analysts": [
    {"name": "Kunal Dhamesha", "firm": "Macquarie"}
  ],
  "qa_segments": [
    {
      "analyst_name": "Kunal Dhamesha",
      "question": "How is the pricing pressure in America?",
      "answers": [
        {
          "speaker": "Vinita Gupta",
          "response": "Pricing pressure has come down to high single digit..."
        }
      ]
    }
  ],
  "key_financial_metrics": {
    "revenue_inr_crores": "6957",
    "ebitda_margin_percentage": "25.6"
  }
}
```

## 🔧 Customization

### Adding New Companies
1. Add company folder in `data/` 
2. Update company patterns in `earnings_extractor.py`
3. Add company-specific extraction rules if needed

### Improving Extraction
- Modify regex patterns in `earnings_extractor.py`
- Add new financial metric patterns
- Enhance Q&A parsing logic

## 📈 Features

- ✅ Multi-PDF batch processing
- ✅ Progress bars and logging
- ✅ Error handling and recovery
- ✅ Detailed extraction reports
- ✅ Company-specific processing
- ✅ Structured JSON output
- ✅ Production-ready code

## 🐛 Troubleshooting

### Common Issues
1. **No PDFs found**: Check that PDFs are in correct folders
2. **Extraction errors**: Check logs/ folder for detailed error messages
3. **Missing data**: Review and adjust regex patterns in extractor
4. **Import errors**: Ensure all dependencies are installed

### Getting Help
- Check the logs/ folder for detailed processing information
- Review the extraction summary report in output/
- Examine the extracted JSON files for data quality

## 📝 License

This project is for internal use. Modify as needed for your requirements.