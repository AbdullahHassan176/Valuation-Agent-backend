# Valuation Documentation

This directory contains policy documents and methodology references for the valuation system.

## Document Structure

- **IRS_Valuation_Methodology.pdf** - Interest Rate Swap valuation procedures
- **XVA_Methodology.pdf** - Credit, Debit, and Funding Value Adjustment procedures  
- **Risk_Management_Policy.pdf** - Sensitivity analysis and risk management requirements
- **IFRS13_Compliance_Policy.pdf** - Fair value hierarchy and compliance requirements
- **Excel_Export_Policy.pdf** - Reporting and export requirements

## Usage

These documents are automatically loaded into the vector store for retrieval-augmented explanations. The system will search these documents to provide context-aware explanations for valuation runs.

## Adding New Documents

To add new policy documents:

1. Place PDF files in this directory
2. The system will automatically process and index them
3. Documents should follow the naming convention: `[Topic]_[Type].pdf`

## Document Metadata

Each document should include:
- Document name
- Section identifiers
- Paragraph identifiers
- Content type (methodology, policy, etc.)
- Version information

