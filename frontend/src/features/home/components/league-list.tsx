import { UserGroup } from "lucide-react";
import { useState } from "react";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import { useGetLeaguesEndpointApiV1LeaguesGet } from "@/api/leagues/leagues";
import SectionWrapper from "@/components/reusable/section-wrapper";
import { Card } from "@/components/ui/card";
import {
	Pagination,
	PaginationContent,
	PaginationItem,
	PaginationNext,
	PaginationPrevious,
} from "@/components/ui/pagination";
import type { ApiError } from "@/config/api/api-error";
import type { AuthUserResponse, LeagueListResponse } from "@/types/schemas";
import LeagueCard from "./league-card";
import LeagueDialog from "./league-dialog";

const PAGE_SIZE = 10;
const SKELETON_CARDS = ["first", "second", "third"];

const LeagueList = () => {
	const [page, setPage] = useState(1);
	const userQuery = useGetMeEndpointApiV1AuthMeGet<AuthUserResponse, ApiError>({
		query: {
			select: (response) => {
				const payload = response as unknown as
					| AuthUserResponse
					| { data: AuthUserResponse };
				return "data" in payload ? payload.data : payload;
			},
		},
	});
	const leaguesQuery = useGetLeaguesEndpointApiV1LeaguesGet<
		LeagueListResponse,
		ApiError
	>(
		{ page, page_size: PAGE_SIZE },
		{
			query: {
				select: (response) => {
					const payload = response as unknown as
						| LeagueListResponse
						| { data: LeagueListResponse };
					return "data" in payload ? payload.data : payload;
				},
			},
		},
	);

	if (leaguesQuery.isPending) {
		return (
			<div className="grid gap-4 lg:grid-cols-3">
				{SKELETON_CARDS.map((card) => (
					<LeagueCard key={card} isLoading />
				))}
			</div>
		);
	}

	if (leaguesQuery.isError) {
		return (
			<p className="text-sm text-destructive" role="alert">
				{leaguesQuery.error.message}
			</p>
		);
	}

	if (!leaguesQuery.data.items.length) {
		return (
			<SectionWrapper>
				<Card className="px-4 border border-dashed border-fpl-pink flex flex-col lg:items-center text-center p-6">
					<div className="bg-primary/50 p-4 rounded-full mx-auto">
						<UserGroup />
					</div>
					<h3 className="text-3xl font-semibold">Ready to start a rivalry?</h3>
					<p className="text-sm text-muted-foreground">
						Create a new league and invite your friends to compete each game
						week.
					</p>
					<LeagueDialog />
				</Card>
			</SectionWrapper>
		);
	}

	return (
		<SectionWrapper className="flex flex-col gap-4">
			<div className="flex flex-col gap-4">
				{leaguesQuery.data.items.map((league) => (
					<LeagueCard
						key={league.slug}
						league={league}
						isOwner={
							userQuery.data?.fpl_account?.fpl_entry_id ===
							league.owner.fpl_entry_id
						}
					/>
				))}
			</div>

			{leaguesQuery.data.pages > 1 && (
				<Pagination>
					<PaginationContent className="w-full justify-between">
						<PaginationItem>
							<PaginationPrevious
								href="#"
								aria-disabled={page === 1}
								className={page === 1 ? "pointer-events-none opacity-50" : ""}
								onClick={(event) => {
									event.preventDefault();
									if (page > 1) {
										setPage((current) => Math.max(1, current - 1));
									}
								}}
							/>
						</PaginationItem>
						<PaginationItem>
							<PaginationNext
								href="#"
								aria-disabled={page >= leaguesQuery.data.pages}
								className={
									page >= leaguesQuery.data.pages
										? "pointer-events-none opacity-50"
										: ""
								}
								onClick={(event) => {
									event.preventDefault();
									if (page < leaguesQuery.data.pages) {
										setPage((current) => current + 1);
									}
								}}
							/>
						</PaginationItem>
					</PaginationContent>
				</Pagination>
			)}
		</SectionWrapper>
	);
};

export default LeagueList;
