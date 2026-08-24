# Home Buying RAG Retrieval Evaluation

**Generated:** 2026-08-24T05:36:40.915810+00:00

## Executive summary

This evaluation measures whether the retriever surfaces the manually identified authoritative source for 15 representative home-buying questions. Judgments are source-level and binary; they do not grade answer style or factual completeness.

| Metric | Score |
| --- | ---: |
| Hit@1 | 66.7% (10/15) |
| Hit@3 | 93.3% (14/15) |
| Hit@5 | 100.0% (15/15) |
| Mean reciprocal rank | 0.806 |
| Mean expected-source recall@5 | 93.3% |
| Mean top reranker score | 0.820 |

### Interpretation

- **Hit@K**: percentage of questions with at least one expected source in the first K unique sources.
- **MRR**: rewards placing the first expected source near rank 1; 1.0 is perfect.
- **Expected-source recall@5**: fraction of all manually expected sources recovered in the top five.
- **Reranker score**: model-provided relevance signal; it is useful for comparisons but is not a calibrated probability.

## Question-level results

| ID | Category | Expected source | First relevant rank | Hit@5 | Recall@5 | Top score |
| --- | --- | --- | ---: | :---: | ---: | ---: |
| Q01 | Closing costs | `cfpb_home_loan_toolkit.pdf`<br>`cfpb_closing_disclosure_sample.pdf` | 2 | Yes | 50.0% | 0.743 |
| Q02 | Adjustable-rate mortgages | `cfpb_arm_charm_booklet.pdf` | 1 | Yes | 100.0% | 0.957 |
| Q03 | Loan estimates | `cfpb_loan_estimate_sample.pdf`<br>`cfpb_home_loan_toolkit.pdf` | 1 | Yes | 50.0% | 0.971 |
| Q04 | California disclosures | `ca_civil_code_1102_disclosure_law.html`<br>`ca_dre_refbook_disclosures.pdf` | 1 | Yes | 100.0% | 0.866 |
| Q05 | Texas disclosures | `trec_sellers_disclosure_notice.pdf` | 1 | Yes | 100.0% | 0.932 |
| Q06 | Homeowners associations | `trec_hoa_addendum.pdf` | 4 | Yes | 100.0% | 0.322 |
| Q07 | Home inspections | `ashi_home_inspection_standards.pdf` | 2 | Yes | 100.0% | 0.986 |
| Q08 | Federal income taxes | `irs_pub530_homeowners_tax.pdf` | 1 | Yes | 100.0% | 0.757 |
| Q09 | Appraisals | `fannie_mae_appraisal_report_1004.pdf` | 2 | Yes | 100.0% | 0.670 |
| Q10 | Homeowners insurance | `naic_homeowners_insurance_guide.pdf` | 1 | Yes | 100.0% | 0.711 |
| Q11 | Fair housing | `hud_fair_housing_booklet.pdf` | 3 | Yes | 100.0% | 0.932 |
| Q12 | Contractors | `ftc_hiring_a_contractor.pdf` | 1 | Yes | 100.0% | 0.713 |
| Q13 | VA loans | `va_home_loan_buyers_guide.pdf` | 1 | Yes | 100.0% | 0.869 |
| Q14 | USDA loans | `usda_rural_housing_loan_guide.pdf` | 1 | Yes | 100.0% | 0.866 |
| Q15 | California down payment help | `calhfa_downpayment_assistance.html` | 1 | Yes | 100.0% | 0.999 |

## Failure analysis

### Expected source retrieved but not ranked first

- **Q01 — Closing costs** Expected source first appeared at rank 2; rank 1 was `va_home_loan_buyers_guide.pdf`.
- **Q06 — Homeowners associations** Expected source first appeared at rank 4; rank 1 was `trec_new_home_contract_incomplete.pdf`.
- **Q07 — Home inspections** Expected source first appeared at rank 2; rank 1 was `va_home_loan_buyers_guide.pdf`.
- **Q09 — Appraisals** Expected source first appeared at rank 2; rank 1 was `va_home_loan_buyers_guide.pdf`.
- **Q11 — Fair housing** Expected source first appeared at rank 3; rank 1 was `cfpb_home_loan_toolkit.pdf`.

### Partial recovery for multi-source questions

- **Q01 — Closing costs** Missing expected source(s): `cfpb_closing_disclosure_sample.pdf`.
- **Q03 — Loan estimates** Missing expected source(s): `cfpb_loan_estimate_sample.pdf`.

### Cross-cutting risks

- Source-level relevance does not guarantee that the retrieved chunk contains every fact needed for a complete answer.
- Forms and sample disclosures can retrieve visually repetitive or boilerplate chunks rather than the field that answers the question.
- Jurisdiction terms are essential. Omitting California or Texas may blend state-specific sources.
- The live namespace may contain stale vectors from earlier ingestions unless it is cleared before rebuilding.
- Reranker scores vary by query and should not be treated as confidence probabilities without calibration.

## Recommendations

1. Preserve the clean rebuild procedure for `recursive-v1` so obsolete chunk IDs do not accumulate.
2. Add title, publisher, jurisdiction, category, and source URL metadata during ingestion.
3. Apply jurisdiction-aware metadata filters or query routing for state-specific questions.
4. Add chunk-level relevance judgments for misses and ambiguous form-based questions.
5. Run this suite after every corpus, chunking, embedding, or reranker change and track metric deltas.
6. Add adversarial questions for unsupported jurisdictions and verify the assistant abstains.

## Per-question retrieved sources

### Q01 — What costs and fees should a buyer expect to see at closing?

1. `va_home_loan_buyers_guide.pdf` — page 12.0, score 0.743
2. `cfpb_home_loan_toolkit.pdf` — page 21.0, score 0.593
3. `irs_pub530_homeowners_tax.pdf` — page 14.0, score 0.590
4. `trec_condo_resale_contract.pdf` — page 4.0, score 0.563
5. `hud_home_buying_guide.pdf` — page 6.0, score 0.377

### Q02 — How can the interest rate and monthly payment change on an adjustable-rate mortgage?

1. `cfpb_arm_charm_booklet.pdf` — page 1.0, score 0.957
2. `hud_home_buying_guide.pdf` — page 5.0, score 0.903
3. `ca_dre_refbook_financing.pdf` — page 6.0, score 0.615

### Q03 — How should I use a Loan Estimate to compare mortgage offers from different lenders?

1. `cfpb_home_loan_toolkit.pdf` — page 11.0, score 0.971
2. `cfpb_arm_charm_booklet.pdf` — page 1.0, score 0.897

### Q04 — What defects and conditions must a California home seller disclose to a buyer?

1. `ca_dre_refbook_disclosures.pdf` — page 17.0, score 0.866
2. `ca_civil_code_1102_disclosure_law.html` — page unknown, score 0.750
3. `ca_dre_refbook_agency.pdf` — page 39.0, score 0.741
4. `trec_purchase_contract.pdf` — page 3.0, score 0.341

### Q05 — What information is included in a Texas seller's disclosure notice?

1. `trec_sellers_disclosure_notice.pdf` — page 0.0, score 0.932
2. `trec_purchase_contract.pdf` — page 3.0, score 0.839
3. `trec_condo_resale_contract.pdf` — page 3.0, score 0.796
4. `trec_new_home_contract_completed.pdf` — page 3.0, score 0.329

### Q06 — What HOA documents, fees, and restrictions should a Texas buyer review?

1. `trec_new_home_contract_incomplete.pdf` — page 4, score 0.322
2. `trec_purchase_contract.pdf` — page 4.0, score 0.286
3. `trec_new_home_contract_completed.pdf` — page 4.0, score 0.219
4. `trec_hoa_addendum.pdf` — page 0.0, score 0.127
5. `trec_condo_resale_contract.pdf` — page 5.0, score 0.125

### Q07 — What systems and components should a standard home inspection cover?

1. `va_home_loan_buyers_guide.pdf` — page 25.0, score 0.986
2. `ashi_home_inspection_standards.pdf` — page 8.0, score 0.972

### Q08 — Which homeownership expenses may be deductible on my federal income tax return?

1. `irs_pub530_homeowners_tax.pdf` — page 2.0, score 0.757
2. `cfpb_closing_disclosure_sample.pdf` — page 12.0, score 0.052

### Q09 — What property details and comparable sales are documented in a residential appraisal report?

1. `va_home_loan_buyers_guide.pdf` — page 24.0, score 0.670
2. `fannie_mae_appraisal_report_1004.pdf` — page 0.0, score 0.390
3. `tx_property_tax_basics.pdf` — page 10.0, score 0.246
4. `ca_dre_refbook_financing.pdf` — page 103, score 0.217

### Q10 — What should I compare when choosing a homeowners insurance policy?

1. `naic_homeowners_insurance_guide.pdf` — page 13.0, score 0.711
2. `cfpb_home_loan_toolkit.pdf` — page 18.0, score 0.215

### Q11 — What kinds of discrimination are prohibited when buying or financing a home?

1. `cfpb_home_loan_toolkit.pdf` — page 16.0, score 0.932
2. `ca_dre_refbook_financing.pdf` — page 77.0, score 0.796
3. `hud_fair_housing_booklet.pdf` — page 4.0, score 0.683
4. `ca_dre_refbook_agency.pdf` — page 33.0, score 0.668

### Q12 — What should I verify before hiring a contractor for repairs or renovations?

1. `ftc_hiring_a_contractor.pdf` — page 2.0, score 0.713
2. `ca_civil_code_1102_disclosure_law.html` — page unknown, score 0.046
3. `va_home_loan_buyers_guide.pdf` — page 16.0, score 0.030

### Q13 — What are the main eligibility, funding fee, and occupancy considerations for a VA home loan?

1. `va_home_loan_buyers_guide.pdf` — page 6.0, score 0.869

### Q14 — Who may qualify for a USDA rural housing loan and what properties are eligible?

1. `usda_rural_housing_loan_guide.pdf` — page 1.0, score 0.866

### Q15 — What down payment assistance options does CalHFA offer California home buyers?

1. `calhfa_downpayment_assistance.html` — page unknown, score 0.999
2. `ca_dre_refbook_financing.pdf` — page 171.0, score 0.924
