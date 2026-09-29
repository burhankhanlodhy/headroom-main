import { Navigate, Route, Routes } from "react-router-dom";
import { AuroraBackground, FullPageCenter, Shell } from "./components/layout";
import Profile from "./pages/Profile";
import ApiKeys from "./pages/ApiKeys";
import Usage from "./pages/Usage";
import Subscriptions from "./pages/Subscriptions";
import Documentation from "./pages/Documentation";
import SignOut from "./pages/SignOut";

export default function App() {
  return (
    <>
      <AuroraBackground />
      <Routes>
        <Route element={<Shell />}>
          <Route index element={<Profile />} />
          <Route path="keys" element={<ApiKeys />} />
          <Route path="usage" element={<Usage />} />
          <Route path="subscriptions" element={<Subscriptions />} />
          <Route path="docs" element={<Documentation />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
        <Route
          path="/signout"
          element={
            <FullPageCenter>
              <SignOut />
            </FullPageCenter>
          }
        />
      </Routes>
    </>
  );
}
