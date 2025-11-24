import React, { useState } from "react";
import { API_ENDPOINT } from "../../../common/constants";
import { useParams } from "react-router";
import ClaimReport from "../../../components/claim-report";

import {
  Alert,
  BreadcrumbGroup,
  Container,
  Link,
  Box,
  Button,
  TextFilter,
  Pagination,
  CollectionPreferences,
  ContentLayout,
  Header,
  Table,
  SpaceBetween,
} from "@cloudscape-design/components";
//import { useOnFollow } from "../common/hooks/use-on-follow";
import { APP_NAME } from "../../../common/constants";
import BaseAppLayout from "../../../components/base-app-layout";

const getClaimReport = async (claimId, token) => {
  // add headers to the request including Access-Control-Allow-Origin
  const headers = {
    Authorization: token.token,
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": "true",
  };
  // Invoket API using GET method, adding headres
  const response = await fetch(
    API_ENDPOINT + "/get-claim-report?claimId=" + claimId,
    {
      method: "GET",
      headers: headers,
    }
  );
  //const response = await fetch('https://nihjudrqe2.execute-api.us-west-2.amazonaws.com/get-claim-report?', headers = headers);
  const data = await response.json();
  return data;
};

export default function ReviewDetail(token) {
  //const onFollow = useOnFollow();
  const [claimReport, setClaimReport] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  let params = useParams()
  console.log(params)

  const reload = () => {
    getClaimReport(params.claimId, token).then((data) => setClaimReport(data));
  }


  React.useEffect(() => {
    reload();
  }, []);

  return (
    <BaseAppLayout
      breadcrumbs={
        <BreadcrumbGroup
          //onFollow={onFollow}
          items={[
            {
              text: APP_NAME,
              href: "/",
            },
            {
              text: "Review claims",
              href: "/workflow/review",
            },
            {
              text: params.claimId,
              href: "/workflow/review",
            },
          ]}
          expandAriaLabel="Show path"
          ariaLabel="Breadcrumbs"
        />
      }
      content={
        <ContentLayout header={<Header variant="h1">Claim Report</Header>}>
          <SpaceBetween size="l">
            <ClaimReport claimData={claimReport} token={token}/>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
