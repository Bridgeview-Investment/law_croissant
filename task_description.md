# Understanding the applicability of legal provisions and rules by identifying entity types: an implementation of RegGenome structured data

# About RegGenome

RegGenome, a University of Cambridge commercial spin-out, is a regulatory data technology company and a leader in the field of computational regulation. We are changing how the world produces and consumes regulatory information. As a regulatory data provider, we process the world’s regulation using AI to transform what is human-readable into machine-readable and machine-consumable data.

# RegGenome Challenge

## Background

The largest regulated financial services firms and their service providers sift through tens of thousands of regulatory notifications annually, at significant cost.

Each group knows that the majority of these notifications are bound to be irrelevant to most of their constituents’ operations but are also wary of missing relevant content. Many therefore use a (largely manual) triaging system to score the relevance of each document to business lines, functions and products. The result is a great deal of redundant work that ties down significant compliance generalist and occasionally specialist resources without always achieving commensurate reductions in risk.

Unfortunately, the granular elements of legal and regulatory text – clauses, sections, etc - typically do not name the types of entities to which each obligation applies, confounding simple NLP based classification. Some publishers are helpful enough to produce glossaries of defined terms within the texts themselves but in many cases the terms and their definitions are ultimately set out in upstream legislation or key rules and must be inferred onto downstream documents, including detailed rules or guidance.  Hierarchies of products, such as [ISO10962](https://www.iso.org/standard/81140.html) (see also [here](https://www.iotafinance.com/en/Classification-of-Financial-Instrument-codes-CFI-ISO-10962-2021.html)), the [Common Domain Model (CDM)](https://cdm.finos.org/docs/product-model/#product), the [ISDA taxonomy](https://www.isda.org/2019/09/04/isda-taxonomy-2-0-finalized/) or the [Financial Instrument Global Identifier (FIGI)](https://www.openfigi.com/about/overview) are very useful analytical tools but are designed and indeed largely reserved for manual application.

Finally, the perimeter of financial regulations is in many cases controversial or hard to define and clarifying the scope of regulated activities or the reach of regulators’ powers is frequently the object of legal advice.

## Challenge

Participants should demonstrate an efficient, technology-enabled method for recognising what types of firms, products, services, or activities each incoming rule or legal provision applies to and organise these into a simple hierarchical structure.

Participants will be provided with a set of RegGenome structured documents, complete with document and sub-document level metadata, as well as links to their origin URLs. They will be asked to derive from this dataset:

1. A table of regulated activities, entities or products discussed in those documents. To the extent possible this should be free of redundancy and repetition.
2. A prediction of which regulated activities, entities, or products each document is relevant to, at both document and sub-document level.
3. Stretch objective – for each of the regulated activities, entities or products identified in objective (1), a link to each of the documents in which they are formally defined and the full text of the definition in question.

## Challenge Collateral

### i. Data Access

All participants will receive access to the RegGenome API. The following describes the data attributes addressable through the API. RegGenome metadata include publishers’ names and hierarchical position, publication dates, document type classification, document-level thematic relevance scores, versioning indicators and sub-document level thematic tags indicating the type of regulatory obligation present in text. 

### ii. Curated Document Collections

RegGenome data include a Legislative Initiatives attribute indicating whether the document in question belongs to one of a pre-defined set of document ‘collections’ curated by RegGenome. The following Legislative Initiatives are in scope of this exercise

- US - Investment Advisers Act (1940) and US - Investment Company Act, 1940
- EU - UCITS Directives
- UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations, 2011 - 2016

### iii. Sample Hierarchies

The following can help participants visualise what outputs might look like – though participants should feel free to optimise

- Sample of a RegGenome taxonomy
- Sample of a controls structure (SCF)