import LeagueDialog from "../components/league-dialog";
import LeagueList from "../components/league-list";

const HomePage = () => {
	return (
		<section className="pt-8 flex flex-col gap-6">
			<div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
				<div className="flex gap-1.5 flex-col">
					<h2 className="text-primary text-3xl font-semibold">
						Your Rival XI Leagues
					</h2>
					<p className="text-sm text-muted-foreground">
						Manage and track your Rival XI leagues all in one place.
					</p>
				</div>
				<LeagueDialog />
			</div>
			<LeagueList />
		</section>
	);
};

export default HomePage;
