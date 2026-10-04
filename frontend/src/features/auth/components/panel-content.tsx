import heroImage from "@/assets/hero.png";

type Props = {
	title: string;
	description: string;
	features: {
		icon: React.ReactNode;
		title: string;
		description: string;
	}[];
};

const PanelContent = ({ title, description, features }: Props) => {
	return (
		<div className="flex flex-col items-start  gap-4 p-6 ">
			<img src={heroImage} alt="RivalXI" className="-ml-4 w-50" />
			<h1 className="text-3xl font-semibold text-card-foreground">{title}</h1>
			<p className="text-sm text-muted-foreground font-light">{description}</p>
			<div className="flex flex-col gap-6">
				{features.map((feature) => (
					<div key={feature.title} className="flex flex-row items-center gap-2">
						<div className="bg-primary/70 p-3 rounded-sm">{feature.icon}</div>
						<div>
							<h2 className="text-lg font-medium">{feature.title}</h2>
							<p className="text-sm font-light text-muted-foreground">
								{feature.description}
							</p>
						</div>
					</div>
				))}
			</div>
		</div>
	);
};

export default PanelContent;
