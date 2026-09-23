import type React from "react";
import heroImage from "@/assets/hero.png";
import SectionWrapper from "@/components/reusable/section-wrapper"; 


type Props = {
	children: React.ReactNode;
};

const AuthWrapper = ({ children }: Props) => {
	return (
		<section className="bg-primary">
			<SectionWrapper className="flex flex-col min-h-dvh items-center justify-center py-10">
				<img src={heroImage} alt="RivalXI" className="mx-auto mb-7 w-40" />
				{children}
			</SectionWrapper>
		</section>
	);
};

export default AuthWrapper;
