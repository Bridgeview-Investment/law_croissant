
Search...
Overview
Authentication
Documents
Publishers
Domains
Sanctions
Controls and Actions
Interrogator
Initiatives
RegGenome Helios API Documentation (0.1.0)
Overview
The RegGenome Helios API allows you to access features and data available in the RegGenome content catalogue.

Authentication
Our REST API is organised into private authenticated endpoints which require requests to be signed. Contact us at product@reg-genome.com for access.

Documents
Get information about documents.

Get paginated documents
Returns paginated documents from the filter.

This will use a filter to fetch a limited set of documents with their attributes and text.

You can use to document_counts endpoint to get an idea of how many documents are available for those filters.

This may be a large amount of data, so recommend accepting gzip encoding.

Authorizations:
JWTBearer
query Parameters
page	
integer (Page) >= 1
Default: 1
page_size	
integer (Page Size)
Default: 100
Request Body schema: application/json
required
jurisdictions	
Array of Jurisdictions (strings) or Jurisdictions (null) (Jurisdictions)
Deprecated
This field is now deprecated and will be removed entirely in an upcoming release, please provide desired jurisdictions to the publishers field instead.

publisher_ids	
Array of Publisher Ids (strings) or Publisher Ids (null) (Publisher Ids)
Deprecated
This field is now deprecated and will be removed entirely in an upcoming release, please provide desired publisher_ids to the publishers field instead.

publishers	
Array of Publishers (objects) or Publishers (null) (Publishers)
If set filters documents to those with at least one publisher in any of the provided publishers or geographical groupings of publishers (jurisdictions)

sector	
SectorLevelsFilter (object) or null
Beta
If set filters documents to those within the specified categories.
If sector is provided at least one of the levels must be specified without an empty list [] or null.

Values within each level are combined with OR logic, while values between levels are combined with AND logic.
Providing:
level_1: ["mining and quarrying", "transportation and storage"], level_2: ["mining of metal ores", "air transport"]
Is equivalent to:
("mining and quarrying" | "transportation and storage") & ("mining of metal ores" | "air transport")

initiatives	
Array of Initiatives (integers) or Initiatives (null) (Initiatives)
If set filters documents to those within any of the specified initiatives.

authoritative	
Array of Authoritative (strings) or Authoritative (null) (Authoritative)
If set filters to documents that are authoritative for a specific domain. These documents have been identified as of substantial authority in the regulatory industry and may be included in control frameworks, legislative and regulatory initiatives, and other document structures that have considerable importance.

has_signposts	
Has Signposts (boolean) or Has Signposts (null) (Has Signposts)
If set filters documents to those with or without signposts.

required_tags	
Array of Required Tags (strings) or Required Tags (null) (Required Tags)
If set filters documents to those which have any or all of the specified tags.

require_all_tags	
Require All Tags (boolean) or Require All Tags (null) (Require All Tags)
If set to true filters documents having all of the specified required_tags. Otherwise, it filters documents having any of the specified required_tags

start_date	
Start Date (string) or Start Date (null) (Start Date)
If set filters documents to those published after (inc) specified date.

end_date	
End Date (string) or End Date (null) (End Date)
If set filters documents to those published before (inc) specified date.

doctypes	
Array of Doctypes (strings) or Doctypes (null) (Doctypes)
Beta
If set filters to documents having specified doctypes.

domains	
Domains (object) or Domains (null) (Domains)
If set filters documents to those with at least the threshold for at least 1 domain specified.

languages	
Languages (object) or Languages (null) (Languages)
If set filters documents to those with at least the threshold for at least 1 language specified.

min_title_length	
Min Title Length (integer) or Min Title Length (null) (Min Title Length)
If set filters to documents with titles of at least the length given.

title_regex	
Title Regex (string) or Title Regex (null) (Title Regex)
Deprecated
If set filters to documents with title matching regex (case-insensitive)

title	
(Title (Title (string) or Array of Title (strings))) or Title (null) (Title)
If set, filters to documents with matching titles.

Single string: Matches titles containing all words (AND logic), regardless of order.
List of strings: Matches titles containing any of the items (OR logic across list items).
To exclude words, prefix them with a hyphen (-).
To search for exact phrases, wrap them in double quotes (").
To search for any of the terms, separate them with OR.
last_updated_from	
Last Updated From (string) or Last Updated From (null) (Last Updated From)
If set filters to documents that have been updated after (inc) specified date.

last_updated_to	
Last Updated To (string) or Last Updated To (null) (Last Updated To)
If set filters to documents that have been updated before (inc) specified date.

publisher_rankings	
Array of Publisher Rankings (integers) or Publisher Rankings (null) (Publisher Rankings)
If set filters to documents that have at least 1 publisher matching any of the provided rankings

remove_near_duplicates	
boolean (Remove Near Duplicates)
Default: false
When true filters out documents that are extremely similar to others.

document_restriction	
Array of strings (Document Restriction)
Default: ["unrestricted","partially_restricted","restricted"]
Items Enum: "unrestricted" "partially_restricted" "restricted"
The restriction level of the document.

unrestricted: all metadata is available.
partially_restricted: document source text, translated text, and signpost inference text are not available.
restricted: no metadata is available.

⚠️ Due to publisher guidelines some metadata is not available for some documents.
Responses
200
Successful Response

403
Forbidden

422
Validation Error


post
/api/v1/customer/documents
Request samples
Payload
Content type
application/json

Copy
Expand allCollapse all
{
"jurisdictions": [
"GB"
],
"publisher_ids": [
"uk-bank-of-england"
],
"publishers": [
{},
{},
{}
],
"sector": {
"level_1": []
},
"initiatives": [
1,
2,
3
],
"authoritative": [
"aml",
"cap"
],
"has_signposts": true,
"required_tags": [
"aml-intlcooperation-tfs",
"aml-tfs-designation"
],
"require_all_tags": true,
"start_date": null,
"end_date": null,
"doctypes": [
"Laws"
],
"domains": {
"aml": 0.05
},
"languages": {
"en": 0.6
},
"min_title_length": 0,
"title_regex": null,
"title": "information on the payer",
"last_updated_from": "2024-01-01T14:00:00",
"last_updated_to": "2024-01-01T14:00:00",
"publisher_rankings": [
1,
8,
11
],
"remove_near_duplicates": false,
"document_restriction": [
"unrestricted",
"partially_restricted"
]
}
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
[
{
"document_id": "e5bb081b-9b63-5d0c-9479-0edcefbd256f",
"processed": "2024-05-10T17:35:27.452100Z",
"publishers": [],
"title": "2016 No. 662: The Proceeds of Crime Act 2002 (External Requests and Orders) (Amendment) Order 2016",
"published": "2024-05-20",
"source_text": [],
"translated_text_en": [],
"languages": {},
"doctype": "Laws",
"authoritative": [],
"initiatives": [],
"sector": {},
"reg_scores": {},
"signposts": [],
"source_urls": [],
"content_type": "application/pdf",
"crawled": "2024-05-10T17:35:27.452100Z",
"princeps": "e5bb081b-9b63-5d0c-9479-0edcefbd256f",
"version_cluster": "e5bb081b-9b63-5d0c-9479-0edcefbd256f",
"last_updated": "2024-01-01T09:00:00Z",
"output_version": 1,
"actionable_items": [],
"restriction": "unrestricted",
"copyright_notice": "Copyright © Bank of England 2024"
}
]
Get Document Metadata
Authorizations:
JWTBearer
path Parameters
document_id
required
string <uuid> (Document Id)
Examples: e5bb081b-9b63-5d0c-9479-0edcefbd256f 000884d4-2464-512c-9dcc-94009d461369 111cbb17-6b6b-5813-f42b-8042d3f63a26
The Regulatory Genome identifier for this regulatory document. A hash of the document.

Responses
200
Successful Response

403
Forbidden

404
Document ID does not exist

422
Validation Error


get
/api/v1/customer/documents/{document_id}
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
{
"document_id": "e5bb081b-9b63-5d0c-9479-0edcefbd256f",
"processed": "2024-05-10T17:35:27.452100Z",
"publishers": [
{}
],
"title": "2016 No. 662: The Proceeds of Crime Act 2002 (External Requests and Orders) (Amendment) Order 2016",
"published": "2024-05-20",
"source_text": [
{},
{}
],
"translated_text_en": [
{}
],
"languages": {
"en": 1
},
"doctype": "Laws",
"authoritative": [
"aml",
"cap"
],
"initiatives": [
{}
],
"sector": {
"level_1": "string",
"level_2": "string",
"level_3": "string",
"level_4": "string"
},
"reg_scores": {
"aml": {}
},
"signposts": [
{}
],
"source_urls": [
"https://www.legislation.gov.uk"
],
"content_type": "application/pdf",
"crawled": "2024-05-10T17:35:27.452100Z",
"princeps": "e5bb081b-9b63-5d0c-9479-0edcefbd256f",
"version_cluster": "e5bb081b-9b63-5d0c-9479-0edcefbd256f",
"last_updated": "2024-01-01T09:00:00Z",
"output_version": 1,
"actionable_items": [
{}
],
"restriction": "unrestricted",
"copyright_notice": "Copyright © Bank of England 2024"
}
Get Document
View document content.

Authorizations:
JWTBearer
path Parameters
document_id
required
string <uuid> (Document Id)
Examples: e5bb081b-9b63-5d0c-9479-0edcefbd256f 000884d4-2464-512c-9dcc-94009d461369 111cbb17-6b6b-5813-f42b-8042d3f63a26
The Regulatory Genome identifier for this regulatory document. A hash of the document.

Responses
307
S3 Presigned-url to access document. Expires in 5 minutes

403
Forbidden

404
Document ID does not exist

422
Validation Error


get
/api/v1/customer/documents/{document_id}/file
Response samples
403422
Content type
application/json

Copy
{
"detail": "User does not have permission to access the requested resource."
}
Count distinct documents
Return a count of distinct documents that match filters.

Multiple filters will be combined with AND operation.

Authorizations:
JWTBearer
Request Body schema: application/json
required
jurisdictions	
Array of Jurisdictions (strings) or Jurisdictions (null) (Jurisdictions)
Deprecated
This field is now deprecated and will be removed entirely in an upcoming release, please provide desired jurisdictions to the publishers field instead.

publisher_ids	
Array of Publisher Ids (strings) or Publisher Ids (null) (Publisher Ids)
Deprecated
This field is now deprecated and will be removed entirely in an upcoming release, please provide desired publisher_ids to the publishers field instead.

publishers	
Array of Publishers (objects) or Publishers (null) (Publishers)
If set filters documents to those with at least one publisher in any of the provided publishers or geographical groupings of publishers (jurisdictions)

sector	
SectorLevelsFilter (object) or null
Beta
If set filters documents to those within the specified categories.
If sector is provided at least one of the levels must be specified without an empty list [] or null.

Values within each level are combined with OR logic, while values between levels are combined with AND logic.
Providing:
level_1: ["mining and quarrying", "transportation and storage"], level_2: ["mining of metal ores", "air transport"]
Is equivalent to:
("mining and quarrying" | "transportation and storage") & ("mining of metal ores" | "air transport")

initiatives	
Array of Initiatives (integers) or Initiatives (null) (Initiatives)
If set filters documents to those within any of the specified initiatives.

authoritative	
Array of Authoritative (strings) or Authoritative (null) (Authoritative)
If set filters to documents that are authoritative for a specific domain. These documents have been identified as of substantial authority in the regulatory industry and may be included in control frameworks, legislative and regulatory initiatives, and other document structures that have considerable importance.

has_signposts	
Has Signposts (boolean) or Has Signposts (null) (Has Signposts)
If set filters documents to those with or without signposts.

required_tags	
Array of Required Tags (strings) or Required Tags (null) (Required Tags)
If set filters documents to those which have any or all of the specified tags.

require_all_tags	
Require All Tags (boolean) or Require All Tags (null) (Require All Tags)
If set to true filters documents having all of the specified required_tags. Otherwise, it filters documents having any of the specified required_tags

start_date	
Start Date (string) or Start Date (null) (Start Date)
If set filters documents to those published after (inc) specified date.

end_date	
End Date (string) or End Date (null) (End Date)
If set filters documents to those published before (inc) specified date.

doctypes	
Array of Doctypes (strings) or Doctypes (null) (Doctypes)
Beta
If set filters to documents having specified doctypes.

domains	
Domains (object) or Domains (null) (Domains)
If set filters documents to those with at least the threshold for at least 1 domain specified.

languages	
Languages (object) or Languages (null) (Languages)
If set filters documents to those with at least the threshold for at least 1 language specified.

min_title_length	
Min Title Length (integer) or Min Title Length (null) (Min Title Length)
If set filters to documents with titles of at least the length given.

title_regex	
Title Regex (string) or Title Regex (null) (Title Regex)
Deprecated
If set filters to documents with title matching regex (case-insensitive)

title	
(Title (Title (string) or Array of Title (strings))) or Title (null) (Title)
If set, filters to documents with matching titles.

Single string: Matches titles containing all words (AND logic), regardless of order.
List of strings: Matches titles containing any of the items (OR logic across list items).
To exclude words, prefix them with a hyphen (-).
To search for exact phrases, wrap them in double quotes (").
To search for any of the terms, separate them with OR.
last_updated_from	
Last Updated From (string) or Last Updated From (null) (Last Updated From)
If set filters to documents that have been updated after (inc) specified date.

last_updated_to	
Last Updated To (string) or Last Updated To (null) (Last Updated To)
If set filters to documents that have been updated before (inc) specified date.

publisher_rankings	
Array of Publisher Rankings (integers) or Publisher Rankings (null) (Publisher Rankings)
If set filters to documents that have at least 1 publisher matching any of the provided rankings

remove_near_duplicates	
boolean (Remove Near Duplicates)
Default: false
When true filters out documents that are extremely similar to others.

document_restriction	
Array of strings (Document Restriction)
Default: ["unrestricted","partially_restricted","restricted"]
Items Enum: "unrestricted" "partially_restricted" "restricted"
The restriction level of the document.

unrestricted: all metadata is available.
partially_restricted: document source text, translated text, and signpost inference text are not available.
restricted: no metadata is available.

⚠️ Due to publisher guidelines some metadata is not available for some documents.
Responses
200
Successful Response

403
Forbidden

422
Validation Error


post
/api/v1/customer/document_counts
Request samples
Payload
Content type
application/json

Copy
Expand allCollapse all
{
"jurisdictions": [
"GB"
],
"publisher_ids": [
"uk-bank-of-england"
],
"publishers": [
{},
{},
{}
],
"sector": {
"level_1": []
},
"initiatives": [
1,
2,
3
],
"authoritative": [
"aml",
"cap"
],
"has_signposts": true,
"required_tags": [
"aml-intlcooperation-tfs",
"aml-tfs-designation"
],
"require_all_tags": true,
"start_date": null,
"end_date": null,
"doctypes": [
"Laws"
],
"domains": {
"aml": 0.05
},
"languages": {
"en": 0.6
},
"min_title_length": 0,
"title_regex": null,
"title": "information on the payer",
"last_updated_from": "2024-01-01T14:00:00",
"last_updated_to": "2024-01-01T14:00:00",
"publisher_rankings": [
1,
8,
11
],
"remove_near_duplicates": false,
"document_restriction": [
"unrestricted",
"partially_restricted"
]
}
Response samples
200403422
Content type
application/json

Copy
{
"status": "ok",
"detail": "string",
"count": 0
}
List all available doctypes
Returns a list of all available doctypes.

Authorizations:
JWTBearer
Responses
200
Successful Response

403
Forbidden


get
/api/v1/customer/doctypes
Response samples
200403
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"doctypes": [
"Laws"
]
}
List all available sector categories
Returns a nested tree structure of the sector categories available at each level.

Authorizations:
JWTBearer
Responses
200
Successful Response

403
Forbidden


get
/api/v1/customer/sectors
Response samples
200403
Content type
application/json

Copy
Expand allCollapse all
{
"mining and quarrying": {
"mining of coal and lignite": {},
"mining of metal ores": {}
},
"transportation and storage": {
"air transport": {},
"water transport": {}
}
}
Publishers
Get information about publishers and jurisdictions.

List publisher IDs
Returns a list of unique publisher IDs filtered based on a specified parameter i.e. jurisdictions.

Authorizations:
JWTBearer
query Parameters
jurisdictions	
Array of Jurisdictions (strings) or Jurisdictions (null) (Jurisdictions)
If set filter to specified jurisdictions. List of ISO-3166-2 codes.

Responses
200
Successful Response

403
Forbidden

422
Validation Error


get
/api/v1/customer/publishers
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"publishers": [
"uk-bank-of-england"
]
}
List publisher rankings
Returns a dictionary of publisher rankings

Authorizations:
JWTBearer
Responses
200
Successful Response

403
Forbidden


get
/api/v1/customer/publishers/rankings
Response samples
200403
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"rankings": {
"1": "Global Governance Bodies",
"2": "International Standard Setting Bodies"
}
}
List all jurisdictions
Returns a list of all available jurisdictions as ISO-3166-2 codes.

Authorizations:
JWTBearer
Responses
200
Successful Response

403
Forbidden


get
/api/v1/customer/publishers/jurisdictions
Response samples
200403
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"jurisdictions": [
"EU"
]
}
Domains
Get information about domains.

List all available domains
Returns a list of all available domains.

Authorizations:
JWTBearer
Responses
200
Successful Response

403
Forbidden


get
/api/v1/customer/domains
Response samples
200403
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"domains": [
"string"
]
}
Sanctions
Get information about Sanctions.

Get Sanctions
Get list of available sanction files.

Authorizations:
JWTBearer
query Parameters
jurisdictions	
Array of Jurisdictions (strings) or Jurisdictions (null) (Jurisdictions)
If set filter to specified jurisdictions. List of ISO-3166-2 codes.

latest_only	
boolean (Latest Only)
Default: true
When true will only return the latest santion file from each source.

Responses
200
Successful Response

403
Forbidden

422
Validation Error


get
/api/v1/customer/sanctions/
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"sanctions": [
{}
]
}
Get Sanction
Get sanction metadata by id.

Authorizations:
JWTBearer
path Parameters
sanction_id
required
string <uuid> (Sanction Id)
Examples: e5bb081b-9b63-5d0c-9479-0edcefbd256f 000884d4-2464-512c-9dcc-94009d461369 111cbb17-6b6b-5813-f42b-8042d3f63a26
The Regulatory Genome identifier for this sanction document. A hash of the document.

Responses
200
Successful Response

403
Forbidden

404
No sanction document exists with that id.

422
Validation Error


get
/api/v1/customer/sanctions/{sanction_id}
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
{
"sanction_id": "e5bb081b-9b63-5d0c-9479-0edcefbd256f",
"title": "string",
"published": "string",
"timestamp": "2019-08-24T14:15:22Z",
"publishers": [
{}
]
}
Get Sanction File
Get sanction file by id.

Authorizations:
JWTBearer
path Parameters
sanction_id
required
string <uuid> (Sanction Id)
Examples: e5bb081b-9b63-5d0c-9479-0edcefbd256f 000884d4-2464-512c-9dcc-94009d461369 111cbb17-6b6b-5813-f42b-8042d3f63a26
The Regulatory Genome identifier for this sanction document. A hash of the document.

Responses
307
S3 Presigned-url to access document. Expires in 5 minutes

403
Forbidden

404
No sanction document exists with that id.

422
Validation Error


get
/api/v1/customer/sanctions/{sanction_id}/file
Response samples
403422
Content type
application/json

Copy
{
"detail": "User does not have permission to access the requested resource."
}
Controls and Actions
Prerelease Get information about Control Frameworks, Controls, and Actionable Items.

These endpoints are provided as a preview of upcoming changes we're planning to launch soon. The exact schema of responses may change when we release.

Get Controls
Prerelease Get controls within a control framework.

Authorizations:
JWTBearer
path Parameters
framework_id
required
integer (Framework Id)
Examples: 1
A unique id for a Control Framework.

query Parameters
nested	
boolean (Nested)
Default: false
Return controls for framework in a nested/tree structure.

Responses
200
Successful Response

403
Forbidden

404
Data not found.

422
Validation Error


get
/api/v1/customer/frameworks/{framework_id}/controls
Response samples
200403422
Content type
application/json
Example

ControlsResponse
ControlsResponse

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"controls": [
{}
]
}
Get Control
Prerelease Get a control and it's actions.

Authorizations:
JWTBearer
path Parameters
control_id
required
integer (Control Id)
Examples: 1
A unique id for a Control.

Responses
200
Successful Response

403
Forbidden

404
Data not found.

422
Validation Error


get
/api/v1/customer/frameworks/control/{control_id}
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"control": {
"control_id": 1,
"path": "string",
"code": "GOV-02.1",
"name": "string",
"description": "string"
},
"actions": [
{}
]
}
Get Actions
Prerelease Get list of actions associated with a control framework.

Authorizations:
JWTBearer
path Parameters
framework_id
required
integer (Framework Id)
Examples: 1
A unique id for a Control Framework.

Responses
200
Successful Response

403
Forbidden

422
Validation Error


get
/api/v1/customer/frameworks/{framework_id}/actions
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"actions": [
{}
]
}
Get Control Frameworks
Prerelease Get list of available control frameworks.

Authorizations:
JWTBearer
Responses
200
Successful Response

403
Forbidden


get
/api/v1/customer/frameworks/
Response samples
200403
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"control_frameworks": [
{}
]
}
Interrogator
Interrogator Q&A service.

Interrogator Search
Prerelease

Authorizations:
JWTBearer
Request Body schema: application/json
required
query
required
string (Query)
Search query. Must be at least 15 non-whitespace characters long

publishers	
Array of Publishers (objects) or Publishers (null) (Publishers)
If set filters documents to those with at least one publisher in any of the provided publishers or geographical groupings of publishers (jurisdictions)

start_date	
Start Date (string) or Start Date (null) (Start Date)
If set filters documents to those published after (inc) specified date.

end_date	
End Date (string) or End Date (null) (End Date)
If set filters documents to those published before (inc) specified date.

doctypes	
Array of Doctypes (strings) or Doctypes (null) (Doctypes)
Beta
If set filters to documents having specified doctypes.

Responses
200
Successful Response

403
Forbidden

422
Validation Error


post
/api/v1/customer/interrogator/search
Request samples
Payload
Content type
application/json

Copy
Expand allCollapse all
{
"query": "string",
"publishers": [
{},
{},
{}
],
"start_date": null,
"end_date": null,
"doctypes": [
"Laws"
]
}
Response samples
200403422
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"results": [
{}
]
}
Submit interrogator feedback
Authorizations:
JWTBearer
Request Body schema: application/json
required
feedback
required
string (Feedback)
Feedback. Must be at least 5 words long

Responses
200
Successful Response

403
Forbidden

422
Validation Error


post
/api/v1/customer/interrogator/feedback
Request samples
Payload
Content type
application/json

Copy
{
"feedback": "string"
}
Response samples
200403422
Content type
application/json

Copy
null
Initiatives
List all available initiatives
Returns a list of all available initiatives.

Authorizations:
JWTBearer
Responses
200
Successful Response

403
Forbidden

404
No Initiatives currently available.


get
/api/v1/customer/initiatives
Response samples
200403
Content type
application/json

Copy
Expand allCollapse all
{
"status": "ok",
"detail": "string",
"initiatives": [
{}
]
}
© 2024 Regulatory Genome Development Ltd

