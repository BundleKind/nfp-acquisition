"""Pull IRS Form 990 data for given states from the Amazon S3 bucket.

The EINs are mapped to URLs via the index files that can be pulled
from the S3 bucket, like this example:
  https://s3.amazonaws.com/irs-form-990/201541349349307794_public.xml.

To get the indexes you need, run the commands:
  aws s3 cp s3://irs-form-990/index_2016.json data/index_2016.json
  aws s3 cp s3://irs-form-990/index_2015.json data/index_2015.json

Documentaton is at:
    https://aws.amazon.com/public-datasets/irs-990/
"""
import csv
import difflib
import glob
import json
import os
import requests
import xml.etree.ElementTree as ET


ns = dict(irs="http://www.irs.gov/efile")

def get(xpath):
    result = root.find(xpath, ns)
    if result is not None:
        return ' '.join(result.text.strip().split())
    else:
        return ''

def getsubgroup(xpath):
    result = root.find(xpath, ns)
    if result is not None:
        return ' '.join(' '.join(result.itertext()).strip().split())
    else:
        return ''


def try_receipts_less_than_25k():
    try:
        amt = float(get('.//irs:ReturnData//irs:GrossReceiptsAmt'))
    except ValueError:
        return False
    return amt < 25000
        

getters = [
    ('EIN', lambda: get('.//irs:EIN')),
    ('TaxYr', lambda: get('.//irs:ReturnHeader//irs:TaxYr')),
    ('BusinessName', lambda: getsubgroup('.//irs:Filer//irs:BusinessName')),
    ('Gross Receipts are under $25k', try_receipts_less_than_25k),
    ('Is Terminated', lambda: ''),
    ('Tax Period Begins', lambda: get('.//irs:TaxPeriodBeginDt')),
    ('Tax Period Ends', lambda: get('.//irs:TaxPeriodEndDt')),
    ('WebsiteAddress', lambda: get('.//irs:ReturnData//irs:WebsiteAddressTxt')),
    ('PrincipalOfficerNm', lambda: get('.//irs:ReturnData//irs:PrincipalOfficerNm')),
    ('Officer Address Line1', lambda: get('.//irs:ReturnData//irs:USAddress//irs:AddressLine1Txt')),
    ('Officer Address Line2', lambda: get('.//irs:ReturnData//irs:USAddress//irs:AddressLine2Txt')),
    ('Officer Address City', lambda: get('.//irs:ReturnData//irs:USAddress//irs:CityNm')),
    ('Officer Address Province', lambda: ''),
    ('Officer Address State', lambda: get('.//irs:ReturnData//irs:USAddress//irs:StateAbbreviationCd')),
    ('Officer Address Postal Code', lambda: get('.//irs:ReturnData//irs:USAddress//irs:ZIPCd')),
    ('Officer Address Country', lambda: 'USA'),
    ('AddressLine1', lambda: get('.//irs:Filer//irs:USAddress//irs:AddressLine1Txt')),
    ('AddressLine2', lambda: get('.//irs:Filer//irs:USAddress//irs:AddressLine2Txt')),
    ('City', lambda: get('.//irs:Filer//irs:USAddress//irs:CityNm')),
    ('Province', lambda: ''),
    ('State', lambda: get('.//irs:Filer//irs:USAddress//irs:StateAbbreviationCd')),
    ('ZIPCd', lambda: get('.//irs:Filer//irs:USAddress//irs:ZIPCd')),
    ('Organization Address Country', lambda: 'USA'),
    ('Doing Business As Name 1', lambda: ''),  # I just don't know the XML tag for this
    ('Doing Business As Name 2', lambda: ''),
    ('Doing Business As Name 3', lambda: ''),
    ('Form', lambda: '990'),
    ('GrossReceiptsAmt', lambda: get('.//irs:ReturnData//irs:GrossReceiptsAmt')),
    ('Is_501c3', lambda: get('.//irs:ReturnData//irs:Organization501c3Ind')),
    ('PhoneNum', lambda: get('.//irs:Filer//irs:PhoneNum')),
    ('ActivityOrMissionDesc', lambda: get('.//irs:ReturnData//irs:ActivityOrMissionDesc')),
    ('FormationYr', lambda: get('.//irs:ReturnData//irs:FormationYr')),
    ('LegalDomicileStateCd', lambda: get('.//irs:ReturnData//irs:LegalDomicileStateCd')),
    ('TotalEmployeeCnt', lambda: get('.//irs:ReturnData//irs:TotalEmployeeCnt')),
    ('TotalVolunteersCnt', lambda: get('.//irs:ReturnData//irs:TotalVolunteersCnt')),
    ('PYTotalRevenueAmt', lambda: get('.//irs:ReturnData//irs:PYTotalRevenueAmt')),
    ('CYTotalRevenueAmt', lambda: get('.//irs:ReturnData//irs:CYTotalRevenueAmt')),
    ('PYSalariesCompEmpBnftPaidAmt', lambda: get('.//irs:ReturnData//irs:PYSalariesCompEmpBnftPaidAmt')),
    ('CYSalariesCompEmpBnftPaidAmt', lambda: get('.//irs:ReturnData//irs:CYSalariesCompEmpBnftPaidAmt')),
    ('TotalAssetsBOYAmt', lambda: get('.//irs:ReturnData//irs:TotalAssetsBOYAmt')),
    ('TotalAssetsEOYAmt', lambda: get('.//irs:ReturnData//irs:TotalAssetsEOYAmt')),
    ('TotalLiabilitiesBOYAmt', lambda: get('.//irs:ReturnData//irs:TotalLiabilitiesBOYAmt')),
    ('TotalLiabilitiesEOYAmt', lambda: get('.//irs:ReturnData//irs:TotalLiabilitiesEOYAmt')),
    ('TotalProgramServiceExpensesAmt', lambda: get('.//irs:ReturnData//irs:TotalProgramServiceExpensesAmt')),
    ('PoliticalCampaignActyInd', lambda: get('.//irs:ReturnData//irs:PoliticalCampaignActyInd')),
    ('LobbyingActivitiesInd', lambda: get('.//irs:ReturnData//irs:LobbyingActivitiesInd')),
    ('SubjectToProxyTaxInd', lambda: get('.//irs:ReturnData//irs:SubjectToProxyTaxInd')),
    ('MoreThan5000KToOrgInd', lambda: get('.//irs:ReturnData//irs:MoreThan5000KToOrgInd')),
    ('MoreThan5000KToIndividualsInd', lambda: get('.//irs:ReturnData//irs:MoreThan5000KToIndividualsInd')),
    ('ProfessionalFundraisingInd', lambda: get('.//irs:ReturnData//irs:ProfessionalFundraisingInd')),
    ('GrantsToOrganizationsInd', lambda: get('.//irs:ReturnData//irs:GrantsToOrganizationsInd')),
    ('GrantsToIndividualsInd', lambda: get('.//irs:ReturnData//irs:GrantsToIndividualsInd')),
    ('MissionDesc', lambda: get('.//irs:ReturnData//irs:MissionDesc')),
    ('Desc', lambda: get('.//irs:ReturnData//irs:Desc')),
]
header = [g[0] for g in getters]


ein_lookups = {}
details = json.loads(open(os.path.join('data', 'index_2015.json')).read())
for row in details['Filings2015']:
    ein_lookups[row['EIN']] = row['URL']

details = json.loads(open(os.path.join('data', 'index_2016.json')).read())
for row in details['Filings2016']:
    ein_lookups[row['EIN']] = row['URL']

del details  # for memory


# ---------- set up for pulling the AWS data --------- #
aws990s = os.path.join('data', 'form990')
if not os.path.exists(aws990s):
    os.makedirs(aws990s)


desired_cities = (
    #('Seattle', 'WA'), ) #,
    ('New York', 'NY'),
    ('Atlanta', 'GA'),
    ('Chicago', 'IL'),
    ('Detroit', 'MI'),
    ('Missoula', 'MT'))

desired_states = ('NY', 'GA', 'IL', 'MI', 'MT')

#for city, state in desired_cities:
for state in desired_states:
    #print('Working on {}, {}'.format(city, state))
    print('Working on', state)
    possible_files = glob.glob(os.path.join('data', 'pub78',state, '*'))
    #possible_cities = [os.path.basename(f)[:-4].lower() for f in possible_files]
    #match = difflib.get_close_matches(city.lower(), possible_cities, n=1)[0]
    #idx = possible_cities.index(match)
    #filename = possible_files[idx]
    if not os.path.exists(os.path.join(aws990s, state)):
        os.makedirs(os.path.join(aws990s, state))
    for filename in possible_files:
        print('.....', filename)
        with open(filename) as list_of_eins:
            eins = [line.split('\t', 1)[0] for line in list_of_eins]
        #if not os.path.exists(os.path.join(aws990s, state)):
        #    os.makedirs(os.path.join(aws990s, state))
        city = os.path.basename(filename)    
        with open(os.path.join(aws990s, state, city), 'w') as csvfile:
            data_writer = csv.writer(csvfile, delimiter='\t')
            data_writer.writerow(header)
            counter = 0
            for ein in eins:
                if ein in ein_lookups:
                    url = ein_lookups[ein]
                    response = requests.get(url)
                    root = ET.fromstring(response.content.decode('utf-8'))
                    data_writer.writerow([g[1]() for g in getters])
                    counter += 1
                    if counter %250 == 0:
                        print(counter)
