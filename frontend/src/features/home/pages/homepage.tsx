import HomeIntroSection from "../components/home-intro";
import LeagueList from "../components/league-list";

const HomePage = () => {
	return (
		<section className="py-10 flex flex-col gap-6">
			<HomeIntroSection />
			<LeagueList />
		</section>
	);
};

export default HomePage;
