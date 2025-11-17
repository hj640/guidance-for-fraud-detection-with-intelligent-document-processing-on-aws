import { 
  REGION,
  COGNITO_USER_POOL_ID,
  COGNITO_USER_POOL_CLIENT_ID
} from "./common/constants";

const awsConfig = {
  Auth: {
    region: REGION,
    userPoolId: COGNITO_USER_POOL_ID,
    userPoolWebClientId: COGNITO_USER_POOL_CLIENT_ID,
    mandatorySignIn: false,
    authenticationFlowType: 'USER_SRP_AUTH'
  }
};

export default awsConfig;