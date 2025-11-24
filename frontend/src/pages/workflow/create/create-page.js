import * as React from "react";
import {
  Flashbar,
  BreadcrumbGroup,
  Button,
  Input,
  ContentLayout,
  FileUpload,
  Form,
  FormField,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";
import { API_ENDPOINT, APP_NAME } from "../../../common/constants";
import BaseAppLayout from "../../../components/base-app-layout";
import uploadFiles from "../../../components/upload-files";
import { Amplify, Auth } from "aws-amplify";


function validateClaimId(claimId) {
  if (claimId.length < 5) {
    return "Claim ID must be at least 5 characters long";
  }
  if (claimId.length > 20) {
    return "Claim ID must be less than 20 characters long";
  }
  if (!/^[a-zA-Z0-9-]+$/.test(claimId)) {
    return "Claim ID must only contain letters, numbers and dashes";
  }
  return undefined;
}

function validateFiles(files) {
  if (files.length == 0) {
    return "Please upload at least one file";
  }
  return undefined;
}

export default function Create(token) {
  const [files, setFiles] = React.useState([]);
  const [claimId, setClaimId] = React.useState("");
  const [submitted, setSubmitted] = React.useState(false);
  const [succesfulSubmission, setSuccesfulSubmission] = React.useState(false);
  const [processingStatus, setProcessingStatus] = React.useState("IDLE");

  // Poll for claim status
  React.useEffect(() => {
    if (processingStatus === "PROCESSING" && claimId) {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(
            API_ENDPOINT + "/claim-status/" + claimId,
            {
              method: "GET",
              headers: {
                Authorization: token.token,
              },
            }
          );
          const data = await response.json();
          
          if (data.status === "COMPLETED") {
            setProcessingStatus("COMPLETED");
            clearInterval(interval);
          } else if (data.status === "FAILED") {
            setProcessingStatus("FAILED");
            clearInterval(interval);
          }
        } catch (error) {
          console.error("Status check failed:", error);
        }
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [processingStatus, claimId, token.token]);

  return (
    <BaseAppLayout
      notifications={
        <Flashbar
          items={[
            succesfulSubmission && processingStatus === "PROCESSING" && {
              type: "info",
              loading: true,
              content: "Processing claim " + claimId + "... This may take 2-5 minutes.",
              id: "processing",
            },
            processingStatus === "COMPLETED" && {
              type: "success",
              dismissible: true,
              content: "Claim " + claimId + " processing completed!",
              action: <Button href={"/workflow/review?claim_id=" + claimId}>View Report</Button>,
              id: "completed",
            },
            processingStatus === "FAILED" && {
              type: "error",
              dismissible: true,
              content: "Claim " + claimId + " processing failed. Please try again.",
              id: "failed",
            },
          ].filter(Boolean)}
        />
      }
      breadcrumbs={
        <BreadcrumbGroup
          items={[
            {
              text: APP_NAME,
              href: "/",
            },
            {
              text: "Create a new claim",
              href: "/workflow/create",
            },
          ]}
          expandAriaLabel="Show path"
          ariaLabel="Breadcrumbs"
        />
      }
      content={
        <ContentLayout
          header={<Header variant="h1">Create a new claim</Header>}
        >
          <Form
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  formAction="none"
                  variant="link"
                  disabled={processingStatus === "UPLOADING" || processingStatus === "PROCESSING"}
                  onClick={() => {
                    setSubmitted(false);
                    setClaimId("");
                    setFiles([]);
                    setSuccesfulSubmission(false);
                    setProcessingStatus("IDLE");
                  }}
                >
                  Cancel
                </Button>
                <Button
                  formAction="Submit"
                  variant="primary"
                  disabled={processingStatus === "UPLOADING" || processingStatus === "PROCESSING"}
                  onClick={() => {
                    setSubmitted(true);
                    if (validateClaimId(claimId) || validateFiles(files)) {
                      return;
                    }
                    
                    setProcessingStatus("UPLOADING");
                    uploadFiles(files, claimId, token);
                    
                    fetch(
                      API_ENDPOINT + "/start-claim-processing?claim_id=" + claimId,
                      {
                        method: "GET",
                        headers: {
                          Authorization: token.token,
                          "Access-Control-Allow-Origin": "*",
                          "Access-Control-Allow-Credentials": "true",
                        },
                      }
                    )
                      .then((response) => response.json())
                      .then((data) => {
                        setSuccesfulSubmission(true);
                        setProcessingStatus("PROCESSING");
                      })
                      .catch((error) => {
                        console.error("Failed to start processing:", error);
                        setProcessingStatus("FAILED");
                      });
                  }}
                >
                  {processingStatus === "UPLOADING" ? "Uploading..." : 
                   processingStatus === "PROCESSING" ? "Processing..." : 
                   "Submit"}
                </Button>
              </SpaceBetween>
            }
            header={
              <Header variant="h3">
                File a new claim with supporting documents
              </Header>
            }
          >
            <SpaceBetween size="l">
              <FormField
                label="New Claim ID"
                errorText={submitted && validateClaimId(claimId)}
              >
                <Input
                  value={claimId}
                  disabled={processingStatus === "UPLOADING" || processingStatus === "PROCESSING"}
                  onChange={(event) => setClaimId(event.detail.value)}
                />
              </FormField>
              <br />
              <FormField
                label="Upload files"
                description="Create a new claim case with documents and media files."
                errorText={submitted && validateFiles(files)}
              >
                <FileUpload
                  onChange={({ detail }) => setFiles(detail.value)}
                  value={files}
                  disabled={processingStatus === "UPLOADING" || processingStatus === "PROCESSING"}
                  i18nStrings={{
                    uploadButtonText: (e) =>
                      e ? "Choose files" : "Choose file",
                    dropzoneText: (e) =>
                      e ? "Drop files to upload" : "Drop file to upload",
                    removeFileAriaLabel: (e) => `Remove file ${e + 1}`,
                    limitShowFewer: "Show fewer files",
                    limitShowMore: "Show more files",
                    errorIconAriaLabel: "Error",
                    warningIconAriaLabel: "Warning",
                  }}
                  multiple
                  showFileLastModified
                  showFileSize
                  showFileThumbnail
                  tokenLimit={10}
                  constraintText="PDFs, images or audio files"
                />
              </FormField>
            </SpaceBetween>
          </Form>
        </ContentLayout>
      }
    />
  );
}
