import { Link } from "react-router-dom";

const NotFoundPage = () => {
	return (
		<div>
			Not Found
			<Link to="/">Go back to home</Link>
		</div>
	);
};

export default NotFoundPage;
