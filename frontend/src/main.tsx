import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { RouterProvider } from "react-router-dom";
import AppProviders from "@/layouts/app-providers";
import { router } from "./routes/index.tsx";

// biome-ignore lint/style/noNonNullAssertion: Non-null assertion for root element
createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<AppProviders>
			<RouterProvider router={router} />
		</AppProviders>
	</StrictMode>,
);
