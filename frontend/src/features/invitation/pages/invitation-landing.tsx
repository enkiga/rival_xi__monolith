import { Navigate, useParams } from "react-router-dom";

export const INVITATION_STORAGE_KEY = "rivalxi_invitation_code";

const InvitationLandingPage = () => {
	const { token } = useParams<{ token: string }>();

	if (!token) return <Navigate to="/" replace />;
	sessionStorage.setItem(INVITATION_STORAGE_KEY, token);
	return <Navigate to="/" replace />;
};

export default InvitationLandingPage;
