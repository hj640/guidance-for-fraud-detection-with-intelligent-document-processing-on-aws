import { HashRouter, BrowserRouter, Routes, Route } from "react-router-dom";
import GlobalHeader from "./components/global-header";
import HomePage from "./pages/home";
import Create from "./pages/workflow/create/create-page";
import Review from "./pages/workflow/review/review-page";
import ReviewDetail from "./pages/workflow/review/review-detail-page";
import { Amplify, Auth } from "aws-amplify";
import "@aws-amplify/ui-react/styles.css";
import { Authenticator } from "@aws-amplify/ui-react";
import awsConfig from "./aws-config";
import NotFound from "./pages/not-found";
import { USE_BROWSER_ROUTER } from "./common/constants";

Amplify.configure(awsConfig);

export default function App() {
  const Router = USE_BROWSER_ROUTER ? BrowserRouter : HashRouter;

  return (
    <div style={{ height: "100%" }}>
      <Authenticator
      initialState="signIn"
      components={{
        SignUp: {
          FormFields() {
            return (
              <>
                <Authenticator.SignUp.FormFields />
                <div>
                  <label>Email</label><br/>
                  <input
                    type="email"
                    name="email"
                    placeholder="Enter your email"
                  />
                </div>
              </>
            );
          },
        },
      }}
    >
        {({ signOut, user }) => {
          const token = user?.signInUserSession?.idToken?.jwtToken;
          return (
              <Router>
                <GlobalHeader signOut={signOut}/>
                <div style={{ height: "56px", backgroundColor: "#000716" }}>&nbsp;</div>
                <div>
                  <Routes>
                    <Route index path="/" element={<HomePage />} />
                    <Route index path="/workflow/create" element={<Create token={token}/>} />
                    <Route index path="/workflow/review" element={<Review token={token}/>} />
                    <Route path = "/workflow/review/:claimId" element={<ReviewDetail token={token}/>}/>
                    <Route path="*" element={<NotFound />} />
                </Routes>
              </div>
            </Router>
          );
        }}
      </Authenticator>
    </div>
  );
}