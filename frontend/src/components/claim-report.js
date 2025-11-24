import React from 'react';
import {
  Alert,
  Grid,
  Container,
  Link,
  Box,
  StatusIndicator,
  Badge,
  KeyValuePairs,
  ContentLayout,
  Header,
  Table,
  SpaceBetween,
  TextContent,
} from "@cloudscape-design/components";
import { API_ENDPOINT } from "../common/constants";

const { useEffect } = React;

function BulletList({ items }) {
  return (
    <div>
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  );
}


export default function ClaimReport(props) {
  const claimData = props.claimData;
  const token = props.token;
  useEffect(() => {
    const handleResizeObserverError = (e) => {
      if (e.message === 'ResizeObserver loop completed with undelivered notifications.') {
        e.stopImmediatePropagation();
      }
    };
    window.addEventListener('error', handleResizeObserverError);
    return () => window.removeEventListener('error', handleResizeObserverError);
  }, []);
  console.log("CLAIM DATA", claimData);
  if (claimData.length == 0) {
    return "Loading";
  }

  return (
    <div>
      <ContentLayout
        header={
          <SpaceBetween size="s">
            <Header
              variant="h1"
              description={
                " Policy No: " +
                claimData.policyNo +
                "\t|\tClaim Date: " +
claimData.claimInfo.claimDate
              }
            >
              ID: {claimData.claimId}
            </Header>
            {claimData.fraudWarning && (
              <Alert type="warning"><strong>{claimData.suspicion}</strong></Alert>
            )}
          </SpaceBetween>
        }
      >
        <SpaceBetween size="l">
          <Container
            header={<Header variant="h2">AI Risk Assessment</Header>}
          >
            <SpaceBetween size="m">
              <KeyValuePairs
                columns={3}
                items={[
                  {
                    label: "Risk Score",
                    value: (
                      <Badge 
                        color={claimData.riskScore >= 8 ? "red" : claimData.riskScore >= 4 ? "grey" : "green"}
                      >
                        {claimData.riskScore || 'N/A'}/10
                      </Badge>
                    )
                  },
                  {
                    label: "Recommended Action", 
                    value: (
                      <Badge 
                        color={claimData.recommendedAction?.startsWith("DENY") ? "red" : 
                              claimData.recommendedAction?.startsWith("INVESTIGATE") ? "grey" : "green"}
                      >
                        {claimData.recommendedAction?.split(' - ')[0] || 'N/A'}
                      </Badge>
                    )
                  },
                  {
                    label: "Fraud Warning",
                    value: claimData.fraudWarning ? "YES" : "NO"
                  }
                ]}
              />

              
              {claimData.inconsistencies && claimData.inconsistencies.length > 0 && (
                <Alert type="error" header="Inconsistencies Found">
                  {claimData.inconsistencies.map((item, index) => (
                    <div key={index}>• {item}</div>
                  ))}
                </Alert>
              )}
              
              <Box variant="h4">AI Analysis</Box>
              <TextContent><strong>Observations:</strong> {claimData.observations}</TextContent>
              <TextContent><strong>Insights:</strong> {claimData.insights}</TextContent>
            </SpaceBetween>
          </Container>

          <SpaceBetween size="s">
            <Container
              header={
                <Header
                  variant="h2"
                  description={claimData.incidentInfo.description}
                >
                  Claim Info
                </Header>
              }
            >
              <SpaceBetween size="s">
                <KeyValuePairs
                  columns={2}
                  items={[
                    {
                      label: "Claim date",
                      value: claimData.claimInfo.claimDate,
                    },
                    {
                      label: "Incident date",
                      value: claimData.incidentInfo.date,
                    },
                    {
                      label: "Estimated Value of Damage",
                      value: typeof claimData.claimInfo.estimatedDamageValue === 'object' ? JSON.stringify(claimData.claimInfo.estimatedDamageValue) : claimData.claimInfo.estimatedDamageValue
                    },
                    {
                      label: "Estimated Cost of Repair",
                      value: typeof claimData.claimInfo.estimatedRepairCost === 'object' ? JSON.stringify(claimData.claimInfo.estimatedRepairCost) : claimData.claimInfo.estimatedRepairCost
                    },
                    {
                      label: "Agent Contact",
                      value: claimData.policyInfo.contact,
                    },
                    {
                      label: "Insurance Company",
                      value: claimData.policyInfo.insuranceCompany,
                    },
                  ]}
                />
              </SpaceBetween>
            </Container>
          </SpaceBetween>

          <Container header={<Header variant="h2">Claimed Property</Header>}>
            <SpaceBetween size="s">
              <KeyValuePairs
                columns={2}
                items={[
                  {
                    label: "Address",
                    value: claimData.propertyInfo.address,
                  },
                  {
                    label: "Type",
                    value: claimData.propertyInfo.type,
                  },
                ]}
              />
              {typeof claimData.propertyInfo.additionalInfo === 'object' ? (
                <KeyValuePairs
                  columns={2}
                  items={[
                    {
                      label: "Damaged Value",
                      value: claimData.propertyInfo.additionalInfo.damagedValue || 'N/A'
                    },
                    {
                      label: "Previous Claim",
                      value: claimData.propertyInfo.additionalInfo.previousClaim ? 'Yes' : 'No'
                    },
                    {
                      label: "Repair Cost",
                      value: claimData.propertyInfo.additionalInfo.repairCost || 'N/A'
                    }
                  ]}
                />
              ) : (
                <Box>{claimData.propertyInfo.additionalInfo}</Box>
              )}
              <Box variant="h4" padding={{ top: "m" }}>
                Description of Damage
              </Box>
              <TextContent>{claimData.descriptionOfDamage}</TextContent>
            </SpaceBetween>
          </Container>
          <Container
            header={
              <Header
                variant="h2"
                //description="Claim details"
              >
                Insurance Policy
              </Header>
            }
          >
            <SpaceBetween size="s">
              <KeyValuePairs
                columns={2}
                items={[
                  {
                    label: "Policy Holder Name",
                    value: claimData.policyHolderDetails.name,
                  },
                  {
                    label: "Policy Address",
                    value: claimData.policyHolderDetails.address,
                  },
                  { 
                    label: "Policy No",
                    value: claimData.policyNo,
                  },
                  {
                    label: "Agent",
                    value: claimData.policyInfo.agentName,
                  },
                  {
                    label: "Contact",
                    value: claimData.policyInfo.contact,
                  },
                  {
                    label: "Insurance Company",
                    value: claimData.policyInfo.insuranceCompany,
                  },
                ]}
              />
            </SpaceBetween>
          </Container>

          <Container
            header={
              <Header
                variant="h2"
                //description="Claim details"
              >
                Proofs of Damage
              </Header>
            }
          >
            <SpaceBetween size="s">
              <Box variant="h4" padding={{ top: "m" }}>
                Customer Call Records
              </Box>
              <Box variant="p">{claimData.callRecordingsSummary}</Box>
              <Box variant="h4" padding={{ top: "m" }}>
                Submitted documents
              </Box>
              <Table
                renderAriaLive={({ firstIndex, lastIndex, totalItemsCount }) =>
                  `Displaying items ${firstIndex} to ${lastIndex} of ${totalItemsCount}`
                }
                items={claimData.proofOfDamage}
                columnDefinitions={[
                  {
                    id: "type",
                    header: "Type",
                    width: 100,
                    cell: (item) => item.type,
                  },
                  {
                    id: "description",
                    header: "Description",
                    width: 550,
                    cell: (item) => item.description,
                  },
                  {
                    id: "validity",
                    header: "Validity",
                    width: 120,
                    cell: (item) => item.validity,
                  },
                  {
                    id: "link",
                    header: "Link",
                    cell: (item) => {
                      if (item.fileName) {
                        return (
                          <Link 
                            href="#" 
                            onFollow={async (e) => {
                              e.preventDefault();
                              try {
                                const response = await fetch(`${API_ENDPOINT}/view-file?claimId=${claimData.claimId}&fileName=${item.fileName}`, {
                                  headers: { 'Authorization': token.token }
                                });
                                const result = await response.json();
                                const data = result.body ? JSON.parse(result.body) : result;
                                if (data.url) window.open(data.url, '_blank');
                              } catch (error) {
                                console.error('Error fetching file URL:', error);
                              }
                            }}
                          >
                            View Image
                          </Link>
                        );
                      }
                      return item.link ? (
                        <Link href={item.link} target="_blank">
                          {item.link}
                        </Link>
                      ) : 'N/A';
                    },
                  },
                ]}
                columnDisplay={[
                  { id: "type", visible: true },
                  { id: "description", visible: true },
                  { id: "validity", visible: true },
                  { id: "link", visible: true },
                ]}
                resizableColumns
                wrapLines
              />
            </SpaceBetween>
            <Box variant="h4" padding={{ top: "m" }}>
              Witness
            </Box>
            <KeyValuePairs
              columns={2}
              items={[
                {
                  label: "Name",
                  value: claimData.witness.name,
                },
                {
                  label: "Contact",
                  value: claimData.policyHolderDetails.phoneNumber,
                },
                {
                  label: "Relationship",
                  value: "Witness",
                },
                {
                  label: "Statement",
                  value: claimData.witness.statement,
                },
              ]}
            />
          </Container>
          <Container
            header={
              <Header
                variant="h2"
                //description="Claim details"
              >
                Cost Estimation by Vendor
              </Header>
            }
          >
            <Table
              renderAriaLive={({ firstIndex, lastIndex, totalItemsCount }) =>
                `Displaying items ${firstIndex} to ${lastIndex} of ${totalItemsCount}`
              }
              items={claimData.estimatesOfTotalCostToRepairPerEachVendor}
              columnDefinitions={[
                {
                  id: "vendor",
                  header: "Vendor Name",
                  width: 200,
                  cell: (item) => item.vendorName,
                },
                {
                  id: "totalcost",
                  header: "Total Cost",
                  width: 200,
                  cell: (item) => item.totalCost,
                },
                {
                  id: "scope",
                  header: "Scope of Work",
                  width: 300,
                  cell: (item) => {
                    if (Array.isArray(item.scopeOfWork)) {
                      return (
                        <div>
                          {item.scopeOfWork.map((work, index) => {
                            const parts = work.split(' - ');
                            return (
                              <div key={index}>{parts[0]}</div>
                            );
                          })}
                        </div>);
                      } 
                      return 'N/A';
                    }, 
                  },
                  {
                    id: "cost",
                    header: "Cost",
                    width: 150,
                    cell: (item) => {
                      if (Array.isArray(item.scopeOfWork)) {
                        return (
                          <div>
                            {item.scopeOfWork.map((work, index) => {
                              const parts = work.split(' - ');
                              return (
                                <div key={index}>${parts[1] || '0'}</div>
                              );
                            })}
                          </div>);
                        } 
                        return 'N/A';
                      }, 
                    },
                  ]}
              columnDisplay={[
                { id: "vendor", visible: true },
                { id: "totalcost", visible: true },
                { id: "scope", visible: true },
                { id: "cost", visible: true },
              ]}
              resizableColumns
              wrapLines
            />
          </Container>
        </SpaceBetween>
      </ContentLayout>
    </div>
  );
}
