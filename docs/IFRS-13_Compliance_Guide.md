# IFRS-13 Compliance Guide

This document describes how the Valuation Agent Workspace enforces IFRS-13 (Fair Value Measurement) compliance requirements.

## 📋 IFRS-13 Overview

IFRS-13 establishes a framework for measuring fair value and requires entities to:
1. **Determine fair value hierarchy levels** (Level 1, 2, 3)
2. **Select principal markets** for valuation
3. **Perform Day-1 P&L checks** against market quotes
4. **Document non-performance risk** considerations
5. **Provide comprehensive disclosures** for Level 3 valuations

## 🏗️ System Architecture

### Governance Module
The system includes a governance module (`backend/governance/`) that enforces:

- **Fair Value Hierarchy Determination**: Automatic classification based on data observability
- **Principal Market Selection**: Configurable market selection rules
- **Day-1 P&L Validation**: Automated checks against par quotes
- **Review Workflow**: Escalation for Level 3 valuations

### Data Observability Framework
```python
class DataObservability:
    LEVEL_1 = "Quoted prices in active markets"
    LEVEL_2 = "Observable inputs (similar instruments)"
    LEVEL_3 = "Unobservable inputs (models, proxies)"
    
    def classify_input(self, data_source, market_activity, observability):
        # Automatic hierarchy determination logic
        pass
```

## 🔍 Fair Value Hierarchy Enforcement

### Level 1 Classification
**Criteria**: Quoted prices in active markets
**System Implementation**:
- Direct market quotes from active exchanges
- Real-time pricing data
- High liquidity instruments
- **Automatic Classification**: System automatically identifies Level 1 inputs

**Examples**:
- Exchange-traded instruments
- Government bonds with active markets
- Currency rates from major exchanges

### Level 2 Classification
**Criteria**: Observable inputs from similar instruments
**System Implementation**:
- Market data from similar instruments
- Interpolated rates from observable curves
- Broker quotes for similar instruments
- **Automatic Classification**: System identifies Level 2 inputs based on observability tags

**Examples**:
- Interpolated rates from observable curves
- Similar instrument pricing
- Market-implied rates

### Level 3 Classification
**Criteria**: Unobservable inputs requiring models
**System Implementation**:
- Model-derived valuations
- Proxy data usage
- Unobservable market inputs
- **Manual Review Required**: System flags Level 3 inputs for review

**Examples**:
- Model-based valuations
- Proxy data for illiquid instruments
- Unobservable market parameters

## 🏪 Principal Market Selection

### Configurable Rules
The system supports configurable principal market selection:

```python
class PrincipalMarketConfig:
    def __init__(self):
        self.market_selection_rules = {
            "currency": "USD",  # Default reporting currency
            "jurisdiction": "US",  # Regulatory jurisdiction
            "liquidity_threshold": 0.1,  # Minimum liquidity requirement
            "volume_threshold": 1000000,  # Minimum volume requirement
        }
    
    def select_principal_market(self, available_markets):
        # Principal market selection logic
        pass
```

### Market Selection Criteria
1. **Liquidity**: Highest liquidity market
2. **Volume**: Highest trading volume
3. **Accessibility**: Most accessible to entity
4. **Regulatory**: Appropriate regulatory framework

## 💰 Day-1 P&L Validation

### Automated Checks
The system performs automated Day-1 P&L validation:

```python
class Day1PandLValidator:
    def __init__(self, tolerance=0.01):  # 1% tolerance
        self.tolerance = tolerance
    
    def validate_day1_pnl(self, model_pv, market_quote):
        """Validate Day-1 P&L against market quotes"""
        pnl_difference = abs(model_pv - market_quote) / market_quote
        
        if pnl_difference > self.tolerance:
            return {
                "status": "FAILED",
                "difference": pnl_difference,
                "requires_review": True
            }
        else:
            return {
                "status": "PASSED",
                "difference": pnl_difference,
                "requires_review": False
            }
```

### Validation Process
1. **Market Quote Retrieval**: Get current market quotes
2. **Model Valuation**: Calculate model-based fair value
3. **Difference Calculation**: Compare model vs market
4. **Tolerance Check**: Validate against acceptable tolerance
5. **Review Escalation**: Flag for review if outside tolerance

## 🚨 Review Workflow

### Automatic Escalation
The system automatically escalates runs requiring review:

```python
class ReviewWorkflow:
    def __init__(self):
        self.escalation_triggers = [
            "level_3_inputs",
            "proxy_data_usage",
            "day1_pnl_failure",
            "unobservable_inputs"
        ]
    
    def check_escalation_required(self, run_data):
        """Check if run requires review escalation"""
        for trigger in self.escalation_triggers:
            if self._check_trigger(trigger, run_data):
                return True
        return False
```

### Review Requirements
**Level 3 Valuations**:
- Detailed rationale for unobservable inputs
- Model validation documentation
- Sensitivity analysis results
- Independent review approval

**Proxy Data Usage**:
- Justification for proxy selection
- Similarity analysis
- Adjustment methodology
- Validation results

## 📊 Non-Performance Risk

### Credit Risk Considerations
The system incorporates non-performance risk through:

1. **Credit Curves**: Counterparty and own credit curves
2. **CVA/DVA Calculations**: Credit value adjustments
3. **Collateral Considerations**: CSA impact on valuations
4. **Recovery Rates**: Default recovery assumptions

### Implementation
```python
class NonPerformanceRisk:
    def __init__(self):
        self.credit_curves = {}
        self.recovery_rates = {}
        self.collateral_agreements = {}
    
    def calculate_credit_adjustment(self, exposure, credit_curve):
        """Calculate credit adjustment for non-performance risk"""
        pass
```

## 📋 Disclosure Requirements

### Level 3 Disclosures
The system automatically generates required disclosures:

1. **Valuation Techniques**: Methodology documentation
2. **Input Sensitivity**: Key assumption impacts
3. **Model Validation**: Backtesting and calibration
4. **Audit Trail**: Complete calculation lineage

### Disclosure Generation
```python
class DisclosureGenerator:
    def generate_level3_disclosures(self, run_data):
        """Generate required Level 3 disclosures"""
        disclosures = {
            "valuation_techniques": self._document_techniques(run_data),
            "input_sensitivity": self._calculate_sensitivity(run_data),
            "model_validation": self._document_validation(run_data),
            "audit_trail": self._generate_audit_trail(run_data)
        }
        return disclosures
```

## 🔧 System Configuration

### Governance Settings
```python
class GovernanceSettings:
    def __init__(self):
        self.ifrs13_config = {
            "hierarchy_determination": "automatic",
            "principal_market_selection": "configurable",
            "day1_pnl_tolerance": 0.01,
            "review_escalation": "automatic",
            "disclosure_generation": "automatic"
        }
```

### Data Observability Tags
The system uses data observability tags to automatically classify inputs:

```python
class DataObservabilityTags:
    LEVEL_1 = {
        "market_activity": "high",
        "observability": "direct",
        "liquidity": "high",
        "source": "exchange"
    }
    
    LEVEL_2 = {
        "market_activity": "medium",
        "observability": "indirect",
        "liquidity": "medium",
        "source": "interpolated"
    }
    
    LEVEL_3 = {
        "market_activity": "low",
        "observability": "unobservable",
        "liquidity": "low",
        "source": "model"
    }
```

## 📈 Monitoring and Reporting

### Compliance Dashboard
The system provides a compliance dashboard showing:

1. **Hierarchy Distribution**: Level 1/2/3 breakdown
2. **Review Status**: Pending reviews and approvals
3. **Day-1 P&L Results**: Validation outcomes
4. **Disclosure Completeness**: Required disclosures status

### Automated Reporting
```python
class ComplianceReporter:
    def generate_compliance_report(self, period):
        """Generate IFRS-13 compliance report"""
        report = {
            "hierarchy_summary": self._get_hierarchy_summary(period),
            "review_status": self._get_review_status(period),
            "day1_pnl_results": self._get_day1_pnl_results(period),
            "disclosure_status": self._get_disclosure_status(period)
        }
        return report
```

## 🚨 Error Handling

### Validation Failures
The system handles various validation failures:

1. **Data Quality Issues**: Missing or stale data
2. **Model Failures**: Calibration or validation failures
3. **Compliance Violations**: IFRS-13 requirements not met
4. **Review Escalation**: Manual review required

### Error Recovery
```python
class ErrorRecovery:
    def handle_validation_failure(self, error_type, run_data):
        """Handle validation failures and recovery"""
        if error_type == "data_quality":
            return self._request_data_refresh(run_data)
        elif error_type == "model_failure":
            return self._escalate_to_quant_team(run_data)
        elif error_type == "compliance_violation":
            return self._escalate_to_compliance_team(run_data)
```

## 📚 Best Practices

### Implementation Guidelines
1. **Regular Data Updates**: Ensure market data is current
2. **Model Validation**: Regular model validation and calibration
3. **Review Processes**: Timely review and approval workflows
4. **Documentation**: Complete documentation of assumptions and rationale

### Quality Assurance
1. **Automated Checks**: System performs automated compliance checks
2. **Manual Review**: Human review for complex cases
3. **Independent Validation**: Independent review for Level 3 valuations
4. **Audit Trail**: Complete audit trail for all decisions

## 🔍 Testing and Validation

### Compliance Testing
The system includes comprehensive compliance testing:

1. **Hierarchy Testing**: Verify correct hierarchy classification
2. **Market Selection Testing**: Validate principal market selection
3. **Day-1 P&L Testing**: Test Day-1 P&L validation logic
4. **Disclosure Testing**: Verify disclosure generation

### Test Scenarios
```python
class ComplianceTestScenarios:
    def test_level1_classification(self):
        """Test Level 1 input classification"""
        pass
    
    def test_level3_escalation(self):
        """Test Level 3 escalation workflow"""
        pass
    
    def test_day1_pnl_validation(self):
        """Test Day-1 P&L validation"""
        pass
    
    def test_disclosure_generation(self):
        """Test disclosure generation"""
        pass
```

## 📞 Support and Escalation

### Compliance Support
- **IFRS-13 Questions**: Accounting Team
- **Regulatory Issues**: Compliance Team
- **Model Validation**: Quant Team
- **System Issues**: IT Support Team

### Escalation Procedures
1. **Level 1**: System automated resolution
2. **Level 2**: Team lead review
3. **Level 3**: Management escalation
4. **Level 4**: Executive escalation

---

**Note**: This guide should be used in conjunction with internal policies and procedures. Always consult with appropriate subject matter experts for complex or unusual situations.

