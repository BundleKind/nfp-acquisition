CREATE TABLE IF NOT EXISTS nfp (
    ein TEXT PRIMARY KEY ON CONFLICT REPLACE,
    name TEXT,
    mission TEXT,
    activity TEXT,
    description TEXT,
    doing_business_as1 TEXT,
    doing_business_as2 TEXT,
    doing_business_as3 TEXT,
    is_501c3 INTEGER,
    year_formed INTEGER
);

CREATE TABLE IF NOT EXISTS year_terminated (
    ein TEXT NOT NULL,
    year INTEGER NOT NULL,
    FOREIGN KEY (ein) REFERENCES nfp(ein)
);

CREATE TABLE IF NOT EXISTS tax_return (
    ein TEXT NOT NULL,
    tax_year INTEGER NOT NULL,
    gross_receipts_lt_25k INTEGER,
    total_employees INTEGER,
    total_volunteers INTEGER,
    py_total_revenue NUM,
    cy_total_revenue NUM,
    gross_receipts NUM,
    assets_at_beginning_of_year NUM,
    assets_at_end_of_year NUM,
    liabilities_at_beginning_of_year NUM,
    liabilities_at_end_of_year NUM,
    total_program_service_expenses NUM,
    does_political_campain_activity INTEGER,
    does_lobbying INTEGER,
    does_professional_fundrasing INTEGER,
    does_grants_to_organizations INTEGER,
    does_grants_to_individuals INTEGER,
    FOREIGN KEY (ein) REFERENCES nfp(ein)
);

CREATE TABLE IF NOT EXISTS latest_contact_info (
    ein TEXT NOT NULL,
    url TEXT,
    phone_num TEXT,
    business_addr_line_1 TEXT,
    business_addr_line_2 TEXT,
    business_addr_city TEXT,
    business_addr_state TEXT,
    business_addr_zip TEXT,
    principal_officer TEXT,
    principal_officer_addr_line_1 TEXT,
    principal_officer_addr_line_2 TEXT,
    principal_officer_city TEXT,
    principal_officer_state TEXT,
    principal_officer_zip TEXT,
    lon NUM,
    lat NUM
);

CREATE TABLE IF NOT EXISTS tag (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tag_lookup (
  tag_id INTEGER NOT NULL,
  ein TEXT NOT NULL,
  FOREIGN KEY (tag_id) REFERENCES tag(id),
  FOREIGN KEY (ein) REFERENCES nfp(ein),
  UNIQUE (tag_id, ein) ON CONFLICT REPLACE
);


CREATE VIEW IF NOT EXISTS ein_to_tag AS
  SELECT ein, tag.name AS tag
  FROM tag_lookup AS tl
  JOIN tag ON tl.tag_id = tag.id;

CREATE VIEW IF NOT EXISTS ein_to_joined_tags AS
  SELECT ein, group_concat(tag) AS joined_tags
  FROM ein_to_tag
  GROUP BY ein;

CREATE VIEW IF NOT EXISTS combined_data AS
  SELECT 
    tr.*,
    nfp.name,
    nfp.mission,
    nfp.activity,
    nfp.description,
    nfp.doing_business_as1 AS dba,
    etjt.joined_tags,
    nfp.is_501c3,
    nfp.year_formed,
    yt.year AS year_terminated,
    lci.url,
    lci.phone_num,
    lci.business_addr_city AS city,
    lci.business_addr_state AS state,
    lci.business_addr_zip AS zip,
    lci.principal_officer,
    lci.principal_officer_city,
    lci.principal_officer_state,
    lci.principal_officer_zip,
    lci.lon,
    lci.lat
FROM nfp
LEFT JOIN year_terminated AS yt ON nfp.ein = yt.ein
LEFT JOIN tax_return AS tr ON nfp.ein = tr.ein
LEFT JOIN latest_contact_info AS lci ON nfp.ein = lci.ein
LEFT JOIN ein_to_joined_tags AS etjt ON nfp.ein = etjt.ein;
