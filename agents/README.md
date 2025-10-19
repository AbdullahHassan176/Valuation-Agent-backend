# Contract Parsing Agent

This module implements intelligent contract parsing for financial instruments using spaCy NLP and regex patterns.

## Features

- **PDF Text Extraction**: Supports multiple PDF parsing methods (pdfplumber, PyPDF2)
- **Field Extraction**: Extracts key financial instrument fields with confidence scores
- **Instrument Detection**: Automatically detects IRS vs CCS instruments
- **Validation**: Confidence-based validation with configurable thresholds
- **LangGraph Integration**: Ready for LangGraph workflow integration

## Supported Fields

### IRS (Interest Rate Swap) Fields
- `notional`: Notional amount in base currency
- `currency`: Currency code (USD, EUR, etc.)
- `fixed_rate`: Fixed interest rate percentage
- `floating_index`: Floating rate index (SOFR, LIBOR, etc.)
- `effective_date`: Contract start date
- `maturity_date`: Contract end date
- `frequency`: Payment frequency (quarterly, semi-annual, etc.)
- `day_count`: Day count convention (ACT/360, ACT/365, etc.)
- `business_day_convention`: Business day adjustment rule

### CCS (Cross Currency Swap) Fields
- All IRS fields plus:
- `ccy1`, `ccy2`: Currency pair
- `notional1`, `notional2`: Notional amounts in each currency
- `index1`, `index2`: Floating rate indices for each currency

## Usage

### Basic Usage

```python
from agents.contract_parser import ContractParser

parser = ContractParser()
extraction = parser.parse_contract(pdf_text)

print(f"Instrument: {extraction.instrument_type}")
print(f"Confidence: {extraction.overall_confidence}")
for field in extraction.fields:
    print(f"{field.field_name}: {field.value} (confidence: {field.confidence})")
```

### LangGraph Node

```python
from agents.contract_parser import parse_contract_node

result = parse_contract_node(pdf_text)
# Returns dict with fields, confidence, validation results
```

### API Endpoint

```bash
curl -X POST "http://localhost:8000/agents/parse_contract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf"
```

## Confidence Scoring

Each extracted field receives a confidence score (0.0 to 1.0) based on:

- **Pattern Match Quality**: Exact vs fuzzy matches
- **Context Length**: Longer matches get higher confidence
- **Field Validation**: Type-specific validation (dates, amounts, etc.)
- **Cross-Validation**: Consistency checks between related fields

### Confidence Thresholds

| Field | Threshold | Reason |
|-------|-----------|---------|
| notional | 0.7 | Critical for pricing |
| currency | 0.8 | Must be accurate |
| effective_date | 0.8 | Affects all calculations |
| maturity_date | 0.8 | Affects all calculations |
| fixed_rate | 0.6 | Important but can be validated |
| floating_index | 0.7 | Affects floating leg pricing |
| frequency | 0.6 | Can be inferred from context |
| day_count | 0.5 | Often standardized |
| business_day_convention | 0.5 | Often standardized |

## Validation

The parser performs several validation checks:

1. **Required Fields**: Ensures all critical fields are present
2. **Confidence Thresholds**: Blocks low-confidence extractions
3. **Data Type Validation**: Validates dates, numbers, currencies
4. **Consistency Checks**: Cross-validates related fields
5. **Overall Confidence**: Ensures minimum overall extraction quality

## Error Handling

- **PDF Validation**: Checks file format and readability
- **Text Extraction**: Fallback methods for difficult PDFs
- **Pattern Matching**: Graceful handling of unmatched patterns
- **Type Conversion**: Safe conversion with fallbacks

## Testing

Run the test script to verify functionality:

```bash
cd backend
python test_contract_parser.py
```

Create a test PDF:

```bash
python create_test_pdf.py
```

## Dependencies

- `spacy`: Natural language processing
- `PyPDF2`: PDF text extraction (fallback)
- `pdfplumber`: Advanced PDF text extraction
- `reportlab`: PDF generation for testing

## Configuration

Confidence thresholds and patterns can be customized in the `ContractParser` class:

```python
parser = ContractParser()
parser.confidence_thresholds["notional"] = 0.8  # Stricter threshold
parser.patterns["notional"].append(r"new_pattern")  # Add custom pattern
```

## Future Enhancements

- **Machine Learning**: Train custom models for better extraction
- **Template Recognition**: Detect common contract templates
- **Multi-language**: Support for non-English contracts
- **OCR Integration**: Handle scanned PDFs
- **Blockchain Integration**: Extract DeFi protocol parameters



