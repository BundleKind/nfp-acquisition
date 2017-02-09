insertions = {
  "statements": {
    "nfp": """
      INSERT INTO nfp (
        ein,
        name,
        mission,
        activity,
        description,
        doing_business_as1,
        doing_business_as2,
        doing_business_as3,
        is_501c3,
        year_formed
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """,
    "year_terminated": "INSERT INTO year_terminated (ein, year) VALUES (?, ?);",
    "tax_return": """
      INSERT INTO tax_return (
        ein,
        tax_year,
        gross_receipts_lt_25k,
        total_employees,
        total_volunteers,
        py_total_revenue,
        cy_total_revenue,
        gross_receipts,
        assets_at_beginning_of_year,
        assets_at_end_of_year,
        liabilities_at_beginning_of_year,
        liabilities_at_end_of_year,
        total_program_service_expenses,
        does_political_campain_activity,
        does_lobbying,
        does_professional_fundrasing,
        does_grants_to_organizations,
        does_grants_to_individuals
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """,
    "latest_contact_info": """
      INSERT INTO latest_contact_info (
        ein,
        url,
        phone_num,
        business_addr_line_1,
        business_addr_line_2,
        business_addr_city,
        business_addr_state,
        business_addr_zip,
        principal_officer,
        principal_officer_addr_line_1,
        principal_officer_addr_line_2,
        principal_officer_city,
        principal_officer_state,
        principal_officer_zip)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """,
    "latest_contact_info_geo_update": """
        UPDATE OR IGNORE latest_contact_info
        SET (lon, lat) = (?, ?) WHERE ein = ?;
    """,
    "tag": "INSERT INTO tag (name) VALUES(?)",
    "tag_lookup": """
        INSERT INTO tag_lookup (tag_id, ein)
        SELECT (id, ?) FROM tag WHERE tag.name = ?
    """
  },
  "columns": {
    "nfp": [
        "EIN", "BusinessName",
        "MissionDesc", "ActivityOrMissionDesc", "Desc",
        "Doing Business As Name 1", "Doing Business As Name 2", "Doing Business As Name 3",
        "Is_501c3", "FormationYr"
    ],
    "year_terminated": ["EIN", "TaxYr"],
    "tax_return": [
        "EIN", "TaxYr", "Gross Receipts are under $25k",
        "TotalEmployeeCnt", "TotalVolunteersCnt", "PYTotalRevenueAmt", "CYTotalRevenueAmt",
        "GrossReceiptsAmt",
        "TotalAssetsBOYAmt", "TotalAssetsEOYAmt", "TotalLiabilitiesBOYAmt", "TotalLiabilitiesEOYAmt",
        "TotalProgramServiceExpensesAmt",
        "PoliticalCampaignActyInd", "LobbyingActivitiesInd", "ProfessionalFundraisingInd",
        "GrantsToOrganizationsInd", "GrantsToIndividualsInd"
    ],
    "tax_return_cast_to_int": [
        "Gross Receipts are under $25k",
        "PoliticalCampaignActyInd", "LobbyingActivitiesInd", "ProfessionalFundraisingInd",
        "GrantsToOrganizationsInd", "GrantsToIndividualsInd"
    ],
    "latest_contact_info": [
        "EIN", "WebsiteAddress", "PhoneNum",
        "AddressLine1", "AddressLine2", "City", "State", "ZIPCd",
        "PrincipalOfficerNm",
        "Officer Address Line1", "Officer Address Line2",
        "Officer Address City", "Officer Address State", "Officer Address Postal Code"
    ],
    "latest_contact_info_geo_update": ["lat_lon", "id"],
  }
}
